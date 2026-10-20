from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "deploy" / "capital-firewall-signer" / "bootstrap-windows-workstation-v1.ps1"
RUNBOOK = ROOT / "docs" / "CAPITAL_FIREWALL_GRANT_SIGNER_WORKSTATION_V1.md"


def test_workstation_bootstrap_has_fail_closed_host_guards():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "#Requires -RunAsAdministrator" in source
    assert 'Get-CimInstance -ClassName Win32_OperatingSystem' in source
    assert '[int]$os.ProductType -ne 1' in source
    assert "KNOWN_PROVIDER_HOST_FORBIDDEN" in source
    assert "SELF_HOSTED_ACTIONS_RUNNER_HOST_FORBIDDEN" in source
    assert "ACTIVE_MT5_TERMINAL_HOST_FORBIDDEN" in source
    assert "HOSTNAME_CONFIRMATION_MISMATCH" in source


def test_workstation_bootstrap_only_creates_locked_empty_layout():
    source = SCRIPT.read_text(encoding="utf-8")
    assert 'RuntimeUser = "capital-firewall"' in source
    assert 'ForexAI-CapitalFirewall' in source
    for child in ('"keys"', '"in"', '"out"', '"state"'):
        assert child in source
    assert "PASSWORD_MUST_BE_AT_LEAST_16_CHARACTERS" in source
    assert "/inheritance:r" in source
    assert "*S-1-5-18:(OI)(CI)F" in source
    assert "*S-1-5-32-544:(OI)(CI)F" in source
    assert "KEYS_CREATED=0" in source
    assert "REGISTRY_CREATED=0" in source
    assert "SOURCE_PACKET_CREATED=0" in source
    assert "GRANT_ISSUED=0" in source
    assert "ORDERS_SUBMITTED=0" in source
    assert "DEMO_AUTHORIZED=0" in source
    assert "LIVE_ENABLED=0" in source


def test_workstation_bootstrap_does_not_create_signing_or_trading_authority():
    source = SCRIPT.read_text(encoding="utf-8").lower()
    forbidden = (
        "ssh-keygen",
        "openssl",
        "ed25519privatekey.generate",
        "sqlite3",
        "systemctl",
        "grant_private_key",
        "forexai_capital_firewall_grant_public_key",
        "source-packet.json",
        "github_token",
        "ordersend",
        "order_send",
    )
    for token in forbidden:
        assert token not in source, f"unexpected authority/configuration action: {token}"


def test_workstation_runbook_does_not_misrepresent_air_gap_or_host_independence():
    source = RUNBOOK.read_text(encoding="utf-8")
    assert "NOT PROVISIONED" in source
    assert "not a fully air-gapped/HSM signer" in source
    assert "not proof of independent custody" in source
    assert "WIN-P7MA35DRF6Q" in source
    assert "current-main" in source
    assert "anti-replay registry" in source
    assert "Kill Switch DENY" in source


def test_deployment_plan_keeps_no_new_vps_route_conditional_and_linux_fallback():
    deployment = (ROOT / "docs" / "CAPITAL_FIREWALL_GRANT_SIGNER_DEPLOYMENT_V1.md").read_text(encoding="utf-8")
    assert "Route A is an existing independently administered Windows client workstation" in deployment
    assert "Route B is a dedicated Linux LTS VPS" in deployment
    assert "No workstation has yet been identified or verified as independent" in deployment
    assert "No instance has been ordered or provisioned" in deployment
