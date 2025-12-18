"""
法规文档转换占位模块（通用框架 + 站点适配器）。

当前仅提供占位接口，后续按 Story-10 实现实际解析逻辑。
"""

import io
import logging
import os
import re
from typing import List, Dict, Tuple, Optional

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


_CLAUSE_PATTERNS = [
    re.compile(r"^\s*(Article|Art\.?)\s+([0-9A-Za-z\.\-]+)\s+(.*)$", re.IGNORECASE),
    re.compile(r"^\s*Section\s+([0-9A-Za-z\.\-]+)\s+(.*)$", re.IGNORECASE),
    re.compile(r"^\s*Art\.\s*([0-9A-Za-z\.\-]+)\s*[:\.]?\s*(.*)$", re.IGNORECASE),
]


def _extract_clause_title(line: str) -> Optional[Tuple[str, str]]:
    for pat in _CLAUSE_PATTERNS:
        m = pat.match(line)
        if m:
            if len(m.groups()) == 3:
                _, clause, title = m.groups()
            else:
                clause, title = m.groups()
            return clause.strip(), (title or "").strip()
    return None


def segment_text(text: str) -> List[Dict]:
    """
    基于条款编号与标题分段。对简单 Article/Section/Art. 模式做启发式解析。
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    segments: List[Dict] = []
    current: Dict = {}

    def _flush():
        if current.get("clause"):
            body_lines = current.get("body_lines", [])
            body = "\n".join(body_lines).strip()
            title = current.get("title") or (body.split("\n")[0] if body else "")
            segments.append(
                {
                    "clause": current["clause"],
                    "title": title.strip(),
                    "body": body,
                }
            )

    for line in lines:
        parsed = _extract_clause_title(line)
        if parsed:
            _flush()
            clause, title = parsed
            current = {"clause": clause, "title": title, "body_lines": []}
            continue
        # 非标题行，追加正文
        current.setdefault("body_lines", []).append(line)

    _flush()

    if not segments:
        raise RulesyncConvertError("未解析到任何条款编号/标题")

    return segments


_ALLOWED_REGULATIONS = {"gdpr", "ccpa", "cpra", "lgpd", "pipl", "appi"}
_ALLOWED_SEVERITY = {"low", "medium", "high"}


def _build_rules(segments: List[Dict], source_url: str, regulation: str, version: str) -> List[Dict]:
    regulation_norm = regulation.lower()
    if regulation_norm not in _ALLOWED_REGULATIONS:
        raise RulesyncConvertError(f"未支持的法规/站点: {regulation}")

    rules: List[Dict] = []
    for idx, seg in enumerate(segments, 1):
        rule_id = f"{regulation_norm.upper()}-{idx:03d}"
        rules.append(
            {
                "rule_id": rule_id,
                "regulation": regulation_norm.upper(),
                "title": seg.get("title", ""),
                "clause": seg.get("clause", ""),
                "description": seg.get("body", ""),
                "source_url": source_url,
                "version": version,
                "severity": "medium",
                "pattern": "",
                "evidence": "",
                "recommendation": "",
                "confidence": 1.0,
                "issues": [],
            }
        )
    return rules


def _validate_rules(rules: List[Dict]) -> None:
    for idx, rule in enumerate(rules, 1):
        missing = [k for k in ["rule_id", "regulation", "title", "clause", "description", "source_url", "version"] if not rule.get(k)]
        if missing:
            raise RulesyncConvertError(f"规则 {idx} 缺少必填字段: {','.join(missing)}")
        if rule.get("severity") not in _ALLOWED_SEVERITY:
            raise RulesyncConvertError(f"规则 {idx} severity 非法: {rule.get('severity')}")
        conf = rule.get("confidence")
        if not isinstance(conf, (int, float)) or conf < 0 or conf > 1:
            raise RulesyncConvertError(f"规则 {idx} confidence 非法: {conf}")
        if not isinstance(rule.get("issues"), list):
            raise RulesyncConvertError(f"规则 {idx} issues 类型应为数组")


def extract_rules_from_file(path: Path, source_url: str, regulation: str) -> List[Dict]:
    """
    从本地 HTML/PDF 提取规则列表。
    """
    text, _ = read_document(path)
    segments = segment_text(text)
    rules = _build_rules(segments, source_url=source_url, regulation=regulation, version="1.0.0")
    _validate_rules(rules)
    return rules


def convert_files_to_yaml(
    inputs: List[Path],
    out_path: Path,
    source_url: str,
    regulation: str,
    version: str = "1.0.0",
) -> Path:
    """
    将多个本地 HTML/PDF 转换为单一 YAML 文件。
    """
    all_segments: List[Dict] = []
    for path in inputs:
        text, _ = read_document(path)
        segs = segment_text(text)
        all_segments.extend(segs)

    rules = _build_rules(all_segments, source_url=source_url, regulation=regulation, version=version)
    _validate_rules(rules)

    try:
        import yaml  # type: ignore
    except Exception as exc:
        raise RulesyncConvertError(f"缺少 PyYAML 依赖: {exc}") from exc

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(rules, f, allow_unicode=True, sort_keys=False)
    return out_path
