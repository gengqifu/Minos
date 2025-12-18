import json
from pathlib import Path

import pytest

from minos import manifest_scanner


def _write_manifest(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "AndroidManifest.xml"
    path.write_text(content, encoding="utf-8")
    return path


def _make_rule(rule_id: str, rtype: str, **kwargs):
    base = {"rule_id": rule_id, "type": rtype, "regulation": kwargs.get("regulation", "GDPR"), "severity": kwargs.get("severity", "medium")}
    base.update(kwargs)
    return base


def test_sensitive_permission_hits(tmp_path: Path):
    manifest = """
    <manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example">
      <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
    </manifest>
    """
    manifest_path = _write_manifest(tmp_path, manifest)
    rules = [
        _make_rule("PERM_SENSITIVE_LOCATION", "permission", pattern="android.permission.ACCESS_FINE_LOCATION", regulation="PIPL", severity="high"),
    ]
    findings, stats = manifest_scanner.scan_manifest(manifest_path, rules, source_flags={"PERM_SENSITIVE_LOCATION": "region"})
    assert any(f["rule_id"] == "PERM_SENSITIVE_LOCATION" for f in findings)
    assert any(f["source"] == "region" for f in findings if f["rule_id"] == "PERM_SENSITIVE_LOCATION")
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
        _make_rule("EXPORTED_ACTIVITY", "component", component="activity", regulation="GDPR", severity="high"),
    ]
    findings, stats = manifest_scanner.scan_manifest(manifest_path, rules, source_flags={"EXPORTED_ACTIVITY": "region"})
    assert any(f["rule_id"] == "EXPORTED_ACTIVITY" for f in findings)
    assert any(f["source"] == "region" for f in findings if f["rule_id"] == "EXPORTED_ACTIVITY")
    assert stats.get("count_by_regulation", {}).get("GDPR", 0) >= 1


def test_invalid_manifest_errors(tmp_path: Path):
    manifest_path = _write_manifest(tmp_path, "<manifest><application></application>")
    rules = []
    with pytest.raises(manifest_scanner.ManifestScanError):
        manifest_scanner.scan_manifest(manifest_path, rules, source_flags={})


def test_scan_from_directory(tmp_path: Path):
    manifest_main = """
    <manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example">
      <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
    </manifest>
    """
    manifest_flavor = """
    <manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example">
      <application>
        <activity android:name=".ExposedActivity" android:exported="true"/>
      </application>
    </manifest>
    """
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    _write_manifest(project_dir, manifest_main)
    flavor_dir = project_dir / "src/main"
    flavor_dir.mkdir(parents=True, exist_ok=True)
    (flavor_dir / "AndroidManifest.xml").write_text(manifest_flavor, encoding="utf-8")
    rules = [
        _make_rule("PERM_SENSITIVE_LOCATION", "permission", pattern="android.permission.ACCESS_FINE_LOCATION", regulation="PIPL", severity="high"),
        _make_rule("EXPORTED_ACTIVITY", "component", component="activity", regulation="GDPR", severity="high"),
    ]
    findings, _ = manifest_scanner.scan_manifest(
        project_dir,
        rules,
        source_flags={"PERM_SENSITIVE_LOCATION": "region", "EXPORTED_ACTIVITY": "region"},
    )
    assert any(f["rule_id"] == "PERM_SENSITIVE_LOCATION" for f in findings)
    assert any(f["rule_id"] == "EXPORTED_ACTIVITY" for f in findings)


def test_scan_from_apk_with_plain_manifest(tmp_path: Path):
    manifest = """
    <manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example">
      <application>
        <activity android:name=".ExposedActivity" android:exported="true"/>
      </application>
    </manifest>
    """
    manifest_path = _write_manifest(tmp_path, manifest)
    apk_path = tmp_path / "app.apk"
    # 创建包含文本 manifest 的 zip 作为模拟 apk
    import zipfile

    with zipfile.ZipFile(apk_path, "w") as zf:
        zf.write(manifest_path, arcname="AndroidManifest.xml")

    rules = [
        _make_rule("EXPORTED_ACTIVITY", "component", component="activity", regulation="GDPR", severity="high"),
    ]
    findings, _ = manifest_scanner.scan_manifest(apk_path, rules, source_flags={"EXPORTED_ACTIVITY": "region"})
    assert any(f["rule_id"] == "EXPORTED_ACTIVITY" for f in findings)


def test_findings_fields_and_stats(tmp_path: Path):
    manifest = """
    <manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example">
      <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
      <application>
        <activity android:name=".ExposedActivity" android:exported="true"/>
      </application>
    </manifest>
    """
    manifest_path = _write_manifest(tmp_path, manifest)
    rules = [
        _make_rule("PERM_SENSITIVE_LOCATION", "permission", pattern="android.permission.ACCESS_FINE_LOCATION", regulation="PIPL", severity="high"),
        _make_rule("EXPORTED_ACTIVITY", "component", component="activity", regulation="GDPR", severity="high"),
    ]
    findings, stats = manifest_scanner.scan_manifest(
        manifest_path,
        rules,
        source_flags={"PERM_SENSITIVE_LOCATION": "region", "EXPORTED_ACTIVITY": "manual"},
    )
    required_keys = {"rule_id", "regulation", "source", "location", "evidence", "severity", "recommendation"}
    for f in findings:
        assert required_keys.issubset(f.keys())
    assert stats["count_by_regulation"].get("PIPL", 0) >= 1
    assert stats["count_by_regulation"].get("GDPR", 0) >= 1


def test_rule_source_precedence(tmp_path: Path):
    manifest = """
    <manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example">
      <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
    </manifest>
    """
    manifest_path = _write_manifest(tmp_path, manifest)
    # 规则自带 source=manual
    rules = [
        _make_rule(
            "PERM_SENSITIVE_LOCATION",
            "permission",
            pattern="android.permission.ACCESS_FINE_LOCATION",
            regulation="PIPL",
            severity="high",
            source="manual",
        )
    ]
    findings, _ = manifest_scanner.scan_manifest(manifest_path, rules, source_flags={})
    assert findings and findings[0]["source"] == "manual"
    # source_flags 优先覆盖规则内 source
    findings2, _ = manifest_scanner.scan_manifest(
        manifest_path, rules, source_flags={"PERM_SENSITIVE_LOCATION": "region"}
    )
    assert findings2 and findings2[0]["source"] == "region"


@pytest.mark.xfail(reason="待实现 YAML 规则禁用/覆盖逻辑")
def test_disabled_rule_should_not_hit(tmp_path: Path):
    manifest = """
    <manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example">
      <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
    </manifest>
    """
    manifest_path = _write_manifest(tmp_path, manifest)
    rules = [
        _make_rule(
            "PERM_SENSITIVE_LOCATION",
            "permission",
            pattern="android.permission.ACCESS_FINE_LOCATION",
            regulation="PIPL",
            severity="high",
            disabled=True,
        ),
    ]
    findings, stats = manifest_scanner.scan_manifest(manifest_path, rules, source_flags={"PERM_SENSITIVE_LOCATION": "region"})
    assert not findings
    assert not stats.get("count_by_regulation")


@pytest.mark.xfail(reason="待实现 YAML 规则覆盖逻辑（同 rule_id 后者覆盖前者）")
def test_rule_override_by_rule_id(tmp_path: Path):
    manifest = """
    <manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example">
      <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
    </manifest>
    """
    manifest_path = _write_manifest(tmp_path, manifest)
    rules = [
        _make_rule("PERM_SENSITIVE_LOCATION", "permission", pattern="android.permission.ACCESS_FINE_LOCATION", regulation="PIPL", severity="high"),
        _make_rule("PERM_SENSITIVE_LOCATION", "permission", pattern="android.permission.ACCESS_FINE_LOCATION", regulation="PIPL", severity="low"),
    ]
    findings, _ = manifest_scanner.scan_manifest(manifest_path, rules, source_flags={"PERM_SENSITIVE_LOCATION": "region"})
    assert len(findings) == 1
    assert findings[0]["severity"] == "low"
