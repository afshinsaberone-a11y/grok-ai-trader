import ast
import hashlib
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
    assert all(item["release_tag"] for item in specs)
    assert all(item["expected_tag_object_type"] in {"commit", "tag"} for item in specs)
    assert all(re.fullmatch(r"[0-9a-f]{40}", item["expected_tag_object_sha"]) for item in specs)
    assert all(item["expected_release_tag_signature_verified"] is False for item in specs)
    assert "github_release_tag_metadata" in source
    assert "UPSTREAM_RELEASE_TAG_REF_CHANGED" in source
    assert "UPSTREAM_RELEASE_TAG_TARGET_COMMIT_MISMATCH" in source
    assert "UPSTREAM_RELEASE_TAG_SIGNATURE_STATUS_CHANGED" in source
    assert "upstream_sources_without_verified_commit_or_signed_release_tag" in source
    assert next(item for item in specs if item["name"] == "cffi")["expected_signature_verified"] is True
    assert all(
        item["expected_signature_verified"] is False
        for item in specs if item["name"] != "cffi"
    )
    assert all(term in source for term in ("git", "checkout", "HEAD"))
    assert "github_commit_signature_verified" in source
    assert "UNSIGNED_COMMIT_REQUIRES_INDEPENDENT_SOURCE_REVIEW" not in source
    assert "UNSIGNED_RELEASE_DIFF_EXACT_PATCH_HASHES_REQUIRE_INDEPENDENT_SOURCE_REVIEW" in source
    assert "UNSIGNED_UPSTREAM_FILE_BLOB_MISMATCH" in source
    assert "UNSIGNED_UPSTREAM_FILE_PATCH_MISMATCH" in source
    assert "UNSIGNED_UPSTREAM_FILE_PATCH_MISSING" in source
    assert "UNSIGNED_UPSTREAM_COMMIT_CHANGED_UNREVIEWED_FILES" in source
    assert "GITHUB_SOURCE_COMMIT_FILE_LIST_MISSING" in source
    unsigned_allowlists = {
        item["name"]: sorted(item["expected_unsigned_commit_files"])
        for item in specs if item["name"] != "cffi"
    }
    assert unsigned_allowlists == {
        "pycparser": ["MANIFEST.in", "pyproject.toml"],
        "colorama": ["README-hacking.md", "colorama/__init__.py"],
        "pygments": ["CHANGES", "pygments/__init__.py"],
    }
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
    assert workflow.count("uses: actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6") == 4
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

    # Path.read_text normalizes CRLF on Windows. The manifest digest must bind
    # this canonical LF text, not the autocrlf-dependent checkout bytes.
    canonical_lock_sha256 = hashlib.sha256(lock_text.encode("utf-8")).hexdigest()
    assert canonical_lock_sha256 == "72df1444b9b6994f598d1b4cb0e7e054545329a4157415285e91247882f0d7ec"
    assert 'build_tool_lock_sha256 = hashlib.sha256(build_tool_lock_text.encode("utf-8")).hexdigest()' in builder

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
    # The PyPI setuptools wheel is removed from this lock. A separate source-built
    # wheel is tied to signed upstream commit/tag metadata and its exact local hash.
    assert "setuptools==80.9.0" not in lock_text
    assert "build_provider_setuptools_source_bootstrap_v1.py" in workflow
    assert "provider-setuptools-source-bootstrap/v1" in workflow
    assert "SETUPTOOLS_BOOTSTRAP_HASH_LOCK_INSTALL_FAILED" in workflow
    assert "SETUPTOOLS_BOOTSTRAP_ATTESTATION_VERIFICATION_FAILED" in workflow
    assert "setuptools_source_bootstrap_manifest_sha256" in builder
    assert '"packages_without_verified_pypi_provenance": []' in builder
    assert '"source_built_packages_without_pypi_provenance": ["setuptools==80.9.0"]' in builder
    assert '"production_approved": False' in builder
    assert '"bootstrap_approved": False' in builder


def test_release_tag_metadata_binds_release_ref_to_exact_commit_and_reports_signature_state(monkeypatch):
    import importlib.util
    import json

    root = Path(__file__).resolve().parents[1]
    builder_path = root / "tools" / "build_provider_source_wheel_candidate_v1.py"
    spec = importlib.util.spec_from_file_location("provider_source_wheel_builder_tag_test", builder_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    cffi = next(item for item in module.SOURCE_SPECS if item["name"] == "cffi")
    calls = []

    class Response:
        def __init__(self, payload):
            self.payload = json.dumps(payload).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return self.payload

    def fake_urlopen(request, timeout=25):
        calls.append(request.full_url)
        return Response({
            "ref": "refs/tags/v2.1.1",
            "object": {
                "sha": "fd33e7700f0ebafe6f30bd5053f13327221b77a2",
                "type": "commit",
                "url": "https://api.github.com/repos/python-cffi/cffi/git/commits/fd33e7700f0ebafe6f30bd5053f13327221b77a2",
            },
        })

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)
    result = module.github_release_tag_metadata(cffi)
    assert result["github_release_tag"] == "v2.1.1"
    assert result["github_release_tag_target_commit"] == cffi["commit"]
    assert result["github_release_tag_object_type"] == "commit"
    assert result["github_release_tag_signature_verified"] is False
    assert result["upstream_release_identity_policy"] == (
        "UNSIGNED_RELEASE_TAG_REQUIRES_COMMIT_SIGNATURE_OR_INDEPENDENT_REVIEW"
    )
    assert len(calls) == 1

    pygments = next(item for item in module.SOURCE_SPECS if item["name"] == "pygments")
    calls.clear()

    def fake_annotated_urlopen(request, timeout=25):
        calls.append(request.full_url)
        if "/git/ref/tags/" in request.full_url:
            payload = {
                "ref": "refs/tags/2.21.0",
                "object": {
                    "sha": "2ade8335807203e11d67effb4108c78672519f0d",
                    "type": "tag",
                    "url": "https://api.github.com/repos/pygments/pygments/git/tags/2ade8335807203e11d67effb4108c78672519f0d",
                },
            }
        else:
            payload = {
                "sha": "2ade8335807203e11d67effb4108c78672519f0d",
                "tag": "2.21.0",
                "object": {
                    "sha": "a43b45dcf081b6010c6ab4428f149f7f6d2499c4",
                    "type": "commit",
                },
                "verification": {"verified": False, "reason": "unsigned"},
            }
        return Response(payload)

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_annotated_urlopen)
    annotated = module.github_release_tag_metadata(pygments)
    assert annotated["github_release_tag_ref_sha"] == pygments["expected_tag_object_sha"]
    assert annotated["github_release_tag_target_commit"] == pygments["commit"]
    assert annotated["github_release_tag_signature_verified"] is False
    assert annotated["github_release_tag_signature_reason"] == "unsigned"
    assert len(calls) == 2

    def fake_mismatched_urlopen(request, timeout=25):
        return Response({
            "ref": "refs/tags/2.21.0",
            "object": {
                "sha": "f" * 40,
                "type": "tag",
            },
        })

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_mismatched_urlopen)
    try:
        module.github_release_tag_metadata(pygments)
    except RuntimeError as exc:
        assert "UPSTREAM_RELEASE_TAG_REF_CHANGED" in str(exc)
    else:
        raise AssertionError("unexpectedly moved release tag must fail closed")


def test_helper_tool_lock_candidates_are_generated_hashed_and_offline_install_tested():
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github" / "workflows" / "provider-source-wheel-candidate.yml").read_text(encoding="utf-8")
    compiler_input = (root / "requirements-provider-lock-compiler.in").read_text(encoding="utf-8")
    verifier_input = (root / "requirements-provider-pypi-verifier.in").read_text(encoding="utf-8")

    assert compiler_input.strip().endswith("pip-tools==7.6.1")
    assert verifier_input.strip().endswith("pypi-attestations==0.0.30")
    assert "requirements-provider-lock-compiler.in" in workflow
    assert "requirements-provider-pypi-verifier.in" in workflow
    assert "requirements-provider-lock-compiler.lock.txt" in workflow
    assert "requirements-provider-pypi-verifier.lock.txt" in workflow
    assert "SOURCE_LOCK_COMPILER_TOOL_LOCK_COMPILE_FAILED" in workflow
    assert "SOURCE_PYPI_VERIFIER_TOOL_LOCK_COMPILE_FAILED" in workflow
    assert "SOURCE_HELPER_TOOL_LOCK_PIN_OR_HASH_VALIDATION_FAILED" in workflow
    assert "SOURCE_HELPER_TOOL_LOCK_TOP_LEVEL_PIN_MISMATCH" in workflow
    assert "SOURCE_HELPER_TOOL_LOCK_BINARY_DOWNLOAD_FAILED" in workflow
    assert "SOURCE_HELPER_TOOL_LOCK_OFFLINE_INSTALL_FAILED" in workflow
    assert "SOURCE_HELPER_TOOL_LOCK_IMPORT_FAILED" in workflow
    assert "importlib.metadata.version('pip-tools')" in workflow
    assert "importlib.metadata.version('pypi-attestations')" in workflow

    # Both helper environments must start from committed target-specific locks.
    compiler_lock = (root / "requirements-provider-lock-compiler.lock.txt").read_text(encoding="utf-8")
    verifier_lock = (root / "requirements-provider-pypi-verifier.windows-py313.lock.txt").read_text(encoding="utf-8")
    compiler_rows = re.findall(r"(?m)^([A-Za-z0-9][A-Za-z0-9._-]*)==([^ ]+) --hash=sha256:([0-9a-f]{64})$", compiler_lock)
    verifier_rows = re.findall(r"(?m)^([A-Za-z0-9][A-Za-z0-9._-]*)==([^ ]+) --hash=sha256:([0-9a-f]{64})$", verifier_lock)
    assert len(compiler_rows) == 9
    assert len({row[0].lower().replace("-", "").replace("_", "").replace(".", "") for row in compiler_rows}) == 9
    assert len(verifier_rows) == 34
    assert len({row[0].lower().replace("-", "").replace("_", "").replace(".", "") for row in verifier_rows}) == 34
    verifier_pins = {name.lower().replace("-", "").replace("_", "").replace(".", ""): (version, digest) for name, version, digest in verifier_rows}
    assert verifier_pins["pypiattestations"] == ("0.0.30", "b3a9c53f6cb89e5e7b5b70e6cfca97cfc66008c1ed54087355e06e40071cef21")
    assert "requirements-provider-pypi-verifier.windows-py313.lock.txt" in workflow
    assert "--require-hashes --only-binary=:all: --no-deps --dest $verifierWheelhouse -r $verifierLock" in workflow
    assert "--no-index --find-links $verifierWheelhouse --require-hashes --only-binary=:all: -r $verifierLock" in workflow
    assert "SOURCE_PYPI_VERIFIER_HASHED_OFFLINE_INSTALL_FAILED" in workflow
    assert "SOURCE_PYPI_VERIFIER_LOCK_AND_FREEZE_MATCH=PASS" in workflow
    assert "piptools --version" not in workflow
    assert "--require-hashes --only-binary=:all: --no-deps --dest $checkWheelhouse -r $toolLock.path" in workflow
    assert "tools/compact_provider_target_lock_v1.py --lock $toolLock.path --wheelhouse $checkWheelhouse --output $targetLockPath" in workflow
    assert "$targetPins.Count -ne $pins.Count -or $targetHashes.Count -ne $pins.Count" in workflow
    assert "--no-index --find-links $checkWheelhouse --require-hashes --only-binary=:all: -r $targetLockPath" in workflow
    assert "$locks.Count -ne 4" in workflow
    assert "--require-hashes --only-binary=:all: -r $compilerLock" in workflow
    assert "SOURCE_HELPER_TOOL_TARGET_LOCK_COMPACTION_FAILED" in workflow
    assert "'CANDIDATE_LOCKS_GENERATED_AND_OFFLINE_TESTED_NOT_APPROVED'" in workflow
    assert "production_approved = $false" in workflow
    assert "bootstrap_approved = $false" in workflow
    assert "artifacts/provider-source-build/tool-lock-candidates/*" in workflow
    assert "provider-helper-tool-lock-candidates/v1" in workflow
    assert "subject-path: artifacts/provider-source-build/tool-lock-candidates/*.lock.txt" in workflow
    assert "HELPER_TOOL_LOCK_ATTESTATION_VERIFICATION_FAILED" in workflow
    assert "HELPER_TOOL_LOCK_ATTESTATION_VERIFY=PASS:" in workflow



def test_unsigned_release_commit_must_match_exact_blob_and_patch_evidence(monkeypatch):
    import importlib.util
    import json

    root = Path(__file__).resolve().parents[1]
    builder_path = root / "tools" / "build_provider_source_wheel_candidate_v1.py"
    spec = importlib.util.spec_from_file_location("provider_source_unsigned_diff_gate", builder_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    pycparser = next(item for item in module.SOURCE_SPECS if item["name"] == "pycparser")
    evidence = pycparser["expected_unsigned_file_evidence"]
    patches = {
        "MANIFEST.in": "\n".join([
            "@@ -4,5 +4,5 @@ recursive-include pycparser *.py *.cfg",
            " recursive-include utils/fake_libc_include *.h",
            " include README.*",
            " include LICENSE",
            "-include CHANGES",
            "+include OLDER_CHANGES",
            " include setup.*",
        ]),
        "pyproject.toml": "\n".join([
            "@@ -1,5 +1,5 @@",
            " [build-system]",
            '-requires = ["setuptools>=69"]',
            '+requires = ["setuptools>=77.0.3"]',
            ' build-backend = "setuptools.build_meta"',
            " ",
            " [project]",
        ]),
    }
    for filename, patch_text in patches.items():
        assert hashlib.sha256(patch_text.encode("utf-8")).hexdigest() == evidence[filename]["patch_sha256"]


    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def read(self):
            return json.dumps(self.payload).encode("utf-8")

    def response_for(files, *, alter_patch=False, omit_patch=False, alter_blob=False):
        rows = []
        for name in files:
            if name not in evidence:
                rows.append({
                    "filename": name, "status": "modified", "sha": "a" * 40,
                    "patch": "@@ unrelated source change @@",
                })
                continue
            expected = evidence[name]
            row = {
                "filename": name,
                "status": "modified",
                "sha": ("f" * 40 if alter_blob and name == "pyproject.toml" else expected["blob_sha"]),
            }
            if not omit_patch:
                patch = patches[name]
                if alter_patch and name == "pyproject.toml":
                    patch += "\n# unexpected build configuration change"
                row["patch"] = patch
            rows.append(row)
        return FakeResponse({
            "sha": pycparser["commit"],
            "commit": {"verification": {"verified": False, "reason": "unsigned"}},
            "files": rows,
        })

    allowed = ["pyproject.toml", "MANIFEST.in"]
    monkeypatch.setattr(module.urllib.request, "urlopen", lambda request, timeout=25: response_for(allowed))
    result = module.github_commit_metadata(pycparser["repository"], pycparser["commit"])
    assert result["github_commit_changed_files"] == sorted(allowed)
    assert result["unsigned_commit_changed_files_match_allowlist"] is True
    assert result["unsigned_commit_patch_hashes_match"] is True
    assert result["expected_unsigned_commit_files"] == ["MANIFEST.in", "pyproject.toml"]
    assert result["unsigned_commit_file_evidence"]["pyproject.toml"]["blob_sha"] == evidence["pyproject.toml"]["blob_sha"]
    assert result["upstream_signature_policy"] == (
        "UNSIGNED_RELEASE_DIFF_EXACT_PATCH_HASHES_REQUIRE_INDEPENDENT_SOURCE_REVIEW"
    )

    altered_files = allowed + ["pycparser/c_parser.py"]
    monkeypatch.setattr(module.urllib.request, "urlopen", lambda request, timeout=25: response_for(altered_files))
    try:
        module.github_commit_metadata(pycparser["repository"], pycparser["commit"])
    except RuntimeError as exc:
        assert "UNSIGNED_UPSTREAM_COMMIT_CHANGED_UNREVIEWED_FILES" in str(exc)
    else:
        raise AssertionError("unexpected source-file changes must block source build")

    # Same path and pinned commit are insufficient if the actual API patch changes.
    monkeypatch.setattr(module.urllib.request, "urlopen", lambda request, timeout=25: response_for(allowed, alter_patch=True))
    try:
        module.github_commit_metadata(pycparser["repository"], pycparser["commit"])
    except RuntimeError as exc:
        assert "UNSIGNED_UPSTREAM_FILE_PATCH_MISMATCH" in str(exc)
    else:
        raise AssertionError("changed patch at an allowed path must block source build")

    monkeypatch.setattr(module.urllib.request, "urlopen", lambda request, timeout=25: response_for(allowed, alter_blob=True))
    try:
        module.github_commit_metadata(pycparser["repository"], pycparser["commit"])
    except RuntimeError as exc:
        assert "UNSIGNED_UPSTREAM_FILE_BLOB_MISMATCH" in str(exc)
    else:
        raise AssertionError("changed blob at an allowed path must block source build")

    monkeypatch.setattr(module.urllib.request, "urlopen", lambda request, timeout=25: response_for(allowed, omit_patch=True))
    try:
        module.github_commit_metadata(pycparser["repository"], pycparser["commit"])
    except RuntimeError as exc:
        assert "UNSIGNED_UPSTREAM_FILE_PATCH_MISSING" in str(exc)
    else:
        raise AssertionError("missing patch must block source build")

    # Missing diff metadata is never interpreted as acceptable.
    monkeypatch.setattr(
        module.urllib.request,
        "urlopen",
        lambda request, timeout=25: FakeResponse({
            "sha": pycparser["commit"],
            "commit": {"verification": {"verified": False, "reason": "unsigned"}},
        }),
    )
    try:
        module.github_commit_metadata(pycparser["repository"], pycparser["commit"])
    except RuntimeError as exc:
        assert "GITHUB_SOURCE_COMMIT_FILE_LIST_MISSING" in str(exc)
    else:
        raise AssertionError("missing source diff metadata must fail closed")
