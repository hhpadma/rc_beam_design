from dataclasses import dataclass

from beam_design.core.model import BeamDesignContext
from beam_design.core.result import CheckResult


@dataclass(frozen=True)
class ACIDeflectionRequirementCheck:
    check_id: str = "aci318.geometry.deflection_requirement"
    title: str = "Calculated deflection requirement"

    def check(self, context: BeamDesignContext) -> CheckResult:
        if bool(context.metadata.get("aci_minimum_depth_satisfied", False)):
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "Minimum beam depth is satisfied; calculated deflection check is not required for this provision.",
            )

        calculated = context.metadata.get("aci_calculated_deflection_in")
        limit = context.metadata.get("aci_deflection_limit_in")
        if calculated is None or limit is None:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "Provide calculated deflection and deflection limit when minimum depth is not satisfied.",
            )

        calculated = float(calculated)
        limit = float(limit)
        ratio = calculated / limit if limit else None
        kwargs = {
            "demand": calculated,
            "capacity": limit,
            "ratio": ratio,
            "references": ("ACI 318-14 9.3.2.1", "ACI 318-14 24.2"),
        }
        if calculated <= limit:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult.fail_result(self.check_id, self.title, **kwargs)
