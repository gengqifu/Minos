import pytest

from minos import cli


@pytest.mark.xfail(raises=SystemExit, strict=True, reason="scan CLI not implemented yet")
def test_scan_cli_requires_input():
    cli.main(["scan"])


@pytest.mark.xfail(raises=SystemExit, strict=True, reason="scan CLI not implemented yet")
def test_scan_cli_source_mode_and_format():
    cli.main(["scan", "--mode", "source", "--format", "both", "--output-dir", "out", "--input", "app/src"])


@pytest.mark.xfail(raises=SystemExit, strict=True, reason="scan CLI not implemented yet")
def test_scan_cli_apk_mode():
    cli.main(["scan", "--mode", "apk", "--apk-path", "app-release.apk", "--format", "json"])


@pytest.mark.xfail(raises=SystemExit, strict=True, reason="scan CLI not implemented yet")
def test_scan_cli_stdout_summary():
    cli.main(
        [
            "scan",
            "--mode",
            "both",
            "--apk-path",
            "app-release.apk",
            "--input",
            "app/src",
            "--output-dir",
            "out",
        ]
    )
