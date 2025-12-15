"""
地区 -> 法规映射工具。
"""

from typing import Dict, List, Tuple

# 默认地区与法规映射
DEFAULT_REGION_MAP: Dict[str, List[str]] = {
    "EU": ["GDPR"],
    "US-CA": ["CCPA/CPRA"],
}

# 默认可选法规列表（可扩展）
DEFAULT_REGULATIONS = ["GDPR", "CCPA/CPRA", "LGPD", "PIPL", "APPI"]

# 默认可选地区列表（可扩展）
DEFAULT_REGIONS = ["EU", "US-CA", "US", "BR", "CN", "JP"]


def load_regions() -> List[str]:
    """加载可选地区列表。"""
    return list(DEFAULT_REGIONS)


def load_regulations() -> List[str]:
    """加载可选法规列表。"""
    return list(DEFAULT_REGULATIONS)


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
    for reg in regions:
        if reg not in DEFAULT_REGION_MAP:
            raise ValueError(f"未知地区: {reg}")

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
