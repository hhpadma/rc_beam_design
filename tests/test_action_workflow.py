import pytest

from beam_design.beam_loads import BeamLineActionBuilder
from beam_design.codes.aci318.actions import (
    ACICoefficientBeamActionBuilder,
    ACIMomentCoefficient,
    ACIShearCoefficient,
)
from beam_design.codes.aci318.load_combinations import ACILoadCombinations, ActionPattern
from beam_design.core.actions import ActionType
from beam_design.section_calculations import SectionSelfWeightCalculator
from beam_design.section_assembler import SectionAssembler
from tests.sp17_examples import SP17_BEAM_EXAMPLE_1


def test_section_self_weight_is_calculated_from_section_instance_area():
    example = SP17_BEAM_EXAMPLE_1
    assembly = example.rectangular_beam_assembly()
    calculator = SectionSelfWeightCalculator(unit_weight_pcf=150.0)

    assert assembly.section.area == example.beam_width_in * example.selected_beam_depth_in
    assert pytest.approx(calculator.line_load_klf(assembly)) == example.beam_self_weight_klf


def test_self_weight_calculation_attaches_to_section_assembly_immutably():
    example = SP17_BEAM_EXAMPLE_1
    assembly = example.rectangular_beam_assembly()
    updated = SectionSelfWeightCalculator(unit_weight_pcf=150.0).apply(assembly)

    assert "self_weight_klf" not in assembly.calculations
    assert pytest.approx(updated.calculations["self_weight_klf"]) == example.beam_self_weight_klf


def test_sp17_line_load_actions_include_section_instance_self_weight():
    example = SP17_BEAM_EXAMPLE_1
    actions = example.line_load_actions()

    assert actions.action_type == ActionType.LINE_LOAD
    assert pytest.approx(actions.by_source()["D"]) == example.total_dead_load_klf
    assert pytest.approx(actions.by_source()["L"]) == example.live_load_klf


def test_line_action_builder_uses_default_section_for_initial_design_self_weight():
    example = SP17_BEAM_EXAMPLE_1
    default_section = example.rectangular_beam_assembly()
    builder = BeamLineActionBuilder(
        default_section=default_section,
        self_weight=SectionSelfWeightCalculator(unit_weight_pcf=example.normalweight_concrete_unit_weight_pcf),
        label="initial design loads",
    )

    actions = builder.line_actions()

    assert pytest.approx(actions.by_source()["D"]) == example.beam_self_weight_klf


def test_line_action_builder_uses_explicit_section_for_review_self_weight():
    example = SP17_BEAM_EXAMPLE_1
    default_section = SectionAssembler.rectangular_assembly(width=12.0, depth=24.0, clear_cover=1.5)
    review_section = example.rectangular_beam_assembly()
    builder = BeamLineActionBuilder(
        default_section=default_section,
        self_weight=SectionSelfWeightCalculator(unit_weight_pcf=example.normalweight_concrete_unit_weight_pcf),
    )

    actions = builder.line_actions(section=review_section)

    assert pytest.approx(actions.by_source()["D"]) == example.beam_self_weight_klf


def test_aci_coefficient_method_converts_line_actions_to_moment_actions_before_combination():
    example = SP17_BEAM_EXAMPLE_1
    line_actions = example.line_load_actions()
    moment_actions = ACICoefficientBeamActionBuilder(span_ft=example.clear_span_in / 12.0).moment_actions(
        line_actions,
        ACIMomentCoefficient(divisor=10.0, label="test positive moment"),
    )
    envelope = ACILoadCombinations().action_envelope(
        ActionPattern.from_action_set(moment_actions),
        include_lateral=False,
    )

    assert moment_actions.action_type == ActionType.MOMENT
    assert envelope.governing.equation == "5.3.1b"


def test_aci_coefficient_method_converts_line_actions_to_shear_actions_before_combination():
    example = SP17_BEAM_EXAMPLE_1
    line_actions = example.line_load_actions()
    shear_actions = ACICoefficientBeamActionBuilder(span_ft=example.clear_span_in / 12.0).shear_actions(
        line_actions,
        ACIShearCoefficient(factor=0.5, label="test end shear"),
    )
    envelope = ACILoadCombinations().action_envelope(
        ActionPattern.from_action_set(shear_actions),
        include_lateral=False,
    )

    assert shear_actions.action_type == ActionType.SHEAR
    assert envelope.governing.equation == "5.3.1b"
