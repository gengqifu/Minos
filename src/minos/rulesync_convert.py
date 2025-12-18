"""
法规文档转换占位模块（通用框架 + 站点适配器）。

当前仅提供占位接口，后续按 Story-10 实现实际解析逻辑。
"""

import html as html_lib
import re
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class RulesyncConvertError(Exception):
    """转换失败基础异常。"""


def _read_text_file(path: Path) -> str:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _clean_html_text(text: str) -> str:
    """
    简单 HTML 清洗：去标签、转义实体、保留换行便于分段。
    """
    # 替换常见块级标签为换行以保留结构
    text = re.sub(r"</?(h[1-6]|p|div|section|article|br|li)[^>]*>", "\n", text, flags=re.IGNORECASE)
    # 去掉其他标签
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    # 规整空白
    text = re.sub(r"[ \t\r]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def _read_pdf_file(path: Path) -> str:
    """
    尝试读取 PDF 文本。优先使用 pypdf；若未安装则以文本方式兜底（便于测试样例）。
    """
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        # 兜底：当作文本文件读取（测试样例用）
        return _read_text_file(path)

    try:
        reader = PdfReader(str(path))
        texts = []
        for page in reader.pages:
            try:
                texts.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n".join(texts)
    except Exception as exc:
        # 若 PyPDF2 解析失败，回退到按文本读取，便于测试样例与非标准 PDF
        try:
            return _read_text_file(path)
        except Exception:
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
        raw = _read_text_file(path)
        return _clean_html_text(raw), "text/html"
    if suffix == ".pdf":
        return _read_pdf_file(path), "application/pdf"

    raise RulesyncConvertError(f"不支持的文件类型: {path.suffix}")


_CLAUSE_PATTERNS = [
    re.compile(r"^\s*(Article|Art\.?)\s+([0-9A-Za-z\.\-\u00ba\u00b0]+)(?:\s+(.*))?$", re.IGNORECASE),
    re.compile(r"^\s*Section\s+([0-9A-Za-z\.\-\u00ba\u00b0]+)(?:\s+(.*))?$", re.IGNORECASE),
    re.compile(r"^\s*Art\.\s*([0-9A-Za-z\.\-\u00ba\u00b0]+)\s*[:\.]?\s*(.*)?$", re.IGNORECASE),
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


class BaseAdapter:
    """站点适配器基类。"""

    def extract_segments(self, text: str, source_url: str) -> List[Dict]:
        raise NotImplementedError


class GenericAdapter(BaseAdapter):
    """默认适配器：基于通用条款模式分段。"""

    def extract_segments(self, text: str, source_url: str) -> List[Dict]:
        return segment_text(text)


class EurlexAdapter(GenericAdapter):
    """EUR-Lex GDPR 适配器：基于清洗后文本做 Article 分段，忽略 Annex。"""

    def extract_segments(self, text: str, source_url: str) -> List[Dict]:
        text = _clean_html_text(text)
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
            # Annex/附录后内容忽略
            if re.match(r"^annex\b", line, re.IGNORECASE):
                break
            parsed = _extract_clause_title(line)
            if parsed:
                _flush()
                clause, title = parsed
                current = {"clause": clause, "title": title, "body_lines": []}
                continue
            if current:
                current.setdefault("body_lines", []).append(line)

        _flush()
        if not segments:
            raise RulesyncConvertError("未解析到任何条款编号/标题")
        return segments


class LeginfoAdapter(GenericAdapter):
    """leginfo CCPA/CPRA 适配器：基于 Section 分段，过滤目录/附录。"""

    def extract_segments(self, text: str, source_url: str) -> List[Dict]:
        text = _clean_html_text(text)
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
            # 跳过目录/附录关键词
            if re.match(r"^(table of contents|appendix|annex)\b", line, re.IGNORECASE):
                continue
            parsed = _extract_clause_title(line)
            if parsed:
                _flush()
                clause, title = parsed
                current = {"clause": clause, "title": title, "body_lines": []}
                continue
            if current:
                current.setdefault("body_lines", []).append(line)

        _flush()
        if not segments:
            raise RulesyncConvertError("未解析到任何条款编号/标题")
        return segments


class PlanaltoAdapter(GenericAdapter):
    """LGPD planalto 适配器：基于 Art. 分段，过滤 índice/附录。"""

    def extract_segments(self, text: str, source_url: str) -> List[Dict]:
        text = _clean_html_text(text)
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
            if re.match(r"^(indice|sum[áa]rio)\b", line, re.IGNORECASE):
                continue
            if re.match(r"^anexo\b", line, re.IGNORECASE):
                break
            parsed = _extract_clause_title(line)
            if parsed:
                _flush()
                clause, title = parsed
                current = {"clause": clause, "title": title, "body_lines": []}
                continue
            if current:
                current.setdefault("body_lines", []).append(line)

        _flush()
        if not segments:
            raise RulesyncConvertError("未解析到任何条款编号/标题")
        return segments


ADAPTERS = {
    "gdpr": EurlexAdapter(),
    "ccpa": LeginfoAdapter(),
    "cpra": LeginfoAdapter(),
    "lgpd": PlanaltoAdapter(),
    "pipl": GenericAdapter(),
    "appi": GenericAdapter(),
}


def _get_adapter(regulation: str) -> BaseAdapter:
    reg = regulation.lower()
    adapter = ADAPTERS.get(reg)
    if not adapter:
        raise RulesyncConvertError(f"未支持的法规/站点: {regulation}")
    return adapter


def _build_rules(segments: List[Dict], source_url: str, regulation: str, version: str) -> List[Dict]:
    regulation_norm = regulation.lower()

    rules: List[Dict] = []
    for idx, seg in enumerate(segments, 1):
        rule_id = f"{regulation_norm.upper()}-{idx:03d}"
        title = (seg.get("title") or "").strip()
        clause = (seg.get("clause") or "").strip()
        body = (seg.get("body") or "").strip()
        description = body or title or clause
        rules.append(
            {
                "rule_id": rule_id,
                "regulation": regulation_norm.upper(),
                "title": title,
                "clause": clause,
                "description": description,
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
    adapter = _get_adapter(regulation)
    text, _ = read_document(path)
    segments = adapter.extract_segments(text, source_url=source_url)
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
    adapter = _get_adapter(regulation)

    all_segments: List[Dict] = []
    for path in inputs:
        text, _ = read_document(path)
        segs = adapter.extract_segments(text, source_url=source_url)
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


def _cache_filename(url: str) -> str:
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return f"{h}.html"


def fetch_url(url: str, cache_dir: Path, timeout: int = 20) -> Path:
    """
    下载 URL 到缓存目录；若缓存已存在则直接返回。
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / _cache_filename(url)
    if target.exists():
        return target
    # 支持 file:// 直接读取
    if url.startswith("file://"):
        src_path = Path(url.replace("file://", "", 1))
        if not src_path.exists():
            raise RulesyncConvertError(f"文件不存在: {url}")
        target.write_bytes(src_path.read_bytes())
        return target
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            content = resp.read()
        target.write_bytes(content)
        return target
    except urllib.error.URLError as exc:  # pragma: no cover - 依赖网络
        raise RulesyncConvertError(f"下载失败: {exc}") from exc
    except Exception as exc:  # pragma: no cover
        raise RulesyncConvertError(f"下载失败: {exc}") from exc


def convert_url_to_yaml(
    url: str,
    cache_dir: Path,
    out_path: Path,
    regulation: str,
    version: str = "1.0.0",
    timeout: int = 20,
) -> Path:
    """
    下载 URL（带缓存）并转换为 YAML。
    """
    cache_file = fetch_url(url, cache_dir=cache_dir, timeout=timeout)
    return convert_files_to_yaml(inputs=[cache_file], out_path=out_path, source_url=url, regulation=regulation, version=version)
