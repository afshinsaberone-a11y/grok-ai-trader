import ast
import re
from pathlib import Path


def test_source_wheel_builder_has_immutable_sources_and_discloses_signature_status():
    root = Path(__file__).resolve().parents[1]
    builder_path = root / "tools" / "build_provider_source_wheel_candidate_v1.py"
    source = builder_path.read_text(encoding="utf-8")
    module = ast.parse(source, filename=str(builder_path))
    assignments = {}
    for node in module.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            assignments[node.targets[0].id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            assignments[node.target.id] = node.value
    specs = ast.literal_eval(assignments["SOURCE_SPECS"])
    assert {item["name"] for item in specs} == {"cffi", "pycparser", "colorama", "pygments"}
    assert all(re.fullmatch(r"[0-9a-f]{40}", item["commit"]) for item in specs)
    assert all(item["git_url"].startswith("https://github.com/") for item in specs)
    assert next(item for item in specs if item["name"] == "cffi")["expected_signature_verified"] is True
    assert all(
        item["expected_signature_verified"] is False
        for item in specs if item["name"] != "cffi"
    )
    assert all(term in source for term in ("git", "checkout", "HEAD"))
    assert "github_commit_signature_verified" in source
    assert "UNSIGNED_COMMIT_REQUIRES_INDEPENDENT_SOURCE_REVIEW" in source
    assert 'production_approved": False' in source
    assert 'bootstrap_approved": False' in source
    assert "transitive_build_tool_dependencies_hash_locked" in source


def test_source_wheel_candidate_workflow_is_pinned_and_cannot_deploy_or_trade():
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github" / "workflows" / "provider-source-wheel-candidate.yml").read_text(encoding="utf-8")
    refs = re.findall(r"(?m)^\s*uses:\s*([^\s#]+)", workflow)
    assert refs == [
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
        "actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0",
        "actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6",
        "actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6",
        "actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9",
    ]
    assert "runs-on: windows-2022" in workflow
    assert "permissions:\n  contents: read\n  id-token: write\n  attestations: write\n  artifact-metadata: write" in workflow
    assert "persist-credentials: false" in workflow
    assert "contents: write" not in workflow
    assert "secrets:" not in workflow
    assert "subject-path: artifacts/provider-source-build/wheels/*.whl" in workflow
    assert "predicate-path: artifacts/provider-source-build/source-build-manifest.json" in workflow
    assert "gh attestation verify" in workflow
    assert "PRODUCTION_LOCKS_CHANGED=false" in workflow
    assert "BOOTSTRAP_AUTHORIZED=false" in workflow
    assert "DEMO_TRADING_AUTHORIZED=false" in workflow
    assert "LIVE_TRADING_ALLOWED=false" in workflow
    assert "ORDERS_SUBMITTED=false" in workflow
    assert "order_send" not in workflow


def test_offline_lock_overlay_assembly_fails_closed_and_preserves_hashes():
    import importlib.util

    root = Path(__file__).resolve().parents[1]
    helper_path = root / "tools" / "assemble_provider_offline_wheelhouse_v1.py"
    helper_source = helper_path.read_text(encoding="utf-8")
    spec = importlib.util.spec_from_file_location("offline_wheelhouse_candidate_helper", helper_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    first, second, added = "a" * 64, "b" * 64, "c" * 64
    sample = (
        "cffi==2.1.1 \\\n"
        f"    --hash=sha256:{first} \\\n"
        f"    --hash=sha256:{second}\n"
        "    # via cryptography\n"
        "cryptography==50.0.2 \\\n"
        f"    --hash=sha256:{'d' * 64}\n"
    )
    updated = module.add_hash(sample, "cffi", "2.1.1", added)
    assert f"--hash=sha256:{first}" in updated
    assert f"--hash=sha256:{second}" in updated
    assert f"--hash=sha256:{added}" in updated
    assert updated.count(f"--hash=sha256:{added}") == 1
    try:
        module.add_hash(sample, "cffi", "2.0.0", added)
    except RuntimeError as exc:
        assert "LOCK_PACKAGE_VERSION_MISMATCH" in str(exc)
    else:
        raise AssertionError("wrong package version must fail closed")
    try:
        module.add_hash(sample, "cffi", "2.1.1", "bad")
    except ValueError as exc:
        assert "CUSTOM_WHEEL_SHA256_INVALID" in str(exc)
    else:
        raise AssertionError("bad custom wheel digest must fail closed")

    assert "PASS_CRYPTOGRAPHICALLY_VERIFIED_EXPECTED_REPOSITORY" in helper_source
    assert "BLOCKED_PROVENANCE_MISSING" in helper_source
    assert "additional_custom_wheel_hashes" in helper_source
    assert 'production_approved":False' in helper_source or '"production_approved":False' in helper_source


def test_source_wheel_workflow_enforces_offline_candidate_lock_gates():
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github" / "workflows" / "provider-source-wheel-candidate.yml").read_text(encoding="utf-8")
    helper = (root / "tools" / "assemble_provider_offline_wheelhouse_v1.py").read_text(encoding="utf-8")
    assert "pip download --disable-pip-version-check --require-hashes --only-binary=:all: --no-deps" in workflow
    assert "--no-index --find-links $wheelhouse --require-hashes --only-binary=:all:" in workflow
    assert "OFFLINE_PROVIDER_CONTRACT_TESTS_FAILED" in workflow
    assert "provider-offline-wheelhouse/v1" in workflow
    assert workflow.count("uses: actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6") == 2
    assert "WHEELHOUSE_ATTESTATION_VERIFICATION_FAILED" in workflow
    assert "production_approved" in helper and "bootstrap_approved" in helper
    assert "BOOTSTRAP_AUTHORIZED=false" in workflow
    assert "DEMO_TRADING_AUTHORIZED=false" in workflow
    assert "LIVE_TRADING_ALLOWED=false" in workflow
    assert "ORDERS_SUBMITTED=false" in workflow
    assert "order_send" not in workflow


def test_source_build_tool_closure_is_hash_locked_and_manifest_binds_exact_lock():
    root = Path(__file__).resolve().parents[1]
    lock_path = root / "requirements-provider-source-build-tools.lock.txt"
    lock_text = lock_path.read_text(encoding="utf-8")
    workflow = (root / ".github" / "workflows" / "provider-source-wheel-candidate.yml").read_text(encoding="utf-8")
    builder = (root / "tools" / "build_provider_source_wheel_candidate_v1.py").read_text(encoding="utf-8")

    expected = {
        "hatchling": "1.27.0",
        "packaging": "26.3",
        "pathspec": "1.1.1",
        "pip": "26.2.2",
        "pluggy": "1.7.0",
        "setuptools": "80.9.0",
        "trove-classifiers": "2026.9.21.13",
        "wheel": "0.45.1",
    }
    pins = {
        re.sub(r"[-_.]+", "-", name).lower(): version
        for name, version in re.findall(
            r"(?m)^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s\\]+)\s*\\?\s*$",
            lock_text,
        )
    }
    assert pins == expected
    hashes = re.findall(r"--hash=sha256:([0-9a-f]{64})", lock_text)
    assert len(hashes) == len(expected)
    assert all(len(value) == 64 for value in hashes)

    assert "requirements-provider-source-build-tools.lock.txt" in workflow
    assert "--require-hashes --only-binary=:all: -r $buildToolsLock" in workflow
    assert "SOURCE_BUILD_TOOL_HASH_LOCK_INSTALL_FAILED" in workflow
    assert "SOURCE_BUILD_TOOL_FREEZE_MISMATCH" in workflow
    assert "'pip==26.2.2'" in workflow
    assert "BUILD_TOOL_LOCK_FILENAME" in builder
    assert "SOURCE_BUILD_TOOL_LOCK_PINS_MISMATCH" in builder
    assert "SOURCE_BUILD_TOOL_LOCK_HASH_COUNT_MISMATCH" in builder
    assert "SOURCE_BUILD_TOOL_FREEZE_MISMATCH" in builder
    assert '"transitive_build_tool_dependencies_hash_locked": True' in builder
    # Hash-locking fixes byte integrity, not missing publisher provenance.
    assert "setuptools==80.9.0" in lock_text
    assert '"packages_without_verified_pypi_provenance": ["setuptools==80.9.0"]' in builder
    assert '"production_approved": False' in builder
    assert '"bootstrap_approved": False' in builder
