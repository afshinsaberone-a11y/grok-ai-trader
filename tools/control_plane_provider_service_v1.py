"""Fail-closed polling entry point for the external ForexAI admission Provider.

This process only consumes a real, externally signed source packet and invokes
the existing one-shot issuer. It never fabricates source evidence, initializes
the production registry, touches MT5, enables the Kill Switch, or places orders.
Provision and run it only after the Provider host runbook's identity, key-custody,
registry, backup, and secret-manager gates have been approved.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import tempfile
import threading
import time
from typing import Callable, Mapping

from tools import control_plane_admission_provider_v1 as admission_provider
from tools.control_plane_provider_host_preflight_v1 import (
    REGISTRY_ENVIRONMENT,
    inspect_environment,
)


SCHEMA = "forexai.control_plane_provider_service.v1"
SOURCE_PACKET_NAME = "current-source-packet.json"
MAX_SEEN_PACKET_HASHES = 256


class ProviderServiceError(RuntimeError):
    """A sanitized service configuration or execution failure."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _emit(status: str, reason: str | None = None, packet_sha256: str | None = None) -> None:
    """Emit a deliberately small record; never print packet IDs, paths, or secrets."""
    value: dict[str, object] = {
        "schema": SCHEMA,
        "timestamp_utc": _utc_now(),
        "status": status,
        "orders_submitted": False,
        "demo_trading_authorized": False,
        "live_trading_allowed": False,
    }
    if reason:
        value["reason"] = reason
    if packet_sha256:
        value["packet_sha256_prefix"] = packet_sha256[:12]
    print(json.dumps(value, sort_keys=True), flush=True)


def _require_directory(path_value: str | Path, code: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_symlink():
        raise ProviderServiceError(code)
    if not path.is_dir():
        raise ProviderServiceError(code)
    return path.resolve()


def validate_runtime(
    input_directory: str | Path,
    output_directory: str | Path,
    state_directory: str | Path,
    private_key_path: str | Path,
    environ: Mapping[str, str] | None = None,
) -> tuple[Path, Path, Path, Path]:
    """Validate only prerequisites; do not create directories or initialize state."""
    env = os.environ if environ is None else environ
    input_dir = _require_directory(input_directory, "PROVIDER_INPUT_DIRECTORY_NOT_READY")
    output_dir = _require_directory(output_directory, "PROVIDER_OUTPUT_DIRECTORY_NOT_READY")
    state_dir = _require_directory(state_directory, "PROVIDER_STATE_DIRECTORY_NOT_READY")

    key_path = Path(private_key_path).expanduser()
    if key_path.is_symlink() or not key_path.is_file():
        raise ProviderServiceError("PROVIDER_ADMISSION_KEY_FILE_NOT_READY")
    key_path = key_path.resolve()

    registry_value = env.get(REGISTRY_ENVIRONMENT, "").strip()
    if not registry_value:
        raise ProviderServiceError("PROVIDER_ISSUANCE_REGISTRY_NOT_CONFIGURED")
    registry_path = Path(os.path.expandvars(os.path.expanduser(registry_value)))
    if not registry_path.is_absolute():
        raise ProviderServiceError("PROVIDER_ISSUANCE_REGISTRY_PATH_NOT_ABSOLUTE")
    if registry_path.is_symlink() or not registry_path.is_file():
        raise ProviderServiceError("PROVIDER_ISSUANCE_REGISTRY_NOT_INITIALIZED")

    if not env.get("FOREXAI_PROVIDER_SIGNING_KEY_PASSPHRASE", ""):
        raise ProviderServiceError("PROVIDER_SIGNING_PASSPHRASE_NOT_IN_PROCESS")
    # This performs the existing non-authorizing key-format/distinctness check
    # and a disposable SQLite probe in the registry parent. It never opens the
    # production registry, issues a request, or grants trading authority.
    report = inspect_environment(env)
    if report.get("status") != "PREFLIGHT_PASS_SOURCE_EVIDENCE_STILL_REQUIRED":
        raise ProviderServiceError("PROVIDER_HOST_PREFLIGHT_BLOCKED")
    return input_dir, output_dir, state_dir, key_path


def _read_stable_packet(path: Path, stability_delay_seconds: float = 0.05) -> bytes | None:
    """Read a stable regular-file snapshot without following a symlink."""
    if path.is_symlink():
        raise ProviderServiceError("PROVIDER_SOURCE_PACKET_SYMLINK_FORBIDDEN")
    if not path.is_file():
        return None
    try:
        before = path.stat()
        first = path.read_bytes()
        if stability_delay_seconds > 0:
            time.sleep(stability_delay_seconds)
        if path.is_symlink() or not path.is_file():
            raise ProviderServiceError("PROVIDER_SOURCE_PACKET_CHANGED_DURING_READ")
        second = path.read_bytes()
        after = path.stat()
    except ProviderServiceError:
        raise
    except OSError:
        raise ProviderServiceError("PROVIDER_SOURCE_PACKET_READ_FAILED") from None
    same_file = (
        before.st_size == after.st_size
        and before.st_mtime_ns == after.st_mtime_ns
        and len(first) == len(second) == after.st_size
    )
    if not same_file or first != second:
        return None
    return second


def _invoke_issuer(packet_path: Path, output_path: Path, private_key_path: Path) -> dict[str, str]:
    """Call the one-shot issuer while suppressing its stdout/stderr from service logs."""
    captured = io.StringIO()
    try:
        with redirect_stdout(captured), redirect_stderr(captured):
            exit_code = admission_provider.main([
                "--packet", str(packet_path),
                "--output", str(output_path),
                "--provider-private-key", str(private_key_path),
            ])
        lines = [line for line in captured.getvalue().splitlines() if line.strip()]
        parsed = json.loads(lines[-1]) if lines else {}
        if exit_code == 0 and parsed.get("status") == "PASS":
            return {"status": "PASS", "reason": ""}
        reason = parsed.get("reason")
        if not isinstance(reason, str) or not reason.startswith("PROVIDER_"):
            reason = "PROVIDER_ISSUANCE_BLOCKED"
        return {"status": "BLOCKED", "reason": reason}
    except Exception:
        # Intentionally suppress exception details: they may contain local paths
        # or implementation data not appropriate for operational logs.
        return {"status": "BLOCKED", "reason": "PROVIDER_ISSUER_INVOCATION_FAILED"}


def _process_snapshot(
    packet_bytes: bytes,
    output_path: Path,
    private_key_path: Path,
    temporary_directory: Path,
    issuer: Callable[[Path, Path, Path], dict[str, str]] = _invoke_issuer,
) -> dict[str, str]:
    """Stage a private, short-lived snapshot, then invoke the existing issuer."""
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=".source-packet-",
            suffix=".json",
            dir=temporary_directory,
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(packet_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        return issuer(temp_path, output_path, private_key_path)
    except OSError:
        return {"status": "BLOCKED", "reason": "PROVIDER_PACKET_SNAPSHOT_FAILED"}
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                # Do not leak a path. A cleanup failure must remain visible.
                _emit("BLOCKED", "PROVIDER_PACKET_SNAPSHOT_CLEANUP_FAILED")


def poll_once(
    input_directory: str | Path,
    output_directory: str | Path,
    private_key_path: str | Path,
    state_directory: str | Path,
    seen_hashes: dict[str, bool],
    *,
    stability_delay_seconds: float = 0.05,
    processor: Callable[[bytes, Path, Path, Path], dict[str, str]] = _process_snapshot,
) -> dict[str, object] | None:
    """Process a stable packet at most once per service process."""
    input_dir = _require_directory(input_directory, "PROVIDER_INPUT_DIRECTORY_NOT_READY")
    output_dir = _require_directory(output_directory, "PROVIDER_OUTPUT_DIRECTORY_NOT_READY")
    state_dir = _require_directory(state_directory, "PROVIDER_STATE_DIRECTORY_NOT_READY")
    key_path = Path(private_key_path).expanduser()
    if key_path.is_symlink() or not key_path.is_file():
        raise ProviderServiceError("PROVIDER_ADMISSION_KEY_FILE_NOT_READY")
    source_path = input_dir / SOURCE_PACKET_NAME

    try:
        packet_bytes = _read_stable_packet(source_path, stability_delay_seconds)
    except ProviderServiceError as exc:
        return {
            "status": "BLOCKED",
            "reason": str(exc),
            "orders_submitted": False,
            "demo_trading_authorized": False,
            "live_trading_allowed": False,
        }
    if packet_bytes is None:
        return None

    packet_hash = hashlib.sha256(packet_bytes).hexdigest()
    if packet_hash in seen_hashes:
        return None
    seen_hashes[packet_hash] = True
    while len(seen_hashes) > MAX_SEEN_PACKET_HASHES:
        seen_hashes.pop(next(iter(seen_hashes)))

    output_path = output_dir / f"admission-{packet_hash}.json"
    if output_path.is_symlink() or output_path.exists():
        result = {"status": "BLOCKED", "reason": "PROVIDER_OUTPUT_ALREADY_EXISTS"}
    else:
        result = processor(packet_bytes, output_path, key_path, output_dir)

    status = result.get("status", "BLOCKED")
    reason = result.get("reason", "")
    return {
        "status": status if status in {"PASS", "BLOCKED"} else "BLOCKED",
        "reason": reason or None,
        "packet_sha256_prefix": packet_hash[:12],
        # A successful issuer result means only that a signed request was issued.
        # It is not an execution authorization and this service never submits orders.
        "signed_request_created": status == "PASS",
        "orders_submitted": False,
        "demo_trading_authorized": False,
        "live_trading_allowed": False,
    }


@contextmanager
def single_instance_lock(lock_path: str | Path):
    """Acquire an OS-enforced non-blocking lock; leave the harmless lock file in place."""
    path = Path(lock_path)
    if path.is_symlink() or not path.parent.is_dir():
        raise ProviderServiceError("PROVIDER_SERVICE_LOCK_PATH_INVALID")
    try:
        descriptor = os.open(str(path), os.O_CREAT | os.O_RDWR, 0o600)
    except OSError:
        raise ProviderServiceError("PROVIDER_SERVICE_LOCK_UNAVAILABLE") from None
    handle = os.fdopen(descriptor, "r+b", buffering=0)
    locked = False
    try:
        if os.fstat(handle.fileno()).st_size == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
        except (OSError, ImportError):
            raise ProviderServiceError("PROVIDER_SERVICE_ALREADY_RUNNING") from None
        yield
    finally:
        if locked:
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            except (OSError, ImportError):
                pass
        handle.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-directory",
        default=r"C:\ProgramData\ForexAI-Provider\in",
    )
    parser.add_argument(
        "--output-directory",
        default=r"C:\ProgramData\ForexAI-Provider\out",
    )
    parser.add_argument(
        "--state-directory",
        default=r"C:\ProgramData\ForexAI-Provider\state",
    )
    parser.add_argument(
        "--provider-private-key",
        default=r"C:\ProgramData\ForexAI-Provider\keys\admission-provider-ed25519.pem",
    )
    parser.add_argument("--poll-interval-seconds", type=float, default=0.25)
    args = parser.parse_args(argv)

    if not 0.1 <= args.poll_interval_seconds <= 2.0:
        _emit("BLOCKED", "PROVIDER_POLL_INTERVAL_OUT_OF_RANGE")
        return 2

    try:
        input_dir, output_dir, state_dir, key_path = validate_runtime(
            args.input_directory,
            args.output_directory,
            args.state_directory,
            args.provider_private_key,
        )
        stop_event = threading.Event()

        def request_stop(_signum: int, _frame: object) -> None:
            stop_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, request_stop)
            except (ValueError, OSError):
                pass

        lock_path = state_dir / "provider-service.lock"
        with single_instance_lock(lock_path):
            _emit("STARTED")
            seen_hashes: dict[str, bool] = {}
            while not stop_event.is_set():
                try:
                    result = poll_once(
                        input_dir, output_dir, key_path, state_dir, seen_hashes
                    )
                    if result is not None:
                        _emit(
                            str(result.get("status", "BLOCKED")),
                            str(result["reason"]) if result.get("reason") else None,
                            str(result["packet_sha256_prefix"])
                            if result.get("packet_sha256_prefix") else None,
                        )
                except ProviderServiceError as exc:
                    _emit("BLOCKED", str(exc))
                except Exception:
                    _emit("BLOCKED", "PROVIDER_SERVICE_POLL_FAILED")
                stop_event.wait(args.poll_interval_seconds)
            _emit("STOPPED")
        return 0
    except ProviderServiceError as exc:
        _emit("BLOCKED", str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
