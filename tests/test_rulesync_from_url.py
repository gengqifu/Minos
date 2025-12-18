import json
from pathlib import Path

import pytest

from minos import cli


def _read_metadata(cache_dir: Path, reg: str, version: str = "latest"):
    meta_path = cache_dir / reg / version / "metadata.json"
    return json.loads(meta_path.read_text()) if meta_path.exists() else None


@pytest.mark.xfail(reason="story-11: rulesync --from-url 单步模式待实现")
def test_rulesync_from_url_default_mapping(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    args = [
        "rulesync",
        "--from-url",
        "--regulation",
        "GDPR",  # 大小写不敏感
        "--version",
        "v1",
        "--cache-dir",
        str(cache_dir),
    ]
    exit_code = cli.main(args)
    assert exit_code == 0
    meta = _read_metadata(cache_dir, "gdpr", "v1")
    assert meta is not None
    assert meta["source"].startswith("https://eur-lex.europa.eu/eli/reg/2016/679/oj")
    assert meta["version"] == "v1"
    assert meta.get("active") is True


@pytest.mark.xfail(reason="story-11: rulesync --from-url 单步模式待实现")
def test_rulesync_from_url_sync_all_when_no_regulation(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    args = [
        "rulesync",
        "--from-url",
        "--version",
        "v1",
        "--cache-dir",
        str(cache_dir),
    ]
    exit_code = cli.main(args)
    assert exit_code == 0
    for reg in ["gdpr", "ccpa", "lgpd", "pipl", "appi"]:
        meta = _read_metadata(cache_dir, reg, "v1")
        assert meta is not None
        assert meta.get("active") is True


@pytest.mark.xfail(reason="story-11: rulesync --from-url 单步模式待实现")
def test_rulesync_from_url_non_whitelist_rejected(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    args = [
        "rulesync",
        "--from-url",
        "https://example.com/rules.tar.gz",
        "--regulation",
        "unknown",
        "--cache-dir",
        str(cache_dir),
    ]
    exit_code = cli.main(args)
    assert exit_code != 0
    assert not (cache_dir / "unknown").exists()


@pytest.mark.xfail(reason="story-11: rulesync --from-url 单步模式待实现")
def test_rulesync_from_url_allow_custom_sources(tmp_path: Path, monkeypatch):
    cache_dir = tmp_path / "cache"
    # 模拟下载逻辑，直接写出一个假的 tar 包路径或绕过下载
    def fake_convert(*args, **kwargs):
        target = cache_dir / "dummy"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("rules: []")
        return target

    monkeypatch.setattr("minos.rulesync_convert.convert_url_to_yaml", fake_convert, raising=False)

    args = [
        "rulesync",
        "--from-url",
        "https://example.com/custom",
        "--regulation",
        "custom",
        "--version",
        "v1",
        "--cache-dir",
        str(cache_dir),
        "--allow-custom-sources",
    ]
    exit_code = cli.main(args)
    assert exit_code == 0
    meta = _read_metadata(cache_dir, "custom", "v1")
    assert meta is not None
    assert meta["source"].startswith("https://example.com/custom")
