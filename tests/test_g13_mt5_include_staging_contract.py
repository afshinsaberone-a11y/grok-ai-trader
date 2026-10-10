from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_g13_mt5_include_staging_does_not_copy_tree_onto_itself():
    workflow = (
        ROOT / ".github" / "workflows" / "forexai-g13-mt5-compile-parity.yml"
    ).read_text(encoding="utf-8")
    stage = workflow.split(
        "      - name: Stage MT5 include tree for service-account MetaEditor", 1
    )[1].split("      - name: Generate fresh frozen EAs", 1)[0]

    assert "$sourceCanonical = [System.IO.Path]::GetFullPath($source)" in stage
    assert "$targetCanonical = [System.IO.Path]::GetFullPath($target)" in stage
    assert "[System.StringComparison]::OrdinalIgnoreCase" in stage
    assert "MT5_INCLUDE_TREE_ALREADY_AT_TARGET=true" in stage
    assert "MT5_INCLUDE_TREE_COPIED_TO_SERVICE_PROFILE=true" in stage
    assert "Trade\\\\Trade.mqh" in stage
    assert "if (!(Test-Path -LiteralPath $trade -PathType Leaf))" in stage

    same_tree_guard = stage.index("if ([System.String]::Equals($sourceCanonical, $targetCanonical")
    copy_tree = stage.index(
        "Copy-Item -LiteralPath $_.FullName -Destination $target -Recurse -Force"
    )
    assert same_tree_guard < copy_tree
    assert "} else {" in stage[same_tree_guard:copy_tree]
