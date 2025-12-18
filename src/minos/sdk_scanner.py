"""
SDK/敏感 API/字符串 扫描（简化实现）：
- 支持扫描目录、文本文件、APK 压缩包，按规则 pattern 做子串匹配。
- 可选输出 JSON/HTML 报告。
"""

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_RULES_PATH = Path(__file__).parent / "rules" / "sdk_rules.yaml"


def _iter_file_contents(path: Path):
    if path.is_dir():
        for p in path.rglob("*"):
            if p.is_file():
                yield p, p.read_bytes()
    elif path.is_file() and path.suffix.lower() == ".apk":
        with zipfile.ZipFile(path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                content = zf.read(info.filename)
                yield Path(info.filename), content
    elif path.is_file():
        yield path, path.read_bytes()
    else:
        raise FileNotFoundError(f"输入不存在: {path}")


def _match_rule(content: bytes, rule: Dict[str, Any]) -> bool:
    pattern = rule.get("pattern")
    if not pattern:
        return False
    return pattern.encode(errors="ignore") in content


def load_rules_from_yaml(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"规则文件不存在: {path}")
    try:
        import yaml  # type: ignore
    except Exception as exc:
        raise RuntimeError(f"缺少 PyYAML 依赖: {exc}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("规则 YAML 应为列表")
    return data


def load_default_rules() -> List[Dict[str, Any]]:
    return load_rules_from_yaml(DEFAULT_RULES_PATH)


def scan_sdk_api(
    inputs: List[Path],
    rules: List[Dict[str, Any]],
    source_flags: Dict[str, str],
    report_dir: Optional[Path] = None,
    report_name: str = "sdk_scan",
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    扫描输入（APK/源码路径），返回 (findings, stats)。
    规则支持 type=sdk/api/string，均基于模式子串匹配。
    """
    # 规则归一化：支持 disabled，后出现的同 rule_id 覆盖前者
    normalized: Dict[str, Dict[str, Any]] = {}
    for r in rules:
        rid = r.get("rule_id")
        if not rid:
            continue
        if r.get("disabled") is True:
            normalized[rid] = {"disabled": True}
            continue
        normalized[rid] = r
    active_rules = [r for r in normalized.values() if not r.get("disabled")]

    findings: List[Dict[str, Any]] = []
    stats: Dict[str, Any] = {"count_by_regulation": {}, "count_by_severity": {}}

    for input_path in inputs:
        print(f"[sdk] scanning input={input_path}")
        try:
            for fpath, content in _iter_file_contents(input_path):
                print(f"[sdk] parsing file={fpath}")
                for rule in active_rules:
                    rtype = rule.get("type")
                    if rtype not in {"sdk", "api", "string"}:
                        print(f"[sdk] skip rule {rule.get('rule_id')} unsupported type={rtype}")
                        continue
                    if _match_rule(content, rule):
                        finding = {
                            "rule_id": rule.get("rule_id"),
                            "regulation": rule.get("regulation"),
                            "severity": rule.get("severity", "medium"),
                            "source": source_flags.get(rule.get("rule_id"), "region"),
                            "location": str(fpath),
                            "evidence": f"pattern matched: {rule.get('pattern')}",
                            "recommendation": rule.get("recommendation", ""),
                        }
                        print(
                            f"[sdk] hit rule_id={finding['rule_id']} regulation={finding['regulation']} "
                            f"source={finding['source']} location={finding['location']}"
                        )
                        findings.append(finding)
        except FileNotFoundError as exc:
            print(f"[sdk] error: {exc}")
            continue

    for f in findings:
        reg = f.get("regulation")
        sev = f.get("severity")
        if reg:
            stats["count_by_regulation"][reg] = stats["count_by_regulation"].get(reg, 0) + 1
        if sev:
            stats["count_by_severity"][sev] = stats["count_by_severity"].get(sev, 0) + 1

    summary = (
        f"[sdk] scanned inputs={len(inputs)}, findings={len(findings)}, "
        f"by_regulation={stats['count_by_regulation']}, by_severity={stats['count_by_severity']}"
    )
    print(summary)

    if report_dir:
        report_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        meta = {
            "generated_at": timestamp,
            "inputs": [str(p) for p in inputs],
            "rule_count": len(rules),
            "finding_count": len(findings),
        }
        report = {"meta": meta, "findings": findings, "stats": stats}

        json_path = report_dir / f"{report_name}.json"
        html_path = report_dir / f"{report_name}.html"

        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))

        rows = "\n".join(
            [
                "<tr>"
                f"<td>{f.get('rule_id','')}</td>"
                f"<td>{f.get('regulation','')}</td>"
                f"<td>{f.get('source','')}</td>"
                f"<td>{f.get('severity','')}</td>"
                f"<td>{f.get('location','')}</td>"
                f"<td>{f.get('evidence','')}</td>"
                f"<td>{f.get('recommendation','')}</td>"
                "</tr>"
                for f in findings
            ]
        )
        html_content = f"""<!DOCTYPE html>
<html><body>
<h3>SDK/API Scan Report</h3>
<p>Generated at: {timestamp}</p>
<p>Inputs: {', '.join(meta['inputs'])}</p>
<p>Findings: {len(findings)}</p>
<p>Stats by regulation: {stats.get('count_by_regulation')}</p>
<p>Stats by severity: {stats.get('count_by_severity')}</p>
<table border="1" cellpadding="4" cellspacing="0">
<thead><tr><th>rule_id</th><th>regulation</th><th>source</th><th>severity</th><th>location</th><th>evidence</th><th>recommendation</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
</body></html>
"""
        html_path.write_text(html_content)
        print(f"[sdk] report saved: json={json_path} html={html_path}")

    return findings, stats
