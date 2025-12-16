"""
Manifest 扫描：解析权限/导出组件，按规则匹配并生成 findings/stats。
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Tuple

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"


class ManifestScanError(Exception):
    """Manifest 扫描异常。"""


def _parse_manifest(manifest_path: Path) -> ET.Element:
    try:
        tree = ET.parse(manifest_path)
        return tree.getroot()
    except Exception as exc:
        raise ManifestScanError(f"解析 Manifest 失败: {exc}") from exc


def _match_permission(root: ET.Element, rule: Dict[str, Any]) -> List[Dict[str, Any]]:
    pattern = rule.get("pattern")
    if not pattern:
        return []
    findings = []
    for perm in root.findall("uses-permission"):
        name = perm.attrib.get(f"{ANDROID_NS}name") or perm.attrib.get("android:name")
        if name == pattern:
            findings.append(
                {
                    "rule_id": rule.get("rule_id"),
                    "regulation": rule.get("regulation"),
                    "severity": rule.get("severity", "medium"),
                    "location": "AndroidManifest.xml",
                    "evidence": f"uses-permission: {name}",
                    "recommendation": rule.get("recommendation", ""),
                }
            )
    return findings


def _match_components(root: ET.Element, rule: Dict[str, Any]) -> List[Dict[str, Any]]:
    component = rule.get("component")
    if component not in {"activity", "service", "provider"}:
        return []
    findings = []
    app = root.find("application")
    if app is None:
        return findings
    for elem in app.findall(component):
        exported = elem.attrib.get(f"{ANDROID_NS}exported") or elem.attrib.get("android:exported")
        if str(exported).lower() != "true":
            continue
        name = elem.attrib.get(f"{ANDROID_NS}name") or elem.attrib.get("android:name") or ""
        findings.append(
            {
                "rule_id": rule.get("rule_id"),
                "regulation": rule.get("regulation"),
                "severity": rule.get("severity", "high"),
                "location": f"AndroidManifest.xml:{component}",
                "evidence": f"{component} exported=true name={name}",
                "recommendation": rule.get("recommendation", ""),
            }
        )
    return findings


def scan_manifest(
    manifest_path: Path, rules: List[Dict[str, Any]], source_flags: Dict[str, str]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    扫描 Manifest，返回 (findings, stats)。
    rules 示例：
    - 权限：{"rule_id": "...", "type": "permission", "pattern": "android.permission.ACCESS_FINE_LOCATION", "regulation": "...", "severity": "..."}
    - 组件：{"rule_id": "...", "type": "component", "component": "activity", "regulation": "...", "severity": "..."}
    """
    root = _parse_manifest(manifest_path)
    findings: List[Dict[str, Any]] = []

    for rule in rules:
        rtype = rule.get("type")
        if rtype == "permission":
            findings.extend(_match_permission(root, rule))
        elif rtype == "component":
            findings.extend(_match_components(root, rule))

    # 添加来源标记
    for f in findings:
        f["source"] = source_flags.get(f["rule_id"], "region")

    # 统计
    stats: Dict[str, Any] = {"count_by_regulation": {}, "count_by_severity": {}}
    for f in findings:
        reg = f.get("regulation")
        sev = f.get("severity")
        if reg:
            stats["count_by_regulation"][reg] = stats["count_by_regulation"].get(reg, 0) + 1
        if sev:
            stats["count_by_severity"][sev] = stats["count_by_severity"].get(sev, 0) + 1

    return findings, stats
