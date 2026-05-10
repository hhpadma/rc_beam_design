import pytest

from beam_design.codes.aci318.analysis import (
    ACIBeamLoadApplicationLocation,
    ACISimplifiedAnalysisInput,
    ACISimplifiedBeamAnalysis,
)
from beam_design.codes.aci318.shear import evaluate_one_way_shear_without_axial
from beam_design.codes.aci318.shear.reinforcement import (
    design_perpendicular_stirrup_spacing,
    rectangular_tie_effective_area,
)
from beam_design.codes.aci318.shear.requirements import ACIShearSectionDimensionLimitCheck
from beam_design.core.actions import ActionType
from beam_design.core.model import BeamDesignContext, FactoredLoad
from beam_design.core.result import CheckStatus
from tests.sp17_examples import SP17_BEAM_EXAMPLE_1


def test_sp17_step_6_shear_design_uses_vu_at_d_and_requires_shear_reinforcement():
    example = SP17_BEAM_EXAMPLE_1
    effective_depth_in = 27.5
    effective_depth_ft = effective_depth_in / 12.0
    analysis_input = ACISimplifiedAnalysisInput(
        line_actions=example.line_load_actions(),
        clear_spans_ft=(example.clear_span_in / 12.0,) * 6,
        supports_integral=True,
        load_application_location=ACIBeamLoadApplicationLocation.TOP,
        concentrated_load_between_face_and_d=False,
        effective_depth_ft=effective_depth_ft,
    )
    result = ACISimplifiedBeamAnalysis().analyze(analysis_input)
    governing_shear = result.action_table.governing_by_group(ActionType.SHEAR)["support-1-shear"]

    shear_design = evaluate_one_way_shear_without_axial(
        factored_shear_lb=governing_shear.magnitude * 1000.0,
        concrete_strength_psi=example.concrete_strength_psi,
        web_width_in=example.beam_width_in,
        effective_depth_in=effective_depth_in,
        lambda_factor=example.lambda_factor,
    )

    assert pytest.approx(governing_shear.magnitude, abs=0.3) == 63.5
    assert "at d from face" in governing_shear.label
    assert pytest.approx(shear_design.concrete_shear.strength_kip, rel=1e-3) == 70.0
    assert pytest.approx(shear_design.concrete_design_strength_kip, rel=1e-3) == 52.5
    assert shear_design.concrete_design_strength_kip < shear_design.factored_shear_kip
    assert shear_design.shear_reinforcement_required
    assert pytest.approx(shear_design.minimum_reinforcement.threshold_kip, rel=1e-3) == 26.25
    assert shear_design.minimum_shear_reinforcement_required


def test_sp17_step_6_checks_section_dimensions_before_shear_reinforcement_design():
    example = SP17_BEAM_EXAMPLE_1
    effective_depth_in = 27.5
    analysis_input = ACISimplifiedAnalysisInput(
        line_actions=example.line_load_actions(),
        clear_spans_ft=(example.clear_span_in / 12.0,) * 6,
        supports_integral=True,
        load_application_location=ACIBeamLoadApplicationLocation.TOP,
        concentrated_load_between_face_and_d=False,
        effective_depth_ft=effective_depth_in / 12.0,
    )
    result = ACISimplifiedBeamAnalysis().analyze(analysis_input)
    governing_shear = result.action_table.governing_by_group(ActionType.SHEAR)["support-1-shear"]
    section = example.rectangular_beam_assembly().section
    context = BeamDesignContext(
        section=section,
        concrete=example.concrete(),
        steel=example.steel(),
        load=FactoredLoad(shear=governing_shear.magnitude * 1000.0),
        metadata={"aci_lambda": example.lambda_factor},
    )

    check = ACIShearSectionDimensionLimitCheck().check(context)

    assert check.status == CheckStatus.PASS
    assert pytest.approx(check.demand / 1000.0, abs=0.3) == 63.5
    assert pytest.approx(check.data["Vc"] / 1000.0, rel=1e-3) == 70.0
    assert pytest.approx(check.capacity / 1000.0, rel=1e-2) == 262.5


def test_sp17_step_6_vertical_stirrup_trial_spacing_and_aci_max_spacing():
    example = SP17_BEAM_EXAMPLE_1
    effective_depth_in = 27.5
    shear_design = evaluate_one_way_shear_without_axial(
        factored_shear_lb=63_500.0,
        concrete_strength_psi=example.concrete_strength_psi,
        web_width_in=example.beam_width_in,
        effective_depth_in=effective_depth_in,
        lambda_factor=example.lambda_factor,
    )
    av = rectangular_tie_effective_area(single_leg_area_in2=0.11, legs=2)

    stirrup_design = design_perpendicular_stirrup_spacing(
        required_shear_reinforcement_strength_lb=shear_design.required_stirrup_shear_strength_lb,
        area_in2=av,
        yield_strength_psi=60_000.0,
        effective_depth_in=effective_depth_in,
        concrete_strength_psi=example.concrete_strength_psi,
        web_width_in=example.beam_width_in,
    )

    assert pytest.approx(shear_design.required_stirrup_shear_strength_kip, abs=0.1) == 14.7
    assert pytest.approx(stirrup_design.calculated_spacing_in, abs=0.1) == 24.8
    assert pytest.approx(stirrup_design.spacing_limit.threshold_kip, abs=0.1) == 140.0
    assert stirrup_design.spacing_limit.limit_expression == "lesser of d/2 and 24 in."
    assert pytest.approx(stirrup_design.spacing_limit.max_spacing_in, abs=0.1) == 13.8
    assert stirrup_design.selected_spacing_satisfies_limit(12.0)
