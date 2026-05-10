from beam_design.codes.aci318 import ACI318
from beam_design.codes.aci318.flexure import ACITensionStrainLimitCheck
from beam_design.codes.aci318.sections import (
    ACIDeflectionRequirementCheck,
    ACIFlangeWidthCheck,
    ACIMinimumBeamDepthCheck,
    ACITBeamCompositeConstructionCheck,
    ACITBeamFlangeTransverseReinforcementCheck,
    ACITorsionFlangeWidthCheck,
    torsion_overhanging_flange_limit,
)
from beam_design.core.model import BeamDesignContext, FactoredLoad
from beam_design.core.result import CheckStatus
from beam_design.mat_concrete import Concrete
from beam_design.mat_steel import Steel
from beam_design.section_assembler import SectionAssembler
from tests.sp17_examples import SP17_BEAM_EXAMPLE_1


def _context(section, metadata=None, load=None):
    return BeamDesignContext(
        section=section,
        concrete=Concrete(fc=5000),
        steel=Steel(fy=60000),
        load=FactoredLoad() if load is None else load,
        metadata={} if metadata is None else metadata,
    )


def test_aci_pre_flexure_geometry_checks_are_registered():
    rules = ACI318().geometry_rules()
    rule_types = {type(rule) for rule in rules}

    assert ACIMinimumBeamDepthCheck in rule_types
    assert ACIDeflectionRequirementCheck in rule_types
    assert ACITBeamCompositeConstructionCheck in rule_types
    assert ACIFlangeWidthCheck in rule_types
    assert ACITBeamFlangeTransverseReinforcementCheck in rule_types
    assert ACITorsionFlangeWidthCheck in rule_types


def test_t_beam_composite_construction_check_passes_for_monolithic_construction():
    example = SP17_BEAM_EXAMPLE_1
    section = SectionAssembler.t_beam(
        web_width=example.beam_width_in,
        total_depth=30.0,
        flange_width=example.aci_example_effective_flange_width_in,
        flange_thickness=example.slab_thickness_in,
    )
    result = ACITBeamCompositeConstructionCheck().check(
        _context(section, {"aci_flange_and_web_monolithic": True})
    )

    assert result.status == CheckStatus.PASS


def test_t_beam_composite_construction_check_fails_without_monolithic_or_composite_action():
    example = SP17_BEAM_EXAMPLE_1
    section = SectionAssembler.t_beam(
        web_width=example.beam_width_in,
        total_depth=30.0,
        flange_width=example.aci_example_effective_flange_width_in,
        flange_thickness=example.slab_thickness_in,
    )
    result = ACITBeamCompositeConstructionCheck().check(_context(section))

    assert result.status == CheckStatus.FAIL


def test_flange_transverse_reinforcement_check_only_applies_when_slab_bars_are_parallel():
    example = SP17_BEAM_EXAMPLE_1
    section = SectionAssembler.t_beam(
        web_width=example.beam_width_in,
        total_depth=30.0,
        flange_width=example.aci_example_effective_flange_width_in,
        flange_thickness=example.slab_thickness_in,
    )
    not_applicable = ACITBeamFlangeTransverseReinforcementCheck().check(_context(section))
    failing = ACITBeamFlangeTransverseReinforcementCheck().check(
        _context(section, {"aci_primary_slab_reinforcement_parallel_to_beam": True})
    )
    passing = ACITBeamFlangeTransverseReinforcementCheck().check(
        _context(
            section,
            {
                "aci_primary_slab_reinforcement_parallel_to_beam": True,
                "aci_flange_transverse_reinforcement_per_7_5_2_3": True,
            },
        )
    )

    assert not_applicable.status == CheckStatus.NOT_APPLICABLE
    assert failing.status == CheckStatus.FAIL
    assert passing.status == CheckStatus.PASS


def test_deflection_requirement_check_uses_calculated_deflection_when_min_depth_is_not_satisfied():
    section = SectionAssembler.rectangular(width=18.0, depth=20.0, cover=1.5)
    result = ACIDeflectionRequirementCheck().check(
        _context(
            section,
            {
                "aci_calculated_deflection_in": 0.75,
                "aci_deflection_limit_in": 1.0,
            },
        )
    )

    assert result.status == CheckStatus.PASS


def test_torsion_overhanging_flange_limit_uses_greater_projection_but_no_more_than_4h():
    assert torsion_overhanging_flange_limit(7.0, 12.0, 20.0) == 20.0
    assert torsion_overhanging_flange_limit(7.0, 12.0, 40.0) == 28.0


def test_torsion_flange_width_check_fails_when_overhang_is_too_wide():
    section = SectionAssembler.t_beam(web_width=18.0, total_depth=30.0, flange_width=90.0, flange_thickness=7.0)
    result = ACITorsionFlangeWidthCheck().check(
        _context(
            section,
            {
                "aci_torsion_design_required": True,
                "aci_slab_thickness_in": 7.0,
                "aci_torsion_projection_above_slab_in": 12.0,
                "aci_torsion_projection_below_slab_in": 20.0,
            },
        )
    )

    assert result.status == CheckStatus.FAIL


def test_tension_strain_limit_check_is_registered_with_flexure_rules():
    rule_types = {type(rule) for rule in ACI318().flexure_rules()}

    assert ACITensionStrainLimitCheck in rule_types


def test_tension_strain_limit_check_passes_with_metadata_strain():
    section = SectionAssembler.rectangular(width=18.0, depth=30.0, cover=1.5)
    result = ACITensionStrainLimitCheck().check(
        _context(section, {"aci_tension_strain": 0.005})
    )

    assert result.status == CheckStatus.PASS
