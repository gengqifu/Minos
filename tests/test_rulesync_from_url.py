import json
from pathlib import Path

import pytest

from minos import cli


def _read_metadata(cache_dir: Path, reg: str, version: str = "latest"):
    meta_path = cache_dir / reg / version / "metadata.json"
    return json.loads(meta_path.read_text()) if meta_path.exists() else None


def _mock_convert(monkeypatch, cache_dir: Path):
    def fake_convert(url: str, cache_dir: Path, out_path: Path, regulation: str, version: str):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("[]", encoding="utf-8")
        return out_path

    monkeypatch.setattr("minos.rulesync_convert.convert_url_to_yaml", fake_convert)


def test_rulesync_from_url_default_mapping(tmp_path: Path, monkeypatch):
    cache_dir = tmp_path / "cache"
    _mock_convert(monkeypatch, cache_dir)
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


def test_rulesync_from_url_default_version(tmp_path: Path, monkeypatch):
    cache_dir = tmp_path / "cache"
    _mock_convert(monkeypatch, cache_dir)
    args = [
        "rulesync",
        "--from-url",
        "--regulation",
        "gdpr",
        "--cache-dir",
        str(cache_dir),
    ]
    exit_code = cli.main(args)
    assert exit_code == 0
    meta = _read_metadata(cache_dir, "gdpr", "latest")
    assert meta is not None
    assert meta["version"] == "latest"
    assert meta.get("active") is True


def test_rulesync_from_url_sync_all_when_no_regulation(tmp_path: Path, monkeypatch):
    cache_dir = tmp_path / "cache"
    _mock_convert(monkeypatch, cache_dir)
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


def test_rulesync_from_url_allow_custom_sources(tmp_path: Path, monkeypatch):
    cache_dir = tmp_path / "cache"

    def fake_convert(url: str, cache_dir: Path, out_path: Path, regulation: str, version: str):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("[]", encoding="utf-8")
        return out_path

    monkeypatch.setattr("minos.rulesync_convert.convert_url_to_yaml", fake_convert)

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
