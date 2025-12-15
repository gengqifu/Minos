"""
规则同步模块：拉取、校验、缓存与回滚。
"""

import hashlib
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class RulesyncError(Exception):
    """基础规则同步异常。"""


class RulesyncChecksumError(RulesyncError):
    """校验失败异常。"""


def _calc_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_metadata(cache_dir: Path, version: str, source: str, sha256: str, active: bool) -> None:
    meta = {
        "version": version,
        "source": source,
        "sha256": sha256,
        "gpg": None,
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "active": active,
    }
    meta_path = cache_dir / version / "metadata.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def _set_active(cache_dir: Path, version: str) -> None:
    for meta_file in cache_dir.glob("*/metadata.json"):
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        meta["active"] = meta_file.parent.name == version
        meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def sync_rules(
    source: str,
    version: str,
    cache_dir: Path,
    expected_sha256: Optional[str] = None,
    gpg_key: Optional[str] = None,
    offline: bool = False,
) -> Path:
    """
    从受控仓库拉取规则包、校验并写入缓存目录，返回激活版本路径。
    支持：
    - 校验（SHA256，预留 GPG）
    - 离线模式使用缓存
    - 元数据写入（版本、来源、校验结果、时间戳、active 标记）
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    target_dir = cache_dir / version
    if offline:
        if target_dir.exists():
            _set_active(cache_dir, version)
            return target_dir
        raise RulesyncError("离线模式下未找到缓存的规则版本")

    source_path = Path(source)
    if not source_path.exists():
        raise RulesyncError(f"规则源不存在: {source}")

    sha256 = _calc_sha256(source_path)
    if expected_sha256 and sha256 != expected_sha256:
        raise RulesyncChecksumError("规则包校验失败")

    if target_dir.exists():
        # 清理已有版本目录
        for child in target_dir.iterdir():
            if child.is_dir():
                for sub in child.rglob("*"):
                    if sub.is_file():
                        sub.unlink()
                child.rmdir()
            else:
                child.unlink()
        target_dir.rmdir()
    target_dir.mkdir(parents=True, exist_ok=True)

    # 解压 tar.gz 到目标目录
    with tarfile.open(source_path, "r:gz") as tar:
        tar.extractall(path=target_dir)

    _write_metadata(cache_dir, version, str(source_path), sha256, active=True)
    _set_active(cache_dir, version)
    return target_dir


def list_versions(cache_dir: Path) -> list[str]:
    """列出缓存的规则版本。"""
    if not cache_dir.exists():
        return []
    versions: list[str] = []
    for p in cache_dir.iterdir():
        if p.is_dir():
            versions.append(p.name)
    return versions


def activate_version(cache_dir: Path, version: str) -> Path:
    """切换激活规则版本。"""
    target_dir = cache_dir / version
    if not target_dir.exists():
        raise RulesyncError(f"未找到指定版本: {version}")
    _set_active(cache_dir, version)
    return target_dir


def rollback(cache_dir: Path, current_version: str, target_version: Optional[str] = None) -> Path:
    """
    回滚到指定版本；若未指定则回滚到上一个版本。
    """
    versions = sorted(list_versions(cache_dir))
    if target_version:
        if target_version not in versions:
            raise RulesyncError(f"未找到目标版本: {target_version}")
        return activate_version(cache_dir, target_version)

    if current_version not in versions:
        raise RulesyncError(f"当前版本不存在: {current_version}")
    idx = versions.index(current_version)
    if idx == 0:
        raise RulesyncError("没有更早的版本可回滚")
    prev_version = versions[idx - 1]
    return activate_version(cache_dir, prev_version)
