"""Contract tests for the read-only self-hosted runner egress diagnostic."""
from pathlib import Path


def test_runner_network_diagnostic_is_read_only_and_checks_codeload():
    root = Path(__file__).resolve().parents[1]
    script_path = root / "tools" / "diagnose_github_runner_network_v1.ps1"
    script = script_path.read_text(encoding="utf-8")

    for required in (
        "forexai.github_runner_network_diagnostic.v1",
        "https://github.com/",
        "https://api.github.com/",
        "https://codeload.github.com/actions/checkout/zip/11d5960a326750d5838078e36cf38b85af677262",
        "https://codeload.github.com/actions/download-artifact/zip/d3f86a106a0bac45b974a628896c90dbdf5c8093",
        "request.Method = 'HEAD'",
        "TIMEOUT",
        "codeload.github.com",
        "credentials_sent = $false",
        "secrets_read = $false",
        "files_changed = $false",
        "firewall_changed = $false",
        "runner_configuration_changed = $false",
        "orders_submitted = $false",
        "demo_trading_authorized = $false",
        "live_trading_allowed = $false",
    ):
        assert required in script

    for forbidden in (
        "Set-NetFirewallRule",
        "New-NetFirewallRule",
        "Remove-NetFirewallRule",
        "SetEnvironmentVariable(",
        "New-Service",
        "Set-Service",
        "Start-Service",
        "Stop-Service",
        "WriteAllText(",
        "WriteAllBytes(",
        "GITHUB_TOKEN",
        "FOREXAI_PROVIDER_SIGNING_KEY_PASSPHRASE",
    ):
        assert forbidden not in script

    assert "Authorization" not in script
    assert "request.Headers" not in script


def test_runner_network_diagnostic_documents_bounded_timeout():
    root = Path(__file__).resolve().parents[1]
    script = (root / "tools" / "diagnose_github_runner_network_v1.ps1").read_text(
        encoding="utf-8"
    )
    assert "[ValidateRange(3, 30)]" in script
    assert "$request.Timeout = $Timeout * 1000" in script
    assert "$request.ReadWriteTimeout = $Timeout * 1000" in script
