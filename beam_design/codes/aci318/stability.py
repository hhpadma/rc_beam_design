from dataclasses import dataclass

from beam_design.core.model import BeamDesignContext
from beam_design.core.result import CheckResult


def lateral_bracing_spacing_limit(least_compression_width_in: float) -> float:
    if least_compression_width_in <= 0:
        raise ValueError("Least compression flange or face width must be positive.")
    return 50.0 * least_compression_width_in


@dataclass(frozen=True)
class ACILateralStabilityCheck:
    """ACI 318-14 9.2.3 lateral stability check for unbraced beams."""

    check_id: str = "aci318.beam_stability.lateral_bracing"
    title: str = "Beam lateral stability"

    def check(self, context: BeamDesignContext) -> CheckResult:
        continuously_braced = context.metadata.get("aci_continuously_laterally_braced")
        if continuously_braced is True:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "Beam is continuously laterally braced.",
            )

        spacing = context.metadata.get("aci_lateral_bracing_spacing_in")
        width = context.metadata.get("aci_least_compression_width_in")
        if spacing is None or width is None:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "Provide aci_lateral_bracing_spacing_in and aci_least_compression_width_in for unbraced beams.",
            )

        spacing = float(spacing)
        width = float(width)
        limit = lateral_bracing_spacing_limit(width)
        eccentric_loads = bool(context.metadata.get("aci_eccentric_loads", False))
        eccentric_effects_accounted = bool(context.metadata.get("aci_eccentric_loads_accounted_for", not eccentric_loads))
        ratio = spacing / limit if limit else None
        data = {
            "lateral_bracing_spacing_in": spacing,
            "least_compression_width_in": width,
            "spacing_limit_in": limit,
            "eccentric_loads": eccentric_loads,
            "eccentric_loads_accounted_for": eccentric_effects_accounted,
        }
        kwargs = {
            "demand": spacing,
            "capacity": limit,
            "ratio": ratio,
            "references": ("ACI 318-14 9.2.3.1",),
            "data": data,
        }

        if spacing > limit:
            return CheckResult.fail_result(
                self.check_id,
                self.title,
                message="Lateral bracing spacing exceeds 50 times the least compression flange or face width.",
                **kwargs,
            )
        if eccentric_loads and not eccentric_effects_accounted:
            return CheckResult.fail_result(
                self.check_id,
                self.title,
                message="Effects of eccentric loads must be accounted for in lateral bracing spacing.",
                **kwargs,
            )

        message = "Lateral bracing spacing is within the ACI 50b limit."
        if eccentric_loads:
            message += " Eccentric load effects were marked as accounted for."
        return CheckResult.pass_result(self.check_id, self.title, message=message, **kwargs)
