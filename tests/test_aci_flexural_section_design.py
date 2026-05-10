import pytest

from beam_design.codes.aci318.analysis import ACISimplifiedAnalysisInput, ACISimplifiedBeamAnalysis
from beam_design.codes.aci318.flexure import (
    ACIBarSelector,
    ACIFlexuralSectionBuilder,
    ACIFlexuralSectionDesigner,
    evaluate_flexural_strain,
    minimum_flexural_reinforcement_area,
    net_tensile_strain,
    required_flexural_reinforcement,
    solve_required_tension_area,
)
from beam_design.codes.aci318.strength_reduction import ACIStrainControlRegion
from beam_design.core.actions import ActionType
from beam_design.core.analysis import CriticalActionRecord, CriticalLocationRole
from beam_design.core.reinforcement import LongitudinalFace
from beam_design.rebar import BarTag, RebarCatalog
from beam_design.section_assembler import SectionAssembler
from tests.sp17_examples import SP17_BEAM_EXAMPLE_1


def _sp17_action_table():
    example = SP17_BEAM_EXAMPLE_1
    data = ACISimplifiedAnalysisInput(
        line_actions=example.line_load_actions(),
        clear_spans_ft=(example.clear_span_in / 12.0,) * 6,
        current_span_index=1,
        prismatic=True,
        uniformly_distributed=True,
        supports_integral=True,
    )
    return ACISimplifiedBeamAnalysis().analyze(data).action_table


def _sp17_t_beam_assembly():
    example = SP17_BEAM_EXAMPLE_1
    return SectionAssembler.t_beam_assembly(
        web_width=example.beam_width_in,
        total_depth=example.selected_beam_depth_in,
        flange_width=example.aci_example_effective_flange_width_in,
        flange_thickness=example.slab_thickness_in,
        clear_cover=1.5,
    )


def test_required_flexural_reinforcement_solves_strength_equation():
    required = required_flexural_reinforcement(
        moment_ft_kip=428.0,
        phi=0.90,
        concrete_strength_psi=5000.0,
        steel_yield_psi=60000.0,
        compression_width_in=18.0,
        effective_depth_in=27.5,
    )

    assert pytest.approx(required.design_strength_ft_kip) == 428.0
    assert pytest.approx(required.required_area_in2, rel=1e-2) == 3.62
    assert pytest.approx(required.stress_block_depth_in, rel=1e-2) == 2.84


def test_minimum_flexural_reinforcement_matches_sp17_example():
    minimum = minimum_flexural_reinforcement_area(
        concrete_strength_psi=5000.0,
        steel_yield_psi=60000.0,
        web_width_in=18.0,
        effective_depth_in=27.5,
    )

    assert pytest.approx(minimum.concrete_term_area_in2, rel=1e-2) == 1.75
    assert pytest.approx(minimum.steel_term_area_in2, rel=1e-2) == 1.65
    assert pytest.approx(minimum.required_area_in2, rel=1e-2) == 1.75
    assert minimum.governing_equation == "ACI 318-14 9.6.1.2a"


def test_flexural_section_designer_creates_one_design_per_moment_design_group():
    example = SP17_BEAM_EXAMPLE_1
    table = _sp17_action_table()
    designer = ACIFlexuralSectionDesigner(
        base_section=_sp17_t_beam_assembly(),
        concrete=example.concrete(),
        steel=example.steel(),
        preferred_bar=BarTag.B25,
        stirrup_bar=BarTag.B10,
    )

    designs = designer.design_from_action_table(table)

    assert len(designs) == len(table.design_groups(ActionType.MOMENT))
    assert len(designs) == 13


def test_positive_moment_design_uses_flange_width_and_bottom_partial_reinforcement():
    example = SP17_BEAM_EXAMPLE_1
    table = _sp17_action_table()
    designer = ACIFlexuralSectionDesigner(
        base_section=_sp17_t_beam_assembly(),
        concrete=example.concrete(),
        steel=example.steel(),
        preferred_bar=BarTag.B25,
        stirrup_bar=BarTag.B10,
    )

    design = next(item for item in designer.design_from_action_table(table) if item.design_group == "span-1-positive-flexure")

    assert design.tension_face == LongitudinalFace.BOTTOM
    assert design.compression_width_in == example.aci_example_effective_flange_width_in
    assert design.assembly.cage.bottom_area == design.provided_area_in2
    assert design.assembly.cage.top_area == 0.0


def test_flexural_section_design_uses_minimum_reinforcement_when_it_controls():
    example = SP17_BEAM_EXAMPLE_1
    record = CriticalActionRecord(
        id="S1-midspan-small-M",
        span_index=0,
        role=CriticalLocationRole.MIDSPAN,
        action_type=ActionType.MOMENT,
        value=1.0,
        position_ft=17.0,
        local_position_ft=17.0,
        design_group="span-1-positive-flexure",
    )
    designer = ACIFlexuralSectionDesigner(
        base_section=_sp17_t_beam_assembly(),
        concrete=example.concrete(),
        steel=example.steel(),
        preferred_bar=BarTag.B25,
        stirrup_bar=BarTag.B10,
    )

    design = designer.design_group(record.design_group, (record,), record)

    assert design.minimum_reinforcement_controls
    assert design.bar_selection.required_area_in2 == design.minimum_required.required_area_in2
    assert design.provided_area_in2 >= design.minimum_required.required_area_in2


def test_negative_support_design_uses_web_width_and_top_partial_reinforcement_for_linked_sections():
    example = SP17_BEAM_EXAMPLE_1
    table = _sp17_action_table()
    designer = ACIFlexuralSectionDesigner(
        base_section=_sp17_t_beam_assembly(),
        concrete=example.concrete(),
        steel=example.steel(),
        preferred_bar=BarTag.B25,
        stirrup_bar=BarTag.B10,
    )

    design = next(item for item in designer.design_from_action_table(table) if item.design_group == "support-1-negative-flexure")

    assert {record.id for record in design.records} == {"S1-right_support-M", "S2-left_support-M"}
    assert design.governing_record.id == "S1-right_support-M"
    assert design.tension_face == LongitudinalFace.TOP
    assert design.compression_width_in == example.beam_width_in
    assert design.assembly.cage.top_area == design.provided_area_in2
    assert design.assembly.cage.bottom_area == 0.0


def test_provided_bar_count_is_ceil_of_required_area():
    example = SP17_BEAM_EXAMPLE_1
    table = _sp17_action_table()
    preferred_bar = RebarCatalog.get(BarTag.B25)
    designer = ACIFlexuralSectionDesigner(
        base_section=_sp17_t_beam_assembly(),
        concrete=example.concrete(),
        steel=example.steel(),
        preferred_bar=BarTag.B25,
        stirrup_bar=BarTag.B10,
    )

    design = next(item for item in designer.design_from_action_table(table) if item.design_group == "support-1-negative-flexure")

    assert design.provided_count * preferred_bar.area_in2 == design.provided_area_in2
    assert design.provided_area_in2 >= design.required.required_area_in2
    assert design.provided_strength_ratio >= 1.0


def test_required_steel_solver_accepts_aci_provided_stress_block_function():
    result = solve_required_tension_area(
        moment_ft_kip=428.0,
        phi=0.90,
        steel_yield_psi=60000.0,
        effective_depth_in=27.5,
        stress_block_depth=lambda area: area * 60000.0 / (0.85 * 5000.0 * 18.0),
    )

    assert pytest.approx(result.design_strength_ft_kip) == 428.0
    assert result.iterations > 0


def test_bar_selector_can_choose_economical_same_diameter_candidate_without_preferred_bar():
    selection = ACIBarSelector(available_bars=(BarTag.B20, BarTag.B25)).select(
        required_area_in2=2.0,
        tension_face=LongitudinalFace.BOTTOM,
    )

    assert selection.selected.bar_tag == BarTag.B25
    assert selection.provided_area_in2 >= 2.0
    assert selection.layer_specs[0].face == LongitudinalFace.BOTTOM


def test_flexural_section_builder_accepts_code_specific_placement_rule_before_assembly():
    def require_at_least_two_bars(_assembler, specs):
        if any(spec.count < 2 for spec in specs):
            raise ValueError("ACI placement rule requires at least two bars.")

    example = SP17_BEAM_EXAMPLE_1
    table = _sp17_action_table()
    builder = ACIFlexuralSectionBuilder(
        base_section=_sp17_t_beam_assembly(),
        concrete=example.concrete(),
        steel=example.steel(),
        bar_selector=ACIBarSelector(preferred_bar=BarTag.B25),
        stirrup_bar=BarTag.B10,
        placement_rules=(require_at_least_two_bars,),
    )

    designs = builder.design_from_action_table(table)

    assert designs


def test_net_tensile_strain_uses_linear_strain_distribution():
    assert pytest.approx(net_tensile_strain(0.003, effective_depth_in=27.5, neutral_axis_depth_in=4.1125)) == (
        0.003 * (27.5 - 4.1125) / 4.1125
    )


def test_flexural_strain_result_verifies_phi_assumption_for_provided_bars():
    result = evaluate_flexural_strain(
        provided_area_in2=4.20,
        concrete_strength_psi=5000.0,
        steel_yield_psi=60000.0,
        steel_modulus_psi=29000000.0,
        compression_width_in=18.0,
        effective_depth_in=27.5,
    )

    assert pytest.approx(result.stress_block_depth_in, rel=1e-2) == 3.29
    assert pytest.approx(result.neutral_axis_depth_in, rel=1e-2) == 4.11
    assert pytest.approx(result.net_tensile_strain, rel=1e-2) == 0.017
    assert result.strain_region == ACIStrainControlRegion.TENSION_CONTROLLED
    assert result.is_tension_controlled
    assert result.satisfies_minimum_beam_strain
    assert result.supports_phi_0_90_assumption


def test_flexural_section_designs_store_strain_table_data_for_report():
    example = SP17_BEAM_EXAMPLE_1
    table = _sp17_action_table()
    designer = ACIFlexuralSectionDesigner(
        base_section=_sp17_t_beam_assembly(),
        concrete=example.concrete(),
        steel=example.steel(),
        preferred_bar=BarTag.B25,
        stirrup_bar=BarTag.B10,
    )
    design = next(item for item in designer.design_from_action_table(table) if item.design_group == "support-1-negative-flexure")

    assert design.strain.stress_block_depth_in > design.required.stress_block_depth_in
    assert design.strain.net_tensile_strain > 0.005
    assert design.strain.phi == 0.90
