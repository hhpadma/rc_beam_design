import pytest

from beam_design.codes.aci318 import (
    ACIStrengthReductionCategory,
    ACIStrainControlRegion,
    ACITransverseReinforcementType,
    PHI_TABLE_21_2_1,
    compression_controlled_strain_limit,
    fixed_phi,
    phi_for_moment_axial,
    strain_control_region,
    strength_reduction_factor,
)
from beam_design.codes.aci318.flexure.strength import ACIFlexuralStrengthCheck
from beam_design.codes.aci318.shear.strength import ACIShearStrengthCheck
from beam_design.core.model import BeamDesignContext
from beam_design.mat_concrete import Concrete
from beam_design.mat_steel import Steel
from beam_design.section_assembler import SectionAssembler


def test_table_21_2_1_fixed_phi_values_are_stored_once():
    assert fixed_phi(ACIStrengthReductionCategory.SHEAR) == 0.75
    assert fixed_phi(ACIStrengthReductionCategory.TORSION) == 0.75
    assert fixed_phi(ACIStrengthReductionCategory.BEARING) == 0.65
    assert fixed_phi(ACIStrengthReductionCategory.POST_TENSIONED_ANCHORAGE_ZONE) == 0.85
    assert fixed_phi(ACIStrengthReductionCategory.PLAIN_CONCRETE) == 0.60
    assert fixed_phi("precast_connection_yielding_steel") == 0.90


def test_table_21_2_1_range_values_are_explicit_records():
    moment_record = strength_reduction_factor(ACIStrengthReductionCategory.MOMENT_AXIAL)
    anchor_record = strength_reduction_factor(ACIStrengthReductionCategory.ANCHOR_IN_CONCRETE)

    assert moment_record.is_range
    assert moment_record.min_phi == 0.65
    assert moment_record.max_phi == 0.90
    assert anchor_record.min_phi == 0.45
    assert anchor_record.max_phi == 0.75
    with pytest.raises(ValueError):
        fixed_phi(ACIStrengthReductionCategory.MOMENT_AXIAL)


def test_phi_table_is_immutable():
    with pytest.raises(TypeError):
        PHI_TABLE_21_2_1[ACIStrengthReductionCategory.SHEAR] = 0.70


def test_compression_controlled_strain_limit_for_grade_60_can_be_0_002():
    assert compression_controlled_strain_limit(60000.0, 29000000.0) == 0.002
    assert pytest.approx(compression_controlled_strain_limit(80000.0, 29000000.0)) == 80000.0 / 29000000.0


def test_phi_for_moment_axial_table_21_2_2_other_ties():
    assert phi_for_moment_axial(0.002, transverse_reinforcement=ACITransverseReinforcementType.OTHER) == 0.65
    assert phi_for_moment_axial(0.005, transverse_reinforcement=ACITransverseReinforcementType.OTHER) == 0.90
    assert pytest.approx(phi_for_moment_axial(0.0035, transverse_reinforcement="other")) == 0.775


def test_phi_for_moment_axial_table_21_2_2_spirals():
    assert phi_for_moment_axial(0.002, transverse_reinforcement=ACITransverseReinforcementType.SPIRAL) == 0.75
    assert phi_for_moment_axial(0.005, transverse_reinforcement=ACITransverseReinforcementType.SPIRAL) == 0.90
    assert pytest.approx(phi_for_moment_axial(0.0035, transverse_reinforcement="spiral")) == 0.825


def test_strain_control_region_classifies_table_21_2_2_regions():
    assert strain_control_region(0.0019) == ACIStrainControlRegion.COMPRESSION_CONTROLLED
    assert strain_control_region(0.0035) == ACIStrainControlRegion.TRANSITION
    assert strain_control_region(0.005) == ACIStrainControlRegion.TENSION_CONTROLLED


def test_active_shear_check_uses_central_strength_reduction_factor():
    assert ACIShearStrengthCheck().phi == fixed_phi(ACIStrengthReductionCategory.SHEAR)


def test_active_flexure_check_uses_strain_based_strength_reduction_factor_when_available():
    section = SectionAssembler.rectangular(width=18.0, depth=30.0, cover=1.5)
    context = BeamDesignContext(
        section=section,
        concrete=Concrete(fc=5000),
        steel=Steel(fy=60000),
        reinforcement=SectionAssembler.rectangular_assembly(
            width=18.0,
            depth=30.0,
            clear_cover=1.5,
        ).reinforcement,
        metadata={
            "aci_tension_strain": 0.0035,
            "aci_transverse_reinforcement_type": "other",
        },
    )

    assert pytest.approx(ACIFlexuralStrengthCheck().strength_reduction_factor(context)) == 0.775


def test_active_flexure_check_defaults_to_tension_controlled_phi_until_strain_is_computed():
    section = SectionAssembler.rectangular(width=18.0, depth=30.0, cover=1.5)
    context = BeamDesignContext(
        section=section,
        concrete=Concrete(fc=5000),
        steel=Steel(fy=60000),
    )

    assert ACIFlexuralStrengthCheck().strength_reduction_factor(context) == 0.90
