"""Capital authorization and reservation firewall v1.

No authorization -> no capital.
The firewall is intentionally strategy-agnostic and delegates durable history to
the append-only TradeLedger. It never changes research evidence or creates market
data.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from tools.trade_ledger_v1 import LedgerError, TradeLedger

REQUIRED_PROOF = {
    "snapshot_id",
    "decision_id",
    "strategy_id",
    "model_id",
    "policy_version",
    "risk_authorization_id",
    "authorization_expiry",
    "input_hash",
    "execution_contract_version",
}


class CapitalFirewallError(RuntimeError):
    """Fail-closed capital/risk authorization error."""


class AuthorizationError(CapitalFirewallError):
    """Authorization is missing, invalid, revoked, or expired."""


class ReservationError(CapitalFirewallError):
    """Capital reservation violates authorization or duplication rules."""


@dataclass(frozen=True)
class RiskAuthorization:
    authorization_id: str
    trade_id: str
    authorized_risk: float
    issued_at_utc: str
    expires_at_utc: str
    proof: dict[str, Any]
    status: str = "ACTIVE"


def _parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AuthorizationError("AUTHORIZATION_TIMESTAMP_INVALID") from exc
    if parsed.tzinfo is None:
        raise AuthorizationError("AUTHORIZATION_TIMESTAMP_MUST_BE_TIMEZONE_AWARE")
    return parsed.astimezone(timezone.utc)


def _expired(expires_at_utc: str, now_utc: str | None = None) -> bool:
    now = _parse_utc(now_utc or datetime.now(timezone.utc).isoformat())
    return now >= _parse_utc(expires_at_utc)


class CapitalFirewall:
    """Deterministic authorization/reservation guard over a TradeLedger."""

    def __init__(self, ledger: TradeLedger, *, max_authorized_risk: float = 0.006):
        if max_authorized_risk <= 0 or max_authorized_risk > 0.006:
            raise ValueError("MAX_AUTHORIZED_RISK_OUT_OF_POLICY")
        self.ledger = ledger
        self.max_authorized_risk = float(max_authorized_risk)

    def _events(self, trade_id: str, event_type: str) -> list[Any]:
        return [
            event for event in self.ledger.events
            if event.trade_id == trade_id and event.event_type == event_type
        ]

    def _event_by_idempotency(self, trade_id: str, idempotency_key: str) -> Any | None:
        matches = [
            event for event in self.ledger.events
            if event.trade_id == trade_id and event.idempotency_key == idempotency_key
        ]
        if len(matches) > 1:
            raise CapitalFirewallError("IDEMPOTENCY_KEY_NOT_UNIQUE")
        return matches[0] if matches else None

    def _assert_idempotent_semantics(self, existing: Any, *, event_type: str, payload: Mapping[str, Any]) -> None:
        if existing.event_type != event_type or existing.payload != dict(payload):
            raise CapitalFirewallError("IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_SEMANTICS")

    def _authorization(self, trade_id: str, authorization_id: str) -> RiskAuthorization:
        events = [
            event for event in self._events(trade_id, "CAPITAL_AUTHORIZATION_ISSUED")
            if event.payload.get("authorization_id") == authorization_id
        ]
        if len(events) != 1:
            raise AuthorizationError("AUTHORIZATION_NOT_FOUND_OR_AMBIGUOUS")
        payload = events[0].payload
        return RiskAuthorization(
            authorization_id=authorization_id,
            trade_id=trade_id,
            authorized_risk=float(payload["authorized_risk"]),
            issued_at_utc=str(payload["issued_at_utc"]),
            expires_at_utc=str(payload["expires_at_utc"]),
            proof=dict(payload["proof"]),
            status=str(payload.get("status", "ACTIVE")),
        )

    def _assert_authorization_current(
        self,
        auth: RiskAuthorization,
        now_utc: str | None = None,
    ) -> None:
        if auth.status != "ACTIVE":
            raise AuthorizationError("AUTHORIZATION_NOT_ACTIVE")
        if _expired(auth.expires_at_utc, now_utc):
            raise AuthorizationError("AUTHORIZATION_EXPIRED")

    def _active_reserved_amount(self, trade_id: str, authorization_id: str) -> float:
        created = {
            str(event.payload["reservation_id"]): float(event.payload["amount"])
            for event in self._events(trade_id, "CAPITAL_RESERVATION_CREATED")
            if str(event.payload.get("authorization_id")) == authorization_id
        }
        released = {
            str(event.payload["reservation_id"])
            for event in self._events(trade_id, "CAPITAL_RESERVATION_RELEASED")
            if str(event.payload.get("authorization_id")) == authorization_id
        }
        return sum(amount for rid, amount in created.items() if rid not in released)

    def issue_authorization(
        self,
        *,
        trade_id: str,
        authorization_id: str,
        authorized_risk: float,
        issued_at_utc: str,
        expires_at_utc: str,
        proof: Mapping[str, Any],
        event_id: str,
        idempotency_key: str,
    ) -> RiskAuthorization:
        if not authorization_id or not trade_id:
            raise AuthorizationError("AUTHORIZATION_IDENTITY_MISSING")
        if not isinstance(authorized_risk, (int, float)) or authorized_risk <= 0:
            raise AuthorizationError("AUTHORIZED_RISK_MUST_BE_POSITIVE")
        if authorized_risk > self.max_authorized_risk:
            raise AuthorizationError("AUTHORIZED_RISK_EXCEEDS_GLOBAL_CAP")
        issued = _parse_utc(issued_at_utc)
        expires = _parse_utc(expires_at_utc)
        if expires <= issued:
            raise AuthorizationError("AUTHORIZATION_EXPIRY_MUST_BE_AFTER_ISSUANCE")
        if _expired(expires_at_utc, issued_at_utc):
            raise AuthorizationError("AUTHORIZATION_ALREADY_EXPIRED")

        proof_dict = dict(proof)
        if set(proof_dict) != REQUIRED_PROOF:
            missing = sorted(REQUIRED_PROOF - set(proof_dict))
            extra = sorted(set(proof_dict) - REQUIRED_PROOF)
            raise AuthorizationError(f"TRADE_PROOF_SCHEMA_MISMATCH:missing={missing}:extra={extra}")
        if proof_dict["risk_authorization_id"] != authorization_id:
            raise AuthorizationError("PROOF_AUTHORIZATION_ID_MISMATCH")
        if proof_dict["authorization_expiry"] != expires_at_utc:
            raise AuthorizationError("PROOF_AUTHORIZATION_EXPIRY_MISMATCH")

        payload = {
            "authorization_id": authorization_id,
            "authorized_risk": float(authorized_risk),
            "issued_at_utc": issued_at_utc,
            "expires_at_utc": expires_at_utc,
            "proof": proof_dict,
            "status": "ACTIVE",
        }
        existing = self._event_by_idempotency(trade_id, idempotency_key)
        if existing is not None:
            try:
                self._assert_idempotent_semantics(existing, event_type="CAPITAL_AUTHORIZATION_ISSUED", payload=payload)
            except CapitalFirewallError as exc:
                raise AuthorizationError(str(exc)) from exc
            return self._authorization(trade_id, authorization_id)

        self.ledger.assert_no_unresolved_reconciliation()
        if self.ledger.state_of(trade_id) != "RISK_RESERVED":
            raise AuthorizationError("TRADE_MUST_BE_RISK_RESERVED_BEFORE_AUTHORIZATION")

        self.ledger.append(
            trade_id=trade_id,
            state=None,
            event_type="CAPITAL_AUTHORIZATION_ISSUED",
            payload=payload,
            idempotency_key=idempotency_key,
            event_id=event_id,
            timestamp_utc=issued_at_utc,
        )
        return self._authorization(trade_id, authorization_id)

    def authorize_trade(
        self,
        *,
        trade_id: str,
        authorization_id: str,
        now_utc: str,
        event_id: str,
        idempotency_key: str,
    ) -> None:
        auth = self._authorization(trade_id, authorization_id)
        existing = self._event_by_idempotency(trade_id, idempotency_key)
        auth_payload = {
            "authorization_id": authorization_id,
            "authorization_expires_at": auth.expires_at_utc,
            "authorized_risk": auth.authorized_risk,
        }
        if existing is not None:
            try:
                self._assert_idempotent_semantics(existing, event_type="TRADE_AUTHORIZED", payload=auth_payload)
            except CapitalFirewallError as exc:
                raise AuthorizationError(str(exc)) from exc
            return
        self.ledger.assert_no_unresolved_reconciliation()
        self._assert_authorization_current(auth, now_utc)
        if self.ledger.state_of(trade_id) != "RISK_RESERVED":
            raise AuthorizationError("TRADE_STATE_NOT_READY_FOR_AUTHORIZATION")
        self.ledger.append(
            trade_id=trade_id,
            state="AUTHORIZED",
            event_type="TRADE_AUTHORIZED",
            payload=auth_payload,
            idempotency_key=idempotency_key,
            event_id=event_id,
            timestamp_utc=now_utc,
        )

    def reserve(
        self,
        *,
        trade_id: str,
        authorization_id: str,
        amount: float,
        reservation_id: str,
        now_utc: str,
        event_id: str,
        idempotency_key: str,
    ) -> None:
        auth = self._authorization(trade_id, authorization_id)
        existing_events = self._events(trade_id, "CAPITAL_RESERVATION_CREATED")
        same_reservation = [
            event for event in existing_events
            if event.payload.get("reservation_id") == reservation_id
        ]
        reservation_payload = {
            "reservation_id": reservation_id,
            "authorization_id": authorization_id,
            "amount": float(amount),
            "expires_at_utc": auth.expires_at_utc,
        }
        prior_by_key = self._event_by_idempotency(trade_id, idempotency_key)
        if same_reservation:
            prior = same_reservation[0]
            if prior.payload != reservation_payload:
                raise ReservationError("RESERVATION_ID_REUSED_WITH_DIFFERENT_SEMANTICS")
            return
        if prior_by_key is not None:
            try:
                self._assert_idempotent_semantics(prior_by_key, event_type="CAPITAL_RESERVATION_CREATED", payload=reservation_payload)
            except CapitalFirewallError as exc:
                raise ReservationError(str(exc)) from exc
            return

        self.ledger.assert_no_unresolved_reconciliation()
        self._assert_authorization_current(auth, now_utc)
        if self.ledger.state_of(trade_id) != "AUTHORIZED":
            raise ReservationError("TRADE_MUST_BE_AUTHORIZED_BEFORE_RESERVATION")
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ReservationError("RESERVATION_AMOUNT_MUST_BE_POSITIVE")
        if amount > auth.authorized_risk:
            raise ReservationError("RESERVATION_EXCEEDS_AUTHORIZED_RISK")
        if self._active_reserved_amount(trade_id, authorization_id) + float(amount) > auth.authorized_risk:
            raise ReservationError("ACTIVE_RESERVATIONS_EXCEED_AUTHORIZATION")
        self.ledger.append(
            trade_id=trade_id,
            state=None,
            event_type="CAPITAL_RESERVATION_CREATED",
            payload=reservation_payload,
            idempotency_key=idempotency_key,
            event_id=event_id,
            timestamp_utc=now_utc,
        )

    def assert_execution_allowed(
        self,
        *,
        trade_id: str,
        authorization_id: str,
        required_risk: float,
        now_utc: str,
    ) -> None:
        self.ledger.assert_no_unresolved_reconciliation()
        auth = self._authorization(trade_id, authorization_id)
        self._assert_authorization_current(auth, now_utc)
        if self.ledger.state_of(trade_id) != "AUTHORIZED":
            raise AuthorizationError("EXECUTION_REQUIRES_AUTHORIZED_STATE")
        if required_risk <= 0 or required_risk > auth.authorized_risk:
            raise AuthorizationError("EXECUTION_RISK_EXCEEDS_AUTHORIZATION")
        active = self._active_reserved_amount(trade_id, authorization_id)
        if active < required_risk:
            raise AuthorizationError("EXECUTION_REQUIRES_SUFFICIENT_CAPITAL_RESERVATION")

    def release(
        self,
        *,
        trade_id: str,
        authorization_id: str,
        reservation_id: str,
        now_utc: str,
        event_id: str,
        idempotency_key: str,
    ) -> None:
        self.ledger.assert_no_unresolved_reconciliation()
        prior_by_key = self._event_by_idempotency(trade_id, idempotency_key)
        auth = self._authorization(trade_id, authorization_id)
        if prior_by_key is not None:
            # The reservation payload must be known before accepting a retry.
            known = [
                event for event in self._events(trade_id, "CAPITAL_RESERVATION_CREATED")
                if event.payload.get("reservation_id") == reservation_id
                and event.payload.get("authorization_id") == authorization_id
            ]
            if len(known) != 1:
                raise ReservationError("RESERVATION_NOT_FOUND")
            release_payload = {
                "reservation_id": reservation_id,
                "authorization_id": authorization_id,
                "amount": float(known[0].payload["amount"]),
                "released_at_utc": now_utc,
                "authorization_status": auth.status,
            }
            try:
                self._assert_idempotent_semantics(prior_by_key, event_type="CAPITAL_RESERVATION_RELEASED", payload=release_payload)
            except CapitalFirewallError as exc:
                raise ReservationError(str(exc)) from exc
            return
        _parse_utc(now_utc)
        if self.ledger.state_of(trade_id) not in {"CLOSED", "RECONCILED"}:
            raise ReservationError("RESERVATION_RELEASE_REQUIRES_CLOSED_OR_RECONCILED_TRADE")
        reservations = [
            event for event in self._events(trade_id, "CAPITAL_RESERVATION_CREATED")
            if event.payload.get("reservation_id") == reservation_id
            and event.payload.get("authorization_id") == authorization_id
        ]
        if len(reservations) != 1:
            raise ReservationError("RESERVATION_NOT_FOUND")
        release_payload = {
            "reservation_id": reservation_id,
            "authorization_id": authorization_id,
            "amount": float(reservations[0].payload["amount"]),
            "released_at_utc": now_utc,
            "authorization_status": auth.status,
        }
        self.ledger.append(
            trade_id=trade_id,
            state=None,
            event_type="CAPITAL_RESERVATION_RELEASED",
            payload=release_payload,
            idempotency_key=idempotency_key,
            event_id=event_id,
            timestamp_utc=now_utc,
        )
