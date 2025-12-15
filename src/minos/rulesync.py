"""
规则同步模块占位符。
后续需实现：规则拉取、校验、缓存与回滚逻辑。
"""

from pathlib import Path
from typing import Optional


class RulesyncError(Exception):
    """基础规则同步异常。"""


class RulesyncChecksumError(RulesyncError):
    """校验失败异常。"""


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
    需支持：
    - 校验（SHA256，预留 GPG）
    - 离线模式使用缓存
    - 元数据写入（版本、来源、校验结果、时间戳、active 标记）
    """
    raise NotImplementedError


def list_versions(cache_dir: Path) -> list[str]:
    """列出缓存的规则版本。"""
    raise NotImplementedError


def activate_version(cache_dir: Path, version: str) -> Path:
    """切换激活规则版本。"""
    raise NotImplementedError
