from pathlib import Path

from minos import manifest_scanner


def _write_manifest(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "AndroidManifest.xml"
    path.write_text(content, encoding="utf-8")
    return path


def test_scan_manifest_with_yaml_permission(tmp_path: Path):
    manifest = """
    <manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example">
      <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
    </manifest>
    """
    manifest_path = _write_manifest(tmp_path, manifest)
    rules_yaml = tmp_path / "rules.yaml"
    rules_yaml.write_text(
        """
- rule_id: PERM_SENSITIVE_LOCATION
  type: permission
  pattern: android.permission.ACCESS_FINE_LOCATION
  regulation: PIPL
  severity: high
- rule_id: EXPORTED_ACTIVITY
  type: component
  component: activity
  regulation: GDPR
  severity: high
  disabled: true
        """,
        encoding="utf-8",
    )
    findings, stats = manifest_scanner.scan_manifest_with_yaml(
        manifest_path, rules_yaml, source_flags={"PERM_SENSITIVE_LOCATION": "region"}
    )
    assert any(f["rule_id"] == "PERM_SENSITIVE_LOCATION" for f in findings)
    assert not any(f["rule_id"] == "EXPORTED_ACTIVITY" for f in findings)
    assert stats["count_by_regulation"].get("PIPL", 0) == 1


def test_scan_manifest_rule_override(tmp_path: Path):
    manifest = """
    <manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example">
      <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
    </manifest>
    """
    manifest_path = _write_manifest(tmp_path, manifest)
    rules_yaml = tmp_path / "rules.yaml"
    rules_yaml.write_text(
        """
- rule_id: PERM_SENSITIVE_LOCATION
  type: permission
  pattern: android.permission.ACCESS_FINE_LOCATION
  regulation: PIPL
  severity: high
- rule_id: PERM_SENSITIVE_LOCATION
  type: permission
  pattern: android.permission.ACCESS_FINE_LOCATION
  regulation: PIPL
  severity: low
        """,
        encoding="utf-8",
    )
    findings, _ = manifest_scanner.scan_manifest_with_yaml(
        manifest_path, rules_yaml, source_flags={"PERM_SENSITIVE_LOCATION": "region"}
    )
    assert len(findings) == 1
    assert findings[0]["severity"] == "low"
