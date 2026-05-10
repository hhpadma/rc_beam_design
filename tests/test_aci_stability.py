from beam_design.codes.aci318 import ACI318, ACILateralStabilityCheck, lateral_bracing_spacing_limit
from beam_design.core.model import BeamDesignContext
from beam_design.core.result import CheckStatus
from beam_design.mat_concrete import Concrete
from beam_design.mat_steel import Steel
from beam_design.section_assembler import SectionAssembler


def _context(metadata):
    return BeamDesignContext(
        section=SectionAssembler.rectangular(width=18.0, depth=30.0, cover=1.5),
        concrete=Concrete(fc=5000),
        steel=Steel(fy=60000),
        metadata=metadata,
    )


def test_lateral_bracing_spacing_limit_is_50_times_least_compression_width():
    assert lateral_bracing_spacing_limit(18.0) == 900.0


def test_lateral_stability_check_not_applicable_when_continuously_braced():
    result = ACILateralStabilityCheck().check(
        _context({"aci_continuously_laterally_braced": True})
    )

    assert result.status == CheckStatus.NOT_APPLICABLE


def test_lateral_stability_check_passes_when_spacing_is_within_50b():
    result = ACILateralStabilityCheck().check(
        _context(
            {
                "aci_continuously_laterally_braced": False,
                "aci_lateral_bracing_spacing_in": 600.0,
                "aci_least_compression_width_in": 18.0,
            }
        )
    )

    assert result.status == CheckStatus.PASS
    assert result.demand == 600.0
    assert result.capacity == 900.0


def test_lateral_stability_check_fails_when_spacing_exceeds_50b():
    result = ACILateralStabilityCheck().check(
        _context(
            {
                "aci_continuously_laterally_braced": False,
                "aci_lateral_bracing_spacing_in": 1000.0,
                "aci_least_compression_width_in": 18.0,
            }
        )
    )

    assert result.status == CheckStatus.FAIL
    assert "50 times" in result.message


def test_lateral_stability_check_fails_when_eccentric_load_effects_are_not_accounted_for():
    result = ACILateralStabilityCheck().check(
        _context(
            {
                "aci_continuously_laterally_braced": False,
                "aci_lateral_bracing_spacing_in": 600.0,
                "aci_least_compression_width_in": 18.0,
                "aci_eccentric_loads": True,
                "aci_eccentric_loads_accounted_for": False,
            }
        )
    )

    assert result.status == CheckStatus.FAIL
    assert "eccentric loads" in result.message


def test_aci_stability_rules_include_lateral_stability_check():
    rules = ACI318().stability_rules()

    assert len(rules) == 1
    assert isinstance(rules[0], ACILateralStabilityCheck)
