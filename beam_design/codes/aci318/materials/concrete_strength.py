from dataclasses import dataclass
from enum import Enum

from beam_design.core.model import BeamDesignContext
from beam_design.core.result import CheckResult


class ACIConcreteType(Enum):
    NORMALWEIGHT = "normalweight"
    LIGHTWEIGHT = "lightweight"


class ACIConcreteMemberCondition(Enum):
    GENERAL = "general"
    SPECIAL_MOMENT_FRAME = "special_moment_frame"
    SPECIAL_STRUCTURAL_WALL = "special_structural_wall"


class ACIExposureClass(Enum):
    F0 = "F0"
    F1 = "F1"
    F2 = "F2"
    F3 = "F3"
    S0 = "S0"
    S1 = "S1"
    S2 = "S2"
    S3 = "S3"
    W0 = "W0"
    W1 = "W1"
    C0 = "C0"
    C1 = "C1"
    C2 = "C2"


@dataclass(frozen=True)
class ACIExposureProfile:
    concrete_type: ACIConcreteType = ACIConcreteType.NORMALWEIGHT
    member_condition: ACIConcreteMemberCondition = ACIConcreteMemberCondition.GENERAL
    exposure_classes: tuple[ACIExposureClass, ...] = (ACIExposureClass.F0,)


_BASE_EXPOSURE_STRENGTH_PSI: dict[ACIExposureClass, int] = {
    ACIExposureClass.F0: 2500,
    ACIExposureClass.F1: 3500,
    ACIExposureClass.F2: 4500,
    ACIExposureClass.F3: 5000,
    ACIExposureClass.S0: 2500,
    ACIExposureClass.S1: 4000,
    ACIExposureClass.S2: 4500,
    ACIExposureClass.S3: 4500,
    ACIExposureClass.W0: 2500,
    ACIExposureClass.W1: 4000,
    ACIExposureClass.C0: 2500,
    ACIExposureClass.C1: 2500,
    ACIExposureClass.C2: 5000,
}

_CONDITION_MINIMUM_STRENGTH_PSI: dict[
    tuple[ACIConcreteType, ACIConcreteMemberCondition],
    int,
] = {
    (ACIConcreteType.NORMALWEIGHT, ACIConcreteMemberCondition.GENERAL): 2500,
    (ACIConcreteType.NORMALWEIGHT, ACIConcreteMemberCondition.SPECIAL_MOMENT_FRAME): 3000,
    (ACIConcreteType.NORMALWEIGHT, ACIConcreteMemberCondition.SPECIAL_STRUCTURAL_WALL): 3000,
    (ACIConcreteType.LIGHTWEIGHT, ACIConcreteMemberCondition.GENERAL): 3000,
    (ACIConcreteType.LIGHTWEIGHT, ACIConcreteMemberCondition.SPECIAL_MOMENT_FRAME): 5000,
    (ACIConcreteType.LIGHTWEIGHT, ACIConcreteMemberCondition.SPECIAL_STRUCTURAL_WALL): 5000,
}


def _coerce_enum(value: object, enum_type: type[Enum]) -> Enum:
    if isinstance(value, enum_type):
        return value
    if isinstance(value, str):
        normalized = value.strip()
        for item in enum_type:
            if normalized.lower() == item.value.lower() or normalized.upper() == item.name.upper():
                return item
    raise ValueError(f"{value!r} is not a valid {enum_type.__name__}.")


def exposure_profile_from_metadata(metadata: dict[str, object]) -> ACIExposureProfile:
    raw_classes = metadata.get("aci_exposure_classes", (ACIExposureClass.F0,))
    if isinstance(raw_classes, (str, ACIExposureClass)):
        raw_classes = (raw_classes,)

    exposure_classes = tuple(
        _coerce_enum(exposure_class, ACIExposureClass)
        for exposure_class in raw_classes
    )
    return ACIExposureProfile(
        concrete_type=_coerce_enum(
            metadata.get("aci_concrete_type", ACIConcreteType.NORMALWEIGHT),
            ACIConcreteType,
        ),
        member_condition=_coerce_enum(
            metadata.get("aci_member_condition", ACIConcreteMemberCondition.GENERAL),
            ACIConcreteMemberCondition,
        ),
        exposure_classes=exposure_classes,
    )


def minimum_concrete_strength(profile: ACIExposureProfile) -> int:
    exposure_minimum = max(_BASE_EXPOSURE_STRENGTH_PSI[item] for item in profile.exposure_classes)
    condition_minimum = _CONDITION_MINIMUM_STRENGTH_PSI[
        (profile.concrete_type, profile.member_condition)
    ]
    return max(exposure_minimum, condition_minimum)


@dataclass(frozen=True)
class ACIConcreteMinimumStrengthCheck:
    check_id: str = "aci318.material.concrete.minimum_strength"
    title: str = "Minimum concrete compressive strength"

    def check(self, context: BeamDesignContext) -> CheckResult:
        profile = exposure_profile_from_metadata(context.metadata)
        required = minimum_concrete_strength(profile)
        provided = context.concrete.compressive_strength
        ratio = required / provided if provided else None
        kwargs = {
            "demand": required,
            "capacity": provided,
            "ratio": ratio,
            "references": ("ACI 318-14 9.2.1.1", "ACI 318-14 Chapter 19"),
            "data": {
                "concrete_type": profile.concrete_type.value,
                "member_condition": profile.member_condition.value,
                "exposure_classes": tuple(item.value for item in profile.exposure_classes),
            },
        }
        if provided >= required:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult.fail_result(self.check_id, self.title, **kwargs)
