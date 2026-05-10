import pytest

from beam_design.codes.aci318.shear import (
    ACIConcreteShearEquation,
    circular_tie_or_spiral_effective_area,
    concrete_shear_axial_compression_detailed,
    concrete_shear_axial_compression_simple,
    concrete_shear_axial_tension,
    concrete_shear_no_axial_detailed,
    concrete_shear_no_axial_simple,
    design_perpendicular_stirrup_spacing,
    evaluate_one_way_shear_without_axial,
    inclined_stirrup_shear_strength,
    longitudinal_reinforcement_ratio,
    max_shear_reinforcement_spacing_nonprestressed_beam,
    minimum_shear_reinforcement_trigger,
    perpendicular_stirrup_spacing_for_required_vs,
    rectangular_tie_effective_area,
    required_area_per_spacing_for_perpendicular_stirrups,
    required_shear_reinforcement_strength,
    transverse_reinforcement_shear_strength,
)
from beam_design.codes.aci318.shear.one_way import sqrt_concrete_strength_for_shear
from beam_design.core.reinforcement import LongitudinalFace, LongitudinalLayerSpec
from beam_design.codes.aci318.shear.strength import ACIShearStrengthCheck
from beam_design.core.model import BeamDesignContext, ReinforcementLayout
from beam_design.mat_concrete import Concrete
from beam_design.mat_steel import Steel
from beam_design.section_assembler import SectionAssembler


def test_concrete_shear_no_axial_simple_uses_aci_22_5_5_1():
    result = concrete_shear_no_axial_simple(
        concrete_strength_psi=5000.0,
        web_width_in=18.0,
        effective_depth_in=27.5,
    )

    assert result.equation == ACIConcreteShearEquation.NO_AXIAL_SIMPLE
    assert pytest.approx(result.strength_kip, rel=1e-3) == 70.004


def test_longitudinal_reinforcement_ratio_uses_web_width_and_effective_depth():
    assert pytest.approx(longitudinal_reinforcement_ratio(3.6, 18.0, 27.5)) == 3.6 / (18.0 * 27.5)


def test_concrete_shear_no_axial_detailed_returns_least_table_22_5_5_1_expression():
    result = concrete_shear_no_axial_detailed(
        concrete_strength_psi=5000.0,
        web_width_in=18.0,
        effective_depth_in=27.5,
        tension_steel_area_in2=3.6,
        factored_shear_lb=63_000.0,
        factored_moment_lb_in=389.0 * 12_000.0,
    )

    assert result.equation == ACIConcreteShearEquation.NO_AXIAL_DETAILED_A
    assert result.strength_lb == min(result.terms_lb.values())
    assert pytest.approx(result.strength_kip, rel=1e-2) == 69.92


def test_concrete_shear_axial_compression_simple_uses_positive_compression():
    result = concrete_shear_axial_compression_simple(
        concrete_strength_psi=5000.0,
        web_width_in=18.0,
        effective_depth_in=27.5,
        gross_area_in2=18.0 * 30.0,
        axial_compression_lb=108_000.0,
    )

    assert result.equation == ACIConcreteShearEquation.AXIAL_COMPRESSION_SIMPLE
    assert result.strength_lb > concrete_shear_no_axial_simple(5000.0, 18.0, 27.5).strength_lb


def test_concrete_shear_axial_compression_detailed_skips_inapplicable_expression_a():
    result = concrete_shear_axial_compression_detailed(
        concrete_strength_psi=5000.0,
        web_width_in=18.0,
        effective_depth_in=27.5,
        gross_area_in2=18.0 * 30.0,
        total_depth_in=30.0,
        tension_steel_area_in2=3.6,
        factored_shear_lb=63_000.0,
        factored_moment_lb_in=10_000.0,
        axial_compression_lb=108_000.0,
    )

    assert ACIConcreteShearEquation.AXIAL_COMPRESSION_DETAILED_A.value not in result.terms_lb
    assert result.equation == ACIConcreteShearEquation.AXIAL_COMPRESSION_DETAILED_B


def test_concrete_shear_axial_tension_is_not_less_than_zero():
    result = concrete_shear_axial_tension(
        concrete_strength_psi=5000.0,
        web_width_in=18.0,
        effective_depth_in=27.5,
        gross_area_in2=18.0 * 30.0,
        axial_tension_lb=400_000.0,
    )

    assert result.equation == ACIConcreteShearEquation.AXIAL_TENSION
    assert result.strength_lb == 0.0


def test_active_shear_check_reuses_one_way_no_axial_concrete_shear_calculator():
    section = SectionAssembler.rectangular(width=18.0, depth=30.0, cover=1.5)
    context = BeamDesignContext(
        section=section,
        concrete=Concrete(fc=5000.0),
        steel=Steel(fy=60000.0),
        load=None,
    )

    assert ACIShearStrengthCheck().concrete_shear_capacity(context) == concrete_shear_no_axial_simple(
        concrete_strength_psi=5000.0,
        web_width_in=18.0,
        effective_depth_in=context.effective_depth,
    ).strength_lb


def test_concrete_shear_calculations_cap_sqrt_fc_at_100_unless_explicitly_allowed():
    capped = concrete_shear_no_axial_simple(14_400.0, 18.0, 27.5)
    uncapped = concrete_shear_no_axial_simple(14_400.0, 18.0, 27.5, allow_sqrt_fc_above_100=True)

    assert sqrt_concrete_strength_for_shear(14_400.0) == 100.0
    assert sqrt_concrete_strength_for_shear(14_400.0, allow_above_100=True) == 120.0
    assert capped.sqrt_fc_used_psi == 100.0
    assert uncapped.sqrt_fc_used_psi == 120.0
    assert uncapped.strength_lb > capped.strength_lb


def test_active_shear_check_caps_stirrup_yield_strength_for_deformed_bar_stirrups():
    section = SectionAssembler.rectangular(width=18.0, depth=30.0, cover=1.5)
    from beam_design.reinforcement_assembler import ReinforcementAssembler
    from beam_design.rebar import BarTag

    reinforcement_assembler = ReinforcementAssembler(section=section, stirrup_bar=BarTag.B10)
    cage = reinforcement_assembler.cage(
        longitudinal_specs=(LongitudinalLayerSpec(LongitudinalFace.BOTTOM, BarTag.B25, 2),),
        transverse_zones=(reinforcement_assembler.transverse_zone(0, 60, BarTag.B10, spacing=6, legs=2),),
    )
    context = BeamDesignContext(
        section=section,
        concrete=Concrete(fc=5000.0),
        steel=Steel(fy=80_000.0),
        reinforcement=ReinforcementLayout(cage=cage),
    )
    av = cage.first_transverse_zone.area_per_set
    expected = av * 60_000.0 * context.effective_depth / 6.0

    assert pytest.approx(ACIShearStrengthCheck().stirrup_shear_capacity(context)) == expected


def test_one_way_shear_design_section_reports_required_stirrup_shear_strength():
    result = evaluate_one_way_shear_without_axial(
        factored_shear_lb=63_500.0,
        concrete_strength_psi=5000.0,
        web_width_in=18.0,
        effective_depth_in=27.5,
    )

    assert pytest.approx(result.concrete_shear.strength_kip, rel=1e-3) == 70.004
    assert pytest.approx(result.concrete_design_strength_kip, rel=1e-3) == 52.503
    assert result.shear_reinforcement_required
    assert result.minimum_shear_reinforcement_required
    assert pytest.approx(result.required_stirrup_shear_strength_kip, rel=1e-3) == (63.5 / 0.75) - 70.004


def test_required_shear_reinforcement_strength_uses_aci_22_5_10_1():
    required = required_shear_reinforcement_strength(
        factored_shear_lb=63_500.0,
        phi=0.75,
        concrete_shear_strength_lb=70_004.0,
    )

    assert required.shear_reinforcement_required
    assert pytest.approx(required.required_shear_reinforcement_strength_kip, rel=1e-3) == (63.5 / 0.75) - 70.004


def test_transverse_reinforcement_shear_strength_uses_effective_area_of_all_legs():
    av = rectangular_tie_effective_area(single_leg_area_in2=0.11, legs=2)
    vs = transverse_reinforcement_shear_strength(
        area_in2=av,
        yield_strength_psi=60_000.0,
        effective_depth_in=27.5,
        spacing_in=8.0,
    )

    assert av == 0.22
    assert pytest.approx(vs) == 0.22 * 60_000.0 * 27.5 / 8.0


def test_perpendicular_stirrup_spacing_inverts_aci_22_5_10_5_3():
    spacing = perpendicular_stirrup_spacing_for_required_vs(
        area_in2=0.22,
        yield_strength_psi=60_000.0,
        effective_depth_in=27.5,
        required_shear_reinforcement_strength_lb=14_666.6667,
    )

    assert pytest.approx(spacing, rel=1e-3) == 24.75


def test_max_shear_reinforcement_spacing_for_nonprestressed_beam_uses_table_9_7_6_2_2():
    low = max_shear_reinforcement_spacing_nonprestressed_beam(
        required_shear_reinforcement_strength_lb=14_666.6667,
        concrete_strength_psi=5000.0,
        web_width_in=18.0,
        effective_depth_in=27.5,
    )
    high = max_shear_reinforcement_spacing_nonprestressed_beam(
        required_shear_reinforcement_strength_lb=150_000.0,
        concrete_strength_psi=5000.0,
        web_width_in=18.0,
        effective_depth_in=27.5,
    )

    assert pytest.approx(low.threshold_kip, rel=1e-3) == 140.007
    assert low.limit_expression == "lesser of d/2 and 24 in."
    assert pytest.approx(low.max_spacing_in) == 13.75
    assert high.limit_expression == "lesser of d/4 and 12 in."
    assert pytest.approx(high.max_spacing_in) == 6.875


def test_minimum_shear_reinforcement_trigger_uses_general_beam_rule_by_default():
    general = minimum_shear_reinforcement_trigger(
        factored_shear_lb=30_000.0,
        phi=0.75,
        concrete_shear_strength_lb=70_000.0,
    )
    explicit_exception = minimum_shear_reinforcement_trigger(
        factored_shear_lb=30_000.0,
        phi=0.75,
        concrete_shear_strength_lb=70_000.0,
        exception_applies=True,
    )

    assert pytest.approx(general.threshold_kip) == 26.25
    assert general.minimum_reinforcement_required
    assert pytest.approx(explicit_exception.threshold_kip) == 52.5
    assert not explicit_exception.minimum_reinforcement_required


def test_perpendicular_stirrup_spacing_design_combines_strength_and_spacing_limit():
    design = design_perpendicular_stirrup_spacing(
        required_shear_reinforcement_strength_lb=14_666.6667,
        area_in2=0.22,
        yield_strength_psi=60_000.0,
        effective_depth_in=27.5,
        concrete_strength_psi=5000.0,
        web_width_in=18.0,
    )

    assert pytest.approx(design.calculated_spacing_in, rel=1e-3) == 24.75
    assert pytest.approx(design.spacing_limit.max_spacing_in) == 13.75
    assert design.selected_spacing_satisfies_limit(12.0)
    assert not design.selected_spacing_satisfies_limit(14.0)


def test_inclined_stirrup_shear_strength_uses_angle_factor():
    vs = inclined_stirrup_shear_strength(
        area_in2=0.22,
        yield_strength_psi=60_000.0,
        effective_depth_in=27.5,
        spacing_in=8.0,
        angle_degrees=45.0,
    )

    assert pytest.approx(vs, rel=1e-12) == 0.22 * 60_000.0 * (2**0.5) * 27.5 / 8.0


def test_spiral_effective_area_and_required_area_per_spacing_helpers():
    assert circular_tie_or_spiral_effective_area(0.11) == 0.22
    assert pytest.approx(
        required_area_per_spacing_for_perpendicular_stirrups(
            required_shear_reinforcement_strength_lb=14_662.67,
            yield_strength_psi=60_000.0,
            effective_depth_in=27.5,
        )
    ) == 14_662.67 / (60_000.0 * 27.5)
