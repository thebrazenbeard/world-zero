import pytest

from worldzero.regions.definitions import RegionDefinition, RegionSet


def test_region_set_is_versioned_and_ordered():
    regions = RegionSet(
        version="WZ-MACRO-2",
        regions=(
            RegionDefinition("north", "North"),
            RegionDefinition("south", "South"),
        ),
    )
    assert regions.ids == ("north", "south")
    assert regions.version == "WZ-MACRO-2"


def test_region_set_rejects_duplicate_ids():
    with pytest.raises(ValueError, match="duplicate"):
        RegionSet(
            version="v1",
            regions=(RegionDefinition("x", "X"), RegionDefinition("x", "Again")),
        )


def test_region_set_rejects_empty_version():
    with pytest.raises(ValueError, match="version"):
        RegionSet(version=" ", regions=(RegionDefinition("x", "X"),))


def test_canonical_macroregion_manifest_is_data_controlled_and_versioned():
    from pathlib import Path

    from worldzero.regions.definitions import RegionSetStatus, load_region_set_manifest

    manifest = load_region_set_manifest(Path("regions/WZ_MACROREGION_V0.yaml"))
    assert manifest.status is RegionSetStatus.FROZEN
    assert manifest.region_set.version == "WZ_MACROREGION_V0"
    assert len(manifest.region_set.ids) == 10
    assert "north_america" in manifest.region_set.ids
    assert "sub_saharan_africa" in manifest.region_set.ids
