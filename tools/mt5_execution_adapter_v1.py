"""MT5 execution adapter boundary v1.

This is the production control-plane boundary between the current-authority
admission gate and a broker/MT5 transport. It deliberately does not contain a
network client or fabricate broker responses.

Safety property:
- admission must pass immediately before submission;
- ORDER_SUBMITTED is durably recorded before broker I/O;
- any broker I/O uncertainty leaves the trade unresolved and blocks blind retry;
- only an explicit broker response can advance the ledger to ACCEPTED or REJECTED; partial/unknown outcomes stay unresolved.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Protocol

from tools.capital_firewall_v1 import AuthorizationError, CapitalFirewall
from tools.execution_admission_v1 import check_execution_admission
from tools.runtime_authorization_auth_v1 import (
    DEFAULT_KEY_ID,
    DEFAULT_SECRET_ENV,
    ControlPlaneAuthenticationError,
    load_control_plane_secret,
    verify_authenticated_envelope_current,
)
from tools.trade_ledger_v1 import LedgerError, TradeLedger


class MT5ExecutionAdapterError(RuntimeError):
    """Fail-closed execution adapter error."""


class BrokerGateway(Protocol):
    def submit_authorized_order(
        self,
        *,
        request: Mapping[str, Any],
        admission: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Submit one already-admitted request to the broker transport."""


@dataclass(frozen=True)
class SubmissionResult:
    status: str
    trade_id: str
    authorization_id: str
    reservation_id: str
    request_hash: str
    broker_order_id: str | None
    broker_deal_id: str | None


_REQUIRED_BROKER_RESPONSE = {
    "status",
    "symbol",
    "timeframe",
    "side",
    "volume",
    "broker_order_id",
    "broker_deal_id",
    "broker_retcode",
}
_ALLOWED_BROKER_RESPONSE_FIELDS = _REQUIRED_BROKER_RESPONSE | {
    "broker_reason",
    "filled_volume",
    "remaining_volume",
}


def _require_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise MT5ExecutionAdapterError(f"BROKER_RESPONSE_{field.upper()}_INVALID")
    return value


class MT5ExecutionAdapter:
    def __init__(
        self,
        ledger: TradeLedger,
        firewall: CapitalFirewall,
        gateway: BrokerGateway,
        *,
        control_plane_secret: str | bytes,
        control_plane_key_id: str = "forexai-control-plane-v1",
    ) -> None:
        self.ledger = ledger
        self.firewall = firewall
        self.gateway = gateway
        self.control_plane_secret = control_plane_secret
        self.control_plane_key_id = control_plane_key_id

    @classmethod
    def from_environment(
        cls,
        ledger: TradeLedger,
        firewall: CapitalFirewall,
        gateway: BrokerGateway,
        *,
        secret_env: str = DEFAULT_SECRET_ENV,
        key_id_env: str = "FOREXAI_CONTROL_PLANE_KEY_ID",
    ) -> "MT5ExecutionAdapter":
        import os

        key_id = os.environ.get(key_id_env, DEFAULT_KEY_ID)
        return cls(
            ledger,
            firewall,
            gateway,
            control_plane_secret=load_control_plane_secret(secret_env),
            control_plane_key_id=key_id,
        )

    def submit(
        self,
        *,
        authenticated_envelope: Mapping[str, Any],
        request: Mapping[str, Any],
        now_utc: str,
        event_id: str,
        idempotency_key: str,
    ) -> SubmissionResult:
        try:
            authenticated = verify_authenticated_envelope_current(
                self.firewall,
                authenticated_envelope,
                secret=self.control_plane_secret,
                now_utc=now_utc,
                expected_key_id=self.control_plane_key_id,
            )
            envelope = authenticated_envelope["envelope"]
            admission = check_execution_admission(
                self.firewall,
                envelope,
                request=request,
                now_utc=now_utc,
            )
        except (AuthorizationError, LedgerError, ControlPlaneAuthenticationError) as exc:
            raise MT5ExecutionAdapterError(str(exc)) from exc

        trade_id = admission["trade_id"]
        authorization_id = admission["authorization_id"]
        reservation_id = admission["reservation_id"]
        request_hash = admission["request_hash"]

        if self.ledger.state_of(trade_id) != "AUTHORIZED":
            raise MT5ExecutionAdapterError("MT5_ADAPTER_TRADE_NOT_AUTHORIZED")

        submission_payload = {
            "authorization_id": authorization_id,
            "reservation_id": reservation_id,
            "request_hash": request_hash,
            "symbol": admission["symbol"],
            "timeframe": admission["timeframe"],
            "side": admission["side"],
            "volume": admission["volume"],
            "execution_contract_version": admission["execution_contract_version"],
        }

        self.ledger.assert_no_unresolved_reconciliation()
        try:
            self.ledger.append(
                trade_id=trade_id,
                state="ORDER_SUBMITTED",
                event_type="ORDER_SUBMITTED",
                payload=submission_payload,
                idempotency_key=idempotency_key,
                event_id=event_id,
                timestamp_utc=now_utc,
            )
        except Exception as exc:
            raise MT5ExecutionAdapterError("MT5_ADAPTER_ORDER_INTENT_NOT_DURABLE") from exc

        # No retry is attempted here. If broker I/O raises or times out, the
        # durable ORDER_SUBMITTED state forces broker reconciliation/recovery.
        try:
            response = self.gateway.submit_authorized_order(
                request=request,
                admission=admission,
            )
        except Exception as exc:
            try:
                self.ledger.append(
                    trade_id=trade_id,
                    state=None,
                    event_type="BROKER_OUTCOME_UNKNOWN",
                    payload={
                        **submission_payload,
                        "error_type": type(exc).__name__,
                    },
                    idempotency_key=idempotency_key + ":unknown",
                    event_id=event_id + ":unknown",
                    timestamp_utc=now_utc,
                )
            except Exception as journal_exc:
                raise MT5ExecutionAdapterError(
                    "MT5_ADAPTER_BROKER_OUTCOME_UNKNOWN_AND_JOURNAL_FAILED"
                ) from journal_exc
            raise MT5ExecutionAdapterError(
                "MT5_ADAPTER_BROKER_OUTCOME_UNKNOWN_RECONCILIATION_REQUIRED"
            ) from exc

        if not isinstance(response, Mapping):
            raise MT5ExecutionAdapterError("MT5_ADAPTER_BROKER_RESPONSE_NOT_MAPPING")
        response_fields = set(response)
        if not _REQUIRED_BROKER_RESPONSE <= response_fields:
            raise MT5ExecutionAdapterError("MT5_ADAPTER_BROKER_RESPONSE_FIELDS_MISSING")
        if not response_fields <= _ALLOWED_BROKER_RESPONSE_FIELDS:
            raise MT5ExecutionAdapterError("MT5_ADAPTER_BROKER_RESPONSE_FIELDS_UNKNOWN")

        status = response["status"]
        if status not in {"ACCEPTED", "REJECTED", "PARTIAL", "PENDING"}:
            raise MT5ExecutionAdapterError("MT5_ADAPTER_BROKER_STATUS_INVALID")

        for field in ("symbol", "timeframe", "side"):
            if response[field] != admission[field]:
                raise MT5ExecutionAdapterError(
                    f"MT5_ADAPTER_BROKER_{field.upper()}_MISMATCH"
                )
        if response["volume"] != admission["volume"]:
            raise MT5ExecutionAdapterError("MT5_ADAPTER_BROKER_VOLUME_MISMATCH")

        broker_order_id = response["broker_order_id"]
        if broker_order_id is not None:
            broker_order_id = _require_nonempty_string(broker_order_id, "broker_order_id")
        broker_deal_id = response["broker_deal_id"]
        if broker_deal_id is not None:
            broker_deal_id = _require_nonempty_string(broker_deal_id, "broker_deal_id")
        broker_retcode = _require_nonempty_string(response["broker_retcode"], "broker_retcode")

        requested_volume = float(admission["volume"])
        try:
            filled_volume = float(response.get("filled_volume", 0.0))
            remaining_volume = float(
                response.get("remaining_volume", max(0.0, requested_volume - filled_volume))
            )
        except (TypeError, ValueError, OverflowError) as exc:
            raise MT5ExecutionAdapterError("MT5_ADAPTER_BROKER_FILL_VOLUME_INVALID") from exc
        if (
            not math.isfinite(filled_volume)
            or not math.isfinite(remaining_volume)
            or filled_volume < 0
            or remaining_volume < 0
            or filled_volume > requested_volume
            or not math.isclose(
                filled_volume + remaining_volume,
                requested_volume,
                rel_tol=0.0,
                abs_tol=1e-9,
            )
        ):
            raise MT5ExecutionAdapterError("MT5_ADAPTER_BROKER_FILL_VOLUME_INVALID")

        if status == "PARTIAL":
            if not broker_order_id or filled_volume <= 0 or filled_volume >= requested_volume or remaining_volume <= 0:
                raise MT5ExecutionAdapterError("MT5_ADAPTER_PARTIAL_RESPONSE_INVALID")
            try:
                self.ledger.append(
                    trade_id=trade_id,
                    state=None,
                    event_type="BROKER_PARTIAL_EXECUTION_OBSERVED",
                    payload={
                        **submission_payload,
                        "broker_order_id": broker_order_id,
                        "broker_deal_id": broker_deal_id,
                        "broker_retcode": broker_retcode,
                        "filled_volume": filled_volume,
                        "remaining_volume": remaining_volume,
                    },
                    idempotency_key=idempotency_key + ":partial",
                    event_id=event_id + ":partial",
                    timestamp_utc=now_utc,
                )
            except Exception as exc:
                raise MT5ExecutionAdapterError(
                    "MT5_ADAPTER_PARTIAL_OUTCOME_JOURNAL_FAILED_RECONCILIATION_REQUIRED"
                ) from exc
            raise MT5ExecutionAdapterError(
                "MT5_ADAPTER_PARTIAL_EXECUTION_RECONCILIATION_REQUIRED"
            )

        if status == "PENDING":
            if not broker_order_id or broker_deal_id is not None or filled_volume != 0:
                raise MT5ExecutionAdapterError("MT5_ADAPTER_PENDING_RESPONSE_INVALID")
            pending_payload = {
                **submission_payload,
                "broker_order_id": broker_order_id,
                "broker_deal_id": None,
                "broker_retcode": broker_retcode,
                "broker_reason": _require_nonempty_string(
                    response.get("broker_reason"), "broker_reason"
                ),
                "filled_volume": 0.0,
                "remaining_volume": requested_volume,
            }
            try:
                self.ledger.append(
                    trade_id=trade_id,
                    state=None,
                    event_type="BROKER_ORDER_PENDING",
                    payload=pending_payload,
                    idempotency_key=idempotency_key + ":pending",
                    event_id=event_id + ":pending",
                    timestamp_utc=now_utc,
                )
            except Exception as exc:
                raise MT5ExecutionAdapterError(
                    "MT5_ADAPTER_PENDING_OUTCOME_JOURNAL_FAILED"
                ) from exc
            raise MT5ExecutionAdapterError(
                "MT5_ADAPTER_BROKER_ORDER_PENDING_RECONCILIATION_REQUIRED"
            )

        if status == "REJECTED":
            if filled_volume != 0 or broker_deal_id is not None:
                raise MT5ExecutionAdapterError("MT5_ADAPTER_REJECTED_RESPONSE_SHOWS_EXECUTION")
            broker_reason = _require_nonempty_string(
                response.get("broker_reason"), "broker_reason"
            )
            rejected_payload = {
                **submission_payload,
                "broker_order_id": broker_order_id,
                "broker_deal_id": None,
                "broker_retcode": broker_retcode,
                "broker_reason": broker_reason,
                "filled_volume": 0.0,
                "remaining_volume": requested_volume,
            }
            try:
                self.ledger.append(
                    trade_id=trade_id,
                    state="REJECTED",
                    event_type="BROKER_ORDER_REJECTED",
                    payload=rejected_payload,
                    idempotency_key=idempotency_key + ":rejected",
                    event_id=event_id + ":rejected",
                    timestamp_utc=now_utc,
                )
            except Exception as exc:
                raise MT5ExecutionAdapterError(
                    "MT5_ADAPTER_REJECTION_OUTCOME_NOT_DURABLE"
                ) from exc
            return SubmissionResult(
                status="REJECTED",
                trade_id=trade_id,
                authorization_id=authorization_id,
                reservation_id=reservation_id,
                request_hash=request_hash,
                broker_order_id=broker_order_id,
                broker_deal_id=None,
            )

        if filled_volume > requested_volume:
            raise MT5ExecutionAdapterError("MT5_ADAPTER_BROKER_FILL_VOLUME_OVERFLOW")

        accepted_payload = {
            **submission_payload,
            "broker_order_id": _require_nonempty_string(broker_order_id, "broker_order_id"),
            "broker_deal_id": broker_deal_id,
            "broker_retcode": broker_retcode,
            "filled_volume": filled_volume,
            "remaining_volume": remaining_volume,
            "fill_status": "FILLED" if filled_volume == requested_volume else "PENDING",
        }
        try:
            self.ledger.append(
                trade_id=trade_id,
                state="ACCEPTED",
                event_type="ACCEPTED",
                payload=accepted_payload,
                idempotency_key=idempotency_key + ":accepted",
                event_id=event_id + ":accepted",
                timestamp_utc=now_utc,
            )
        except Exception as exc:
            raise MT5ExecutionAdapterError(
                "MT5_ADAPTER_ACCEPTED_OUTCOME_NOT_DURABLE_RECONCILIATION_REQUIRED"
            ) from exc

        return SubmissionResult(
            status="ACCEPTED",
            trade_id=trade_id,
            authorization_id=authorization_id,
            reservation_id=reservation_id,
            request_hash=request_hash,
            broker_order_id=broker_order_id,
            broker_deal_id=broker_deal_id,
        )
