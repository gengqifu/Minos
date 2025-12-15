import hashlib
import json
import tarfile
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from minos import rulesync
from minos import cli


def _create_rules_pkg(tmpdir: Path, version: str, content: str = "rule") -> Path:
    """在临时目录下生成规则包 tar.gz，返回包路径和 sha256。"""
    pkg_dir = tmpdir / f"rules-{version}"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    rules_file = pkg_dir / "rules.txt"
    rules_file.write_text(content, encoding="utf-8")
    tar_path = tmpdir / f"rules-{version}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(pkg_dir, arcname="rules")
    sha256 = hashlib.sha256(tar_path.read_bytes()).hexdigest()
    return tar_path, sha256


def _read_metadata(cache_dir: Path, version: str) -> dict:
    meta_path = cache_dir / version / "metadata.json"
    return json.loads(meta_path.read_text(encoding="utf-8"))


def test_sync_rules_success_writes_metadata_and_activates(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    pkg_path, sha256 = _create_rules_pkg(tmp_path, "v1.0.0")

    active_path = rulesync.sync_rules(
        source=str(pkg_path),
        version="v1.0.0",
        cache_dir=cache_dir,
        expected_sha256=sha256,
    )

    meta = _read_metadata(cache_dir, "v1.0.0")
    assert active_path.exists()
    assert meta["version"] == "v1.0.0"
    assert meta["source"] == str(pkg_path)
    assert meta["sha256"] == sha256
    assert meta.get("active") is True


def test_sync_rules_checksum_mismatch_raises_and_no_activate(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    pkg_path, sha256 = _create_rules_pkg(tmp_path, "v1.0.0")

    with pytest.raises(rulesync.RulesyncChecksumError):
        rulesync.sync_rules(
            source=str(pkg_path),
            version="v1.0.0",
            cache_dir=cache_dir,
            expected_sha256="badchecksum",
        )

    assert not (cache_dir / "v1.0.0").exists()


def test_offline_uses_cached_version(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    pkg_path, sha256 = _create_rules_pkg(tmp_path, "v1.0.0")

    # 先正常同步一次
    rulesync.sync_rules(
        source=str(pkg_path),
        version="v1.0.0",
        cache_dir=cache_dir,
        expected_sha256=sha256,
    )

    # 离线模式，不应触发拉取，直接使用缓存
    active_path = rulesync.sync_rules(
        source=str(pkg_path),
        version="v1.0.0",
        cache_dir=cache_dir,
        expected_sha256=sha256,
        offline=True,
    )
    assert active_path.exists()


def test_activate_version_switches_active_pointer(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    pkg1, sha1 = _create_rules_pkg(tmp_path, "v1.0.0")
    pkg2, sha2 = _create_rules_pkg(tmp_path, "v1.1.0")

    rulesync.sync_rules(str(pkg1), "v1.0.0", cache_dir, expected_sha256=sha1)
    rulesync.sync_rules(str(pkg2), "v1.1.0", cache_dir, expected_sha256=sha2)

    path = rulesync.activate_version(cache_dir, "v1.0.0")
    meta = _read_metadata(cache_dir, "v1.0.0")
    assert path.exists()
    assert meta.get("active") is True


def test_list_versions_returns_all_cached(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    pkg1, sha1 = _create_rules_pkg(tmp_path, "v1.0.0")
    pkg2, sha2 = _create_rules_pkg(tmp_path, "v1.1.0")

    rulesync.sync_rules(str(pkg1), "v1.0.0", cache_dir, expected_sha256=sha1)
    rulesync.sync_rules(str(pkg2), "v1.1.0", cache_dir, expected_sha256=sha2)

    versions = rulesync.list_versions(cache_dir)
    assert set(versions) >= {"v1.0.0", "v1.1.0"}


def test_metadata_fields_after_sync(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    pkg_path, sha256 = _create_rules_pkg(tmp_path, "v1.0.0")

    rulesync.sync_rules(
        source=str(pkg_path),
        version="v1.0.0",
        cache_dir=cache_dir,
        expected_sha256=sha256,
        gpg_key="dummy-key",
    )

    meta = _read_metadata(cache_dir, "v1.0.0")
    assert meta["version"] == "v1.0.0"
    assert meta["source"] == str(pkg_path)
    assert meta["sha256"] == sha256
    assert meta["gpg"] == "dummy-key"
    # installed_at 可解析为 ISO 时间
    datetime.fromisoformat(meta["installed_at"])
    assert meta.get("active") is True


def test_cli_rulesync_success(tmp_path: Path, monkeypatch):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    pkg_path, sha256 = _create_rules_pkg(tmp_path, "v1.0.0")

    args = [
        "rulesync",
        str(pkg_path),
        "v1.0.0",
        "--sha256",
        sha256,
        "--cache-dir",
        str(cache_dir),
    ]

    # 捕获退出码
    exit_code = cli.main(args)
    assert exit_code == 0
    meta = _read_metadata(cache_dir, "v1.0.0")
    assert meta["sha256"] == sha256


def test_cli_rulesync_checksum_fail_exit_code(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    pkg_path, sha256 = _create_rules_pkg(tmp_path, "v1.0.0")

    args = [
        "rulesync",
        str(pkg_path),
        "v1.0.0",
        "--sha256",
        "bad",
        "--cache-dir",
        str(cache_dir),
    ]

    exit_code = cli.main(args)
    assert exit_code == 2
    assert not (cache_dir / "v1.0.0").exists()


def test_cli_rulesync_retries_then_success(monkeypatch, tmp_path: Path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    pkg_path, sha256 = _create_rules_pkg(tmp_path, "v1.0.0")

    calls = {"n": 0}

    real_sync = rulesync.sync_rules

    def flaky_sync(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise rulesync.RulesyncError("transient")
        return real_sync(*args, **kwargs)

    monkeypatch.setattr(rulesync, "sync_rules", flaky_sync)

    args = [
        "rulesync",
        str(pkg_path),
        "v1.0.0",
        "--sha256",
        sha256,
        "--cache-dir",
        str(cache_dir),
        "--retries",
        "1",
    ]

    exit_code = cli.main(args)
    assert exit_code == 0
    assert calls["n"] == 2


def test_cli_rollback_to_previous(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    pkg1, sha1 = _create_rules_pkg(tmp_path, "v1.0.0")
    pkg2, sha2 = _create_rules_pkg(tmp_path, "v1.1.0")

    cli.main(["rulesync", str(pkg1), "v1.0.0", "--sha256", sha1, "--cache-dir", str(cache_dir)])
    cli.main(["rulesync", str(pkg2), "v1.1.0", "--sha256", sha2, "--cache-dir", str(cache_dir)])

    exit_code = cli.main(
        ["rulesync", str(pkg2), "v1.1.0", "--cache-dir", str(cache_dir), "--rollback-to", "v1.0.0"]
    )
    assert exit_code == 0
    meta = _read_metadata(cache_dir, "v1.0.0")
    assert meta.get("active") is True


def test_cleanup_keeps_latest_versions(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    pkg1, sha1 = _create_rules_pkg(tmp_path, "v1.0.0")
    pkg2, sha2 = _create_rules_pkg(tmp_path, "v1.1.0")
    pkg3, sha3 = _create_rules_pkg(tmp_path, "v1.2.0")

    cli.main(["rulesync", str(pkg1), "v1.0.0", "--sha256", sha1, "--cache-dir", str(cache_dir)])
    cli.main(["rulesync", str(pkg2), "v1.1.0", "--sha256", sha2, "--cache-dir", str(cache_dir)])
    cli.main(
        [
            "rulesync",
            str(pkg3),
            "v1.2.0",
            "--sha256",
            sha3,
            "--cache-dir",
            str(cache_dir),
            "--cleanup-keep",
            "2",
        ]
    )

    versions = set(rulesync.list_versions(cache_dir))
    assert versions == {"v1.1.0", "v1.2.0"}
