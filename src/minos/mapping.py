"""
地区 -> 法规映射占位实现。
后续需实现：加载地区/法规列表，合并并标注来源（region/manual）。
"""

from typing import Dict, List, Tuple


def load_regions() -> List[str]:
    """加载地区列表（占位）。"""
    raise NotImplementedError


def load_regulations() -> List[str]:
    """加载法规列表（占位）。"""
    raise NotImplementedError


def merge_mapping(regions: List[str], manual_add: List[str] | None = None, manual_remove: List[str] | None = None) -> Tuple[List[str], Dict[str, str]]:
    """
    根据地区映射并集法规，支持手动增删，返回最终法规列表和来源标记。
    """
    raise NotImplementedError
