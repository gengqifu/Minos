import hashlib
import tarfile
from pathlib import Path

import pytest

try:
    from minos import rulesync
except ImportError:  # pragma: no cover - 模块缺失时跳过
    rulesync = None


def _create_pkg(tmpdir: Path, regulation: str, version: str) -> tuple[Path, str]:
    pkg_dir = tmpdir / f"{regulation}-{version}"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / f"{regulation}.txt").write_text(f"{regulation}-{version}", encoding="utf-8")
    tar_path = tmpdir / f"{regulation}-{version}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(pkg_dir, arcname="rules")
    sha256 = hashlib.sha256(tar_path.read_bytes()).hexdigest()
    return tar_path, sha256


def test_sync_default_all_regulations_isolates_cache(tmp_path: Path):
    if rulesync is None:
        pytest.skip("rulesync 模块不可用")

    cache_root = tmp_path / "rules"
    regs = ["gdpr", "ccpa", "cpra", "lgpd", "pipl", "appi"]
    sources = {}
    for reg in regs:
        pkg, sha = _create_pkg(tmp_path, reg, "v1")
        sources[reg] = (pkg, sha)

    def fake_download(regulation: str, version: str, target_dir: Path):
        pkg, sha = sources[regulation]
        # 模拟下载并解压
        rulesync.sync_rules(str(pkg), version, cache_dir=target_dir, expected_sha256=sha)
        return sha

    # 假定将来有 sync_regulations API：传入 None 时默认全量
    rulesync.sync_regulations(
        regulations=None, version="v1", cache_root=cache_root, downloader=fake_download, cleanup_keep=1
    )

    for reg in regs:
        reg_dir = cache_root / reg
        assert reg_dir.exists()
        assert (reg_dir / "v1").exists()


def test_sync_subset_only_target_regulations(tmp_path: Path):
    if rulesync is None:
        pytest.skip("rulesync 模块不可用")

    cache_root = tmp_path / "rules"
    regs = ["gdpr", "ccpa", "lgpd"]
    sources = {}
    for reg in regs:
        pkg, sha = _create_pkg(tmp_path, reg, "v1")
        sources[reg] = (pkg, sha)

    def fake_download(regulation: str, version: str, target_dir: Path):
        pkg, sha = sources[regulation]
        rulesync.sync_rules(str(pkg), version, cache_dir=target_dir, expected_sha256=sha)
        return sha

    target_regs = ["gdpr", "lgpd"]
    rulesync.sync_regulations(
        regulations=target_regs, version="v1", cache_root=cache_root, downloader=fake_download, cleanup_keep=1
    )

    for reg in target_regs:
        assert (cache_root / reg / "v1").exists()
    assert not (cache_root / "ccpa").exists()


def test_sync_failure_keeps_existing_cache(tmp_path: Path):
    if rulesync is None:
        pytest.skip("rulesync 模块不可用")

    cache_root = tmp_path / "rules"
    reg = "gdpr"
    pkg_v1, sha1 = _create_pkg(tmp_path, reg, "v1")

    # 先落地 v1
    rulesync.sync_rules(str(pkg_v1), "v1", cache_dir=cache_root / reg, expected_sha256=sha1)

    def broken_download(regulation: str, version: str, target_dir: Path):
        raise rulesync.RulesyncError("network failure")

    with pytest.raises(rulesync.RulesyncError):
        rulesync.sync_regulations(
            regulations=[reg], version="v2", cache_root=cache_root, downloader=broken_download, cleanup_keep=1
        )

    # v1 应仍然存在
    assert (cache_root / reg / "v1").exists()


def test_offline_without_cache_raises(tmp_path: Path):
    if rulesync is None:
        pytest.skip("rulesync 模块不可用")

    cache_root = tmp_path / "rules"
    reg = "gdpr"
    with pytest.raises(rulesync.RulesyncError):
        rulesync.sync_regulations(
            regulations=[reg],
            version="v1",
            cache_root=cache_root,
            downloader=None,
            offline=True,
        )


def test_sync_overwrites_old_version_and_keeps_latest(tmp_path: Path):
    if rulesync is None:
        pytest.skip("rulesync 模块不可用")

    cache_root = tmp_path / "rules"
    reg = "gdpr"
    pkg_v1, sha1 = _create_pkg(tmp_path, reg, "v1")
    pkg_v2, sha2 = _create_pkg(tmp_path, reg, "v2")

    def download_v1(regulation: str, version: str, target_dir: Path):
        rulesync.sync_rules(str(pkg_v1), version, cache_dir=target_dir, expected_sha256=sha1)
        return sha1

    rulesync.sync_regulations([reg], "v1", cache_root, downloader=download_v1)
    assert (cache_root / reg / "v1").exists()

    def download_v2(regulation: str, version: str, target_dir: Path):
        rulesync.sync_rules(str(pkg_v2), version, cache_dir=target_dir, expected_sha256=sha2)
        return sha2

    # 默认 cleanup_keep=1，仅保留最新 v2
    rulesync.sync_regulations([reg], "v2", cache_root, downloader=download_v2)
    assert not (cache_root / reg / "v1").exists()
    assert (cache_root / reg / "v2").exists()


@pytest.mark.parametrize("protocol", ["http", "git", "oci"])
def test_remote_sync_success_protocols(tmp_path: Path, protocol: str):
    if rulesync is None:
        pytest.skip("rulesync 模块不可用")

    cache_root = tmp_path / "rules"
    reg = "gdpr"
    pkg, sha = _create_pkg(tmp_path, reg, "v1")

    def remote_download(regulation: str, version: str, target_dir: Path):
        assert regulation == reg
        assert protocol in {"http", "git", "oci"}
        rulesync.sync_rules(str(pkg), version, cache_dir=target_dir, expected_sha256=sha)
        return sha

    rulesync.sync_regulations([reg], "v1", cache_root, downloader=remote_download, cleanup_keep=1)
    assert (cache_root / reg / "v1").exists()


def test_remote_sync_retries_then_success(tmp_path: Path):
    if rulesync is None:
        pytest.skip("rulesync 模块不可用")

    cache_root = tmp_path / "rules"
    reg = "gdpr"
    pkg, sha = _create_pkg(tmp_path, reg, "v1")
    calls = {"n": 0}

    def flaky_download(regulation: str, version: str, target_dir: Path):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise rulesync.RulesyncError("timeout")
        rulesync.sync_rules(str(pkg), version, cache_dir=target_dir, expected_sha256=sha)
        return sha

    rulesync.sync_regulations([reg], "v1", cache_root, downloader=flaky_download, cleanup_keep=1, retries=2)
    assert calls["n"] == 3
    assert (cache_root / reg / "v1").exists()


@pytest.mark.parametrize("protocol", ["http", "git", "oci"])
def test_remote_sync_failure_keeps_cache(tmp_path: Path, protocol: str):
    if rulesync is None:
        pytest.skip("rulesync 模块不可用")

    cache_root = tmp_path / "rules"
    reg = "gdpr"
    pkg_v1, sha1 = _create_pkg(tmp_path, reg, "v1")
    rulesync.sync_rules(str(pkg_v1), "v1", cache_dir=cache_root / reg, expected_sha256=sha1)

    calls = {"n": 0}

    def broken_download(regulation: str, version: str, target_dir: Path):
        calls["n"] += 1
        raise rulesync.RulesyncError(f"{protocol} down")

    with pytest.raises(rulesync.RulesyncError):
        rulesync.sync_regulations(
            [reg],
            "v2",
            cache_root,
            downloader=broken_download,
            cleanup_keep=1,
            retries=1,
        )

    assert calls["n"] == 2
    assert (cache_root / reg / "v1").exists()
    assert not (cache_root / reg / "v2").exists()
