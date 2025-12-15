import pytest
import json

from minos import mapping


def test_single_region_mapping():
    regions = ["EU"]
    regs, sources = mapping.merge_mapping(regions, manual_add=None, manual_remove=None)
    assert set(regs) == {"GDPR"}
    assert sources["GDPR"] == "region"


def test_multi_region_union():
    regions = ["EU", "US-CA"]
    regs, sources = mapping.merge_mapping(regions, manual_add=None, manual_remove=None)
    assert set(regs) == {"GDPR", "CCPA/CPRA"}
    assert sources["GDPR"] == "region"
    assert sources["CCPA/CPRA"] == "region"


def test_manual_add_and_remove():
    regions = ["EU"]
    regs, sources = mapping.merge_mapping(regions, manual_add=["LGPD"], manual_remove=["GDPR"])
    assert set(regs) == {"LGPD"}
    assert sources["LGPD"] == "manual"


def test_invalid_region_raises():
    with pytest.raises(Exception):
        mapping.merge_mapping(["INVALID"], manual_add=None, manual_remove=None)


def test_build_selection_output():
    data = mapping.build_selection(["EU", "US-CA"], manual_add=["LGPD"], manual_remove=["GDPR"])
    assert set(data["regions"]) == {"EU", "US-CA"}
    assert set(data["regulations"]) == {"CCPA/CPRA", "LGPD"}
    assert data["source_flags"]["CCPA/CPRA"] == "region"
    assert data["source_flags"]["LGPD"] == "manual"


def test_load_config_and_merge(tmp_path):
    cfg = {
        "regions": ["EU"],
        "manual_add": ["LGPD"],
        "manual_remove": ["GDPR"],
    }
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    loaded = mapping.load_config(cfg_path)
    regs, sources = mapping.merge_mapping(
        regions=loaded["regions"],
        manual_add=loaded["manual_add"],
        manual_remove=loaded["manual_remove"],
    )
    assert set(regs) == {"LGPD"}
    assert sources["LGPD"] == "manual"


def test_load_config_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        mapping.load_config(tmp_path / "missing.json")


def test_load_config_invalid_format(tmp_path):
    cfg_path = tmp_path / "bad.json"
    cfg_path.write_text('{"regions": "EU"}', encoding="utf-8")
    with pytest.raises(ValueError):
        mapping.load_config(cfg_path)
