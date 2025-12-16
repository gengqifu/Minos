"""
SDK/敏感 API/字符串 扫描占位实现。
后续需实现：
- 解析 APK/源码中的 DEX/字符串/域名等
- 识别已知追踪/广告 SDK、敏感 API/字符串，返回 findings/stats
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple


def scan_sdk_api(
    inputs: List[Path],
    rules: List[Dict[str, Any]],
    source_flags: Dict[str, str],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    扫描输入（APK/源码路径），返回 (findings, stats)。
    """
    raise NotImplementedError("SDK/API scanner not implemented yet")
