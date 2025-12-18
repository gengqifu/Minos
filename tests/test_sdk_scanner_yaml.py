from pathlib import Path

from minos import sdk_scanner


def _write_file(tmp_path: Path, rel: str, content: str) -> Path:
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_sdk_scanner_with_default_rules(tmp_path: Path):
    # 模拟源码文件包含跟踪 SDK 和敏感 API
    f1 = _write_file(tmp_path, "src/Main.java", "com.example.tracker\ngetDeviceId();")
    f2 = _write_file(tmp_path, "assets/strings.txt", "tracker.example.com")

    rules = sdk_scanner.load_default_rules()
    source_flags = {r["rule_id"]: "region" for r in rules}

    findings, stats = sdk_scanner.scan_sdk_api(
        inputs=[tmp_path],
        rules=rules,
        source_flags=source_flags,
    )

    rids = {f["rule_id"] for f in findings}
    assert "SDK_TRACKING" in rids
    assert "API_ID_ACCESS" in rids
    assert "STRING_SUSPICIOUS_DOMAIN" in rids
    assert stats["count_by_regulation"].get("GDPR", 0) >= 1
    assert stats["count_by_regulation"].get("PIPL", 0) >= 1


def test_sdk_scanner_rule_disabled(tmp_path: Path):
    f1 = _write_file(tmp_path, "src/Main.java", "com.example.tracker")
    rules = [
        {"rule_id": "SDK_TRACKING", "type": "sdk", "pattern": "com.example.tracker", "regulation": "GDPR", "severity": "medium", "disabled": True}
    ]
    findings, stats = sdk_scanner.scan_sdk_api(
        inputs=[tmp_path],
        rules=rules,
        source_flags={"SDK_TRACKING": "region"},
    )
    assert not findings
    assert not stats["count_by_regulation"]


def test_sdk_scanner_rule_override(tmp_path: Path):
    f1 = _write_file(tmp_path, "src/Main.java", "com.example.tracker")
    rules = [
        {"rule_id": "SDK_TRACKING", "type": "sdk", "pattern": "com.example.tracker", "regulation": "GDPR", "severity": "medium"},
        {"rule_id": "SDK_TRACKING", "type": "sdk", "pattern": "com.example.tracker", "regulation": "GDPR", "severity": "high"},
    ]
    findings, _ = sdk_scanner.scan_sdk_api(
        inputs=[tmp_path],
        rules=rules,
        source_flags={"SDK_TRACKING": "region"},
    )
    assert findings
    assert findings[0]["severity"] == "high"
