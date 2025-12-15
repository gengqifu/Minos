import pytest

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
