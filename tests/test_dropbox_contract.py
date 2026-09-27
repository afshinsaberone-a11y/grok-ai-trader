import json

from tools.validate_dropbox_contract import ContractError, validate
from tools.dropbox_healthcheck import configured_paths


def test_repository_map_contract_passes():
    mapping = json.loads(
        open("config/dropbox_repository_map.json", encoding="utf-8").read()
    )
    result = validate(mapping)
    assert result["status"] == "PASS"
    assert result["root"] == "/ForexAI"
    assert result["hash_algorithm"] == "SHA-256"
    assert result["utc_required"] is True


def test_repository_map_has_all_expected_planes():
    mapping = json.loads(
        open("config/dropbox_repository_map.json", encoding="utf-8").read()
    )
    paths = configured_paths(mapping)
    for expected in (
        "/ForexAI/00_CONTROL",
        "/ForexAI/01_RAW_MARKET_DATA",
        "/ForexAI/06_BACKTESTS",
        "/ForexAI/09_EVIDENCE_LEDGER",
        "/ForexAI/10_MQL5_RELEASES",
        "/ForexAI/11_GITHUB_ACTIONS",
        "/ForexAI/12_PROJECT_REPORTS",
    ):
        assert expected in paths


def test_repository_map_rejects_wrong_root():
    mapping = {
        "schema_version": "forexai.dropbox_repository_map.v1",
        "dropbox_root": "/Wrong",
        "planes": {},
        "naming": {"hash_algorithm": "SHA-256", "utc_required": True},
    }
    try:
        validate(mapping)
    except ContractError as exc:
        assert "dropbox_root" in str(exc)
    else:
        raise AssertionError("wrong root must fail closed")
