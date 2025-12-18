"""
Manifest 扫描：解析权限/导出组件，按规则匹配并生成 findings/stats。
"""

import zipfile
import xml.etree.ElementTree as ET
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

    # 规则归一化：支持 disabled，后出现的同 rule_id 覆盖前者
    normalized: Dict[str, Dict[str, Any]] = {}
    for rule in rules:
        rid = rule.get("rule_id")
        if not rid:
            continue
        if rule.get("disabled") is True:
            # 标记为禁用则移除已存在的同名规则
            if rid in normalized:
                del normalized[rid]
            normalized[rid] = {"disabled": True}
            continue
        normalized[rid] = rule
    active_rules = [r for r in normalized.values() if not r.get("disabled")]

    findings: List[Dict[str, Any]] = []

    for rule in active_rules:
        rtype = rule.get("type")
        if rtype == "permission":
            findings.extend(_match_permission(root, rule))
        elif rtype == "component":
            findings.extend(_match_components(root, rule))

    # 来源标记：source_flags 优先，其次规则自带 source，默认 region
    source_map: Dict[str, str] = dict(source_flags)
    for rule in active_rules:
        rid = rule.get("rule_id")
        if rid and rid not in source_map and rule.get("source"):
            source_map[rid] = rule.get("source")

    for f in findings:
        f["source"] = source_map.get(f["rule_id"], "region")

    # 统计
    stats: Dict[str, Any] = {"count_by_regulation": {}, "count_by_severity": {}}
    for f in findings:
        reg = f.get("regulation")
        sev = f.get("severity")
        if reg:
            stats["count_by_regulation"][reg] = stats["count_by_regulation"].get(reg, 0) + 1
        if sev:
            stats["count_by_severity"][sev] = stats["count_by_severity"].get(sev, 0) + 1

    # stdout 摘要
    print(
        f"[manifest] scanned {manifest_path}, findings={len(findings)}, "
        f"by_regulation={stats['count_by_regulation']}, by_severity={stats['count_by_severity']}"
    )

    # 详细日志
    print(f"[manifest] rules={len(rules)} matched={len(findings)}")
    if not findings:
        print("[manifest] no findings")
    for f in findings:
        print(
            f"[manifest] hit rule_id={f.get('rule_id')} regulation={f.get('regulation')} "
            f"source={f.get('source')} location={f.get('location')} severity={f.get('severity')}"
        )

    return findings, stats


def load_rules_from_yaml(path: Path) -> List[Dict[str, Any]]:
    """从 YAML 文件加载规则列表。"""
    if not path.exists():
        raise ManifestScanError(f"规则文件不存在: {path}")
    try:
        import yaml  # type: ignore
    except Exception as exc:
        raise ManifestScanError(f"缺少 PyYAML 依赖: {exc}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ManifestScanError(f"读取规则 YAML 失败: {exc}")
    if not isinstance(data, list):
        raise ManifestScanError("规则 YAML 应为列表")
    return data


def load_default_rules() -> List[Dict[str, Any]]:
    """加载内置的 Manifest 规则集。"""
    return load_rules_from_yaml(DEFAULT_RULES_PATH)


def scan_manifest_with_yaml(
    manifest_path: Path, rules_yaml: Path, source_flags: Dict[str, str] | None = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    便捷入口：从 YAML 加载规则并执行扫描。
    """
    rules = load_rules_from_yaml(rules_yaml)
    return scan_manifest(manifest_path, rules, source_flags or {})
DEFAULT_RULES_PATH = Path(__file__).parent / "rules" / "manifest_rules.yaml"
