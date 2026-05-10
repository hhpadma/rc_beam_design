from dataclasses import dataclass


@dataclass(frozen=True)
class ACIMinimumFlexuralReinforcement:
    concrete_strength_psi: float
    steel_yield_psi: float
    web_width_in: float
    effective_depth_in: float
    concrete_term_area_in2: float
    steel_term_area_in2: float
    required_area_in2: float
    governing_equation: str


def minimum_flexural_reinforcement_area(
    concrete_strength_psi: float,
    steel_yield_psi: float,
    web_width_in: float,
    effective_depth_in: float,
) -> ACIMinimumFlexuralReinforcement:
    """ACI 318-14 9.6.1.2 minimum tension reinforcement for nonprestressed beams."""

    if concrete_strength_psi <= 0:
        raise ValueError("Concrete strength must be positive.")
    if steel_yield_psi <= 0:
        raise ValueError("Steel yield strength must be positive.")
    if web_width_in <= 0:
        raise ValueError("Web width must be positive.")
    if effective_depth_in <= 0:
        raise ValueError("Effective depth must be positive.")

    concrete_term = 3.0 * (concrete_strength_psi**0.5) * web_width_in * effective_depth_in / steel_yield_psi
    steel_term = 200.0 * web_width_in * effective_depth_in / steel_yield_psi
    if concrete_term >= steel_term:
        required = concrete_term
        governing = "ACI 318-14 9.6.1.2a"
    else:
        required = steel_term
        governing = "ACI 318-14 9.6.1.2b"

    return ACIMinimumFlexuralReinforcement(
        concrete_strength_psi=concrete_strength_psi,
        steel_yield_psi=steel_yield_psi,
        web_width_in=web_width_in,
        effective_depth_in=effective_depth_in,
        concrete_term_area_in2=concrete_term,
        steel_term_area_in2=steel_term,
        required_area_in2=required,
        governing_equation=governing,
    )
