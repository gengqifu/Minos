import json
import pytest
from pathlib import Path

from minos import sdk_scanner


def test_tracking_sdk_hit(tmp_path: Path):
    apk_path = tmp_path / "app.apk"
    with sdk_scanner.zipfile.ZipFile(apk_path, "w") as zf:
        zf.writestr("classes.dex", b"...com.example.tracker...")  # 模拟 SDK 包名

    rules = [
        {
            "rule_id": "SDK_TRACKING_001",
            "type": "sdk",
            "pattern": "com.example.tracker",
            "regulation": "GDPR",
            "severity": "medium",
        },
    ]
    findings, stats = sdk_scanner.scan_sdk_api([apk_path], rules, source_flags={"SDK_TRACKING_001": "region"})

    assert any(f["rule_id"] == "SDK_TRACKING_001" and f["location"] == "classes.dex" for f in findings)
    assert stats["count_by_regulation"]["GDPR"] == 1
    assert stats["count_by_severity"]["medium"] == 1


def test_sensitive_api_hit(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    java_file = src_dir / "Main.java"
    java_file.write_text("public class Main { void id(){ String id = getDeviceId(); } }")

    rules = [
        {
            "rule_id": "API_ID_ACCESS",
            "type": "api",
            "pattern": "getDeviceId",
            "regulation": "PIPL",
            "severity": "high",
        },
    ]
    findings, stats = sdk_scanner.scan_sdk_api([src_dir], rules, source_flags={"API_ID_ACCESS": "region"})

    assert any(f["rule_id"] == "API_ID_ACCESS" and "Main.java" in f["location"] for f in findings)
    assert stats["count_by_regulation"]["PIPL"] == 1
    assert stats["count_by_severity"]["high"] == 1


def test_suspicious_domain_hit(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    txt_file = src_dir / "strings.txt"
    txt_file.write_text("report to https://tracker.example.com/collect")

    rules = [
        {
            "rule_id": "DOMAIN_SUSPICIOUS",
            "type": "string",
            "pattern": "tracker.example.com",
            "regulation": "LGPD",
            "severity": "medium",
        },
    ]
    findings, stats = sdk_scanner.scan_sdk_api([src_dir], rules, source_flags={"DOMAIN_SUSPICIOUS": "manual"})

    assert any(
        f["rule_id"] == "DOMAIN_SUSPICIOUS"
        and f["source"] == "manual"
        and f["location"].endswith("strings.txt")
        for f in findings
    )
    assert stats["count_by_regulation"]["LGPD"] == 1
    assert stats["count_by_severity"]["medium"] == 1


def test_no_hits_returns_empty(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "Main.java").write_text("public class Main {}")

    rules = []
    findings, stats = sdk_scanner.scan_sdk_api([src_dir], rules, source_flags={})

    assert findings == []
    assert stats["count_by_regulation"] == {}
    assert stats["count_by_severity"] == {}


def test_report_outputs(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "Main.java").write_text("class Main { void t(){ getDeviceId(); } }")
    out_dir = tmp_path / "out"

    rules = [
        {
            "rule_id": "API_ID_ACCESS",
            "type": "api",
            "pattern": "getDeviceId",
            "regulation": "PIPL",
            "severity": "high",
        },
    ]
    findings, stats = sdk_scanner.scan_sdk_api(
        [src_dir], rules, source_flags={"API_ID_ACCESS": "region"}, report_dir=out_dir, report_name="sdk"
    )

    json_path = out_dir / "sdk.json"
    html_path = out_dir / "sdk.html"
    assert json_path.exists()
    assert html_path.exists()

    data = json.loads(json_path.read_text())
    assert data["meta"]["finding_count"] == 1
    assert data["findings"][0]["rule_id"] == "API_ID_ACCESS"
    assert "PIPL" in html_path.read_text()
