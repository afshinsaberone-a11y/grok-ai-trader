"""Fail-closed producer for the G13 Capital Firewall Control Plane v1.

This process is the upstream issuer: it consumes a fresh intent emitted by a
frozen G13 MQL5 candidate, proves the exact Promotion bundle is from current
main, observes the live MT5 Demo account and quote, computes stop-loss risk from
the broker API, appends the hash-chained lifecycle, reserves risk, signs the
runtime envelope, then atomically publishes the MQL5 transport record.

It never calls order_send, never edits the kill switch, and never authorizes a
real account. The EA must independently validate the record and current Demo
kill switch immediately before its one permitted order attempt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from tools.capital_firewall_v1 import AuthorizationError, CapitalFirewall
from tools.mt5_terminal_gateway_v1 import MT5GatewayConfig, MT5GatewayError, MT5TerminalGateway
from tools.runtime_authorization_auth_v1 import (
    DEFAULT_KEY_ID,
    build_authenticated_envelope,
    load_control_plane_secret,
)
from tools.runtime_authorization_envelope_v1 import build_runtime_envelope
from tools.runtime_authorization_record_v1 import (
    build_mql5_authorization_record,
    write_mql5_authorization_record,
)
from tools.trade_ledger_v1 import TradeLedger


CONTROL_PLANE_SCHEMA = "forexai.capital_control_plane.v1"
SIGNAL_INTENT_SCHEMA = "forexai.g13.runtime_signal_intent.m15.v1"
PROMOTION_SCHEMA = "forexai.g13.promotion_manifest.m15.v1"
PROMOTION_ATTESTATION_SCHEMA = "forexai.g13.promotion_run_attestation.m15.v1"
PROVENANCE_SCHEMA = "forexai.g13.promotion_evidence_provenance.m15.v1"
REPOSITORY_DEFAULT = "afshinsaberone-a11y/grok-ai-trader"
SYMBOL = "EURUSD"
TIMEFRAME = "M15"
MAX_AUTHORIZED_RISK = 0.006
MAX_INTENT_AGE_SECONDS = 10
MAX_PRICE_DRIFT_POINTS = 30
AUTHORIZATION_TTL_SECONDS = 30
POLL_SECONDS_DEFAULT = 0.25


class ControlPlaneError(RuntimeError):
    """A fail-closed control-plane rejection."""


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_object(path: Path, reason: str) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ControlPlaneError(reason) from exc
    if not isinstance(raw, dict):
        raise ControlPlaneError(f"{reason}_ROOT_NOT_OBJECT")
    return raw


def _parse_utc(value: Any, reason: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ControlPlaneError(reason)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ControlPlaneError(reason) from exc
    if parsed.tzinfo is None:
        raise ControlPlaneError(reason)
    return parsed.astimezone(timezone.utc)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds")


def fetch_current_main_sha(repository: str, token: str | None = None) -> str:
    """Read the public main ref from GitHub; no stale promotion bundle is accepted."""
    if "/" not in repository or repository.count("/") != 1:
        raise ControlPlaneError("CONTROL_PLANE_REPOSITORY_INVALID")
    url = f"https://api.github.com/repos/{repository}/commits/main"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ForexAI-Capital-Control-Plane/1",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, TimeoutError, UnicodeError, json.JSONDecodeError) as exc:
        raise ControlPlaneError("CONTROL_PLANE_CURRENT_MAIN_UNAVAILABLE") from exc
    sha = payload.get("sha") if isinstance(payload, dict) else None
    if not isinstance(sha, str) or len(sha) != 40:
        raise ControlPlaneError("CONTROL_PLANE_CURRENT_MAIN_INVALID")
    return sha


def validate_promotion_bundle(
    *,
    manifest_path: Path,
    attestation_path: Path,
    provenance_path: Path,
    candidate_id: int | None,
    expected_main_sha: str,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Bind candidate eligibility to the exact, current G13 promotion artifact."""
    manifest = _read_object(manifest_path, "PROMOTION_MANIFEST_UNREADABLE")
    attestation = _read_object(attestation_path, "PROMOTION_ATTESTATION_UNREADABLE")
    provenance = _read_object(provenance_path, "PROMOTION_PROVENANCE_UNREADABLE")

    if manifest.get("schema_version") != PROMOTION_SCHEMA:
        raise ControlPlaneError("PROMOTION_MANIFEST_SCHEMA_INVALID")
    if manifest.get("status") != "PROMOTION_READY":
        raise ControlPlaneError("PROMOTION_MANIFEST_NOT_READY")
    if manifest.get("symbol") != SYMBOL or manifest.get("timeframe") != TIMEFRAME:
        raise ControlPlaneError("PROMOTION_MARKET_IDENTITY_MISMATCH")
    policy = manifest.get("decision_policy")
    if not isinstance(policy, dict):
        raise ControlPlaneError("PROMOTION_POLICY_MISSING")
    if policy.get("ea_generation_allowed") is not True:
        raise ControlPlaneError("PROMOTION_EA_GENERATION_NOT_ALLOWED")
    # Promotion approves research/package generation, not trading. Runtime Demo
    # authority is issued here under separate current-account/risk constraints.
    if policy.get("demo_trading_allowed") is not False or policy.get("live_trading_allowed") is not False:
        raise ControlPlaneError("PROMOTION_POLICY_BOUNDARY_INVALID")

    if attestation.get("schema_version") != PROMOTION_ATTESTATION_SCHEMA:
        raise ControlPlaneError("PROMOTION_ATTESTATION_SCHEMA_INVALID")
    if attestation.get("head_sha") != expected_main_sha:
        raise ControlPlaneError("PROMOTION_ATTESTATION_NOT_CURRENT_MAIN")
    if attestation.get("manifest_sha256") != _sha256_file(manifest_path):
        raise ControlPlaneError("PROMOTION_MANIFEST_ATTESTATION_HASH_MISMATCH")
    if attestation.get("provenance_sha256") != _sha256_file(provenance_path):
        raise ControlPlaneError("PROMOTION_PROVENANCE_ATTESTATION_HASH_MISMATCH")
    if not isinstance(attestation.get("workflow_run_id"), int) or attestation["workflow_run_id"] <= 0:
        raise ControlPlaneError("PROMOTION_RUN_ID_INVALID")

    if provenance.get("schema_version") != PROVENANCE_SCHEMA:
        raise ControlPlaneError("PROMOTION_PROVENANCE_SCHEMA_INVALID")
    if provenance.get("target_sha") != expected_main_sha:
        raise ControlPlaneError("PROMOTION_PROVENANCE_NOT_CURRENT_MAIN")
    sources = provenance.get("sources")
    if not isinstance(sources, dict):
        raise ControlPlaneError("PROMOTION_PROVENANCE_SOURCES_MISSING")
    for key in ("validation", "robustness", "oos"):
        row = sources.get(key)
        if not isinstance(row, dict):
            raise ControlPlaneError(f"PROMOTION_SOURCE_MISSING:{key}")
        if row.get("head_branch") != "main" or row.get("head_sha") != expected_main_sha:
            raise ControlPlaneError(f"PROMOTION_SOURCE_SHA_MISMATCH:{key}")
        if row.get("conclusion") != "success":
            raise ControlPlaneError(f"PROMOTION_SOURCE_NOT_SUCCESSFUL:{key}")
        if not isinstance(row.get("run_id"), int) or row["run_id"] <= 0:
            raise ControlPlaneError(f"PROMOTION_SOURCE_RUN_ID_INVALID:{key}")
        artifact = row.get("artifact")
        if not isinstance(artifact, dict):
            raise ControlPlaneError(f"PROMOTION_SOURCE_ARTIFACT_MISSING:{key}")
        digest = artifact.get("digest")
        if not isinstance(digest, str) or not digest.startswith("sha256:") or len(digest) != 71:
            raise ControlPlaneError(f"PROMOTION_SOURCE_ARTIFACT_DIGEST_INVALID:{key}")
        if artifact.get("expired") is not False:
            raise ControlPlaneError(f"PROMOTION_SOURCE_ARTIFACT_EXPIRED:{key}")

    promoted_ids = manifest.get("promoted_candidate_ids")
    candidates = manifest.get("candidates")
    if (
        not isinstance(promoted_ids, list)
        or not promoted_ids
        or not isinstance(candidates, list)
        or len(promoted_ids) != len(set(promoted_ids))
        or any(not isinstance(cid, int) or cid <= 0 for cid in promoted_ids)
    ):
        raise ControlPlaneError("PROMOTION_CANDIDATE_SET_INVALID")
    if candidate_id is None:
        # Startup validates the entire signed bundle without assuming that a
        # particular candidate is still promoted. Candidate binding is repeated
        # against the exact intent each time a signal is consumed.
        return manifest, None
    if candidate_id not in promoted_ids:
        raise ControlPlaneError("CANDIDATE_NOT_PROMOTED")
    matches = [
        row for row in candidates
        if isinstance(row, dict) and row.get("candidate_id") == candidate_id
    ]
    if len(matches) != 1:
        raise ControlPlaneError("PROMOTED_CANDIDATE_MISSING_OR_AMBIGUOUS")
    candidate = matches[0]
    params = candidate.get("params")
    config_hash = candidate.get("config_hash")
    if not isinstance(params, dict) or not isinstance(config_hash, str):
        raise ControlPlaneError("PROMOTED_CANDIDATE_CONFIG_INVALID")
    if canonical_hash(params) != config_hash:
        raise ControlPlaneError("PROMOTED_CANDIDATE_CONFIG_HASH_MISMATCH")
    if params.get("side") != "short":
        raise ControlPlaneError("G13_M15_SIDE_POLICY_MISMATCH")
    contract = manifest.get("execution_contract")
    if not isinstance(contract, dict):
        raise ControlPlaneError("PROMOTION_EXECUTION_CONTRACT_MISSING")
    try:
        risk_cap = float(contract["risk_pct"])
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise ControlPlaneError("PROMOTION_RISK_POLICY_INVALID") from exc
    if not math.isfinite(risk_cap) or risk_cap <= 0 or risk_cap > MAX_AUTHORIZED_RISK:
        raise ControlPlaneError("PROMOTION_RISK_POLICY_OUT_OF_BOUNDS")
    return manifest, candidate


def _validate_signal_intent(
    intent_path: Path,
    *,
    manifest: Mapping[str, Any],
    candidate: Mapping[str, Any],
    now: datetime,
) -> dict[str, Any]:
    intent = _read_object(intent_path, "SIGNAL_INTENT_UNREADABLE")
    expected_keys = {
        "schema",
        "candidate_id",
        "symbol",
        "timeframe",
        "side",
        "config_hash",
        "signal_bar_epoch",
        "created_at_utc",
        "entry_price",
        "stop_loss",
        "take_profit",
        "volume",
    }
    if set(intent) != expected_keys:
        raise ControlPlaneError("SIGNAL_INTENT_FIELDS_MISMATCH")
    if intent.get("schema") != SIGNAL_INTENT_SCHEMA:
        raise ControlPlaneError("SIGNAL_INTENT_SCHEMA_INVALID")
    cid = candidate.get("candidate_id")
    if intent.get("candidate_id") != cid or cid not in manifest.get("promoted_candidate_ids", []):
        raise ControlPlaneError("SIGNAL_CANDIDATE_IDENTITY_MISMATCH")
    if intent.get("symbol") != SYMBOL or intent.get("timeframe") != TIMEFRAME:
        raise ControlPlaneError("SIGNAL_MARKET_IDENTITY_MISMATCH")
    if intent.get("side") != "SELL":
        raise ControlPlaneError("SIGNAL_SIDE_NOT_ALLOWED")
    if intent.get("config_hash") != candidate.get("config_hash"):
        raise ControlPlaneError("SIGNAL_FROZEN_CONFIG_HASH_MISMATCH")
    if not isinstance(intent.get("signal_bar_epoch"), int) or intent["signal_bar_epoch"] <= 0:
        raise ControlPlaneError("SIGNAL_BAR_ID_INVALID")

    created = _parse_utc(intent.get("created_at_utc"), "SIGNAL_TIMESTAMP_INVALID")
    age = (now - created).total_seconds()
    if age < -1 or age > MAX_INTENT_AGE_SECONDS:
        raise ControlPlaneError("SIGNAL_INTENT_STALE_OR_FUTURE")
    try:
        file_age = now.timestamp() - intent_path.stat().st_mtime
    except OSError as exc:
        raise ControlPlaneError("SIGNAL_INTENT_STAT_FAILED") from exc
    if file_age < -1 or file_age > MAX_INTENT_AGE_SECONDS:
        raise ControlPlaneError("SIGNAL_INTENT_FILE_STALE_OR_FUTURE")

    for field in ("entry_price", "stop_loss", "take_profit", "volume"):
        value = intent.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ControlPlaneError(f"SIGNAL_NUMERIC_FIELD_INVALID:{field}")
        if not math.isfinite(float(value)) or float(value) <= 0:
            raise ControlPlaneError(f"SIGNAL_NUMERIC_FIELD_INVALID:{field}")

    entry = float(intent["entry_price"])
    sl = float(intent["stop_loss"])
    tp = float(intent["take_profit"])
    volume = float(intent["volume"])
    if not (sl > entry > tp):
        raise ControlPlaneError("SIGNAL_SELL_PROTECTIVE_LEVELS_INVALID")
    return intent


def _demo_snapshot(mt5: Any, *, intent: Mapping[str, Any], gateway: MT5TerminalGateway, now: datetime) -> dict[str, Any]:
    account = mt5.account_info()
    terminal = mt5.terminal_info()
    symbol_info = mt5.symbol_info(SYMBOL)
    tick = mt5.symbol_info_tick(SYMBOL)
    if account is None:
        raise ControlPlaneError("MT5_ACCOUNT_INFO_UNAVAILABLE")
    if terminal is None or not bool(getattr(terminal, "connected", False)):
        raise ControlPlaneError("MT5_TERMINAL_NOT_CONNECTED")
    if symbol_info is None or tick is None:
        raise ControlPlaneError("MT5_SYMBOL_OR_TICK_UNAVAILABLE")
    demo_mode = int(getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", 0))
    if int(getattr(account, "trade_mode", -1)) != demo_mode:
        raise ControlPlaneError("MT5_REAL_ACCOUNT_BLOCKED")
    if not bool(getattr(account, "trade_allowed", False)):
        raise ControlPlaneError("MT5_ACCOUNT_TRADING_NOT_ALLOWED")
    if not bool(getattr(account, "trade_expert", False)):
        raise ControlPlaneError("MT5_EXPERT_TRADING_NOT_ALLOWED")
    if not bool(getattr(terminal, "trade_allowed", False)):
        raise ControlPlaneError("MT5_TERMINAL_TRADING_NOT_ALLOWED")

    equity = float(getattr(account, "equity", 0.0) or 0.0)
    balance = float(getattr(account, "balance", 0.0) or 0.0)
    bid = float(getattr(tick, "bid", 0.0) or 0.0)
    ask = float(getattr(tick, "ask", 0.0) or 0.0)
    point = float(getattr(symbol_info, "point", 0.0) or 0.0)
    if not all(math.isfinite(x) for x in (equity, balance, bid, ask, point)):
        raise ControlPlaneError("MT5_ACCOUNT_OR_QUOTE_NONFINITE")
    if equity <= 0 or balance <= 0 or bid <= 0 or ask < bid or point <= 0:
        raise ControlPlaneError("MT5_ACCOUNT_OR_QUOTE_INVALID")
    trade_mode = int(getattr(symbol_info, "trade_mode", -1))
    sell_modes = {
        int(getattr(mt5, "SYMBOL_TRADE_MODE_FULL", 4)),
        int(getattr(mt5, "SYMBOL_TRADE_MODE_SHORTONLY", 3)),
    }
    if trade_mode not in sell_modes:
        raise ControlPlaneError("MT5_SYMBOL_SELL_NOT_ALLOWED")
    order_mode = int(getattr(symbol_info, "order_mode", 0))
    if not (order_mode & int(getattr(mt5, "SYMBOL_ORDER_MARKET", 1))):
        raise ControlPlaneError("MT5_MARKET_ORDERS_NOT_ALLOWED")
    if not (order_mode & int(getattr(mt5, "SYMBOL_ORDER_SL", 16))):
        raise ControlPlaneError("MT5_STOP_LOSS_NOT_ALLOWED")
    if not (order_mode & int(getattr(mt5, "SYMBOL_ORDER_TP", 32))):
        raise ControlPlaneError("MT5_TAKE_PROFIT_NOT_ALLOWED")

    positions = mt5.positions_get()
    if positions is None:
        raise ControlPlaneError("MT5_POSITION_SNAPSHOT_UNAVAILABLE")
    for position in positions:
        magic = int(getattr(position, "magic", 0) or 0)
        if 130002 <= magic <= 130048:
            raise ControlPlaneError("G13_POSITION_ALREADY_OPEN")
    orders_get = getattr(mt5, "orders_get", None)
    if not callable(orders_get):
        raise ControlPlaneError("MT5_PENDING_ORDER_SNAPSHOT_UNAVAILABLE")
    pending_orders = orders_get()
    if pending_orders is None:
        raise ControlPlaneError("MT5_PENDING_ORDER_SNAPSHOT_UNAVAILABLE")
    for order in pending_orders:
        magic = int(getattr(order, "magic", 0) or 0)
        if 130002 <= magic <= 130048:
            raise ControlPlaneError("G13_PENDING_ORDER_ALREADY_EXISTS")

    entry = float(intent["entry_price"])
    if abs(bid - entry) > MAX_PRICE_DRIFT_POINTS * point:
        raise ControlPlaneError("MT5_PRICE_MOVED_BEYOND_SIGNAL_TOLERANCE")
    sl = float(intent["stop_loss"])
    tp = float(intent["take_profit"])
    if not (sl > ask and tp < bid):
        raise ControlPlaneError("MT5_CURRENT_SELL_PROTECTIVE_LEVELS_INVALID")
    stops_level = int(getattr(symbol_info, "trade_stops_level", 0) or 0)
    if stops_level < 0 or (sl - ask) < stops_level * point or (bid - tp) < stops_level * point:
        raise ControlPlaneError("MT5_PROTECTIVE_LEVELS_WITHIN_BROKER_STOP_DISTANCE")

    volume = float(intent["volume"])
    volume_min = float(getattr(symbol_info, "volume_min", 0.0) or 0.0)
    volume_max = float(getattr(symbol_info, "volume_max", 0.0) or 0.0)
    volume_step = float(getattr(symbol_info, "volume_step", 0.0) or 0.0)
    if volume_min <= 0 or volume_max < volume_min or volume_step <= 0:
        raise ControlPlaneError("MT5_VOLUME_CONTRACT_INVALID")
    if volume < volume_min or volume > volume_max:
        raise ControlPlaneError("MT5_VOLUME_OUT_OF_RANGE")
    step_count = (volume - volume_min) / volume_step
    if abs(step_count - round(step_count)) > 1e-6:
        raise ControlPlaneError("MT5_VOLUME_STEP_MISMATCH")

    order_type = int(getattr(mt5, "ORDER_TYPE_SELL"))
    try:
        projected_profit = mt5.order_calc_profit(order_type, SYMBOL, volume, bid, sl)
    except Exception as exc:
        raise ControlPlaneError("MT5_STOP_RISK_CALCULATION_FAILED") from exc
    if projected_profit is None or not math.isfinite(float(projected_profit)) or float(projected_profit) >= 0:
        raise ControlPlaneError("MT5_STOP_RISK_RESULT_INVALID")
    risk_fraction = abs(float(projected_profit)) / equity
    if not math.isfinite(risk_fraction) or risk_fraction <= 0 or risk_fraction > MAX_AUTHORIZED_RISK:
        raise ControlPlaneError("MT5_ACTUAL_STOP_RISK_OUT_OF_BOUNDS")

    # Broker order_check is read-only; there is deliberately no order_send here.
    filling = gateway._select_filling(symbol_info)
    request = {
        "action": int(getattr(mt5, "TRADE_ACTION_DEAL")),
        "symbol": SYMBOL,
        "volume": volume,
        "type": order_type,
        "price": bid,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 130000 + int(intent["candidate_id"]),
        "comment": "ForexAI-ControlPlane",
        "type_time": int(getattr(mt5, "ORDER_TIME_GTC")),
        "type_filling": filling,
    }
    try:
        check = mt5.order_check(request)
    except Exception as exc:
        raise ControlPlaneError("MT5_ORDER_CHECK_FAILED") from exc
    if check is None:
        raise ControlPlaneError("MT5_ORDER_CHECK_UNAVAILABLE")
    check_retcode = int(getattr(check, "retcode", -1))
    if check_retcode != 0:
        raise ControlPlaneError(f"MT5_ORDER_CHECK_REJECTED:{check_retcode}")

    tick_time_msc = int(getattr(tick, "time_msc", 0) or 0)
    if tick_time_msc <= 0:
        raise ControlPlaneError("MT5_TICK_TIMESTAMP_INVALID")
    return {
        "account_mode": "DEMO",
        "equity": equity,
        "balance": balance,
        "bid": bid,
        "ask": ask,
        "point": point,
        "tick_time_msc": tick_time_msc,
        "risk_fraction": risk_fraction,
        "volume": volume,
        "stop_loss": sl,
        "take_profit": tp,
        "order_check_retcode": check_retcode,
        "snapshot_id": "",
    }


def _append_state(
    ledger: TradeLedger,
    *,
    trade_id: str,
    state: str,
    event_type: str,
    payload: Mapping[str, Any],
    timestamp: str,
) -> None:
    event_key = canonical_hash(
        {"trade_id": trade_id, "state": state, "event_type": event_type, "payload": dict(payload)}
    )
    ledger.append(
        trade_id=trade_id,
        state=state,
        event_type=event_type,
        payload=dict(payload),
        idempotency_key=f"cp:{event_key}",
        event_id=f"cp-event:{event_key}",
        timestamp_utc=timestamp,
    )


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    import tempfile

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n",
            dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True, indent=2) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _assert_demo_kill_switch(common_files: Path) -> None:
    switch_path = common_files / "g13_demo_kill_switch.txt"
    try:
        state = switch_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ControlPlaneError("DEMO_KILL_SWITCH_MISSING") from exc
    if state != "ALLOW":
        raise ControlPlaneError("DEMO_KILL_SWITCH_NOT_ALLOW")


def _exclusive_lock(lock_path: Path):
    """Tiny cross-process lock. A stale lock is deliberately not auto-deleted."""
    class Lock:
        def __enter__(self):
            self.lock_path = lock_path
            self.lock_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                self.fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError as exc:
                raise ControlPlaneError("CONTROL_PLANE_LOCK_ALREADY_HELD") from exc
            os.write(self.fd, f"pid={os.getpid()} utc={_utc_text(_utc_now())}\n".encode("ascii"))
            os.fsync(self.fd)
            return self

        def __exit__(self, exc_type, exc, tb):
            os.close(self.fd)
            try:
                self.lock_path.unlink()
            except FileNotFoundError:
                pass
    return Lock()


def process_signal_intent(
    *,
    intent_path: Path,
    manifest_path: Path,
    attestation_path: Path,
    provenance_path: Path,
    current_main_sha: str,
    ledger_path: Path,
    authenticated_envelope_path: Path,
    common_files: Path,
    mt5: Any,
    gateway: MT5TerminalGateway,
    secret: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Issue one current Demo authorization from one fresh real EA intent."""
    now = (now or _utc_now()).astimezone(timezone.utc)
    if not common_files.is_dir():
        raise ControlPlaneError("MT5_COMMON_FILES_DIRECTORY_MISSING")
    _assert_demo_kill_switch(common_files)
    preliminary = _read_object(intent_path, "SIGNAL_INTENT_UNREADABLE")
    try:
        candidate_id = int(preliminary.get("candidate_id", 0))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ControlPlaneError("SIGNAL_CANDIDATE_ID_INVALID") from exc
    manifest, candidate = validate_promotion_bundle(
        manifest_path=manifest_path,
        attestation_path=attestation_path,
        provenance_path=provenance_path,
        candidate_id=candidate_id,
        expected_main_sha=current_main_sha,
    )
    intent = _validate_signal_intent(intent_path, manifest=manifest, candidate=candidate, now=now)
    snapshot = _demo_snapshot(mt5, intent=intent, gateway=gateway, now=now)
    risk_cap = float(manifest["execution_contract"]["risk_pct"])
    risk_fraction = float(snapshot["risk_fraction"])
    if risk_fraction > risk_cap + 1e-9:
        raise ControlPlaneError("ACTUAL_STOP_RISK_EXCEEDS_PROMOTED_RISK_POLICY")

    signal_bar_epoch = int(intent["signal_bar_epoch"])
    decision_id = f"G13-{candidate_id}-{signal_bar_epoch}-SELL"
    trade_id = f"G13-{candidate_id}-{signal_bar_epoch}-S"
    authorization_id = f"AUTH-{_fingerprint(trade_id)}"
    reservation_id = f"RSV-{_fingerprint(trade_id)}"
    input_hash = canonical_hash({
        "intent": intent,
        "promotion_head_sha": current_main_sha,
        "risk_fraction": risk_fraction,
        "account_mode": snapshot["account_mode"],
    })
    snapshot_body = {
        "account_mode": snapshot["account_mode"],
        "equity": snapshot["equity"],
        "balance": snapshot["balance"],
        "bid": snapshot["bid"],
        "ask": snapshot["ask"],
        "tick_time_msc": snapshot["tick_time_msc"],
        "symbol": SYMBOL,
        "timeframe": TIMEFRAME,
        "promotion_head_sha": current_main_sha,
    }
    snapshot_id = "SNAP-" + canonical_hash(snapshot_body)[:24]
    proof = {
        "snapshot_id": snapshot_id,
        "symbol": SYMBOL,
        "timeframe": TIMEFRAME,
        "decision_id": decision_id,
        "strategy_id": "forexai.g13.rsi_divergence.m15",
        "model_id": f"g13-candidate-{candidate_id}-{candidate['config_hash'][:16]}",
        "policy_version": "forexai.capital-policy.v1",
        "risk_authorization_id": authorization_id,
        "authorization_expiry": "",
        "input_hash": input_hash,
        "execution_contract_version": "forexai.execution.v1",
    }
    expires_dt = now + timedelta(seconds=AUTHORIZATION_TTL_SECONDS)
    issued_at = _utc_text(now)
    expires_at = _utc_text(expires_dt)
    proof["authorization_expiry"] = expires_at

    lock_path = ledger_path.with_suffix(ledger_path.suffix + ".control-plane.lock")
    with _exclusive_lock(lock_path):
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger = TradeLedger(ledger_path)
        if ledger.state_of(trade_id) is not None:
            raise ControlPlaneError("SIGNAL_TRADE_ALREADY_PROCESSED")
        ledger.assert_no_unresolved_reconciliation()
        audit_payload = {
            "candidate_id": candidate_id,
            "decision_id": decision_id,
            "config_hash": candidate["config_hash"],
            "input_hash": input_hash,
            "snapshot_id": snapshot_id,
            "promotion_run_id": int(_read_object(attestation_path, "PROMOTION_ATTESTATION_UNREADABLE")["workflow_run_id"]),
            "promotion_head_sha": current_main_sha,
        }
        _append_state(
            ledger, trade_id=trade_id, state="PROPOSED",
            event_type="G13_SIGNAL_PROPOSED", payload=audit_payload, timestamp=issued_at,
        )
        _append_state(
            ledger, trade_id=trade_id, state="VALIDATED",
            event_type="G13_SIGNAL_VALIDATED",
            payload={**audit_payload, "account_mode": "DEMO", "mt5_order_check": "PASS"},
            timestamp=issued_at,
        )
        _append_state(
            ledger, trade_id=trade_id, state="RISK_RESERVED",
            event_type="G13_RISK_RESERVED",
            payload={
                **audit_payload,
                "authorized_risk": risk_fraction,
                "reserved_risk": risk_fraction,
                "risk_unit": "equity_fraction",
            },
            timestamp=issued_at,
        )
        firewall = CapitalFirewall(ledger)
        firewall.issue_authorization(
            trade_id=trade_id,
            authorization_id=authorization_id,
            authorized_risk=risk_fraction,
            issued_at_utc=issued_at,
            expires_at_utc=expires_at,
            proof=proof,
            event_id=f"cp-auth-event:{_fingerprint(trade_id)}",
            idempotency_key=f"cp-auth-key:{_fingerprint(trade_id)}",
        )
        firewall.authorize_trade(
            trade_id=trade_id,
            authorization_id=authorization_id,
            now_utc=issued_at,
            event_id=f"cp-authorized-event:{_fingerprint(trade_id)}",
            idempotency_key=f"cp-authorized-key:{_fingerprint(trade_id)}",
        )
        firewall.reserve(
            trade_id=trade_id,
            authorization_id=authorization_id,
            amount=risk_fraction,
            reservation_id=reservation_id,
            now_utc=issued_at,
            event_id=f"cp-reserve-event:{_fingerprint(trade_id)}",
            idempotency_key=f"cp-reserve-key:{_fingerprint(trade_id)}",
        )
        envelope = build_runtime_envelope(
            firewall,
            trade_id=trade_id,
            authorization_id=authorization_id,
            reservation_id=reservation_id,
            required_risk=risk_fraction,
            now_utc=issued_at,
        ).to_dict()
        authenticated = build_authenticated_envelope(
            envelope, secret=secret, key_id=DEFAULT_KEY_ID
        )
        record = build_mql5_authorization_record(
            firewall,
            authenticated,
            control_plane_secret=secret,
            now_utc=issued_at,
            expected_trade_id=trade_id,
            expected_key_id=DEFAULT_KEY_ID,
        )
        # Publish the authenticated envelope first, then the short-lived .auth
        # file last. The EA cannot attempt an order until the latter is present.
        _atomic_json(authenticated_envelope_path, authenticated)
        auth_path = common_files / f"ForexAI_Authorization_{130000 + candidate_id}_EURUSD.auth"
        write_mql5_authorization_record(auth_path, record)

    # The EA retains the decision in memory; once the authorization record has
    # been atomically published the input must not be processed twice.
    try:
        intent_path.unlink(missing_ok=True)
    except OSError as exc:
        raise ControlPlaneError("SIGNAL_INTENT_CLEANUP_FAILED") from exc

    return {
        "schema": CONTROL_PLANE_SCHEMA,
        "status": "AUTHORIZED_FOR_ONE_CONTROLLED_DEMO_ATTEMPT",
        "candidate_id": candidate_id,
        "symbol": SYMBOL,
        "timeframe": TIMEFRAME,
        "side": "SELL",
        "account_mode": "DEMO",
        "risk_fraction": risk_fraction,
        "promotion_run_id": int(_read_object(attestation_path, "PROMOTION_ATTESTATION_UNREADABLE")["workflow_run_id"]),
        "promotion_head_sha": current_main_sha,
        "trade_id_fingerprint": _fingerprint(trade_id),
        "decision_id_fingerprint": _fingerprint(decision_id),
        "snapshot_id": snapshot_id,
        "envelope_hash": envelope["envelope_hash"],
        "authorization_record": auth_path.name,
        "order_submission_performed": False,
        "live_trading_allowed": False,
        "kill_switch_changed": False,
    }


def _signal_intents(common_files: Path) -> list[Path]:
    return sorted(common_files.glob("ForexAI_G13_SignalIntent_*_EURUSD.json"))


def watch(
    *,
    repository: str,
    manifest_path: Path,
    attestation_path: Path,
    provenance_path: Path,
    ledger_path: Path,
    authenticated_envelope_path: Path,
    common_files: Path,
    terminal_path: str | None,
    secret: str,
    poll_seconds: float = POLL_SECONDS_DEFAULT,
    stop_event: Any | None = None,
) -> int:
    if not secret or len(secret.encode("utf-8")) < 32:
        raise ControlPlaneError("CONTROL_PLANE_SECRET_NOT_CONFIGURED_OR_TOO_SHORT")
    if poll_seconds <= 0 or poll_seconds > 5:
        raise ControlPlaneError("CONTROL_PLANE_POLL_INTERVAL_INVALID")
    gateway = MT5TerminalGateway(
        MT5GatewayConfig(terminal_path=terminal_path, shutdown_after_request=False)
    )
    gateway._initialize()
    seen_errors: set[tuple[str, str]] = set()
    cached_sha = ""
    last_sha_check = 0.0
    try:
        while stop_event is None or not stop_event.is_set():
            for intent_path in _signal_intents(common_files):
                # Kill switch is an operator boundary. DENY means no authorization
                # is emitted; this service never changes it.
                try:
                    _assert_demo_kill_switch(common_files)
                except ControlPlaneError:
                    continue
                try:
                    # Refresh current main for each intent; never authorize from a
                    # SHA cached before the current signal was observed.
                    current_sha = fetch_current_main_sha(repository, os.environ.get("GH_TOKEN"))
                    cached_sha = current_sha
                    last_sha_check = time.monotonic()
                    result = process_signal_intent(
                        intent_path=intent_path,
                        manifest_path=manifest_path,
                        attestation_path=attestation_path,
                        provenance_path=provenance_path,
                        current_main_sha=current_sha,
                        ledger_path=ledger_path,
                        authenticated_envelope_path=authenticated_envelope_path,
                        common_files=common_files,
                        mt5=gateway.mt5,
                        gateway=gateway,
                        secret=secret,
                    )
                    print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
                    seen_errors = {item for item in seen_errors if item[0] != intent_path.name}
                except ControlPlaneError as exc:
                    # Do not log payloads, account identity, raw trade IDs, or local
                    # filesystem paths. The EA drops intents after its short TTL.
                    key = (intent_path.name, str(exc).split(":", 1)[0])
                    if key not in seen_errors:
                        print(
                            json.dumps({
                                "schema": CONTROL_PLANE_SCHEMA,
                                "status": "BLOCKED",
                                "candidate_file": intent_path.name,
                                "reason_code": key[1],
                                "order_submission_performed": False,
                                "kill_switch_changed": False,
                                "live_trading_allowed": False,
                            }, sort_keys=True),
                            flush=True,
                        )
                        seen_errors.add(key)
                except Exception as exc:
                    # Unknown failures do not grant authority. Surface only the
                    # exception class to avoid leaking sensitive runtime values.
                    key = (intent_path.name, type(exc).__name__)
                    if key not in seen_errors:
                        print(json.dumps({
                            "schema": CONTROL_PLANE_SCHEMA,
                            "status": "BLOCKED",
                            "candidate_file": intent_path.name,
                            "reason_code": "UNEXPECTED_" + type(exc).__name__.upper(),
                            "order_submission_performed": False,
                            "live_trading_allowed": False,
                        }, sort_keys=True), flush=True)
                        seen_errors.add(key)
            time.sleep(poll_seconds)
    finally:
        gateway._shutdown()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watch", action="store_true", help="Poll MT5 Common Files for fresh EA signal intents.")
    parser.add_argument("--repository", default=os.environ.get("FOREXAI_G13_SOURCE_REPOSITORY", REPOSITORY_DEFAULT))
    parser.add_argument("--promotion-manifest", type=Path, default=os.environ.get("FOREXAI_G13_PROMOTION_MANIFEST_PATH"))
    parser.add_argument("--promotion-attestation", type=Path, default=os.environ.get("FOREXAI_G13_PROMOTION_ATTESTATION_PATH"))
    parser.add_argument("--promotion-provenance", type=Path, default=os.environ.get("FOREXAI_G13_PROMOTION_PROVENANCE_PATH"))
    parser.add_argument("--ledger", type=Path, default=os.environ.get("FOREXAI_TRADE_LEDGER_PATH"))
    parser.add_argument("--authenticated-envelope-output", type=Path, default=os.environ.get("FOREXAI_AUTHENTICATED_ENVELOPE_PATH"))
    parser.add_argument("--common-files", type=Path, default=os.environ.get("FOREXAI_MT5_COMMON_FILES"))
    parser.add_argument("--terminal-path", default=os.environ.get("FOREXAI_MT5_TERMINAL_PATH", r"C:\Program Files\MetaTrader 5\terminal64.exe"))
    parser.add_argument("--poll-seconds", type=float, default=POLL_SECONDS_DEFAULT)
    parser.add_argument("--secret-env", default="FOREXAI_CONTROL_PLANE_HMAC_SECRET")
    args = parser.parse_args()

    required = {
        "--promotion-manifest": args.promotion_manifest,
        "--promotion-attestation": args.promotion_attestation,
        "--promotion-provenance": args.promotion_provenance,
        "--ledger": args.ledger,
        "--authenticated-envelope-output": args.authenticated_envelope_output,
        "--common-files": args.common_files,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise ControlPlaneError("CONTROL_PLANE_PATHS_NOT_CONFIGURED:" + ",".join(missing))
    if not args.common_files.is_dir():
        raise ControlPlaneError("MT5_COMMON_FILES_DIRECTORY_MISSING")

    secret = load_control_plane_secret(args.secret_env)
    current_sha = fetch_current_main_sha(args.repository, os.environ.get("GH_TOKEN"))
    # Pre-flight validates that the downloaded manifest and provenance are tied to
    # the exact current main SHA before starting the listener.
    validate_promotion_bundle(
        manifest_path=args.promotion_manifest,
        attestation_path=args.promotion_attestation,
        provenance_path=args.promotion_provenance,
        candidate_id=None,
        expected_main_sha=current_sha,
    )
    if not args.watch:
        parser.error("Pass --watch to start the long-running local service.")
    return watch(
        repository=args.repository,
        manifest_path=args.promotion_manifest,
        attestation_path=args.promotion_attestation,
        provenance_path=args.promotion_provenance,
        ledger_path=args.ledger,
        authenticated_envelope_path=args.authenticated_envelope_output,
        common_files=args.common_files,
        terminal_path=args.terminal_path,
        secret=secret,
        poll_seconds=args.poll_seconds,
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ControlPlaneError, AuthorizationError, MT5GatewayError, OSError, ValueError) as exc:
        print(f"FOREXAI_CONTROL_PLANE_FAIL_CLOSED:{str(exc).split(':', 1)[0]}")
        raise SystemExit(2)
