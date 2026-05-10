import pytest

from beam_design.codes.aci318.sections import (
    ACIFlangeConfiguration,
    ACIFlangeWidthCheck,
    ACIFlangeWidthInput,
    ACIMinimumBeamDepthCheck,
    ACISupportCondition,
    effective_flange_width,
    minimum_beam_depth,
)
from beam_design.codes.aci318 import ACI318
from beam_design.core.model import BeamDesignContext
from beam_design.core.result import CheckStatus
from beam_design.mat_concrete import Concrete
from beam_design.mat_steel import Steel
from beam_design.section_assembler import SectionAssembler
from tests.sp17_examples import SP17_BEAM_EXAMPLE_1


def _context(section, metadata):
    return BeamDesignContext(
        section=section,
        concrete=Concrete(fc=5000),
        steel=Steel(fy=60000),
        metadata=metadata,
    )


def test_minimum_beam_depth_matches_sp17_example():
    example = SP17_BEAM_EXAMPLE_1

    assert pytest.approx(
        minimum_beam_depth(
            clear_span_in=example.span_in,
            support_condition=ACISupportCondition.ONE_END_CONTINUOUS,
            fy_psi=example.steel_yield_strength_psi,
        ),
        rel=1e-3,
    ) == 23.351


def test_minimum_beam_depth_check_passes_sp17_selected_depth():
    example = SP17_BEAM_EXAMPLE_1
    section = SectionAssembler.rectangular(
        width=example.beam_width_in,
        depth=30,
        cover=1.5,
    )
    result = ACIMinimumBeamDepthCheck().check(
        _context(
            section,
            {
                "aci_span_length_in": example.span_in,
                "aci_support_condition": "one_end_continuous",
            },
        )
    )

    assert result.status == CheckStatus.PASS
    assert pytest.approx(result.demand, rel=1e-3) == 23.351
    assert result.capacity == 30


def test_minimum_beam_depth_check_fails_if_depth_is_too_small():
    example = SP17_BEAM_EXAMPLE_1
    section = SectionAssembler.rectangular(
        width=example.beam_width_in,
        depth=20,
        cover=1.5,
    )
    result = ACIMinimumBeamDepthCheck().check(
        _context(
            section,
            {
                "aci_span_length_in": example.span_in,
                "aci_support_condition": "one_end_continuous",
            },
        )
    )

    assert result.status == CheckStatus.FAIL


def test_effective_flange_width_matches_sp17_example():
    example = SP17_BEAM_EXAMPLE_1
    data = ACIFlangeWidthInput(
        web_width_in=example.beam_width_in,
        slab_thickness_in=example.slab_thickness_in,
        clear_span_in=example.clear_span_in,
        clear_distance_to_next_beam_in=example.clear_distance_to_next_beam_in,
        configuration=ACIFlangeConfiguration.INTERIOR_T,
    )

    assert effective_flange_width(data) == 120


def test_flange_width_check_passes_sp17_t_beam_geometry():
    example = SP17_BEAM_EXAMPLE_1
    section = SectionAssembler.t_beam(
        web_width=example.beam_width_in,
        total_depth=30,
        flange_width=example.aci_example_effective_flange_width_in,
        flange_thickness=example.slab_thickness_in,
        cover=1.5,
    )
    result = ACIFlangeWidthCheck().check(
        _context(
            section,
            {
                "aci_slab_thickness_in": example.slab_thickness_in,
                "aci_clear_span_in": example.clear_span_in,
                "aci_clear_distance_to_next_beam_in": example.clear_distance_to_next_beam_in,
                "aci_flange_configuration": "interior_t",
                "aci_flange_in_compression": True,
            },
        )
    )

    assert result.status == CheckStatus.PASS
    assert result.capacity == 120
    assert result.demand == 120


def test_flange_width_check_fails_when_provided_width_exceeds_aci_limit():
    example = SP17_BEAM_EXAMPLE_1
    section = SectionAssembler.t_beam(
        web_width=example.beam_width_in,
        total_depth=30,
        flange_width=130,
        flange_thickness=example.slab_thickness_in,
        cover=1.5,
    )
    result = ACIFlangeWidthCheck().check(
        _context(
            section,
            {
                "aci_slab_thickness_in": example.slab_thickness_in,
                "aci_clear_span_in": example.clear_span_in,
                "aci_clear_distance_to_next_beam_in": example.clear_distance_to_next_beam_in,
                "aci_flange_configuration": "interior_t",
                "aci_flange_in_compression": True,
            },
        )
    )

    assert result.status == CheckStatus.FAIL
    assert result.demand == 130
    assert result.capacity == 120


def test_flange_width_is_not_applicable_when_flange_is_in_tension_zone():
    example = SP17_BEAM_EXAMPLE_1
    section = SectionAssembler.t_beam(
        web_width=example.beam_width_in,
        total_depth=30,
        flange_width=example.aci_example_effective_flange_width_in,
        flange_thickness=example.slab_thickness_in,
        cover=1.5,
    )
    result = ACIFlangeWidthCheck().check(
        _context(
            section,
            {
                "aci_slab_thickness_in": example.slab_thickness_in,
                "aci_clear_span_in": example.clear_span_in,
                "aci_clear_distance_to_next_beam_in": example.clear_distance_to_next_beam_in,
                "aci_flange_configuration": "interior_t",
                "aci_flange_in_compression": False,
            },
        )
    )

    assert result.status == CheckStatus.NOT_APPLICABLE
    assert "tension zone" in result.message


def test_aci_geometry_rules_run_against_sp17_example():
    example = SP17_BEAM_EXAMPLE_1
    section = SectionAssembler.t_beam(
        web_width=example.beam_width_in,
        total_depth=30,
        flange_width=example.aci_example_effective_flange_width_in,
        flange_thickness=example.slab_thickness_in,
        cover=1.5,
    )
    context = _context(
        section,
        {
            "aci_span_length_in": example.span_in,
            "aci_support_condition": "one_end_continuous",
            "aci_slab_thickness_in": example.slab_thickness_in,
            "aci_clear_span_in": example.clear_span_in,
            "aci_clear_distance_to_next_beam_in": example.clear_distance_to_next_beam_in,
            "aci_flange_configuration": "interior_t",
            "aci_flange_in_compression": True,
            "aci_minimum_depth_satisfied": True,
            "aci_flange_and_web_monolithic": True,
        },
    )
    results = [rule.check(context) for rule in ACI318().geometry_rules()]

    assert [result.status for result in results] == [
        CheckStatus.PASS,
        CheckStatus.NOT_APPLICABLE,
        CheckStatus.PASS,
        CheckStatus.PASS,
        CheckStatus.NOT_APPLICABLE,
        CheckStatus.NOT_APPLICABLE,
    ]
