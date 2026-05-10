import pytest

from beam_design.codes.aci318 import ACI318
from beam_design.codes.aci318.detailing import (
    ACILongitudinalBarClearSpacingCheck,
    ACITBeamFlangeTensionDistributionCheck,
    ACIFlexuralReinforcementDistributionCheck,
    clear_cover_to_tension_face,
    combined_layer_center_spacing,
    flange_primary_tension_band,
    flange_tension_distribution_requirement,
    max_deformed_bar_spacing_for_crack_control,
    longitudinal_layer_fit,
    longitudinal_layer_required_width,
    minimum_longitudinal_clear_spacing,
    permitted_service_steel_stress,
)
from beam_design.core.model import BeamDesignContext, ReinforcementLayout
from beam_design.core.reinforcement import LongitudinalFace, LongitudinalLayerSpec
from beam_design.core.result import CheckStatus
from beam_design.mat_concrete import Concrete
from beam_design.mat_steel import Steel
from beam_design.rebar import BarTag
from beam_design.reinforcement_assembler import ReinforcementAssembler
from beam_design.section_assembler import SectionAssembler


def test_crack_control_spacing_limit_uses_deformed_bar_row_of_table_24_3_2():
    limit = max_deformed_bar_spacing_for_crack_control(
        service_steel_stress_psi=40_000.0,
        clear_cover_to_tension_face_in=2.0,
    )

    assert pytest.approx(limit.limit_by_cover_in) == 10.0
    assert pytest.approx(limit.limit_by_stress_in) == 12.0
    assert pytest.approx(limit.limit_in) == 10.0


def test_service_steel_stress_can_default_to_two_thirds_fy():
    assert permitted_service_steel_stress(60_000.0) == 40_000.0


def test_t_beam_flange_tension_distribution_requirement_uses_ln_over_10_limit():
    requirement = flange_tension_distribution_requirement(
        effective_flange_width_in=120.0,
        clear_span_in=34.0 * 12.0,
    )

    assert pytest.approx(requirement.max_width_for_primary_tension_reinforcement_in) == 40.8
    assert requirement.outer_flange_reinforcement_required
    assert pytest.approx(requirement.outer_flange_width_requiring_distribution_in) == 79.2


def test_t_beam_primary_tension_band_explains_sp17_11_in_offset():
    band = flange_primary_tension_band(
        effective_flange_width_in=120.0,
        clear_span_in=34.0 * 12.0,
        web_width_in=18.0,
    )

    assert pytest.approx(band.band_width_in) == 40.8
    assert pytest.approx(band.overhang_each_side_of_web_in) == 11.4


def test_sp17_bottom_web_width_demonstration_for_five_no7_bars():
    min_spacing = minimum_longitudinal_clear_spacing(0.875, clear_spacing_floor_in=1.0)
    required_width = longitudinal_layer_required_width(
        bar_count=5,
        bar_diameter_in=0.875,
        minimum_clear_spacing_in=min_spacing,
        clear_cover_in=1.5,
        transverse_bar_diameter_in=0.375,
        side_bar_center_offset_inside_transverse_in=0.75,
    )
    fit = longitudinal_layer_fit(
        web_width_in=18.0,
        bar_count=5,
        bar_diameter_in=0.875,
        minimum_clear_spacing_in=min_spacing,
        clear_cover_in=1.5,
        transverse_bar_diameter_in=0.375,
        side_bar_center_offset_inside_transverse_in=0.75,
    )

    assert pytest.approx(required_width) == 12.75
    assert fit.fits
    assert pytest.approx(fit.clear_spacing_in, abs=0.1) == 2.3


def test_flexural_distribution_check_uses_closest_tension_face_layer():
    section = SectionAssembler.rectangular(width=18.0, depth=30.0, cover=1.5)
    assembler = ReinforcementAssembler(section=section, stirrup_bar=BarTag.B10)
    cage = assembler.cage(
        longitudinal_specs=(
            LongitudinalLayerSpec(LongitudinalFace.BOTTOM, BarTag.B25, 4),
            LongitudinalLayerSpec(LongitudinalFace.BOTTOM, BarTag.B20, 2),
        )
    )
    context = BeamDesignContext(
        section=section,
        concrete=Concrete(fc=5000.0),
        steel=Steel(fy=60_000.0),
        reinforcement=ReinforcementLayout(cage=cage),
        metadata={"aci_tension_face": LongitudinalFace.BOTTOM},
    )

    check = ACIFlexuralReinforcementDistributionCheck().check(context)

    assert check.status == CheckStatus.PASS
    assert pytest.approx(check.data["service_steel_stress_psi"]) == 40_000.0
    assert pytest.approx(check.data["cc_in"], rel=1e-3) == 1.5 + 0.39370079
    assert pytest.approx(check.demand, rel=1e-3) == cage.bottom_layers[0].clear_spacing + cage.bottom_layers[0].bar_diameter
    assert check.demand < check.capacity


def test_flexural_distribution_check_fails_when_bar_spacing_exceeds_crack_control_limit():
    section = SectionAssembler.rectangular(width=48.0, depth=30.0, cover=1.5)
    assembler = ReinforcementAssembler(section=section, stirrup_bar=BarTag.B10)
    cage = assembler.cage(
        longitudinal_specs=(LongitudinalLayerSpec(LongitudinalFace.BOTTOM, BarTag.B25, 2),)
    )
    context = BeamDesignContext(
        section=section,
        concrete=Concrete(fc=5000.0),
        steel=Steel(fy=60_000.0),
        reinforcement=ReinforcementLayout(cage=cage),
        metadata={"aci_tension_face": "bottom"},
    )

    check = ACIFlexuralReinforcementDistributionCheck().check(context)

    assert check.status == CheckStatus.FAIL
    assert check.demand > check.capacity


def test_flexural_distribution_check_combines_same_elevation_detailing_groups():
    section = SectionAssembler.t_beam(
        web_width=18.0,
        total_depth=30.0,
        flange_width=120.0,
        flange_thickness=7.0,
        cover=1.5,
    )
    assembler = ReinforcementAssembler(section=section, stirrup_bar=BarTag.B10)
    distance = 1.5 + 0.375 + 0.875 / 2
    web_bars = assembler.explicit_longitudinal_layer(
        face=LongitudinalFace.TOP,
        bar_tag=BarTag.B25,
        x_positions=(55.0, 57.5, 60.0, 62.5, 65.0),
        distance_from_face=distance,
        placement_label="web main top bars",
    )
    outside_web_bars = assembler.explicit_longitudinal_layer(
        face=LongitudinalFace.TOP,
        bar_tag=BarTag.B25,
        x_positions=(44.0, 76.0),
        distance_from_face=distance,
        placement_label="outside web main top bars",
    )
    cage = assembler.cage(explicit_longitudinal_layers=(web_bars, outside_web_bars))
    context = BeamDesignContext(
        section=section,
        concrete=Concrete(fc=5000.0),
        steel=Steel(fy=60_000.0),
        reinforcement=ReinforcementLayout(cage=cage),
        metadata={"aci_tension_face": "top", "aci_service_steel_stress_psi": 40_000.0},
    )

    check = ACIFlexuralReinforcementDistributionCheck().check(context)

    assert pytest.approx(combined_layer_center_spacing((web_bars, outside_web_bars))) == 11.0
    assert check.status == CheckStatus.FAIL
    assert pytest.approx(check.demand) == 11.0
    assert check.data["placement_labels"] == ("web main top bars", "outside web main top bars")


def test_flexural_distribution_check_is_not_applicable_without_explicit_tension_face():
    section = SectionAssembler.rectangular(width=18.0, depth=30.0, cover=1.5)
    assembler = ReinforcementAssembler(section=section, stirrup_bar=BarTag.B10)
    cage = assembler.cage(
        longitudinal_specs=(LongitudinalLayerSpec(LongitudinalFace.BOTTOM, BarTag.B25, 4),)
    )
    context = BeamDesignContext(
        section=section,
        concrete=Concrete(fc=5000.0),
        steel=Steel(fy=60_000.0),
        reinforcement=ReinforcementLayout(cage=cage),
    )

    check = ACIFlexuralReinforcementDistributionCheck().check(context)

    assert check.status == CheckStatus.NOT_APPLICABLE


def test_t_beam_flange_tension_distribution_check_warns_until_outer_reinforcement_is_marked_provided():
    section = SectionAssembler.t_beam(
        web_width=18,
        total_depth=30,
        flange_width=120,
        flange_thickness=7,
        cover=1.5,
    )
    context = BeamDesignContext(
        section=section,
        concrete=Concrete(fc=5000.0),
        steel=Steel(fy=60_000.0),
        metadata={"aci_tension_face": "top", "aci_clear_span_in": 34.0 * 12.0},
    )
    provided_context = BeamDesignContext(
        section=section,
        concrete=Concrete(fc=5000.0),
        steel=Steel(fy=60_000.0),
        metadata={
            "aci_tension_face": "top",
            "aci_clear_span_in": 34.0 * 12.0,
            "aci_outer_flange_distribution_reinforcement_provided": True,
        },
    )

    warning = ACITBeamFlangeTensionDistributionCheck().check(context)
    passed = ACITBeamFlangeTensionDistributionCheck().check(provided_context)

    assert warning.status == CheckStatus.WARNING
    assert pytest.approx(warning.capacity) == 40.8
    assert warning.data["outer_flange_reinforcement_required"]
    assert passed.status == CheckStatus.PASS


def test_clear_cover_to_tension_face_works_for_top_and_bottom_layers():
    section = SectionAssembler.rectangular(width=18.0, depth=30.0, cover=1.5)
    assembler = ReinforcementAssembler(section=section, stirrup_bar=BarTag.B10)
    cage = assembler.cage(
        longitudinal_specs=(
            LongitudinalLayerSpec(LongitudinalFace.TOP, BarTag.B20, 3),
            LongitudinalLayerSpec(LongitudinalFace.BOTTOM, BarTag.B25, 4),
        )
    )

    assert pytest.approx(clear_cover_to_tension_face(30.0, cage.top_layers[0], LongitudinalFace.TOP)) == 1.5 + 0.39370079
    assert pytest.approx(clear_cover_to_tension_face(30.0, cage.bottom_layers[0], LongitudinalFace.BOTTOM)) == 1.5 + 0.39370079


def test_longitudinal_bar_clear_spacing_check_covers_explicit_layers():
    section = SectionAssembler.rectangular(width=18.0, depth=30.0, cover=1.5)
    assembler = ReinforcementAssembler(section=section, stirrup_bar=BarTag.B10)
    layer = assembler.explicit_longitudinal_layer(
        face=LongitudinalFace.BOTTOM,
        bar_tag=BarTag.B25,
        x_positions=(8.0, 9.0, 10.0),
        placement_label="tight explicit layer",
    )
    cage = assembler.cage(explicit_longitudinal_layers=(layer,))
    context = BeamDesignContext(
        section=section,
        concrete=Concrete(fc=5000.0),
        steel=Steel(fy=60_000.0),
        reinforcement=ReinforcementLayout(cage=cage),
    )

    check = ACILongitudinalBarClearSpacingCheck().check(context)

    assert check.status == CheckStatus.FAIL
    assert check.data["failing_layers"][0]["placement_label"] == "tight explicit layer"


def test_aci_detailing_rules_include_flexural_distribution_check():
    assert any(isinstance(rule, ACIFlexuralReinforcementDistributionCheck) for rule in ACI318().detailing_rules())
    assert any(isinstance(rule, ACITBeamFlangeTensionDistributionCheck) for rule in ACI318().detailing_rules())
    assert any(isinstance(rule, ACILongitudinalBarClearSpacingCheck) for rule in ACI318().detailing_rules())
