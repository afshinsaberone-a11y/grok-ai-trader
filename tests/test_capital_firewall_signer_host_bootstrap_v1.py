from pathlib import Path
import shutil
import subprocess


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "deploy"
    / "capital-firewall-signer"
    / "bootstrap-ubuntu-lts-v1.sh"
)


def test_signer_bootstrap_has_valid_bash_syntax():
    bash = shutil.which("bash")
    assert bash is not None, "CI runner must provide Bash for the Linux bootstrap contract"
    result = subprocess.run(
        [bash, "-n", str(SCRIPT)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_signer_bootstrap_is_fail_closed_before_mutation():
    source = SCRIPT.read_text(encoding="utf-8")
    assert '[[ "${EUID}" -eq 0 ]]' in source
    assert '[[ -t 0 ]] || fail "INTERACTIVE_TTY_REQUIRED"' in source
    assert '[[ "${ID:-}" == "ubuntu" ]]' in source
    assert '"22.04"|"24.04"' in source
    assert 'RUNTIME_IDENTITY_ALREADY_EXISTS_MANUAL_REVIEW_REQUIRED' in source
    assert 'DATA_ROOT_ALREADY_EXISTS_MANUAL_REVIEW_REQUIRED' in source
    assert 'HOSTNAME_CONFIRMATION_MISMATCH' in source


def test_signer_bootstrap_creates_only_locked_identity_and_empty_layout():
    source = SCRIPT.read_text(encoding="utf-8")
    assert 'RUNTIME_USER="capital-firewall"' in source
    assert 'DATA_ROOT="/var/lib/capital-firewall"' in source
    assert '--shell /usr/sbin/nologin' in source
    assert 'install -d -o "$RUNTIME_USER" -g "$RUNTIME_USER" -m 0700' in source
    assert 'KEYS_CREATED=0' in source
    assert 'REGISTRY_CREATED=0' in source
    assert 'SOURCE_PACKET_CREATED=0' in source
    assert 'GRANT_ISSUED=0' in source
    assert 'ORDERS_SUBMITTED=0' in source
    assert 'DEMO_AUTHORIZED=0' in source
    assert 'LIVE_ENABLED=0' in source


def test_signer_bootstrap_does_not_install_or_activate_signing_authority():
    source = SCRIPT.read_text(encoding="utf-8").lower()
    forbidden_commands_or_configs = (
        "ssh-keygen",
        "openssl genpkey",
        "sqlite3",
        "systemctl enable",
        "systemctl start",
        "ufw allow",
        "iptables",
        "nft add rule",
        "curl ",
        "wget ",
        "git clone",
        "forexai_capital_firewall_grant_public_key",
        "source-packet.json",
    )
    for token in forbidden_commands_or_configs:
        assert token not in source, f"unexpected authority/configuration action in bootstrap: {token}"
