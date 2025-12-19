import json
from pathlib import Path

import pytest

from minos import cli


def _write_yaml(path: Path, rules: list[dict]):
    try:
        import yaml  # type: ignore
    except Exception:
        pytest.skip("缺少 PyYAML 依赖")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(rules, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _read_report(output_dir: Path, report_name: str = "scan"):
    json_path = output_dir / f"{report_name}.json"
    return json.loads(json_path.read_text(encoding="utf-8")) if json_path.exists() else None


def test_scan_uses_rules_from_custom_dir(tmp_path: Path, monkeypatch):
    rules_dir = tmp_path / "rules"
    out_dir = tmp_path / "out"
    # 准备规则：Manifest + SDK
    _write_yaml(
        rules_dir / "gdpr" / "v1" / "rules.yaml",
        [
            {"rule_id": "TEST_PERM", "type": "permission", "pattern": "android.permission.INTERNET", "regulation": "GDPR"},
            {"rule_id": "TEST_SDK", "type": "sdk", "pattern": "com.example.tracker", "regulation": "GDPR"},
        ],
    )
    # 准备输入：Manifest + 源码
    manifest_path = tmp_path / "AndroidManifest.xml"
    manifest_path.write_text(
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android"><uses-permission android:name="android.permission.INTERNET"/></manifest>',
        encoding="utf-8",
    )
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "Main.java").write_text("com.example.tracker", encoding="utf-8")

    args = [
        "scan",
        "--mode",
        "both",
        "--manifest",
        str(manifest_path),
        "--input",
        str(src_dir),
        "--regulations",
        "GDPR",
        "--rules-dir",
        str(rules_dir),
        "--output-dir",
        str(out_dir),
        "--format",
        "json",
    ]
    exit_code = cli.main(args)
    report = _read_report(out_dir, "scan")
    assert exit_code == 0
    assert report is not None
    rids = {f["rule_id"] for f in report["findings"]}
    assert "TEST_PERM" in rids
    assert "TEST_SDK" in rids


def test_scan_missing_rules_dir_error(tmp_path: Path):
    out_dir = tmp_path / "out"
    args = [
        "scan",
        "--mode",
        "both",
        "--regulations",
        "gdpr",
        "--rules-dir",
        str(tmp_path / "missing"),
        "--output-dir",
        str(out_dir),
        "--format",
        "json",
    ]
    exit_code = cli.main(args)
    assert exit_code != 0
    assert not (out_dir / "scan.json").exists()


def test_scan_missing_rules_file_error(tmp_path: Path):
    rules_dir = tmp_path / "rules"
    (rules_dir / "gdpr" / "v1").mkdir(parents=True, exist_ok=True)
    out_dir = tmp_path / "out"
    args = [
        "scan",
        "--mode",
        "both",
        "--regulations",
        "gdpr",
        "--rules-dir",
        str(rules_dir),
        "--output-dir",
        str(out_dir),
        "--format",
        "json",
    ]
    exit_code = cli.main(args)
    assert exit_code != 0
    assert not (out_dir / "scan.json").exists()
