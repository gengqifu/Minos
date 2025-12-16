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
    data = json.loads((out_dir / "scan.json").read_text())
    assert set(data.keys()) == {"meta", "findings", "stats"}
    assert data["meta"]["mode"] == "source"
    assert data["meta"]["inputs"] == [str(src_dir)]
    assert "count_by_regulation" in data["stats"]
    assert "count_by_severity" in data["stats"]
    html = (out_dir / "scan.html").read_text()
    assert "Minos Scan Report" in html
    assert "Findings" in html


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


def test_scan_cli_missing_apk_in_apk_mode(capsys):
    exit_code = cli.main(["scan", "--mode", "apk", "--format", "json"])
    captured = capsys.readouterr()
    assert exit_code != 0
    assert "缺少 APK 输入" in captured.err


def test_scan_cli_missing_apk_file(capsys):
    exit_code = cli.main(
        ["scan", "--mode", "apk", "--apk-path", "tests/fixtures/missing.apk", "--format", "json"]
    )
    captured = capsys.readouterr()
    assert exit_code != 0
    assert "APK 不存在" in captured.err


def test_scan_cli_missing_src_in_source_mode(capsys):
    exit_code = cli.main(["scan", "--mode", "source", "--format", "json"])
    captured = capsys.readouterr()
    assert exit_code != 0
    assert "缺少源码输入" in captured.err


def test_scan_cli_stdout_summary(tmp_path: Path, capsys):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "Main.java").write_text("class Main {}")
    out_dir = tmp_path / "out"
    dummy_apk = src_dir / "dummy.apk"
    dummy_apk.write_bytes(b"apk")

    exit_code = cli.main(
        [
            "scan",
            "--mode",
            "both",
            "--apk-path",
            str(dummy_apk),
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
    assert "by_regulation" in captured.out
    assert "by_severity" in captured.out


def test_scan_cli_log_file(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "Main.java").write_text("class Main {}")
    out_dir = tmp_path / "out"
    log_file = tmp_path / "logs/scan.log"

    exit_code = cli.main(
        [
            "scan",
            "--mode",
            "source",
            "--input",
            str(src_dir),
            "--output-dir",
            str(out_dir),
            "--format",
            "json",
            "--log-file",
            str(log_file),
            "--log-level",
            "debug",
            "--log-max-bytes",
            "1024",
            "--log-backup",
            "2",
        ]
    )
    assert exit_code == 0
    assert log_file.exists()
    content = log_file.read_text()
    assert "INFO" in content or "DEBUG" in content


def test_scan_cli_exit_code_success(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "Main.java").write_text("class Main {}")
    out_dir = tmp_path / "out"

    exit_code = cli.main(
        ["scan", "--mode", "source", "--input", str(src_dir), "--output-dir", str(out_dir), "--format", "json"]
    )
    assert exit_code == 0


def test_scan_cli_exit_code_missing_input():
    exit_code = cli.main(["scan", "--mode", "both"])
    assert exit_code != 0


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


def test_scan_cli_multi_inputs_and_apks(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "Main.java").write_text("class Main {}")
    src_dir2 = tmp_path / "src2"
    src_dir2.mkdir()
    (src_dir2 / "Main2.java").write_text("class Main2 {}")
    apk1 = tmp_path / "a.apk"
    apk2 = tmp_path / "b.apk"
    apk1.write_bytes(b"dummy1")
    apk2.write_bytes(b"dummy2")
    out_dir = tmp_path / "out"

    exit_code = cli.main(
        [
            "scan",
            "--mode",
            "both",
            "--input",
            str(src_dir),
            "--input",
            str(src_dir2),
            "--apk-path",
            str(apk1),
            "--apk-path",
            str(apk2),
            "--output-dir",
            str(out_dir),
            "--format",
            "json",
        ]
    )
    assert exit_code == 0
    data = json.loads((out_dir / "scan.json").read_text())
    # four inputs merged
    assert len(data["meta"]["inputs"]) == 4
