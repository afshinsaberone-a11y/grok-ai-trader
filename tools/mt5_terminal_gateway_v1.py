"""Real MetaTrader 5 Python terminal gateway v1.

Optional Windows/MT5 transport implementation for the execution adapter.
This module never creates capital authority and never retries broker I/O.

The MetaTrader5 package is imported lazily so Linux CI can exercise the contract
with a fake module without installing or connecting to MT5.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping

from tools.execution_admission_v1 import verify_admission_auth


class MT5GatewayError(RuntimeError):
    """Fail-closed MT5 terminal gateway error."""


EXECUTION_ADMISSION_SCHEMA = "forexai.execution_admission.v1"
EXECUTION_CONTRACT_VERSION = "forexai.execution.v1"


def _request_hash(request: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            dict(request),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _validate_admission_for_gateway(
    request: Mapping[str, Any],
    admission: Mapping[str, Any],
    *,
    control_plane_secret: str | bytes,
) -> None:
    required = {
        "schema",
        "status",
        "trade_id",
        "authorization_id",
        "reservation_id",
        "symbol",
        "timeframe",
        "side",
        "volume",
        "risk_fraction",
        "stop_loss",
        "take_profit",
        "execution_contract_version",
        "current_firewall_authority",
        "control_plane_authenticated",
        "request_hash",
        "admission_auth_schema",
        "admission_auth_algorithm",
        "admission_auth_tag",
    }
    if set(admission) != required:
        raise MT5GatewayError("MT5_GATEWAY_ADMISSION_FIELDS_MISMATCH")
    if admission["schema"] != EXECUTION_ADMISSION_SCHEMA:
        raise MT5GatewayError("MT5_GATEWAY_ADMISSION_SCHEMA_MISMATCH")
    if admission["status"] != "PASS":
        raise MT5GatewayError("MT5_GATEWAY_ADMISSION_NOT_PASSED")
    if admission["current_firewall_authority"] != "PASS":
        raise MT5GatewayError("MT5_GATEWAY_AUTHORITY_NOT_CURRENT")
    if admission["control_plane_authenticated"] is not True:
        raise MT5GatewayError("MT5_GATEWAY_CONTROL_PLANE_AUTH_REQUIRED")
    if admission["execution_contract_version"] != EXECUTION_CONTRACT_VERSION:
        raise MT5GatewayError("MT5_GATEWAY_EXECUTION_CONTRACT_MISMATCH")
    verify_admission_auth(admission, secret=control_plane_secret)
    if request.get("trade_id") != admission["trade_id"]:
        raise MT5GatewayError("MT5_GATEWAY_TRADE_ID_MISMATCH")
    if request.get("symbol") != admission["symbol"]:
        raise MT5GatewayError("MT5_GATEWAY_SYMBOL_MISMATCH")
    if request.get("timeframe") != admission["timeframe"]:
        raise MT5GatewayError("MT5_GATEWAY_TIMEFRAME_MISMATCH")
    if request.get("side") != admission["side"]:
        raise MT5GatewayError("MT5_GATEWAY_SIDE_MISMATCH")
    if _request_hash(request) != admission["request_hash"]:
        raise MT5GatewayError("MT5_GATEWAY_REQUEST_HASH_MISMATCH")
    try:
        risk = float(admission["risk_fraction"])
    except (TypeError, ValueError, OverflowError) as exc:
        raise MT5GatewayError("MT5_GATEWAY_RISK_INVALID") from exc
    if not math.isfinite(risk) or risk <= 0 or risk > 0.006:
        raise MT5GatewayError("MT5_GATEWAY_RISK_INVALID")


@dataclass(frozen=True)
class MT5GatewayConfig:
    terminal_path: str | None = None
    login: int | None = None
    password: str | None = None
    server: str | None = None
    timeout_ms: int = 60_000
    deviation_points: int = 20
    magic: int = 2026051
    comment: str = "ForexAI-Authorized"
    shutdown_after_request: bool = True
    account_mode: str = "DEMO_ONLY"
    real_trading_confirmation_env: str = "FOREXAI_ALLOW_REAL_TRADING"
    control_plane_secret_env: str = "FOREXAI_CONTROL_PLANE_HMAC_SECRET"
    control_plane_secret: str | bytes | None = None


class MT5TerminalGateway:
    def __init__(self, config: MT5GatewayConfig | None = None, *, mt5_module: Any | None = None):
        self.config = config or MT5GatewayConfig()
        self._mt5 = mt5_module

    @property
    def mt5(self) -> Any:
        if self._mt5 is None:
            try:
                import MetaTrader5 as mt5
            except ImportError as exc:
                raise MT5GatewayError("MT5_PYTHON_PACKAGE_NOT_INSTALLED") from exc
            self._mt5 = mt5
        return self._mt5

    def _initialize(self) -> None:
        mt5 = self.mt5
        kwargs: dict[str, Any] = {"timeout": self.config.timeout_ms}
        if self.config.login is not None:
            kwargs["login"] = self.config.login
        if self.config.password is not None:
            kwargs["password"] = self.config.password
        if self.config.server is not None:
            kwargs["server"] = self.config.server
        try:
            ok = mt5.initialize(self.config.terminal_path, **kwargs) if self.config.terminal_path else mt5.initialize(**kwargs)
        except Exception as exc:
            raise MT5GatewayError("MT5_INITIALIZE_EXCEPTION") from exc
        if not ok:
            last_error = getattr(mt5, "last_error", lambda: None)()
            raise MT5GatewayError(f"MT5_INITIALIZE_FAILED:{last_error}")

    def _assert_account_mode(self) -> None:
        info = self.mt5.account_info()
        if info is None:
            raise MT5GatewayError("MT5_ACCOUNT_INFO_UNAVAILABLE")

        raw_trade_mode = getattr(info, "trade_mode", None)
        if raw_trade_mode is None:
            raise MT5GatewayError("MT5_ACCOUNT_TRADE_MODE_UNAVAILABLE")
        demo_constant = getattr(self.mt5, "ACCOUNT_TRADE_MODE_DEMO", None)
        real_constant = getattr(self.mt5, "ACCOUNT_TRADE_MODE_REAL", None)
        if demo_constant is None or real_constant is None:
            raise MT5GatewayError("MT5_ACCOUNT_TRADE_MODE_CONSTANTS_UNAVAILABLE")
        try:
            trade_mode = int(raw_trade_mode)
            demo_mode = int(demo_constant)
            real_mode = int(real_constant)
        except (TypeError, ValueError, OverflowError) as exc:
            raise MT5GatewayError("MT5_ACCOUNT_TRADE_MODE_INVALID") from exc

        for field in ("trade_allowed", "trade_expert"):
            value = getattr(info, field, None)
            if not isinstance(value, bool) or not value:
                raise MT5GatewayError(f"MT5_ACCOUNT_{field.upper()}_NOT_ALLOWED")

        if self.config.account_mode == "DEMO_ONLY":
            if trade_mode != demo_mode:
                raise MT5GatewayError(
                    "MT5_REAL_ACCOUNT_BLOCKED_BY_DEMO_ONLY_POLICY"
                )
            return

        if self.config.account_mode == "REAL_ALLOWED":
            import os
            if os.environ.get(self.config.real_trading_confirmation_env) != "CONFIRMED":
                raise MT5GatewayError(
                    "MT5_REAL_ACCOUNT_REQUIRES_EXTERNAL_CONFIRMATION"
                )
            if trade_mode not in {demo_mode, real_mode}:
                raise MT5GatewayError("MT5_ACCOUNT_TRADE_MODE_INVALID")
            return

        raise MT5GatewayError("MT5_ACCOUNT_MODE_POLICY_INVALID")

    def _shutdown(self) -> None:
        if self.config.shutdown_after_request:
            try:
                self.mt5.shutdown()
            except Exception:
                # Shutdown failure must not be used to claim execution failure.
                # The order result is already authoritative for this call.
                pass

    def _select_filling(self, symbol_info: Any) -> int:
        mt5 = self.mt5
        trade_exemode = getattr(symbol_info, "trade_exemode", None)
        if trade_exemode != getattr(mt5, "SYMBOL_TRADE_EXECUTION_MARKET", object()):
            return getattr(mt5, "ORDER_FILLING_RETURN")

        flags = int(getattr(symbol_info, "filling_mode", 0))
        if flags & int(getattr(mt5, "SYMBOL_FILLING_FOK")):
            return getattr(mt5, "ORDER_FILLING_FOK")
        if flags & int(getattr(mt5, "SYMBOL_FILLING_IOC")):
            return getattr(mt5, "ORDER_FILLING_IOC")
        raise MT5GatewayError("MT5_NO_SUPPORTED_MARKET_FILLING_MODE")

    @staticmethod
    def _result_dict(result: Any) -> dict[str, Any]:
        if result is None:
            raise MT5GatewayError("MT5_ORDER_SEND_RETURNED_NONE")
        if hasattr(result, "_asdict"):
            return dict(result._asdict())
        if isinstance(result, Mapping):
            return dict(result)
        if hasattr(result, "__dict__"):
            return dict(vars(result))
        raise MT5GatewayError("MT5_ORDER_SEND_RESULT_INVALID")

    def submit_authorized_order(
        self,
        *,
        request: Mapping[str, Any],
        admission: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        secret = self.config.control_plane_secret
        if secret is None:
            import os
            secret = os.environ.get(self.config.control_plane_secret_env)
        if not secret:
            raise MT5GatewayError("MT5_GATEWAY_CONTROL_PLANE_SECRET_NOT_CONFIGURED")
        try:
            _validate_admission_for_gateway(
                request,
                admission,
                control_plane_secret=secret,
            )
        except Exception as exc:
            if isinstance(exc, MT5GatewayError):
                raise
            raise MT5GatewayError(str(exc)) from exc
        mt5 = self.mt5
        self._initialize()
        try:
            self._assert_account_mode()
            symbol = str(admission["symbol"])
            side = str(admission["side"])
            volume = float(admission["volume"])
            sl = float(admission["stop_loss"])
            tp = float(admission["take_profit"])

            info = mt5.symbol_info(symbol)
            if info is None:
                raise MT5GatewayError("MT5_SYMBOL_NOT_FOUND")
            visible = getattr(info, "visible", None)
            if not isinstance(visible, bool):
                raise MT5GatewayError("MT5_SYMBOL_VISIBILITY_UNAVAILABLE")
            if not visible:
                if not mt5.symbol_select(symbol, True):
                    raise MT5GatewayError("MT5_SYMBOL_SELECT_FAILED")

            raw_symbol_trade_mode = getattr(info, "trade_mode", None)
            raw_order_mode = getattr(info, "order_mode", None)
            if raw_symbol_trade_mode is None or raw_order_mode is None:
                raise MT5GatewayError("MT5_SYMBOL_PERMISSION_METADATA_UNAVAILABLE")
            try:
                symbol_trade_mode = int(raw_symbol_trade_mode)
                order_mode = int(raw_order_mode)
            except (TypeError, ValueError, OverflowError) as exc:
                raise MT5GatewayError("MT5_SYMBOL_PERMISSION_METADATA_INVALID") from exc

            disabled = int(getattr(mt5, "SYMBOL_TRADE_MODE_DISABLED", 0))
            close_only = int(getattr(mt5, "SYMBOL_TRADE_MODE_CLOSEONLY", 3))
            long_only = int(getattr(mt5, "SYMBOL_TRADE_MODE_LONGONLY", 1))
            short_only = int(getattr(mt5, "SYMBOL_TRADE_MODE_SHORTONLY", 2))
            if symbol_trade_mode in {disabled, close_only}:
                raise MT5GatewayError("MT5_SYMBOL_NOT_OPEN_FOR_ENTRY")
            if side == "BUY" and symbol_trade_mode == short_only:
                raise MT5GatewayError("MT5_SYMBOL_BUY_NOT_ALLOWED")
            if side == "SELL" and symbol_trade_mode == long_only:
                raise MT5GatewayError("MT5_SYMBOL_SELL_NOT_ALLOWED")

            required_order_flags = (
                int(getattr(mt5, "SYMBOL_ORDER_MARKET", 0))
                | int(getattr(mt5, "SYMBOL_ORDER_SL", 0))
                | int(getattr(mt5, "SYMBOL_ORDER_TP", 0))
            )
            if required_order_flags == 0 or (order_mode & required_order_flags) != required_order_flags:
                raise MT5GatewayError("MT5_SYMBOL_REQUIRED_ORDER_FLAGS_NOT_ALLOWED")

            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                raise MT5GatewayError("MT5_TICK_UNAVAILABLE")
            price = float(tick.ask if side == "BUY" else tick.bid)
            if not math.isfinite(price) or price <= 0:
                raise MT5GatewayError("MT5_MARKET_PRICE_INVALID")

            order_type = (
                mt5.ORDER_TYPE_BUY if side == "BUY" else mt5.ORDER_TYPE_SELL
            )
            filling = self._select_filling(info)
            trade_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": self.config.deviation_points,
                "magic": self.config.magic,
                "comment": self.config.comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": filling,
            }

            try:
                check = mt5.order_check(trade_request)
            except Exception as exc:
                raise MT5GatewayError("MT5_ORDER_CHECK_EXCEPTION") from exc
            if check is None:
                raise MT5GatewayError("MT5_ORDER_CHECK_RETURNED_NONE")
            check_dict = self._result_dict(check)
            check_retcode = int(check_dict.get("retcode", -1))
            if check_retcode != 0:
                return {
                    "status": "REJECTED",
                    "symbol": symbol,
                    "timeframe": admission["timeframe"],
                    "side": side,
                    "volume": volume,
                    "broker_order_id": None,
                    "broker_deal_id": None,
                    "broker_retcode": str(check_retcode),
                    "broker_reason": str(check_dict.get("comment", "order_check rejected")),
                    "filled_volume": 0.0,
                    "remaining_volume": volume,
                }

            try:
                result = mt5.order_send(trade_request)
            except Exception as exc:
                # Unknown transport outcome is deliberately surfaced to the
                # execution adapter, which journals and blocks blind retries.
                raise MT5GatewayError("MT5_ORDER_SEND_EXCEPTION") from exc

            result_dict = self._result_dict(result)
            retcode = int(result_dict.get("retcode", -1))
            order_id = result_dict.get("order")
            deal_id = result_dict.get("deal")
            filled_volume = float(result_dict.get("volume", 0.0) or 0.0)
            broker_comment = str(result_dict.get("comment", ""))

            done = int(getattr(mt5, "TRADE_RETCODE_DONE"))
            partial = int(getattr(mt5, "TRADE_RETCODE_DONE_PARTIAL"))
            placed = int(getattr(mt5, "TRADE_RETCODE_PLACED"))

            common = {
                "symbol": symbol,
                "timeframe": admission["timeframe"],
                "side": side,
                "volume": volume,
                "broker_order_id": str(order_id) if order_id not in (None, 0) else None,
                "broker_deal_id": str(deal_id) if deal_id not in (None, 0) else None,
                "broker_retcode": str(retcode),
                "filled_volume": filled_volume,
                "remaining_volume": max(0.0, volume - filled_volume),
            }

            if retcode == done and deal_id not in (None, 0):
                return {"status": "ACCEPTED", **common}

            if retcode == done:
                raise MT5GatewayError("MT5_DONE_WITHOUT_DEAL")

            if retcode == partial:
                return {"status": "PARTIAL", **common}

            if retcode == placed:
                return {
                    "status": "PENDING",
                    **common,
                    "broker_reason": broker_comment or "order placed without deal ticket",
                }

            return {
                "status": "REJECTED",
                **common,
                "broker_reason": broker_comment or "broker rejected execution request",
                "filled_volume": 0.0,
                "remaining_volume": volume,
                "broker_deal_id": None,
            }
        finally:
            self._shutdown()
