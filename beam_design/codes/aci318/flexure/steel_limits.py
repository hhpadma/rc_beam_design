from dataclasses import dataclass

from beam_design.codes.aci318.flexure.minimum_reinforcement import minimum_flexural_reinforcement_area
from beam_design.core.model import BeamDesignContext
from beam_design.core.result import CheckResult


@dataclass(frozen=True)
class ACIMinimumTensionSteelCheck:
    check_id: str = "aci318.flexure.min_tension_steel"
    title: str = "Minimum tension reinforcement"

    def check(self, context: BeamDesignContext) -> CheckResult:
        b = context.section.width
        d = context.effective_depth
        fc = context.concrete.compressive_strength
        fy = context.steel.yield_strength
        minimum = minimum_flexural_reinforcement_area(fc, fy, b, d)
        as_min = minimum.required_area_in2
        as_t = context.reinforcement.tension_area
        ratio = as_t / as_min if as_min else None
        kwargs = {
            "demand": as_min,
            "capacity": as_t,
            "ratio": ratio,
            "references": ("ACI 318-14 9.6.1.1", "ACI 318-14 9.6.1.2"),
            "data": {
                "aci_9_6_1_2a_area_in2": minimum.concrete_term_area_in2,
                "aci_9_6_1_2b_area_in2": minimum.steel_term_area_in2,
                "governing_equation": minimum.governing_equation,
            },
        }
        if as_t >= as_min:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult.fail_result(self.check_id, self.title, **kwargs)


@dataclass(frozen=True)
class ACIMaximumTensionSteelCheck:
    check_id: str = "aci318.flexure.max_tension_steel"
    title: str = "Maximum tension reinforcement"
    max_steel_ratio: float = 0.025

    def check(self, context: BeamDesignContext) -> CheckResult:
        gross_area = context.section.width * context.effective_depth
        as_max = self.max_steel_ratio * gross_area
        as_t = context.reinforcement.tension_area
        ratio = as_t / as_max if as_max else None
        kwargs = {
            "demand": as_t,
            "capacity": as_max,
            "ratio": ratio,
            "references": ("Project-configurable ACI reinforcement limit",),
        }
        if as_t <= as_max:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult.fail_result(self.check_id, self.title, **kwargs)
