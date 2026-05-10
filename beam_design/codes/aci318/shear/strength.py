from dataclasses import dataclass

from beam_design.codes.aci318.shear.one_way import concrete_shear_no_axial_simple
from beam_design.codes.aci318.shear.reinforcement import rectangular_tie_effective_area, transverse_reinforcement_shear_strength
from beam_design.codes.aci318.materials.reinforcement_strength_limits import (
    ACIReinforcementApplication,
    ACIReinforcementProduct,
    ACIReinforcementUsage,
    max_permitted_design_yield_strength,
)
from beam_design.codes.aci318.strength_reduction import ACIStrengthReductionCategory, fixed_phi
from beam_design.core.model import BeamDesignContext
from beam_design.core.result import CheckResult


@dataclass(frozen=True)
class ACIShearStrengthCheck:
    check_id: str = "aci318.shear.strength"
    title: str = "Shear strength"
    phi: float = fixed_phi(ACIStrengthReductionCategory.SHEAR)

    def check(self, context: BeamDesignContext) -> CheckResult:
        vc = self.concrete_shear_capacity(context)
        vs = self.stirrup_shear_capacity(context)
        capacity = self.phi * (vc + vs)
        demand = context.load.shear
        ratio = demand / capacity if capacity else None
        kwargs = {
            "demand": demand,
            "capacity": capacity,
            "ratio": ratio,
            "references": ("ACI 318 shear strength",),
            "data": {"Vc": vc, "Vs": vs, "phi": self.phi},
        }
        if demand <= capacity:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult.fail_result(self.check_id, self.title, **kwargs)

    def concrete_shear_capacity(self, context: BeamDesignContext) -> float:
        return concrete_shear_no_axial_simple(
            concrete_strength_psi=context.concrete.compressive_strength,
            web_width_in=context.section.width,
            effective_depth_in=context.effective_depth,
            lambda_factor=float(context.metadata.get("aci_lambda", 1.0)),
            allow_sqrt_fc_above_100=bool(context.metadata.get("aci_allow_sqrt_fc_shear_above_100", False)),
        ).strength_lb

    def stirrup_shear_capacity(self, context: BeamDesignContext) -> float:
        position = float(context.metadata.get("transverse_position", 0.0))
        spacing = context.reinforcement.stirrup_spacing_at(position)
        if not spacing:
            return 0.0
        av = rectangular_tie_effective_area(
            single_leg_area_in2=context.reinforcement.stirrup_area_at(position),
            legs=context.reinforcement.stirrup_legs_at(position),
        )
        product = context.metadata.get("aci_shear_reinforcement_product", ACIReinforcementProduct.DEFORMED_BARS)
        max_fyt = max_permitted_design_yield_strength(
            ACIReinforcementUsage.SHEAR,
            ACIReinforcementApplication.STIRRUPS_TIES_HOOPS,
            product,
        )
        fyt = min(context.steel.yield_strength, max_fyt)
        return transverse_reinforcement_shear_strength(
            area_in2=av,
            yield_strength_psi=fyt,
            effective_depth_in=context.effective_depth,
            spacing_in=spacing,
        )
