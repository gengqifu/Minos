from pathlib import Path

from minos import manifest_scanner


def _write_manifest(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "AndroidManifest.xml"
    path.write_text(content, encoding="utf-8")
    return path


def test_default_rules_hit_permission_and_component(tmp_path: Path):
    manifest = """
    <manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example">
      <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
      <application>
        <activity android:name=".MainActivity" android:exported="true"/>
      </application>
    </manifest>
    """
    manifest_path = _write_manifest(tmp_path, manifest)
    rules = manifest_scanner.load_default_rules()
    source_flags = {r["rule_id"]: "region" for r in rules if r.get("rule_id")}
    findings, stats = manifest_scanner.scan_manifest(manifest_path, rules, source_flags=source_flags)
    rule_ids = {f["rule_id"] for f in findings}
    assert "PERM_SENSITIVE_LOCATION" in rule_ids
    assert "EXPORTED_ACTIVITY" in rule_ids
    assert stats["count_by_regulation"].get("PIPL", 0) >= 1
    assert stats["count_by_regulation"].get("GDPR", 0) >= 1
