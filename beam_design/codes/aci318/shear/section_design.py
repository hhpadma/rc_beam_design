from dataclasses import dataclass

from beam_design.codes.aci318.shear.one_way import ACIConcreteShearStrength, concrete_shear_no_axial_simple
from beam_design.codes.aci318.shear.reinforcement import (
    ACIShearMinimumReinforcementTrigger,
    minimum_shear_reinforcement_trigger,
    required_shear_reinforcement_strength,
)
from beam_design.codes.aci318.strength_reduction import ACIStrengthReductionCategory, fixed_phi


@dataclass(frozen=True)
class ACIOneWayShearDesignSection:
    factored_shear_lb: float
    concrete_shear: ACIConcreteShearStrength
    phi: float
    concrete_design_strength_lb: float
    required_nominal_shear_strength_lb: float
    required_stirrup_shear_strength_lb: float
    minimum_reinforcement: ACIShearMinimumReinforcementTrigger

    @property
    def factored_shear_kip(self) -> float:
        return self.factored_shear_lb / 1000.0

    @property
    def concrete_design_strength_kip(self) -> float:
        return self.concrete_design_strength_lb / 1000.0

    @property
    def required_stirrup_shear_strength_kip(self) -> float:
        return self.required_stirrup_shear_strength_lb / 1000.0

    @property
    def shear_reinforcement_required(self) -> bool:
        return self.required_stirrup_shear_strength_lb > 0

    @property
    def minimum_shear_reinforcement_required(self) -> bool:
        return self.minimum_reinforcement.minimum_reinforcement_required

    @property
    def concrete_strength_ratio(self) -> float | None:
        if self.concrete_design_strength_lb <= 0:
            return None
        return self.factored_shear_lb / self.concrete_design_strength_lb


def evaluate_one_way_shear_without_axial(
    factored_shear_lb: float,
    concrete_strength_psi: float,
    web_width_in: float,
    effective_depth_in: float,
    *,
    lambda_factor: float = 1.0,
    phi: float = fixed_phi(ACIStrengthReductionCategory.SHEAR),
    allow_sqrt_fc_above_100: bool = False,
    minimum_reinforcement_exception_applies: bool = False,
) -> ACIOneWayShearDesignSection:
    """Starting ACI shear design step using 22.5.5.1 for Vc."""

    if factored_shear_lb < 0:
        raise ValueError("Factored shear must be entered as a nonnegative magnitude.")
    if phi <= 0:
        raise ValueError("Strength reduction factor must be positive.")

    concrete_shear = concrete_shear_no_axial_simple(
        concrete_strength_psi=concrete_strength_psi,
        web_width_in=web_width_in,
        effective_depth_in=effective_depth_in,
        lambda_factor=lambda_factor,
        allow_sqrt_fc_above_100=allow_sqrt_fc_above_100,
    )
    concrete_design_strength = phi * concrete_shear.strength_lb
    required_nominal = factored_shear_lb / phi
    required_vs = required_shear_reinforcement_strength(
        factored_shear_lb=factored_shear_lb,
        phi=phi,
        concrete_shear_strength_lb=concrete_shear.strength_lb,
    ).required_shear_reinforcement_strength_lb
    minimum_reinforcement = minimum_shear_reinforcement_trigger(
        factored_shear_lb=factored_shear_lb,
        phi=phi,
        concrete_shear_strength_lb=concrete_shear.strength_lb,
        exception_applies=minimum_reinforcement_exception_applies,
    )
    return ACIOneWayShearDesignSection(
        factored_shear_lb=factored_shear_lb,
        concrete_shear=concrete_shear,
        phi=phi,
        concrete_design_strength_lb=concrete_design_strength,
        required_nominal_shear_strength_lb=required_nominal,
        required_stirrup_shear_strength_lb=required_vs,
        minimum_reinforcement=minimum_reinforcement,
    )
