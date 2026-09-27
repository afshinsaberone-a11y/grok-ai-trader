import json

from tools.validate_dropbox_contract import ContractError, validate


def test_repository_map_contract_passes():
    mapping = json.loads(open("config/dropbox_repository_map.json", encoding="utf-8").read())
    result = validate(mapping)
    assert result["status"] == "PASS"
    assert result["root"] == "/ForexAI"
    assert result["hash_algorithm"] == "SHA-256"
    assert result["utc_required"] is True


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
