from research.optimization import g13_promotion_gate_m15 as gate


def _good() -> dict:
    return {
        "schema_version": "forexai.g13.promotion_evidence_provenance.m15.v1",
        "sources": {
            "validation": {
                "run_id": gate.EXPECTED_VALIDATION_RUN,
                "conclusion": "success",
                "head_sha": "validation-sha",
                "local_zip_sha256": "a" * 64,
                "artifact": {
                    "artifact_id": gate.EXPECTED_VALIDATION_ARTIFACT,
                    "digest": "sha256:" + "a" * 64,
                    "expired": False,
                },
            },
            "robustness": {
                "run_id": gate.EXPECTED_ROBUST_RUN,
                "conclusion": "success",
                "head_sha": "robust-sha",
                "local_zip_sha256": "b" * 64,
                "artifact": {
                    "artifact_id": gate.EXPECTED_ROBUST_ARTIFACT,
                    "digest": "sha256:" + "b" * 64,
                    "expired": False,
                },
            },
            "oos": {
                "run_id": gate.EXPECTED_OOS_RUN,
                "conclusion": "success",
                "head_sha": "oos-sha",
                "local_zip_sha256": "c" * 64,
                "artifact": {
                    "artifact_id": gate.EXPECTED_OOS_ARTIFACT,
                    "digest": "sha256:" + "c" * 64,
                    "expired": False,
                },
            },
        },
    }


def test_valid_provenance_is_accepted():
    gate.validate_provenance(_good())


def test_wrong_run_id_is_rejected():
    p = _good()
    p["sources"]["oos"]["run_id"] += 1
    try:
        gate.validate_provenance(p)
    except AssertionError:
        return
    raise AssertionError("wrong OOS run id was accepted")


def test_zip_digest_mismatch_is_rejected():
    p = _good()
    p["sources"]["robustness"]["local_zip_sha256"] = "0" * 64
    try:
        gate.validate_provenance(p)
    except AssertionError:
        return
    raise AssertionError("artifact byte digest mismatch was accepted")


def test_expired_artifact_is_rejected():
    p = _good()
    p["sources"]["validation"]["artifact"]["expired"] = True
    try:
        gate.validate_provenance(p)
    except AssertionError:
        return
    raise AssertionError("expired artifact was accepted")
