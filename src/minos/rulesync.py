"""
规则同步模块：拉取、校验、缓存与回滚。
"""

import hashlib
import json
import shutil
import subprocess
import tarfile
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional


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


def _is_remote_source(source: str) -> bool:
    return source.startswith(("http://", "https://", "git+", "oci://", "oci+"))


def _download_http(source: str, dest: Path, timeout: int = 30) -> None:
    try:
        with urllib.request.urlopen(source, timeout=timeout) as resp, dest.open("wb") as out:
            shutil.copyfileobj(resp, out)
    except Exception as exc:  # pragma: no cover - 依赖外部网络
        raise RulesyncError(f"HTTP 下载失败: {exc}") from exc


def _parse_source_with_path(source: str) -> tuple[str, Optional[str]]:
    raw = source.split("#", 1)
    base = raw[0]
    path = None
    if len(raw) == 2:
        params = urllib.parse.parse_qs(raw[1])
        if "path" in params and params["path"]:
            path = params["path"][0]
    return base, path


def _download_git(source: str, dest: Path) -> None:
    base, path = _parse_source_with_path(source)
    repo_url = base[len("git+") :]
    rel_path = Path(path) if path else Path("rules.tar.gz")
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = Path(tmpdir) / "repo"
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(repo_dir)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except FileNotFoundError as exc:
            raise RulesyncError("未找到 git 命令，请先安装 git") from exc
        except subprocess.CalledProcessError as exc:
            raise RulesyncError(f"git 拉取失败: {exc.stderr.strip()}") from exc

        target = repo_dir / rel_path
        if not target.exists():
            raise RulesyncError(f"git 源未找到路径: {rel_path}")

        if target.is_dir():
            with tarfile.open(dest, "w:gz") as tar:
                tar.add(target, arcname="rules")
        else:
            shutil.copyfile(target, dest)


def _download_oci(source: str, dest: Path) -> None:
    base, path = _parse_source_with_path(source)
    ref = base.replace("oci://", "", 1).replace("oci+", "", 1)
    if not shutil.which("oras"):
        raise RulesyncError("未找到 oras，请先安装以拉取 OCI 制品")
    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir) / "oci"
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["oras", "pull", ref, "-o", str(out_dir)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            raise RulesyncError(f"OCI 拉取失败: {exc.stderr.strip()}") from exc
        rel_path = Path(path) if path else None
        if rel_path:
            target = out_dir / rel_path
            if not target.exists():
                raise RulesyncError(f"OCI 制品未找到路径: {rel_path}")
            shutil.copyfile(target, dest)
            return
        candidates = list(out_dir.rglob("*.tar.gz"))
        if len(candidates) != 1:
            raise RulesyncError("OCI 制品包含多个 tar.gz，请使用 #path 指定")
        shutil.copyfile(candidates[0], dest)


def _prepare_remote_source(source: str, tmpdir: Path) -> Path:
    tmpdir.mkdir(parents=True, exist_ok=True)
    dest = tmpdir / "rules.tar.gz"
    if source.startswith(("http://", "https://")):
        _download_http(source, dest)
    elif source.startswith("git+"):
        _download_git(source, dest)
    elif source.startswith(("oci://", "oci+")):
        _download_oci(source, dest)
    else:
        raise RulesyncError(f"不支持的远端协议: {source}")
    return dest


def _write_metadata(
    cache_dir: Path, version: str, source: str, sha256: str, active: bool, gpg: Optional[str] = None
) -> None:
    meta = {
        "version": version,
        "source": source,
        "sha256": sha256,
        "gpg": gpg,
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


def get_active_path(cache_dir: Path) -> Optional[Path]:
    """返回当前激活的规则目录路径，无则返回 None。"""
    if not cache_dir.exists():
        return None
    for meta_file in cache_dir.glob("*/metadata.json"):
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        if meta.get("active"):
            return meta_file.parent
    return None


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
            print(f"[rulesync] offline mode, using cached version {version}")
            return target_dir
        print("[rulesync] offline mode but version not found")
        raise RulesyncError("离线模式下未找到缓存的规则版本")

    def _sync_from_path(source_path: Path) -> Path:
        if not source_path.exists():
            print(f"[rulesync] source not found: {source}")
            raise RulesyncError(f"规则源不存在: {source}")

        sha256 = _calc_sha256(source_path)
        if expected_sha256 and sha256 != expected_sha256:
            print("[rulesync] checksum mismatch")
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

        print(f"[rulesync] synced {version} from {source} to {target_dir}")
        _write_metadata(cache_dir, version, source, sha256, active=True, gpg=gpg_key)
        _set_active(cache_dir, version)
        return target_dir

    if _is_remote_source(source):
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = _prepare_remote_source(source, Path(tmpdir))
            return _sync_from_path(source_path)

    return _sync_from_path(Path(source))


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


def cleanup(cache_dir: Path, keep: int = 3) -> None:
    """
    清理旧版本/缓存，只保留最新 keep 个版本（按名称排序）。
    """
    if keep <= 0:
        return
    versions = sorted(list_versions(cache_dir))
    if len(versions) <= keep:
        return
    to_delete = versions[:-keep]
    for version in to_delete:
        target_dir = cache_dir / version
        if target_dir.exists() and target_dir.is_dir():
            for sub in target_dir.rglob("*"):
                if sub.is_file():
                    sub.unlink()
            # 删除空目录
            for subdir in sorted(target_dir.rglob("*"), reverse=True):
                if subdir.is_dir():
                    try:
                        subdir.rmdir()
                    except OSError:
                        pass
            try:
                target_dir.rmdir()
            except OSError:
                pass


# 默认法规列表（来自 PRD 法规参考链接）
DEFAULT_REGULATIONS = ["gdpr", "ccpa", "cpra", "lgpd", "pipl", "appi"]


def sync_regulations(
    regulations: Optional[list[str]],
    version: str,
    cache_root: Path,
    downloader: Optional[Callable[[str, str, Path], str]] = None,
    cleanup_keep: int = 1,
    offline: bool = False,
    retries: int = 0,
) -> None:
    """
    同步多个法规集，默认同步 PRD 法规参考链接中的全部法规。
    - regulations: None 表示同步默认列表；否则同步指定子集
    - cache_root: 根缓存目录，下级按法规隔离 (~/.minos/rules/<regulation>)
    - downloader: 可注入的下载器，签名 downloader(regulation, version, cache_root) -> sha256
    - cleanup_keep: 同步成功后保留的版本数（按法规目录内处理）
    - offline: 离线模式，仅使用已有缓存，缺失则报错
    - retries: 下载失败的重试次数（默认 0）
    """
    regs = regulations or DEFAULT_REGULATIONS
    cache_root.mkdir(parents=True, exist_ok=True)

    if downloader is None and not offline:
        raise RulesyncError("在线规则同步未实现，请提供 downloader 或启用离线模式")

    for reg in regs:
        reg_dir = cache_root / reg
        reg_dir.mkdir(parents=True, exist_ok=True)

        if offline:
            active = get_active_path(reg_dir)
            if active is None:
                raise RulesyncError(f"离线模式下未找到 {reg} 缓存")
            print(f"[rulesync] offline use cached {reg} -> {active}")
            continue

        # 通过注入 downloader 拉取指定法规版本并写入隔离目录
        attempts = 0
        while True:
            try:
                downloader(reg, version, reg_dir)  # type: ignore[misc]
                break
            except RulesyncError as exc:
                attempts += 1
                if attempts > retries:
                    raise
                print(f"[rulesync] download failed for {reg}, retry {attempts}/{retries}: {exc}")
            except Exception as exc:
                attempts += 1
                if attempts > retries:
                    raise RulesyncError(f"同步 {reg} 失败: {exc}") from exc
                print(f"[rulesync] download failed for {reg}, retry {attempts}/{retries}: {exc}")

        if cleanup_keep and cleanup_keep > 0:
            cleanup(reg_dir, keep=cleanup_keep)
