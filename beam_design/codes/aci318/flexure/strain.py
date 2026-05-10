from dataclasses import dataclass

from beam_design.codes.aci318.flexure.assumptions import beta1_factor, compression_block_depth_from_tension
from beam_design.codes.aci318.strength_reduction import (
    ACIStrainControlRegion,
    ACITransverseReinforcementType,
    phi_for_moment_axial,
    strain_control_region,
)


@dataclass(frozen=True)
class ACIFlexuralStrainResult:
    provided_area_in2: float
    compression_width_in: float
    effective_depth_in: float
    stress_block_depth_in: float
    neutral_axis_depth_in: float
    net_tensile_strain: float
    phi: float
    strain_region: ACIStrainControlRegion
    tension_controlled_limit: float = 0.005
    minimum_beam_strain: float = 0.004

    @property
    def is_tension_controlled(self) -> bool:
        return self.strain_region == ACIStrainControlRegion.TENSION_CONTROLLED

    @property
    def satisfies_minimum_beam_strain(self) -> bool:
        return self.net_tensile_strain >= self.minimum_beam_strain

    @property
    def supports_phi_0_90_assumption(self) -> bool:
        return self.net_tensile_strain >= self.tension_controlled_limit and self.phi == 0.90


def net_tensile_strain(
    ultimate_concrete_strain: float,
    effective_depth_in: float,
    neutral_axis_depth_in: float,
) -> float:
    if ultimate_concrete_strain <= 0:
        raise ValueError("Ultimate concrete strain must be positive.")
    if effective_depth_in <= 0:
        raise ValueError("Effective depth must be positive.")
    if neutral_axis_depth_in <= 0:
        raise ValueError("Neutral axis depth must be positive.")
    return ultimate_concrete_strain * (effective_depth_in - neutral_axis_depth_in) / neutral_axis_depth_in


def evaluate_flexural_strain(
    provided_area_in2: float,
    concrete_strength_psi: float,
    steel_yield_psi: float,
    steel_modulus_psi: float,
    compression_width_in: float,
    effective_depth_in: float,
    ultimate_concrete_strain: float = 0.003,
    transverse_reinforcement: ACITransverseReinforcementType | str = ACITransverseReinforcementType.OTHER,
) -> ACIFlexuralStrainResult:
    if provided_area_in2 < 0:
        raise ValueError("Provided steel area cannot be negative.")
    a = compression_block_depth_from_tension(
        tension_area_in2=provided_area_in2,
        steel_stress_psi=steel_yield_psi,
        concrete_strength_psi=concrete_strength_psi,
        compression_width_in=compression_width_in,
    )
    beta1 = beta1_factor(concrete_strength_psi)
    c = a / beta1
    strain = net_tensile_strain(ultimate_concrete_strain, effective_depth_in, c)
    phi = phi_for_moment_axial(
        net_tensile_strain=strain,
        fy_psi=steel_yield_psi,
        es_psi=steel_modulus_psi,
        transverse_reinforcement=transverse_reinforcement,
    )
    return ACIFlexuralStrainResult(
        provided_area_in2=provided_area_in2,
        compression_width_in=compression_width_in,
        effective_depth_in=effective_depth_in,
        stress_block_depth_in=a,
        neutral_axis_depth_in=c,
        net_tensile_strain=strain,
        phi=phi,
        strain_region=strain_control_region(strain, steel_yield_psi, steel_modulus_psi),
    )
