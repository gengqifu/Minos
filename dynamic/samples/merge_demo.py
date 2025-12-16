#!/usr/bin/env python3
"""
示例：合并静态与动态 findings，演示 schema 校验与去重。
运行方式：
    python dynamic/samples/merge_demo.py
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent
STATIC_PATH = Path(os.getenv("STATIC_PATH", ROOT / "static_findings.json"))
DYNAMIC_PATH = Path(os.getenv("DYNAMIC_PATH", ROOT / "dynamic_findings.json"))


def load_json(path: Path) -> dict:
    if not path.exists():
        sys.stderr.write(f"[merge-demo] 文件不存在: {path}\n")
        sys.exit(2)
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover - demo script
        sys.stderr.write(f"[merge-demo] 解析失败 {path}: {exc}\n")
        sys.exit(2)


def validate_entry(entry: dict) -> None:
    required = {"type", "source", "rule_id", "regulation", "severity", "location", "evidence"}
    missing = required - set(entry.keys())
    if missing:
        sys.stderr.write(f"[merge-demo] 缺少字段 {missing} in {entry}\n")
        sys.exit(2)


def merge_findings(static_data: dict, dynamic_data: dict) -> dict:
    merged = {"meta": {"mode": "both"}, "findings": [], "stats": {"count_by_source": {}}}
    seen = set()
    for entry in static_data.get("findings", []) + dynamic_data.get("findings", []):
        validate_entry(entry)
        key = (entry.get("rule_id"), entry.get("location"), entry.get("source"))
        if key in seen:
            continue
        seen.add(key)
        detection_type = entry.get("type", "static")
        merged["findings"].append({**entry, "detection_type": detection_type})
        src = entry.get("source", "unknown")
        merged["stats"]["count_by_source"][src] = merged["stats"]["count_by_source"].get(src, 0) + 1
    merged["meta"]["inputs"] = [STATIC_PATH.name, DYNAMIC_PATH.name]
    return merged


def main() -> int:
    static_data = load_json(STATIC_PATH)
    dynamic_data = load_json(DYNAMIC_PATH)
    report = merge_findings(static_data, dynamic_data)
    sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
