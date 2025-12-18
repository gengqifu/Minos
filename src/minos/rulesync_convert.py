"""
法规文档转换占位模块（通用框架 + 站点适配器）。

当前仅提供占位接口，后续按 Story-10 实现实际解析逻辑。
"""

import io
import logging
import os
from typing import List, Dict, Tuple

from pathlib import Path


class RulesyncConvertError(Exception):
    """转换失败基础异常。"""


def _read_text_file(path: Path) -> str:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _read_pdf_file(path: Path) -> str:
    """
    尝试读取 PDF 文本。优先使用 PyPDF2；若未安装则以文本方式兜底（便于测试样例）。
    """
    try:
        import PyPDF2  # type: ignore
    except Exception:
        # 兜底：当作文本文件读取（测试样例用）
        return _read_text_file(path)

    try:
        reader = PyPDF2.PdfReader(str(path))
        texts = []
        for page in reader.pages:
            try:
                texts.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n".join(texts)
    except Exception as exc:
        raise RulesyncConvertError(f"PDF 解析失败: {exc}") from exc


def read_document(path: Path) -> Tuple[str, str]:
    """
    读取本地文档内容，返回 (text, mime)。
    支持 HTML/PDF，占位实现：HTML 视为 utf-8 文本；PDF 尝试解析文本，失败则异常。
    """
    if not path.exists():
        raise RulesyncConvertError(f"文件不存在: {path}")

    suffix = path.suffix.lower()
    if suffix in (".html", ".htm"):
        return _read_text_file(path), "text/html"
    if suffix == ".pdf":
        return _read_pdf_file(path), "application/pdf"

    raise RulesyncConvertError(f"不支持的文件类型: {path.suffix}")


def extract_rules_from_file(path: Path, source_url: str, regulation: str) -> List[Dict]:
    """
    占位接口：从本地 HTML/PDF 提取规则，后续按 Story-10 完成实现。
    """
    raise RulesyncConvertError("转换功能未实现")


def convert_files_to_yaml(
    inputs: List[Path],
    out_path: Path,
    source_url: str,
    regulation: str,
) -> Path:
    """
    占位接口：将多个本地 HTML/PDF 转换为单一 YAML 文件。
    """
    raise RulesyncConvertError("转换功能未实现")
