from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

from beam_design.core.model import BeamDesignContext
from beam_design.core.result import CheckResult


class ACIConcreteCoverExposure(Enum):
    CAST_AGAINST_GROUND = "cast_against_ground"
    WEATHER_OR_GROUND = "weather_or_ground"
    NOT_EXPOSED = "not_exposed"


class ACICoverMemberType(Enum):
    ALL = "all"
    SLAB_JOIST_WALL = "slab_joist_wall"
    BEAM_COLUMN_PEDESTAL_TENSION_TIE = "beam_column_pedestal_tension_tie"


class ACICoverReinforcementType(Enum):
    ALL = "all"
    BAR_NO_6_TO_18 = "bar_no_6_to_18"
    BAR_NO_5_W31_D31_AND_SMALLER = "bar_no_5_w31_d31_and_smaller"
    BAR_NO_14_TO_18 = "bar_no_14_to_18"
    BAR_NO_11_AND_SMALLER = "bar_no_11_and_smaller"
    PRIMARY_REINFORCEMENT_TIES_STIRRUPS_SPIRALS_HOOPS = "primary_reinforcement_ties_stirrups_spirals_hoops"


COVER_TABLE_20_6_1_3_1 = MappingProxyType(
    {
        (
            ACIConcreteCoverExposure.CAST_AGAINST_GROUND,
            ACICoverMemberType.ALL,
            ACICoverReinforcementType.ALL,
        ): 3.0,
        (
            ACIConcreteCoverExposure.WEATHER_OR_GROUND,
            ACICoverMemberType.ALL,
            ACICoverReinforcementType.BAR_NO_6_TO_18,
        ): 2.0,
        (
            ACIConcreteCoverExposure.WEATHER_OR_GROUND,
            ACICoverMemberType.ALL,
            ACICoverReinforcementType.BAR_NO_5_W31_D31_AND_SMALLER,
        ): 1.5,
        (
            ACIConcreteCoverExposure.NOT_EXPOSED,
            ACICoverMemberType.SLAB_JOIST_WALL,
            ACICoverReinforcementType.BAR_NO_14_TO_18,
        ): 1.5,
        (
            ACIConcreteCoverExposure.NOT_EXPOSED,
            ACICoverMemberType.SLAB_JOIST_WALL,
            ACICoverReinforcementType.BAR_NO_11_AND_SMALLER,
        ): 0.75,
        (
            ACIConcreteCoverExposure.NOT_EXPOSED,
            ACICoverMemberType.BEAM_COLUMN_PEDESTAL_TENSION_TIE,
            ACICoverReinforcementType.PRIMARY_REINFORCEMENT_TIES_STIRRUPS_SPIRALS_HOOPS,
        ): 1.5,
    }
)


def specified_concrete_cover(
    exposure: ACIConcreteCoverExposure | str,
    member_type: ACICoverMemberType | str,
    reinforcement_type: ACICoverReinforcementType | str,
) -> float:
    exposure = coerce_cover_exposure(exposure)
    member_type = coerce_cover_member_type(member_type)
    reinforcement_type = coerce_cover_reinforcement_type(reinforcement_type)

    exact_key = (exposure, member_type, reinforcement_type)
    if exact_key in COVER_TABLE_20_6_1_3_1:
        return COVER_TABLE_20_6_1_3_1[exact_key]

    all_member_key = (exposure, ACICoverMemberType.ALL, reinforcement_type)
    if all_member_key in COVER_TABLE_20_6_1_3_1:
        return COVER_TABLE_20_6_1_3_1[all_member_key]

    all_reinforcement_key = (exposure, member_type, ACICoverReinforcementType.ALL)
    if all_reinforcement_key in COVER_TABLE_20_6_1_3_1:
        return COVER_TABLE_20_6_1_3_1[all_reinforcement_key]

    all_key = (exposure, ACICoverMemberType.ALL, ACICoverReinforcementType.ALL)
    if all_key in COVER_TABLE_20_6_1_3_1:
        return COVER_TABLE_20_6_1_3_1[all_key]

    raise ValueError(
        "No ACI 318-14 Table 20.6.1.3.1 cover requirement is defined for "
        f"{exposure.value}, {member_type.value}, {reinforcement_type.value}."
    )


def coerce_cover_exposure(value: ACIConcreteCoverExposure | str) -> ACIConcreteCoverExposure:
    if isinstance(value, ACIConcreteCoverExposure):
        return value
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    return ACIConcreteCoverExposure(normalized)


def coerce_cover_member_type(value: ACICoverMemberType | str) -> ACICoverMemberType:
    if isinstance(value, ACICoverMemberType):
        return value
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    return ACICoverMemberType(normalized)


def coerce_cover_reinforcement_type(value: ACICoverReinforcementType | str) -> ACICoverReinforcementType:
    if isinstance(value, ACICoverReinforcementType):
        return value
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    return ACICoverReinforcementType(normalized)


@dataclass(frozen=True)
class ACIMinimumCoverCheck:
    check_id: str = "aci318.detailing.cover"
    title: str = "Minimum concrete cover"
    default_exposure: ACIConcreteCoverExposure = ACIConcreteCoverExposure.NOT_EXPOSED
    default_member_type: ACICoverMemberType = ACICoverMemberType.BEAM_COLUMN_PEDESTAL_TENSION_TIE
    default_reinforcement_type: ACICoverReinforcementType = (
        ACICoverReinforcementType.PRIMARY_REINFORCEMENT_TIES_STIRRUPS_SPIRALS_HOOPS
    )

    def check(self, context: BeamDesignContext) -> CheckResult:
        exposure = coerce_cover_exposure(context.metadata.get("aci_cover_exposure", self.default_exposure))
        member_type = coerce_cover_member_type(context.metadata.get("aci_cover_member_type", self.default_member_type))
        reinforcement_type = coerce_cover_reinforcement_type(
            context.metadata.get("aci_cover_reinforcement_type", self.default_reinforcement_type)
        )
        required = specified_concrete_cover(exposure, member_type, reinforcement_type)
        provided = context.section.cover
        kwargs = {
            "demand": required,
            "capacity": provided,
            "ratio": required / provided if provided else None,
            "references": ("ACI 318-14 20.6.1.3.1", "ACI 318-14 Table 20.6.1.3.1"),
            "data": {
                "exposure": exposure.value,
                "member_type": member_type.value,
                "reinforcement_type": reinforcement_type.value,
            },
        }
        if provided >= required:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult.fail_result(self.check_id, self.title, **kwargs)
