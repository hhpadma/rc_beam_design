from dataclasses import dataclass

from beam_design.core.model import BeamDesignContext
from beam_design.core.result import CheckResult


@dataclass(frozen=True)
class ACIDevelopmentLengthCheck:
    check_id: str = "aci318.bond.development_length"
    title: str = "Development length"
    top_cast_factor: float = 1.0
    epoxy_factor: float = 1.0

    def check(self, context: BeamDesignContext) -> CheckResult:
        if context.reinforcement.tension_bar is None:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "No tension reinforcement is defined.",
            )

        required = self.required_development_length(context)
        provided = context.metadata.get("development_length_provided")
        if provided is None:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "No provided development length is defined in context metadata.",
            )

        ratio = required / provided if provided else None
        kwargs = {
            "demand": required,
            "capacity": provided,
            "ratio": ratio,
            "references": ("ACI 318 development length",),
        }
        if provided >= required:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult.fail_result(self.check_id, self.title, **kwargs)

    def required_development_length(self, context: BeamDesignContext) -> float:
        fy = context.steel.yield_strength
        fc = context.concrete.compressive_strength
        db = context.reinforcement.tension_bar_diameter
        factor = self.top_cast_factor * self.epoxy_factor
        divisor = 20.0 if db > 0.9 else 25.0
        return fy * db * factor / ((fc**0.5) * divisor)
