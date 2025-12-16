from pathlib import Path
import json

from minos import cli


def test_scan_cli_requires_input(capsys):
    exit_code = cli.main(["scan"])
    captured = capsys.readouterr()
    assert exit_code != 0
    assert "缺少输入" in captured.err


def test_scan_cli_source_mode_and_format(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "Main.java").write_text("class Main {}")
    out_dir = tmp_path / "out"

    exit_code = cli.main(
        [
            "scan",
            "--mode",
            "source",
            "--format",
            "both",
            "--output-dir",
            str(out_dir),
            "--input",
            str(src_dir),
        ]
    )
    assert exit_code == 0
    assert (out_dir / "scan.json").exists()
    assert (out_dir / "scan.html").exists()


def test_scan_cli_apk_mode(tmp_path: Path):
    apk = tmp_path / "app-release.apk"
    apk.write_bytes(b"dummy apk content")
    out_dir = tmp_path / "out"

    exit_code = cli.main(
        [
            "scan",
            "--mode",
            "apk",
            "--apk-path",
            str(apk),
            "--format",
            "json",
            "--output-dir",
            str(out_dir),
        ]
    )
    assert exit_code == 0
    assert (out_dir / "scan.json").exists()
    # html 不生成
    assert not (out_dir / "scan.html").exists()


def test_scan_cli_stdout_summary(tmp_path: Path, capsys):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "Main.java").write_text("class Main {}")
    out_dir = tmp_path / "out"

    exit_code = cli.main(
        [
            "scan",
            "--mode",
            "both",
            "--apk-path",
            str(src_dir / "dummy.apk"),
            "--input",
            str(src_dir),
            "--output-dir",
            str(out_dir),
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "findings=0" in captured.out
    assert "reports=" in captured.out


def test_scan_cli_regions_regs_threads(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "Main.java").write_text("class Main {}")
    out_dir = tmp_path / "out"

    exit_code = cli.main(
        [
            "scan",
            "--mode",
            "source",
            "--input",
            str(src_dir),
            "--regions",
            "eu",
            "--regions",
            "us",
            "--regulations",
            "gdpr",
            "--threads",
            "2",
            "--timeout",
            "30",
            "--log-level",
            "debug",
            "--output-dir",
            str(out_dir),
            "--format",
            "json",
        ]
    )
    assert exit_code == 0
    data = json.loads((out_dir / "scan.json").read_text())
    assert data["meta"]["regions"] == ["eu", "us"]
    assert data["meta"]["regulations"] == ["gdpr"]
    assert data["meta"]["threads"] == 2
    assert data["meta"]["timeout"] == 30
