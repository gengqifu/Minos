import pytest
from pathlib import Path

from minos import sdk_scanner


@pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="SDK/API scanner not implemented yet")
def test_tracking_sdk_hit(tmp_path: Path):
    inputs = [tmp_path / "app.apk"]
    rules = [
        {"rule_id": "SDK_TRACKING_001", "type": "sdk", "pattern": "com.example.tracker", "regulation": "GDPR", "severity": "medium"},
    ]
    findings, stats = sdk_scanner.scan_sdk_api(inputs, rules, source_flags={"SDK_TRACKING_001": "region"})
    assert any(f["rule_id"] == "SDK_TRACKING_001" for f in findings)
    assert stats.get("count_by_regulation", {}).get("GDPR", 0) >= 1


@pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="SDK/API scanner not implemented yet")
def test_sensitive_api_hit(tmp_path: Path):
    inputs = [tmp_path / "src"]
    rules = [
        {"rule_id": "API_ID_ACCESS", "type": "api", "pattern": "getDeviceId", "regulation": "PIPL", "severity": "high"},
    ]
    findings, stats = sdk_scanner.scan_sdk_api(inputs, rules, source_flags={"API_ID_ACCESS": "region"})
    assert any(f["rule_id"] == "API_ID_ACCESS" for f in findings)
    assert stats.get("count_by_regulation", {}).get("PIPL", 0) >= 1


@pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="SDK/API scanner not implemented yet")
def test_suspicious_domain_hit(tmp_path: Path):
    inputs = [tmp_path / "src"]
    rules = [
        {"rule_id": "DOMAIN_SUSPICIOUS", "type": "string", "pattern": "tracker.example.com", "regulation": "LGPD", "severity": "medium"},
    ]
    findings, stats = sdk_scanner.scan_sdk_api(inputs, rules, source_flags={"DOMAIN_SUSPICIOUS": "manual"})
    assert any(f["rule_id"] == "DOMAIN_SUSPICIOUS" for f in findings)
    assert stats.get("count_by_regulation", {}).get("LGPD", 0) >= 1


@pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="SDK/API scanner not implemented yet")
def test_no_hits_returns_empty(tmp_path: Path):
    inputs = [tmp_path / "src"]
    rules = []
    findings, stats = sdk_scanner.scan_sdk_api(inputs, rules, source_flags={})
    assert findings == []
    assert stats.get("count_by_regulation", {}) == {}
