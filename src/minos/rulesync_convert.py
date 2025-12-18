"""
法规文档转换占位模块（通用框架 + 站点适配器）。

当前仅提供占位接口，后续按 Story-10 实现实际解析逻辑。
"""

from pathlib import Path
from typing import List, Dict


class RulesyncConvertError(Exception):
    """转换失败基础异常。"""


def extract_rules_from_file(path: Path, source_url: str, regulation: str) -> List[Dict]:
    """
    占位接口：从本地 HTML/PDF 提取规则，后续按 Story-10 完成实现。
    """
    raise RulesyncConvertError("转换功能未实现")
