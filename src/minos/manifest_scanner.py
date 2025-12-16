"""
Manifest 扫描占位实现。
后续需实现：解析权限/导出组件，按规则匹配并生成 findings/stats。
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple


def scan_manifest(manifest_path: Path, rules: List[Dict[str, Any]], source_flags: Dict[str, str]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    扫描 Manifest，返回 (findings, stats)。
    当前占位，后续补充解析与匹配逻辑。
    """
    raise NotImplementedError("Manifest scanner not implemented yet")
