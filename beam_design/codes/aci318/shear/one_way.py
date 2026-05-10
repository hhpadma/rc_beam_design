from dataclasses import dataclass
from enum import Enum
from math import sqrt


class ACIConcreteShearEquation(Enum):
    NO_AXIAL_SIMPLE = "ACI 318-14 22.5.5.1"
    NO_AXIAL_DETAILED_A = "ACI 318-14 Table 22.5.5.1(a)"
    NO_AXIAL_DETAILED_B = "ACI 318-14 Table 22.5.5.1(b)"
    NO_AXIAL_DETAILED_C = "ACI 318-14 Table 22.5.5.1(c)"
    AXIAL_COMPRESSION_SIMPLE = "ACI 318-14 22.5.6.1"
    AXIAL_COMPRESSION_DETAILED_A = "ACI 318-14 Table 22.5.6.1(a)"
    AXIAL_COMPRESSION_DETAILED_B = "ACI 318-14 Table 22.5.6.1(b)"
    AXIAL_TENSION = "ACI 318-14 22.5.7.1"


@dataclass(frozen=True)
class ACIConcreteShearStrength:
    equation: ACIConcreteShearEquation
    concrete_strength_psi: float
    lambda_factor: float
    web_width_in: float
    effective_depth_in: float
    strength_lb: float
    terms_lb: dict[str, float]
    sqrt_fc_used_psi: float

    @property
    def strength_kip(self) -> float:
        return self.strength_lb / 1000.0


def longitudinal_reinforcement_ratio(tension_steel_area_in2: float, web_width_in: float, effective_depth_in: float) -> float:
    if tension_steel_area_in2 < 0:
        raise ValueError("Tension steel area cannot be negative.")
    _validate_positive(web_width_in, "Web width")
    _validate_positive(effective_depth_in, "Effective depth")
    return tension_steel_area_in2 / (web_width_in * effective_depth_in)


def concrete_shear_no_axial_simple(
    concrete_strength_psi: float,
    web_width_in: float,
    effective_depth_in: float,
    *,
    lambda_factor: float = 1.0,
    allow_sqrt_fc_above_100: bool = False,
) -> ACIConcreteShearStrength:
    """ACI 318-14 22.5.5.1: Vc = 2 lambda sqrt(fc') bw d."""

    _validate_base_inputs(concrete_strength_psi, web_width_in, effective_depth_in, lambda_factor)
    root_fc = sqrt_concrete_strength_for_shear(concrete_strength_psi, allow_above_100=allow_sqrt_fc_above_100)
    vc = 2.0 * lambda_factor * root_fc * web_width_in * effective_depth_in
    return ACIConcreteShearStrength(
        equation=ACIConcreteShearEquation.NO_AXIAL_SIMPLE,
        concrete_strength_psi=concrete_strength_psi,
        lambda_factor=lambda_factor,
        web_width_in=web_width_in,
        effective_depth_in=effective_depth_in,
        strength_lb=vc,
        terms_lb={"22.5.5.1": vc},
        sqrt_fc_used_psi=root_fc,
    )


def concrete_shear_no_axial_detailed(
    concrete_strength_psi: float,
    web_width_in: float,
    effective_depth_in: float,
    tension_steel_area_in2: float,
    factored_shear_lb: float,
    factored_moment_lb_in: float,
    *,
    lambda_factor: float = 1.0,
    allow_sqrt_fc_above_100: bool = False,
) -> ACIConcreteShearStrength:
    """ACI 318-14 Table 22.5.5.1 detailed Vc for nonprestressed members without axial force."""

    _validate_base_inputs(concrete_strength_psi, web_width_in, effective_depth_in, lambda_factor)
    _validate_nonnegative(factored_shear_lb, "Factored shear")
    _validate_positive(factored_moment_lb_in, "Factored moment")
    rho_w = longitudinal_reinforcement_ratio(tension_steel_area_in2, web_width_in, effective_depth_in)
    root_fc = sqrt_concrete_strength_for_shear(concrete_strength_psi, allow_above_100=allow_sqrt_fc_above_100)
    base_area = web_width_in * effective_depth_in
    vu_d_over_mu = factored_shear_lb * effective_depth_in / factored_moment_lb_in
    term_a = (1.9 * lambda_factor * root_fc + 2500.0 * rho_w * vu_d_over_mu) * base_area
    term_b = (1.9 * lambda_factor * root_fc + 2500.0 * rho_w) * base_area
    term_c = 3.5 * lambda_factor * root_fc * base_area
    terms = {
        ACIConcreteShearEquation.NO_AXIAL_DETAILED_A.value: term_a,
        ACIConcreteShearEquation.NO_AXIAL_DETAILED_B.value: term_b,
        ACIConcreteShearEquation.NO_AXIAL_DETAILED_C.value: term_c,
    }
    equation = min(
        (
            ACIConcreteShearEquation.NO_AXIAL_DETAILED_A,
            ACIConcreteShearEquation.NO_AXIAL_DETAILED_B,
            ACIConcreteShearEquation.NO_AXIAL_DETAILED_C,
        ),
        key=lambda item: terms[item.value],
    )
    return ACIConcreteShearStrength(
        equation=equation,
        concrete_strength_psi=concrete_strength_psi,
        lambda_factor=lambda_factor,
        web_width_in=web_width_in,
        effective_depth_in=effective_depth_in,
        strength_lb=terms[equation.value],
        terms_lb=terms,
        sqrt_fc_used_psi=root_fc,
    )


def concrete_shear_axial_compression_simple(
    concrete_strength_psi: float,
    web_width_in: float,
    effective_depth_in: float,
    gross_area_in2: float,
    axial_compression_lb: float,
    *,
    lambda_factor: float = 1.0,
    allow_sqrt_fc_above_100: bool = False,
) -> ACIConcreteShearStrength:
    """ACI 318-14 22.5.6.1. Axial force is positive for compression."""

    _validate_base_inputs(concrete_strength_psi, web_width_in, effective_depth_in, lambda_factor)
    _validate_positive(gross_area_in2, "Gross area")
    _validate_nonnegative(axial_compression_lb, "Axial compression")
    multiplier = 1.0 + axial_compression_lb / (2000.0 * gross_area_in2)
    root_fc = sqrt_concrete_strength_for_shear(concrete_strength_psi, allow_above_100=allow_sqrt_fc_above_100)
    vc = 2.0 * multiplier * lambda_factor * root_fc * web_width_in * effective_depth_in
    return ACIConcreteShearStrength(
        equation=ACIConcreteShearEquation.AXIAL_COMPRESSION_SIMPLE,
        concrete_strength_psi=concrete_strength_psi,
        lambda_factor=lambda_factor,
        web_width_in=web_width_in,
        effective_depth_in=effective_depth_in,
        strength_lb=vc,
        terms_lb={"22.5.6.1": vc},
        sqrt_fc_used_psi=root_fc,
    )


def concrete_shear_axial_compression_detailed(
    concrete_strength_psi: float,
    web_width_in: float,
    effective_depth_in: float,
    gross_area_in2: float,
    total_depth_in: float,
    tension_steel_area_in2: float,
    factored_shear_lb: float,
    factored_moment_lb_in: float,
    axial_compression_lb: float,
    *,
    lambda_factor: float = 1.0,
    allow_sqrt_fc_above_100: bool = False,
) -> ACIConcreteShearStrength:
    """ACI 318-14 Table 22.5.6.1 detailed Vc for members with axial compression."""

    _validate_base_inputs(concrete_strength_psi, web_width_in, effective_depth_in, lambda_factor)
    _validate_positive(gross_area_in2, "Gross area")
    _validate_positive(total_depth_in, "Total depth")
    _validate_nonnegative(factored_shear_lb, "Factored shear")
    _validate_positive(factored_moment_lb_in, "Factored moment")
    _validate_nonnegative(axial_compression_lb, "Axial compression")
    rho_w = longitudinal_reinforcement_ratio(tension_steel_area_in2, web_width_in, effective_depth_in)
    root_fc = sqrt_concrete_strength_for_shear(concrete_strength_psi, allow_above_100=allow_sqrt_fc_above_100)
    base_area = web_width_in * effective_depth_in
    terms: dict[str, float] = {}

    denominator = factored_moment_lb_in - axial_compression_lb * (4.0 * total_depth_in - effective_depth_in) / 8.0
    if denominator > 0:
        term_a = (
            1.9 * lambda_factor * root_fc
            + 2500.0 * rho_w * factored_shear_lb * effective_depth_in / denominator
        ) * base_area
        terms[ACIConcreteShearEquation.AXIAL_COMPRESSION_DETAILED_A.value] = term_a

    compression_factor = 1.0 + axial_compression_lb / (500.0 * gross_area_in2)
    if compression_factor < 0:
        raise ValueError("Axial compression factor cannot be negative.")
    term_b = 3.5 * lambda_factor * root_fc * base_area * sqrt(compression_factor)
    terms[ACIConcreteShearEquation.AXIAL_COMPRESSION_DETAILED_B.value] = term_b

    equation = min(
        (ACIConcreteShearEquation(value) for value in terms),
        key=lambda item: terms[item.value],
    )
    return ACIConcreteShearStrength(
        equation=equation,
        concrete_strength_psi=concrete_strength_psi,
        lambda_factor=lambda_factor,
        web_width_in=web_width_in,
        effective_depth_in=effective_depth_in,
        strength_lb=terms[equation.value],
        terms_lb=terms,
        sqrt_fc_used_psi=root_fc,
    )


def concrete_shear_axial_tension(
    concrete_strength_psi: float,
    web_width_in: float,
    effective_depth_in: float,
    gross_area_in2: float,
    axial_tension_lb: float,
    *,
    lambda_factor: float = 1.0,
    allow_sqrt_fc_above_100: bool = False,
) -> ACIConcreteShearStrength:
    """ACI 318-14 22.5.7.1. Axial tension is entered as a positive magnitude."""

    _validate_base_inputs(concrete_strength_psi, web_width_in, effective_depth_in, lambda_factor)
    _validate_positive(gross_area_in2, "Gross area")
    _validate_nonnegative(axial_tension_lb, "Axial tension")
    signed_axial = -axial_tension_lb
    multiplier = 1.0 + signed_axial / (500.0 * gross_area_in2)
    root_fc = sqrt_concrete_strength_for_shear(concrete_strength_psi, allow_above_100=allow_sqrt_fc_above_100)
    vc = max(2.0 * multiplier * lambda_factor * root_fc * web_width_in * effective_depth_in, 0.0)
    return ACIConcreteShearStrength(
        equation=ACIConcreteShearEquation.AXIAL_TENSION,
        concrete_strength_psi=concrete_strength_psi,
        lambda_factor=lambda_factor,
        web_width_in=web_width_in,
        effective_depth_in=effective_depth_in,
        strength_lb=vc,
        terms_lb={"22.5.7.1": vc},
        sqrt_fc_used_psi=root_fc,
    )


def sqrt_concrete_strength_for_shear(concrete_strength_psi: float, *, allow_above_100: bool = False) -> float:
    _validate_positive(concrete_strength_psi, "Concrete strength")
    root_fc = sqrt(concrete_strength_psi)
    if allow_above_100:
        return root_fc
    return min(root_fc, 100.0)


def _validate_base_inputs(
    concrete_strength_psi: float,
    web_width_in: float,
    effective_depth_in: float,
    lambda_factor: float,
) -> None:
    _validate_positive(concrete_strength_psi, "Concrete strength")
    _validate_positive(web_width_in, "Web width")
    _validate_positive(effective_depth_in, "Effective depth")
    _validate_positive(lambda_factor, "Lambda factor")


def _validate_positive(value: float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive.")


def _validate_nonnegative(value: float, name: str) -> None:
    if value < 0:
        raise ValueError(f"{name} cannot be negative.")
