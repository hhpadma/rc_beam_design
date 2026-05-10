from dataclasses import dataclass
from enum import Enum

from beam_design.core.model import BeamDesignContext
from beam_design.core.result import CheckResult


class ACISupportCondition(Enum):
    SIMPLY_SUPPORTED = "simply_supported"
    ONE_END_CONTINUOUS = "one_end_continuous"
    BOTH_ENDS_CONTINUOUS = "both_ends_continuous"
    CANTILEVER = "cantilever"


_DEPTH_DIVISORS: dict[ACISupportCondition, float] = {
    ACISupportCondition.SIMPLY_SUPPORTED: 16.0,
    ACISupportCondition.ONE_END_CONTINUOUS: 18.5,
    ACISupportCondition.BOTH_ENDS_CONTINUOUS: 21.0,
    ACISupportCondition.CANTILEVER: 8.0,
}


def coerce_support_condition(value: ACISupportCondition | str) -> ACISupportCondition:
    if isinstance(value, ACISupportCondition):
        return value
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    return ACISupportCondition(normalized)


def minimum_beam_depth(
    clear_span_in: float,
    support_condition: ACISupportCondition,
    fy_psi: float = 60000.0,
    lightweight_unit_weight_pcf: float | None = None,
) -> float:
    if clear_span_in <= 0:
        raise ValueError("Clear span must be positive.")

    h_min = clear_span_in / _DEPTH_DIVISORS[support_condition]
    if fy_psi != 60000:
        h_min *= 0.4 + fy_psi / 100000.0

    if lightweight_unit_weight_pcf is not None:
        if 90 <= lightweight_unit_weight_pcf <= 115:
            h_min *= max(1.65 - 0.005 * lightweight_unit_weight_pcf, 1.09)
        elif lightweight_unit_weight_pcf < 90:
            raise ValueError("ACI lightweight modifier is defined here for 90 to 115 pcf concrete.")

    return h_min


@dataclass(frozen=True)
class ACIMinimumBeamDepthCheck:
    check_id: str = "aci318.geometry.minimum_beam_depth"
    title: str = "Minimum beam depth"

    def check(self, context: BeamDesignContext) -> CheckResult:
        span = context.metadata.get("aci_span_length_in", context.metadata.get("aci_clear_span_in"))
        support_condition = context.metadata.get("aci_support_condition")
        if span is None or support_condition is None:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "Provide aci_span_length_in and aci_support_condition to check minimum beam depth.",
            )

        support = coerce_support_condition(support_condition)
        required = minimum_beam_depth(
            clear_span_in=float(span),
            support_condition=support,
            fy_psi=context.steel.yield_strength,
            lightweight_unit_weight_pcf=context.metadata.get("aci_lightweight_unit_weight_pcf"),
        )
        provided = context.section.depth
        ratio = required / provided if provided else None
        kwargs = {
            "demand": required,
            "capacity": provided,
            "ratio": ratio,
            "references": ("ACI 318-14 9.3.1.1", "ACI 318-14 Table 9.3.1.1"),
            "data": {
                "span_length_in": float(span),
                "support_condition": support.value,
                "fy_modifier": 0.4 + context.steel.yield_strength / 100000.0,
                "lightweight_unit_weight_pcf": context.metadata.get("aci_lightweight_unit_weight_pcf"),
            },
        }
        if provided >= required:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult.fail_result(self.check_id, self.title, **kwargs)
