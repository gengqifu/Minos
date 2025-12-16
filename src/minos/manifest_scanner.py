"""
Manifest 扫描：解析权限/导出组件，按规则匹配并生成 findings/stats。
"""

import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"


class ManifestScanError(Exception):
    """Manifest 扫描异常。"""


def _collect_manifest_contents(manifest_input: Path) -> List[bytes]:
    """
    支持三种输入：
    - 直接传入 AndroidManifest.xml 文件
    - 传入源码目录（寻找 AndroidManifest.xml，支持 src/main/AndroidManifest.xml 等主 Manifest）
    - 传入 APK（读取压缩包内的 AndroidManifest.xml，假设为可解析 XML）
    """
    contents: List[bytes] = []
    if manifest_input.is_dir():
        candidates = [
            manifest_input / "AndroidManifest.xml",
            manifest_input / "src/main/AndroidManifest.xml",
            manifest_input / "app/src/main/AndroidManifest.xml",
        ]
        for c in candidates:
            if c.exists():
                contents.append(c.read_bytes())
        if not contents:
            raise ManifestScanError("目录中未找到 AndroidManifest.xml（含 src/main 路径）")
        return contents

    if manifest_input.suffix.lower() == ".apk":
        try:
            with zipfile.ZipFile(manifest_input, "r") as zf:
                content = zf.read("AndroidManifest.xml")
                contents.append(content)
                return contents
        except KeyError:
            raise ManifestScanError("APK 中未找到 AndroidManifest.xml")
        except Exception as exc:
            raise ManifestScanError(f"读取 APK 失败: {exc}") from exc

    if manifest_input.exists():
        contents.append(manifest_input.read_bytes())
        return contents

    raise ManifestScanError(f"未找到 Manifest 输入: {manifest_input}")


def _parse_manifest_content(content: bytes) -> ET.Element:
    try:
        return ET.fromstring(content)
    except Exception as exc:
        raise ManifestScanError(f"解析 Manifest 失败: {exc}") from exc


def _merge_roots(roots: List[ET.Element]) -> ET.Element:
    """合并多个 Manifest：合并 uses-permission 和 application 下的组件。"""
    if not roots:
        raise ManifestScanError("未提供可用的 Manifest 解析结果")
    base = roots[0]
    base_app = base.find("application")
    if base_app is None:
        base_app = ET.SubElement(base, "application")

    for other in roots[1:]:
        for perm in other.findall("uses-permission"):
            base.append(perm)
        other_app = other.find("application")
        if other_app is not None:
            for child in list(other_app):
                base_app.append(child)
    return base


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
    contents = _collect_manifest_contents(manifest_path)
    roots = [_parse_manifest_content(c) for c in contents]
    root = _merge_roots(roots)
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
