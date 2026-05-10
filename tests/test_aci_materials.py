from beam_design.codes.aci318.materials import (
    ACIConcreteMemberCondition,
    ACIConcreteType,
    ACIExposureClass,
    ACIExposureProfile,
    minimum_concrete_strength,
)
from beam_design.codes.aci318.materials.concrete_strength import ACIConcreteMinimumStrengthCheck
from beam_design.core.model import BeamDesignContext, Section
from beam_design.core.result import CheckStatus
from beam_design.mat_concrete import Concrete
from beam_design.mat_steel import Steel


def _context(fc, **metadata):
    return BeamDesignContext(
        section=Section(width=12, depth=24),
        concrete=Concrete(fc=fc),
        steel=Steel(fy=60000),
        metadata=metadata,
    )


def test_general_normalweight_uses_exposure_minimum():
    profile = ACIExposureProfile(
        concrete_type=ACIConcreteType.NORMALWEIGHT,
        member_condition=ACIConcreteMemberCondition.GENERAL,
        exposure_classes=(ACIExposureClass.F3,),
    )

    assert minimum_concrete_strength(profile) == 5000


def test_special_moment_normalweight_sets_3000_minimum_when_exposure_is_low():
    profile = ACIExposureProfile(
        concrete_type=ACIConcreteType.NORMALWEIGHT,
        member_condition=ACIConcreteMemberCondition.SPECIAL_MOMENT_FRAME,
        exposure_classes=(ACIExposureClass.F0,),
    )

    assert minimum_concrete_strength(profile) == 3000


def test_lightweight_special_moment_sets_5000_minimum():
    profile = ACIExposureProfile(
        concrete_type=ACIConcreteType.LIGHTWEIGHT,
        member_condition=ACIConcreteMemberCondition.SPECIAL_MOMENT_FRAME,
        exposure_classes=(ACIExposureClass.S0,),
    )

    assert minimum_concrete_strength(profile) == 5000


def test_concrete_minimum_strength_check_fails_below_required_strength():
    result = ACIConcreteMinimumStrengthCheck().check(
        _context(
            4000,
            aci_concrete_type="normalweight",
            aci_member_condition="general",
            aci_exposure_classes=("F3", "S1"),
        )
    )

    assert result.status == CheckStatus.FAIL
    assert result.demand == 5000
    assert result.capacity == 4000


def test_concrete_minimum_strength_check_passes_at_required_strength():
    result = ACIConcreteMinimumStrengthCheck().check(
        _context(
            5000,
            aci_concrete_type="lightweight",
            aci_member_condition="special_structural_wall",
            aci_exposure_classes=("C0",),
        )
    )

    assert result.status == CheckStatus.PASS
    assert result.demand == 5000
