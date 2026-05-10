from dataclasses import dataclass

from beam_design.codes.aci318.flexure.assumptions import compression_block_depth_from_tension
from beam_design.codes.aci318.strength_reduction import (
    ACITransverseReinforcementType,
    phi_for_moment_axial,
)
from beam_design.core.model import BeamDesignContext
from beam_design.core.result import CheckResult


@dataclass(frozen=True)
class ACIFlexuralStrengthCheck:
    check_id: str = "aci318.flexure.strength"
    title: str = "Flexural strength"
    phi: float | None = None

    def check(self, context: BeamDesignContext) -> CheckResult:
        as_t = context.reinforcement.tension_area
        if as_t <= 0:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "No tension reinforcement is defined.",
            )

        mn = self.nominal_moment_capacity(context)
        phi = self.strength_reduction_factor(context)
        capacity = phi * mn
        demand = context.load.moment
        ratio = demand / capacity if capacity else None

        kwargs = {
            "demand": demand,
            "capacity": capacity,
            "ratio": ratio,
            "references": ("ACI 318 flexural strength block",),
            "data": {"Mn": mn, "phi": phi},
        }
        if demand <= capacity:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult.fail_result(self.check_id, self.title, **kwargs)

    def nominal_moment_capacity(self, context: BeamDesignContext) -> float:
        as_t = context.reinforcement.tension_area
        fy = context.steel.yield_strength
        b = context.section.width
        d = context.effective_depth

        a = compression_block_depth_from_tension(
            tension_area_in2=as_t,
            steel_stress_psi=fy,
            concrete_strength_psi=context.concrete.compressive_strength,
            compression_width_in=b,
        )
        beta1 = context.concrete.beta1_factor
        c = a / beta1
        epsilon_s = context.concrete.ultimate_compressive_strain * (d - c) / c
        fs = min(fy, epsilon_s * context.steel.modulus_of_elasticity)
        return as_t * fs * (d - a / 2)

    def strength_reduction_factor(self, context: BeamDesignContext) -> float:
        if self.phi is not None:
            return self.phi
        strain = context.metadata.get("aci_tension_strain")
        if strain is None:
            return 0.90
        transverse = context.metadata.get("aci_transverse_reinforcement_type", ACITransverseReinforcementType.OTHER)
        return phi_for_moment_axial(
            net_tensile_strain=float(strain),
            fy_psi=context.steel.yield_strength,
            es_psi=context.steel.modulus_of_elasticity,
            transverse_reinforcement=transverse,
        )
