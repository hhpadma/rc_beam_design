from dataclasses import dataclass

from beam_design.core.model import BeamDesignContext
from beam_design.core.result import CheckResult


@dataclass(frozen=True)
class ACITensionStrainLimitCheck:
    check_id: str = "aci318.flexure.tension_strain_limit"
    title: str = "Reinforcement tension strain limit"
    minimum_tension_strain: float = 0.004

    def check(self, context: BeamDesignContext) -> CheckResult:
        gross_area = context.section.area
        axial_limit = 0.10 * context.concrete.compressive_strength * gross_area
        axial_load = context.metadata.get("aci_axial_load_pu_lb", context.load.axial)
        if float(axial_load) >= axial_limit:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "ACI 9.3.3.1 applies only when Pu < 0.10fc'Ag.",
            )

        strain = context.metadata.get("aci_tension_strain")
        if strain is None:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "Tension strain is not available yet; this will be calculated during flexural design.",
            )

        strain = float(strain)
        kwargs = {
            "demand": self.minimum_tension_strain,
            "capacity": strain,
            "ratio": self.minimum_tension_strain / strain if strain else None,
            "references": ("ACI 318-14 9.3.3.1",),
            "data": {
                "axial_load_pu_lb": float(axial_load),
                "axial_limit_lb": axial_limit,
                "tension_strain": strain,
            },
        }
        if strain >= self.minimum_tension_strain:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult.fail_result(self.check_id, self.title, **kwargs)
