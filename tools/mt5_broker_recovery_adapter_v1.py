"""MT5 broker recovery adapter v1.

Bridges the real MT5 terminal to the broker-outcome recovery kernel.
Read-only: it never calls order_send, never retries, and never creates capital
authority. The returned observation is suitable for resolve_broker_outcome().
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tools.mt5_broker_observation_v1 import observe_order


class MT5RecoveryAdapterError(RuntimeError):
    """Unable to obtain an authoritative MT5 broker observation."""


@dataclass(frozen=True)
class MT5RecoveryConfig:
    terminal_path: str | None = None
    login: int | None = None
    password: str | None = None
    server: str | None = None
    timeout_ms: int = 60_000
    shutdown_after_observation: bool = True


class MT5BrokerRecoveryAdapter:
    def __init__(self, config: MT5RecoveryConfig | None = None, *, mt5_module: Any | None = None):
        self.config = config or MT5RecoveryConfig()
        self._mt5 = mt5_module

    @property
    def mt5(self) -> Any:
        if self._mt5 is None:
            try:
                import MetaTrader5 as mt5
            except ImportError as exc:
                raise MT5RecoveryAdapterError("MT5_PYTHON_PACKAGE_NOT_INSTALLED") from exc
            self._mt5 = mt5
        return self._mt5

    def _initialize(self) -> None:
        kwargs: dict[str, Any] = {"timeout": self.config.timeout_ms}
        if self.config.login is not None:
            kwargs["login"] = self.config.login
        if self.config.password is not None:
            kwargs["password"] = self.config.password
        if self.config.server is not None:
            kwargs["server"] = self.config.server
        try:
            ok = (
                self.mt5.initialize(self.config.terminal_path, **kwargs)
                if self.config.terminal_path
                else self.mt5.initialize(**kwargs)
            )
        except Exception as exc:
            raise MT5RecoveryAdapterError("MT5_RECOVERY_INITIALIZE_EXCEPTION") from exc
        if not ok:
            last_error = getattr(self.mt5, "last_error", lambda: None)()
            raise MT5RecoveryAdapterError(f"MT5_RECOVERY_INITIALIZE_FAILED:{last_error}")

    def _shutdown(self) -> None:
        if self.config.shutdown_after_observation:
            try:
                self.mt5.shutdown()
            except Exception:
                pass

    def observe(
        self,
        *,
        broker_order_id: str,
        symbol: str,
        side: str,
        requested_volume: float,
    ) -> dict[str, Any]:
        self._initialize()
        try:
            return observe_order(
                self.mt5,
                broker_order_id=broker_order_id,
                symbol=symbol,
                side=side,
                requested_volume=requested_volume,
            )
        except Exception as exc:
            if isinstance(exc, MT5RecoveryAdapterError):
                raise
            raise MT5RecoveryAdapterError(str(exc)) from exc
        finally:
            self._shutdown()
