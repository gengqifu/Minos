import pytest

from minos import mapping


@pytest.mark.skip(reason="mapping logic not implemented yet")
def test_single_region_mapping():
    regions = ["EU"]
    regs, sources = mapping.merge_mapping(regions, manual_add=None, manual_remove=None)
    assert set(regs) == {"GDPR"}
    assert sources["GDPR"] == "region"


@pytest.mark.skip(reason="mapping logic not implemented yet")
def test_multi_region_union():
    regions = ["EU", "US-CA"]
    regs, sources = mapping.merge_mapping(regions, manual_add=None, manual_remove=None)
    assert set(regs) == {"GDPR", "CCPA/CPRA"}
    assert sources["GDPR"] == "region"
    assert sources["CCPA/CPRA"] == "region"


@pytest.mark.skip(reason="mapping logic not implemented yet")
def test_manual_add_and_remove():
    regions = ["EU"]
    regs, sources = mapping.merge_mapping(regions, manual_add=["LGPD"], manual_remove=["GDPR"])
    assert set(regs) == {"LGPD"}
    assert sources["LGPD"] == "manual"


@pytest.mark.skip(reason="mapping logic not implemented yet")
def test_invalid_region_raises():
    with pytest.raises(Exception):
        mapping.merge_mapping(["INVALID"], manual_add=None, manual_remove=None)
