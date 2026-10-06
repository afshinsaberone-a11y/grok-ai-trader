import csv
from pathlib import Path

import pytest

from research.optimization import g13_controlled_demo_execution_audit as mod


FIELDS = list(mod.REQUIRED_COLUMNS)


def _row(**overrides):
    row = {
        "candidate_id": "2",
        "config_hash": "hash-2",
        "event": "ORDER_ATTEMPT",
        "timestamp_utc": "2026-10-04T21:00:00",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "side": "SELL",
        "order": "7001",
        "deal": "8001",
        "requested_volume": "0.10",
        "executed_volume": "0.10",
        "requested_price": "1.1000",
        "executed_price": "1.1001",
        "sl": "1.1010",
        "tp": "1.0985",
        "spread_points": "8",
        "slippage_points": "1",
        "retcode": "10009",
        "retcode_description": "Request completed",
        "elapsed_ms": "42",
        "comment": "ok",
    }
    row.update(overrides)
    return row


def _transaction(**overrides):
    row = _row(
        event="TRADE_TRANSACTION",
        side="SELL",
        requested_volume="0.0",
        executed_volume="0.10",
        requested_price="0.0",
        executed_price="1.1001",
        sl="0.0",
        tp="0.0",
        spread_points="0.0",
        slippage_points="0.0",
        retcode="10009",
        comment="deal observed",
    )
    row.update(overrides)
    return row


def _write_csv(path: Path, rows):
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _patch(monkeypatch):
    monkeypatch.setattr(mod, "load_promoted_ids", lambda _p: (2,))
    monkeypatch.setattr(mod, "load_frozen_hashes", lambda _p, _ids: {2: "hash-2"})
    monkeypatch.setattr(
        mod,
        "load_context",
        lambda _p: {
            "schema": "forexai.g13.controlled_demo_execution_context.v1",
            "account_mode": "DEMO",
            "live_enabled": False,
            "explicit_demo_authorization": True,
            "kill_switch": "ALLOW",
        },
    )


def test_audit_requires_done_full_fill_and_matching_transaction(tmp_path, monkeypatch):
    _patch(monkeypatch)
    csv_path = tmp_path / "audit.csv"
    _write_csv(csv_path, [_row(), _transaction()])
    result = mod.audit(csv_path, tmp_path / "handoff.json", tmp_path / "context.json", tmp_path / "promotion.json")
    assert result["status"] == "PASS"
    assert result["events"]["ORDER_ATTEMPT"] == 1
    assert result["events"]["TRADE_TRANSACTION"] == 1


@pytest.mark.parametrize(
    ("overrides", "error"),
    [
        ({"retcode": "10010"}, "retcode must be"),
        ({"executed_volume": "0.05"}, "executed_volume"),
        ({"order": "0"}, "broker order ticket missing"),
        ({"deal": "0"}, "broker deal ticket missing"),
    ],
)
def test_audit_rejects_non_accepted_execution(tmp_path, monkeypatch, overrides, error):
    _patch(monkeypatch)
    csv_path = tmp_path / "audit.csv"
    _write_csv(csv_path, [_row(**overrides), _transaction()])
    with pytest.raises(AssertionError) as excinfo:
        mod.audit(csv_path, tmp_path / "handoff.json", tmp_path / "context.json", tmp_path / "promotion.json")
    assert error in str(excinfo.value)


def test_audit_rejects_transaction_id_mismatch(tmp_path, monkeypatch):
    _patch(monkeypatch)
    csv_path = tmp_path / "audit.csv"
    _write_csv(csv_path, [_row(), _transaction(deal="9999")])
    with pytest.raises(AssertionError, match="no matching TRADE_TRANSACTION"):
        mod.audit(csv_path, tmp_path / "handoff.json", tmp_path / "context.json", tmp_path / "promotion.json")
