import pytest

from beam_design.codes.aci318.flexure import (
    ACI_MOMENT_AXIAL_ASSUMPTIONS,
    ACI_MOMENT_AXIAL_ASSUMPTIONS_BY_CLAUSE,
    beta1_factor,
    compression_block_depth_from_tension,
    effective_depth_one_layer,
    equivalent_rectangular_stress_block,
    flexural_assumption_report_rows,
)
from tests.sp17_examples import SP17_BEAM_EXAMPLE_1


def test_flexural_design_assumptions_are_stored_for_report_rows():
    clauses = {assumption.clause for assumption in ACI_MOMENT_AXIAL_ASSUMPTIONS}
    rows = flexural_assumption_report_rows()

    assert "22.2.1.1" in clauses
    assert "22.2.1.2" in clauses
    assert "22.2.2.1" in clauses
    assert "22.2.2.2" in clauses
    assert "22.2.2.4.1" in clauses
    assert "22.2.2.4.3" in clauses
    assert ACI_MOMENT_AXIAL_ASSUMPTIONS_BY_CLAUSE["22.2.2.2"].title == "Concrete tensile strength neglected"
    assert rows[0]["clause"] == "22.2.1.1"


def test_beta1_factor_matches_sp17_5000_psi_flow():
    assert beta1_factor(4000.0) == 0.85
    assert pytest.approx(beta1_factor(5000.0)) == 0.80
    assert beta1_factor(8000.0) == 0.65


def test_equivalent_rectangular_stress_block_stores_aci_concrete_assumptions():
    block = equivalent_rectangular_stress_block(5000.0)

    assert block.alpha1 == 0.85
    assert block.ultimate_concrete_strain == 0.003
    assert block.tensile_strength_neglected
    assert pytest.approx(block.beta1) == 0.80
    assert block.equivalent_concrete_stress_psi == 4250.0
    assert pytest.approx(block.equivalent_depth(10.0)) == 8.0
    assert block.compression_force(width_in=120.0, compression_block_depth_in=2.0) == 1020000.0


def test_effective_depth_one_layer_matches_sp17_moment_design_setup():
    assert effective_depth_one_layer(
        total_depth_in=30.0,
        clear_cover_in=1.5,
        transverse_bar_diameter_in=0.375,
        longitudinal_bar_diameter_in=0.875,
    ) == 27.6875


def test_compression_block_depth_from_tension_matches_sp17_width_selection():
    example = SP17_BEAM_EXAMPLE_1

    positive_coefficient = compression_block_depth_from_tension(
        tension_area_in2=1.0,
        steel_stress_psi=example.steel_yield_strength_psi,
        concrete_strength_psi=example.concrete_strength_psi,
        compression_width_in=example.aci_example_effective_flange_width_in,
    )
    negative_coefficient = compression_block_depth_from_tension(
        tension_area_in2=1.0,
        steel_stress_psi=example.steel_yield_strength_psi,
        concrete_strength_psi=example.concrete_strength_psi,
        compression_width_in=example.beam_width_in,
    )

    assert pytest.approx(positive_coefficient) == 1.0 * 60000.0 / (0.85 * 5000.0 * 120.0)
    assert pytest.approx(negative_coefficient) == 1.0 * 60000.0 / (0.85 * 5000.0 * 18.0)
    assert round(positive_coefficient, 3) == 0.118
    assert round(negative_coefficient, 3) == 0.784
