import json
from pathlib import Path

import pytest

from minos import manifest_scanner


def _write_manifest(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "AndroidManifest.xml"
    path.write_text(content, encoding="utf-8")
    return path


def test_sensitive_permission_hits(tmp_path: Path):
    manifest = """
    <manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example">
      <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
    </manifest>
    """
    manifest_path = _write_manifest(tmp_path, manifest)
    rules = [
        {"rule_id": "PERM_SENSITIVE_LOCATION", "type": "permission", "pattern": "android.permission.ACCESS_FINE_LOCATION", "regulation": "PIPL", "severity": "high"},
    ]
    findings, stats = manifest_scanner.scan_manifest(manifest_path, rules, source_flags={"PERM_SENSITIVE_LOCATION": "region"})
    assert any(f["rule_id"] == "PERM_SENSITIVE_LOCATION" for f in findings)
    assert stats.get("count_by_regulation", {}).get("PIPL", 0) >= 1


def test_exported_component_hits(tmp_path: Path):
    manifest = """
    <manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example">
      <application>
        <activity android:name=".ExposedActivity" android:exported="true"/>
      </application>
    </manifest>
    """
    manifest_path = _write_manifest(tmp_path, manifest)
    rules = [
        {"rule_id": "EXPORTED_ACTIVITY", "type": "component", "component": "activity", "regulation": "GDPR", "severity": "high"},
    ]
    findings, stats = manifest_scanner.scan_manifest(manifest_path, rules, source_flags={"EXPORTED_ACTIVITY": "region"})
    assert any(f["rule_id"] == "EXPORTED_ACTIVITY" for f in findings)
    assert stats.get("count_by_regulation", {}).get("GDPR", 0) >= 1


def test_invalid_manifest_errors(tmp_path: Path):
    manifest_path = _write_manifest(tmp_path, "<manifest><application></application>")
    rules = []
    with pytest.raises(manifest_scanner.ManifestScanError):
        manifest_scanner.scan_manifest(manifest_path, rules, source_flags={})
