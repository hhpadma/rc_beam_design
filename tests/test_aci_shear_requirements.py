from beam_design.codes.aci318.shear import (
    ACIAxialTensionCreepShrinkageShearEffectCheck,
    ACIConcreteShearSqrtStrengthLimitCheck,
    ACIShearReinforcementYieldStrengthLimitCheck,
    ACIShearSectionDimensionLimitCheck,
    ACIVariableDepthShearEffectCheck,
    ACIWebOpeningShearEffectCheck,
)
from beam_design.core.model import BeamDesignContext, FactoredLoad
from beam_design.core.result import CheckStatus
from beam_design.mat_concrete import Concrete
from beam_design.mat_steel import Steel
from beam_design.section_assembler import SectionAssembler


def _context(**metadata):
    return BeamDesignContext(
        section=SectionAssembler.rectangular(width=18.0, depth=30.0, cover=1.5),
        concrete=Concrete(fc=5000.0),
        steel=Steel(fy=60000.0),
        load=FactoredLoad(shear=63_500.0),
        metadata=metadata,
    )


def test_shear_section_dimension_limit_check_passes_sp17_scale_section():
    result = ACIShearSectionDimensionLimitCheck().check(_context())

    assert result.status == CheckStatus.PASS
    assert result.capacity > result.demand


def test_sqrt_fc_limit_check_fails_without_explicit_high_strength_exception():
    context = BeamDesignContext(
        section=SectionAssembler.rectangular(width=18.0, depth=30.0, cover=1.5),
        concrete=Concrete(fc=14_400.0),
        steel=Steel(fy=60000.0),
    )

    assert ACIConcreteShearSqrtStrengthLimitCheck().check(context).status == CheckStatus.FAIL

    allowed = BeamDesignContext(
        section=context.section,
        concrete=context.concrete,
        steel=context.steel,
        metadata={"aci_allow_sqrt_fc_shear_above_100": True},
    )
    assert ACIConcreteShearSqrtStrengthLimitCheck().check(allowed).status == CheckStatus.PASS


def test_shear_reinforcement_yield_strength_limit_fails_for_deformed_bar_above_60000():
    context = BeamDesignContext(
        section=SectionAssembler.rectangular(width=18.0, depth=30.0, cover=1.5),
        concrete=Concrete(fc=5000.0),
        steel=Steel(fy=80_000.0),
    )

    assert ACIShearReinforcementYieldStrengthLimitCheck().check(context).status == CheckStatus.FAIL


def test_web_opening_check_fails_only_when_opening_exists_and_effect_is_not_considered():
    assert ACIWebOpeningShearEffectCheck().check(_context()).status == CheckStatus.NOT_APPLICABLE
    assert ACIWebOpeningShearEffectCheck().check(_context(aci_web_openings_present=True)).status == CheckStatus.FAIL
    assert (
        ACIWebOpeningShearEffectCheck()
        .check(_context(aci_web_openings_present=True, aci_web_opening_shear_effects_considered=True))
        .status
        == CheckStatus.PASS
    )


def test_creep_shrinkage_axial_tension_check_fails_only_when_effect_exists_and_is_not_considered():
    assert ACIAxialTensionCreepShrinkageShearEffectCheck().check(_context()).status == CheckStatus.NOT_APPLICABLE
    assert (
        ACIAxialTensionCreepShrinkageShearEffectCheck()
        .check(_context(aci_restrained_creep_shrinkage_axial_tension_present=True))
        .status
        == CheckStatus.FAIL
    )


def test_variable_depth_effect_is_warning_when_present_but_not_considered():
    assert ACIVariableDepthShearEffectCheck().check(_context()).status == CheckStatus.NOT_APPLICABLE
    assert ACIVariableDepthShearEffectCheck().check(_context(aci_variable_depth_member=True)).status == CheckStatus.WARNING
    assert (
        ACIVariableDepthShearEffectCheck()
        .check(_context(aci_variable_depth_member=True, aci_variable_depth_shear_effect_considered=True))
        .status
        == CheckStatus.PASS
    )
