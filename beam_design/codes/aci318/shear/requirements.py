from dataclasses import dataclass
from math import sqrt

from beam_design.codes.aci318.materials.reinforcement_strength_limits import (
    ACIReinforcementApplication,
    ACIReinforcementProduct,
    ACIReinforcementUsage,
    max_permitted_design_yield_strength,
)
from beam_design.codes.aci318.sections.effective_depth import aci_effective_depth
from beam_design.codes.aci318.shear.one_way import concrete_shear_no_axial_simple, sqrt_concrete_strength_for_shear
from beam_design.codes.aci318.strength_reduction import ACIStrengthReductionCategory, fixed_phi
from beam_design.core.model import BeamDesignContext
from beam_design.core.result import CheckResult, CheckStatus


@dataclass(frozen=True)
class ACIShearSectionDimensionLimitCheck:
    check_id: str = "aci318.shear.section_dimension_limit"
    title: str = "Shear section dimension limit"
    phi: float = fixed_phi(ACIStrengthReductionCategory.SHEAR)

    def check(self, context: BeamDesignContext) -> CheckResult:
        vc = concrete_shear_no_axial_simple(
            concrete_strength_psi=context.concrete.compressive_strength,
            web_width_in=context.section.width,
            effective_depth_in=_effective_depth(context),
            lambda_factor=float(context.metadata.get("aci_lambda", 1.0)),
            allow_sqrt_fc_above_100=bool(context.metadata.get("aci_allow_sqrt_fc_shear_above_100", False)),
        )
        effective_depth = _effective_depth(context)
        limit_term = 8.0 * vc.sqrt_fc_used_psi * context.section.width * effective_depth
        capacity = self.phi * (vc.strength_lb + limit_term)
        demand = abs(context.load.shear)
        ratio = demand / capacity if capacity else None
        kwargs = {
            "demand": demand,
            "capacity": capacity,
            "ratio": ratio,
            "references": ("ACI 318-14 22.5.1.2",),
            "data": {
                "Vc": vc.strength_lb,
                "sqrt_fc_used": vc.sqrt_fc_used_psi,
                "limit_term": limit_term,
                "phi": self.phi,
                "effective_depth": effective_depth,
            },
        }
        if demand <= capacity:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult.fail_result(self.check_id, self.title, **kwargs)


@dataclass(frozen=True)
class ACIConcreteShearSqrtStrengthLimitCheck:
    check_id: str = "aci318.shear.sqrt_fc_limit"
    title: str = "Concrete shear sqrt(fc') limit"

    def check(self, context: BeamDesignContext) -> CheckResult:
        root_fc = sqrt(context.concrete.compressive_strength)
        used = sqrt_concrete_strength_for_shear(
            context.concrete.compressive_strength,
            allow_above_100=bool(context.metadata.get("aci_allow_sqrt_fc_shear_above_100", False)),
        )
        permitted_exception = bool(context.metadata.get("aci_allow_sqrt_fc_shear_above_100", False))
        kwargs = {
            "demand": root_fc,
            "capacity": 100.0 if not permitted_exception else root_fc,
            "ratio": root_fc / 100.0 if not permitted_exception else 1.0,
            "references": ("ACI 318-14 22.5.3.1", "ACI 318-14 22.5.3.2"),
            "data": {"sqrt_fc_actual": root_fc, "sqrt_fc_used": used, "exception_permitted": permitted_exception},
        }
        if root_fc <= 100.0 or permitted_exception:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult.fail_result(self.check_id, self.title, **kwargs)


@dataclass(frozen=True)
class ACIShearReinforcementYieldStrengthLimitCheck:
    check_id: str = "aci318.shear.reinforcement_yield_strength_limit"
    title: str = "Shear reinforcement yield strength limit"

    def check(self, context: BeamDesignContext) -> CheckResult:
        product = context.metadata.get("aci_shear_reinforcement_product", ACIReinforcementProduct.DEFORMED_BARS)
        try:
            limit = max_permitted_design_yield_strength(
                ACIReinforcementUsage.SHEAR,
                ACIReinforcementApplication.STIRRUPS_TIES_HOOPS,
                product,
            )
        except ValueError as exc:
            return CheckResult.fail_result(
                self.check_id,
                self.title,
                message=str(exc),
                references=("ACI 318-14 22.5.3.3", "ACI 318-14 Table 20.2.2.4a"),
            )
        fy = context.steel.yield_strength
        kwargs = {
            "demand": fy,
            "capacity": limit,
            "ratio": fy / limit if limit else None,
            "references": ("ACI 318-14 22.5.3.3", "ACI 318-14 Table 20.2.2.4a"),
            "data": {"product": product.value if hasattr(product, "value") else product},
        }
        if fy <= limit:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult.fail_result(self.check_id, self.title, **kwargs)


@dataclass(frozen=True)
class ACIWebOpeningShearEffectCheck:
    check_id: str = "aci318.shear.web_opening_effect"
    title: str = "Effect of web openings on shear"

    def check(self, context: BeamDesignContext) -> CheckResult:
        openings_present = bool(context.metadata.get("aci_web_openings_present", False))
        considered = bool(context.metadata.get("aci_web_opening_shear_effects_considered", False))
        if not openings_present:
            return CheckResult.not_applicable(self.check_id, self.title, "No web openings indicated.")
        kwargs = {
            "references": ("ACI 318-14 22.5.1.7",),
            "data": {"openings_present": openings_present, "effects_considered": considered},
        }
        if considered:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult.fail_result(self.check_id, self.title, **kwargs)


@dataclass(frozen=True)
class ACIAxialTensionCreepShrinkageShearEffectCheck:
    check_id: str = "aci318.shear.creep_shrinkage_axial_tension_effect"
    title: str = "Creep and shrinkage axial tension effect on shear"

    def check(self, context: BeamDesignContext) -> CheckResult:
        effect_present = bool(context.metadata.get("aci_restrained_creep_shrinkage_axial_tension_present", False))
        considered = bool(context.metadata.get("aci_restrained_creep_shrinkage_axial_tension_considered", False))
        if not effect_present:
            return CheckResult.not_applicable(self.check_id, self.title, "No restrained creep/shrinkage axial tension indicated.")
        kwargs = {
            "references": ("ACI 318-14 22.5.1.8",),
            "data": {"effect_present": effect_present, "effects_considered": considered},
        }
        if considered:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult.fail_result(self.check_id, self.title, **kwargs)


@dataclass(frozen=True)
class ACIVariableDepthShearEffectCheck:
    check_id: str = "aci318.shear.variable_depth_effect"
    title: str = "Variable-depth inclined flexural compression effect"

    def check(self, context: BeamDesignContext) -> CheckResult:
        variable_depth = bool(context.metadata.get("aci_variable_depth_member", False))
        considered = bool(context.metadata.get("aci_variable_depth_shear_effect_considered", False))
        if not variable_depth:
            return CheckResult.not_applicable(self.check_id, self.title, "Member is not indicated as variable depth.")
        status = CheckStatus.PASS if considered else CheckStatus.WARNING
        return CheckResult(
            check_id=self.check_id,
            title=self.title,
            status=status,
            message="ACI permits this effect to be considered; mark considered when used in Vc.",
            references=("ACI 318-14 22.5.1.9",),
            data={"variable_depth_member": variable_depth, "effects_considered": considered},
        )


def _effective_depth(context: BeamDesignContext) -> float:
    return aci_effective_depth(context)
