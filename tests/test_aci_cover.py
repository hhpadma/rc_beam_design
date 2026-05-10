import pytest

from beam_design.codes.aci318.detailing import (
    ACICoverMemberType,
    ACICoverReinforcementType,
    ACIConcreteCoverExposure,
    ACIMinimumCoverCheck,
    COVER_TABLE_20_6_1_3_1,
    specified_concrete_cover,
)
from beam_design.core.model import BeamDesignContext
from beam_design.core.result import CheckStatus
from beam_design.mat_concrete import Concrete
from beam_design.mat_steel import Steel
from beam_design.section_assembler import SectionAssembler


def _context(cover, metadata=None):
    return BeamDesignContext(
        section=SectionAssembler.rectangular(width=18.0, depth=30.0, cover=cover),
        concrete=Concrete(fc=5000),
        steel=Steel(fy=60000),
        metadata={} if metadata is None else metadata,
    )


def test_cover_table_20_6_1_3_1_rows_are_stored():
    assert len(COVER_TABLE_20_6_1_3_1) == 6
    assert specified_concrete_cover("cast_against_ground", "all", "all") == 3.0
    assert specified_concrete_cover("weather_or_ground", "all", "bar_no_6_to_18") == 2.0
    assert specified_concrete_cover("weather_or_ground", "all", "bar_no_5_w31_d31_and_smaller") == 1.5
    assert specified_concrete_cover("not_exposed", "slab_joist_wall", "bar_no_14_to_18") == 1.5
    assert specified_concrete_cover("not_exposed", "slab_joist_wall", "bar_no_11_and_smaller") == 0.75
    assert (
        specified_concrete_cover(
            "not_exposed",
            "beam_column_pedestal_tension_tie",
            "primary_reinforcement_ties_stirrups_spirals_hoops",
        )
        == 1.5
    )


def test_cover_table_is_immutable():
    with pytest.raises(TypeError):
        COVER_TABLE_20_6_1_3_1[
            (
                ACIConcreteCoverExposure.NOT_EXPOSED,
                ACICoverMemberType.BEAM_COLUMN_PEDESTAL_TENSION_TIE,
                ACICoverReinforcementType.PRIMARY_REINFORCEMENT_TIES_STIRRUPS_SPIRALS_HOOPS,
            )
        ] = 2.0


def test_minimum_cover_check_defaults_to_non_exposed_cast_in_place_beam():
    result = ACIMinimumCoverCheck().check(_context(cover=1.5))

    assert result.status == CheckStatus.PASS
    assert result.demand == 1.5
    assert result.capacity == 1.5


def test_minimum_cover_check_fails_for_cast_against_ground_with_only_beam_cover():
    result = ACIMinimumCoverCheck().check(
        _context(
            cover=1.5,
            metadata={
                "aci_cover_exposure": "cast_against_ground",
                "aci_cover_member_type": "all",
                "aci_cover_reinforcement_type": "all",
            },
        )
    )

    assert result.status == CheckStatus.FAIL
    assert result.demand == 3.0


def test_minimum_cover_check_passes_weather_exposure_for_smaller_bars():
    result = ACIMinimumCoverCheck().check(
        _context(
            cover=1.5,
            metadata={
                "aci_cover_exposure": "weather_or_ground",
                "aci_cover_member_type": "all",
                "aci_cover_reinforcement_type": "bar_no_5_w31_d31_and_smaller",
            },
        )
    )

    assert result.status == CheckStatus.PASS
    assert result.data["exposure"] == "weather_or_ground"
