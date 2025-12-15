"""
地区 -> 法规映射工具。
"""

from typing import Dict, List, Tuple
import json
from pathlib import Path

# 默认地区与法规映射（可扩展/覆盖）
DEFAULT_REGION_MAP: Dict[str, List[str]] = {
    "EU": ["GDPR"],
    "US-CA": ["CCPA/CPRA"],
    "US": [],
    "BR": ["LGPD"],
    "CN": ["PIPL"],
    "JP": ["APPI"],
}

# 默认可选法规列表（可扩展）
DEFAULT_REGULATIONS = ["GDPR", "CCPA/CPRA", "LGPD", "PIPL", "APPI"]

# 默认可选地区列表（可扩展）
DEFAULT_REGIONS = ["EU", "US-CA", "US", "BR", "CN", "JP"]


def load_regions(region_map: Dict[str, List[str]] | None = None) -> List[str]:
    """加载可选地区列表，支持覆盖映射表。"""
    region_map = region_map or DEFAULT_REGION_MAP
    return list(region_map.keys())


def load_regulations(regulations: List[str] | None = None) -> List[str]:
    """
    加载可选法规列表，支持覆盖/扩展。
    """
    regulations = regulations or DEFAULT_REGULATIONS
    return list(regulations)


def merge_mapping(
    regions: List[str],
    manual_add: List[str] | None = None,
    manual_remove: List[str] | None = None,
) -> Tuple[List[str], Dict[str, str]]:
    """
    根据地区映射并集法规，支持手动增删，返回最终法规列表和来源标记。
    来源标记：
    - region: 由地区映射产生
    - manual: 手动添加
    """
    manual_add = manual_add or []
    manual_remove = manual_remove or []

    # 校验地区合法性
    invalid_regions = [reg for reg in regions if reg not in DEFAULT_REGION_MAP]
    if invalid_regions:
        raise ValueError(f"未知地区: {', '.join(invalid_regions)}")

    regs_set: set[str] = set()
    source_flags: Dict[str, str] = {}

    # 地区映射
    for region in regions:
        mapped = DEFAULT_REGION_MAP.get(region, [])
        for r in mapped:
            regs_set.add(r)
            source_flags.setdefault(r, "region")

    # 手动添加
    for r in manual_add:
        regs_set.add(r)
        source_flags[r] = "manual"

    # 手动移除
    for r in manual_remove:
        if r in regs_set:
            regs_set.remove(r)
        source_flags.pop(r, None)

    regs_list = sorted(regs_set)
    return regs_list, source_flags


def build_selection(
    regions: List[str],
    manual_add: List[str] | None = None,
    manual_remove: List[str] | None = None,
    region_map: Dict[str, List[str]] | None = None,
) -> Dict[str, object]:
    """
    生成供扫描器/报告使用的配置输出：
    {
      "regions": [...],
      "regulations": [...],
      "source_flags": {regulation: "region"|"manual"},
      "report": {
        "regions": [...],
        "regulations": [...],
        "source_flags": {...}
      }
    }
    """
    regs, flags = merge_mapping(regions, manual_add=manual_add, manual_remove=manual_remove)
    return {
        "regions": regions,
        "regulations": regs,
        "source_flags": flags,
        "report": {
            "regions": regions,
            "regulations": regs,
            "source_flags": flags,
        },
        "summary": {
            "regions": regions,
            "regulations": regs,
        },
    }


def load_config(config_path: Path) -> Dict[str, List[str]]:
    """
    从 JSON 配置文件读取地区/法规选择：
    {
      "regions": [...],
      "manual_add": [...],
      "manual_remove": [...]
    }
    """
    if not config_path.exists():
        raise FileNotFoundError(f"未找到配置文件: {config_path}")
    data = json.loads(config_path.read_text(encoding="utf-8"))
    regions = data.get("regions") or []
    manual_add = data.get("manual_add") or []
    manual_remove = data.get("manual_remove") or []
    if not isinstance(regions, list) or not isinstance(manual_add, list) or not isinstance(manual_remove, list):
        raise ValueError("配置格式错误，需包含数组字段 regions/manual_add/manual_remove")
    return {"regions": regions, "manual_add": manual_add, "manual_remove": manual_remove}
