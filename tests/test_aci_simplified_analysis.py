import pytest

from beam_design.codes.aci318.analysis import (
    ACIBeamLoadApplicationLocation,
    ACIApproximateMomentCase,
    ACIApproximateShearCase,
    ACIShearCriticalPlane,
    ACISimplifiedAnalysisInput,
    ACISimplifiedBeamAnalysis,
)
from beam_design.core.analysis import CriticalLocationRole
from beam_design.core.actions import ActionType
from beam_design.section_designer import SectionDesignInput
from tests.sp17_examples import SP17_BEAM_EXAMPLE_1


def _sp17_analysis_input():
    example = SP17_BEAM_EXAMPLE_1
    return ACISimplifiedAnalysisInput(
        line_actions=example.line_load_actions(),
        clear_spans_ft=(example.clear_span_in / 12.0,) * 6,
        current_span_index=1,
        prismatic=True,
        uniformly_distributed=True,
        supports_integral=True,
    )


def test_aci_simplified_analysis_is_applicable_to_sp17_example():
    data = _sp17_analysis_input()
    messages = ACISimplifiedBeamAnalysis().validate(data)

    assert messages == ()


def test_aci_simplified_analysis_rejects_nonuniform_loads():
    data = ACISimplifiedAnalysisInput(
        line_actions=SP17_BEAM_EXAMPLE_1.line_load_actions(),
        clear_spans_ft=(34.0, 34.0, 34.0),
        uniformly_distributed=False,
    )

    assert "Loads are not uniformly distributed." in ACISimplifiedBeamAnalysis().validate(data)


def test_aci_simplified_analysis_rejects_large_adjacent_span_difference():
    data = ACISimplifiedAnalysisInput(
        line_actions=SP17_BEAM_EXAMPLE_1.line_load_actions(),
        clear_spans_ft=(30.0, 40.0, 30.0),
    )

    assert "Longer adjacent span exceeds the shorter span by more than 20 percent." in ACISimplifiedBeamAnalysis().validate(data)


def test_aci_simplified_analysis_returns_independent_analysis_result():
    example = SP17_BEAM_EXAMPLE_1
    result = ACISimplifiedBeamAnalysis().analyze(_sp17_analysis_input())

    assert result.applicable
    assert pytest.approx(result.factored_line_load_klf) == example.factored_dead_live_load_klf
    assert result.moment_actions.action_type == ActionType.MOMENT
    assert result.shear_actions.action_type == ActionType.SHEAR
    assert result.critical_sections


def test_aci_simplified_analysis_generates_sp17_default_moment_actions():
    example = SP17_BEAM_EXAMPLE_1
    result = ACISimplifiedBeamAnalysis().analyze(
        _sp17_analysis_input(),
    )
    actions = {component.label: component.value for component in result.moment_actions.components}
    span_ft = example.clear_span_in / 12.0
    wu = example.factored_dead_live_load_klf

    assert pytest.approx(actions["positive interior span"]) == wu * span_ft**2 / 16.0
    assert pytest.approx(actions["negative exterior support, column"]) == -wu * span_ft**2 / 16.0
    assert pytest.approx(actions["negative first interior support, more than two spans"]) == -wu * span_ft**2 / 10.0
    assert pytest.approx(actions["negative face of other supports"]) == -wu * span_ft**2 / 11.0


def test_aci_simplified_analysis_generates_sp17_default_shear_actions():
    example = SP17_BEAM_EXAMPLE_1
    result = ACISimplifiedBeamAnalysis().analyze(
        _sp17_analysis_input(),
    )
    actions = {component.label: component.value for component in result.shear_actions.components}
    span_ft = example.clear_span_in / 12.0
    wu = example.factored_dead_live_load_klf

    assert pytest.approx(actions["exterior face of first interior support"]) == 1.15 * wu * span_ft / 2.0
    assert pytest.approx(actions["face of all other supports"]) == wu * span_ft / 2.0


def test_aci_simplified_analysis_can_generate_specific_table_case_only():
    example = SP17_BEAM_EXAMPLE_1
    result = ACISimplifiedBeamAnalysis().analyze(
        _sp17_analysis_input(),
        moment_cases=(ACIApproximateMomentCase.POSITIVE_INTERIOR_SPAN,),
        shear_cases=(ACIApproximateShearCase.FACE_ALL_OTHER_SUPPORTS,),
    )

    assert len(result.moment_actions.components) == 1
    assert result.moment_actions.components[0].label == "positive interior span"
    assert len(result.shear_actions.components) == 1
    assert result.shear_actions.components[0].label == "face of all other supports"


def test_analysis_critical_section_becomes_section_design_input():
    result = ACISimplifiedBeamAnalysis().analyze(_sp17_analysis_input())
    design_input = SectionDesignInput.from_critical_section(result.critical_sections[0])

    assert design_input.moment == result.critical_sections[0].moment
    assert design_input.shear == result.critical_sections[0].shear
    assert design_input.torsion is None


def test_aci_simplified_analysis_stores_span_action_table():
    result = ACISimplifiedBeamAnalysis().analyze(_sp17_analysis_input())
    table = result.action_table

    assert table is not None
    assert len(table.records) == 6 * 5
    assert len(table.by_action_type(ActionType.MOMENT)) == 6 * 3
    assert len(table.by_action_type(ActionType.SHEAR)) == 6 * 2
    assert table.by_span(0)[0].role == CriticalLocationRole.LEFT_SUPPORT


def test_span_action_table_links_adjacent_support_faces_for_constructibility():
    example = SP17_BEAM_EXAMPLE_1
    result = ACISimplifiedBeamAnalysis().analyze(_sp17_analysis_input())
    table = result.action_table
    group = table.design_groups(ActionType.MOMENT)["support-1-negative-flexure"]
    governing = table.governing_by_group(ActionType.MOMENT)["support-1-negative-flexure"]
    span_ft = example.clear_span_in / 12.0
    wu = example.factored_dead_live_load_klf

    assert {record.id for record in group} == {"S1-right_support-M", "S2-left_support-M"}
    assert pytest.approx(abs(governing.value)) == wu * span_ft**2 / 10.0


def test_span_action_table_stores_shear_separately_from_flexure_locations():
    example = SP17_BEAM_EXAMPLE_1
    result = ACISimplifiedBeamAnalysis().analyze(_sp17_analysis_input())
    table = result.action_table
    support_group = table.design_groups(ActionType.SHEAR)["support-1-shear"]
    governing = table.governing_by_group(ActionType.SHEAR)["support-1-shear"]
    span_ft = example.clear_span_in / 12.0
    wu = example.factored_dead_live_load_klf

    assert {record.id for record in support_group} == {"S1-right_shear-V", "S2-left_shear-V"}
    assert pytest.approx(governing.magnitude) == 1.15 * wu * span_ft / 2.0
    assert all(record.role in (CriticalLocationRole.RIGHT_SHEAR, CriticalLocationRole.LEFT_SHEAR) for record in support_group)


def test_simplified_analysis_defaults_to_conservative_shear_at_face_without_near_support_load_data():
    result = ACISimplifiedBeamAnalysis().analyze(_sp17_analysis_input())
    shear = next(record for record in result.action_table.records if record.id == "S1-left_shear-V")

    assert shear.local_position_ft == 0.0
    assert "face of support" in shear.label


def test_simplified_analysis_can_store_shear_at_d_when_aci_conditions_are_explicitly_satisfied():
    example = SP17_BEAM_EXAMPLE_1
    effective_depth_ft = 27.5 / 12.0
    data = ACISimplifiedAnalysisInput(
        line_actions=example.line_load_actions(),
        clear_spans_ft=(example.clear_span_in / 12.0,) * 6,
        supports_integral=True,
        load_application_location=ACIBeamLoadApplicationLocation.TOP,
        concentrated_load_between_face_and_d=False,
        effective_depth_ft=effective_depth_ft,
    )

    result = ACISimplifiedBeamAnalysis().analyze(data)
    shear = next(record for record in result.action_table.records if record.id == "S1-left_shear-V")

    assert pytest.approx(shear.local_position_ft) == effective_depth_ft
    assert pytest.approx(shear.value) == example.factored_dead_live_load_klf * (example.clear_span_in / 12.0) / 2.0 - (
        example.factored_dead_live_load_klf * effective_depth_ft
    )
    assert "at d from face" in shear.label


def test_simplified_analysis_keeps_face_shear_when_loads_are_not_applied_near_top():
    example = SP17_BEAM_EXAMPLE_1
    data = ACISimplifiedAnalysisInput(
        line_actions=example.line_load_actions(),
        clear_spans_ft=(example.clear_span_in / 12.0,) * 6,
        supports_integral=True,
        load_application_location=ACIBeamLoadApplicationLocation.BOTTOM,
        concentrated_load_between_face_and_d=False,
        effective_depth_ft=27.5 / 12.0,
    )

    result = ACISimplifiedBeamAnalysis().analyze(data)
    shear = next(record for record in result.action_table.records if record.id == "S1-left_shear-V")

    assert shear.local_position_ft == 0.0
    assert "face of support" in shear.label


def test_simplified_analysis_accepts_explicit_shear_critical_plane_override():
    example = SP17_BEAM_EXAMPLE_1
    data = ACISimplifiedAnalysisInput(
        line_actions=example.line_load_actions(),
        clear_spans_ft=(example.clear_span_in / 12.0,) * 6,
        supports_integral=True,
        shear_critical_plane=ACIShearCriticalPlane.FACE_OF_SUPPORT,
        load_application_location=ACIBeamLoadApplicationLocation.TOP,
        concentrated_load_between_face_and_d=False,
        effective_depth_ft=27.5 / 12.0,
    )

    result = ACISimplifiedBeamAnalysis().analyze(data)
    shear = next(record for record in result.action_table.records if record.id == "S1-left_shear-V")

    assert shear.local_position_ft == 0.0
    assert "face of support" in shear.label
