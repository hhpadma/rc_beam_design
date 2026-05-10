from dataclasses import dataclass
from math import cos, radians, sin

from beam_design.codes.aci318.shear.one_way import sqrt_concrete_strength_for_shear


@dataclass(frozen=True)
class ACIRequiredShearReinforcement:
    factored_shear_lb: float
    phi: float
    concrete_shear_strength_lb: float
    required_shear_reinforcement_strength_lb: float

    @property
    def shear_reinforcement_required(self) -> bool:
        return self.required_shear_reinforcement_strength_lb > 0

    @property
    def required_shear_reinforcement_strength_kip(self) -> float:
        return self.required_shear_reinforcement_strength_lb / 1000.0


@dataclass(frozen=True)
class ACIShearMinimumReinforcementTrigger:
    """ACI 318-14 9.6.3.1 trigger for minimum shear reinforcement."""

    factored_shear_lb: float
    phi: float
    concrete_shear_strength_lb: float
    threshold_lb: float
    minimum_reinforcement_required: bool
    exception_used: bool

    @property
    def threshold_kip(self) -> float:
        return self.threshold_lb / 1000.0


@dataclass(frozen=True)
class ACIShearSpacingLimit:
    """ACI 318-14 Table 9.7.6.2.2 for nonprestressed RC beams."""

    required_shear_reinforcement_strength_lb: float
    threshold_lb: float
    effective_depth_in: float
    max_spacing_in: float
    limit_expression: str

    @property
    def threshold_kip(self) -> float:
        return self.threshold_lb / 1000.0

    @property
    def high_shear_branch(self) -> bool:
        return self.required_shear_reinforcement_strength_lb > self.threshold_lb


@dataclass(frozen=True)
class ACIPerpendicularStirrupSpacingDesign:
    """Trial spacing for vertical stirrups against ACI 22.5.10 and 9.7.6.2.2."""

    required_shear_reinforcement_strength_lb: float
    area_in2: float
    yield_strength_psi: float
    effective_depth_in: float
    calculated_spacing_in: float | None
    spacing_limit: ACIShearSpacingLimit

    @property
    def shear_reinforcement_required(self) -> bool:
        return self.required_shear_reinforcement_strength_lb > 0

    def selected_spacing_satisfies_limit(self, spacing_in: float) -> bool:
        if spacing_in <= 0:
            raise ValueError("Selected spacing must be positive.")
        return spacing_in <= self.spacing_limit.max_spacing_in


def required_shear_reinforcement_strength(
    factored_shear_lb: float,
    phi: float,
    concrete_shear_strength_lb: float,
) -> ACIRequiredShearReinforcement:
    """ACI 318-14 22.5.10.1: Vs >= Vu / phi - Vc."""

    if factored_shear_lb < 0:
        raise ValueError("Factored shear must be entered as a nonnegative magnitude.")
    if phi <= 0:
        raise ValueError("Strength reduction factor must be positive.")
    if concrete_shear_strength_lb < 0:
        raise ValueError("Concrete shear strength cannot be negative.")

    required = max(factored_shear_lb / phi - concrete_shear_strength_lb, 0.0)
    return ACIRequiredShearReinforcement(
        factored_shear_lb=factored_shear_lb,
        phi=phi,
        concrete_shear_strength_lb=concrete_shear_strength_lb,
        required_shear_reinforcement_strength_lb=required,
    )


def minimum_shear_reinforcement_trigger(
    factored_shear_lb: float,
    phi: float,
    concrete_shear_strength_lb: float,
    *,
    exception_applies: bool = False,
) -> ACIShearMinimumReinforcementTrigger:
    """ACI 318-14 9.6.3.1 trigger.

    By default no Table 9.6.3.1 exception is assumed. If a caller has
    explicitly established a beam-specific exception, the trigger shifts to
    Vu > phi Vc.
    """

    if factored_shear_lb < 0:
        raise ValueError("Factored shear must be entered as a nonnegative magnitude.")
    if phi <= 0:
        raise ValueError("Strength reduction factor must be positive.")
    if concrete_shear_strength_lb < 0:
        raise ValueError("Concrete shear strength cannot be negative.")

    phi_vc = phi * concrete_shear_strength_lb
    threshold = phi_vc if exception_applies else 0.5 * phi_vc
    return ACIShearMinimumReinforcementTrigger(
        factored_shear_lb=factored_shear_lb,
        phi=phi,
        concrete_shear_strength_lb=concrete_shear_strength_lb,
        threshold_lb=threshold,
        minimum_reinforcement_required=factored_shear_lb > threshold,
        exception_used=exception_applies,
    )


def rectangular_tie_effective_area(single_leg_area_in2: float, legs: int) -> float:
    """ACI 318-14 22.5.10.5.5: Av is effective area of all legs within spacing s."""

    if single_leg_area_in2 < 0:
        raise ValueError("Single leg area cannot be negative.")
    if legs <= 0:
        raise ValueError("Number of legs must be positive.")
    return single_leg_area_in2 * legs


def circular_tie_or_spiral_effective_area(single_bar_area_in2: float) -> float:
    """ACI 318-14 22.5.10.5.6: Av is two times the area of the bar or wire."""

    if single_bar_area_in2 < 0:
        raise ValueError("Single bar area cannot be negative.")
    return 2.0 * single_bar_area_in2


def transverse_reinforcement_shear_strength(
    area_in2: float,
    yield_strength_psi: float,
    effective_depth_in: float,
    spacing_in: float,
) -> float:
    """ACI 318-14 22.5.10.5.3 for perpendicular transverse reinforcement."""

    _validate_transverse_inputs(area_in2, yield_strength_psi, effective_depth_in, spacing_in)
    return area_in2 * yield_strength_psi * effective_depth_in / spacing_in


def perpendicular_stirrup_spacing_for_required_vs(
    area_in2: float,
    yield_strength_psi: float,
    effective_depth_in: float,
    required_shear_reinforcement_strength_lb: float,
) -> float | None:
    """Invert ACI 318-14 22.5.10.5.3 to get the largest spacing for required Vs."""

    if required_shear_reinforcement_strength_lb < 0:
        raise ValueError("Required shear reinforcement strength cannot be negative.")
    if area_in2 < 0:
        raise ValueError("Area cannot be negative.")
    if yield_strength_psi <= 0 or effective_depth_in <= 0:
        raise ValueError("Yield strength and effective depth must be positive.")
    if required_shear_reinforcement_strength_lb == 0:
        return None
    return area_in2 * yield_strength_psi * effective_depth_in / required_shear_reinforcement_strength_lb


def inclined_stirrup_shear_strength(
    area_in2: float,
    yield_strength_psi: float,
    effective_depth_in: float,
    spacing_in: float,
    angle_degrees: float,
) -> float:
    """ACI 318-14 22.5.10.5.4 for inclined stirrups."""

    _validate_transverse_inputs(area_in2, yield_strength_psi, effective_depth_in, spacing_in)
    if angle_degrees < 45.0 or angle_degrees >= 180.0:
        raise ValueError("Inclined stirrup angle must be at least 45 degrees and less than 180 degrees.")
    angle = radians(angle_degrees)
    return area_in2 * yield_strength_psi * (sin(angle) + cos(angle)) * effective_depth_in / spacing_in


def max_shear_reinforcement_spacing_nonprestressed_beam(
    required_shear_reinforcement_strength_lb: float,
    concrete_strength_psi: float,
    web_width_in: float,
    effective_depth_in: float,
    *,
    allow_sqrt_fc_above_100: bool = False,
) -> ACIShearSpacingLimit:
    """ACI 318-14 Table 9.7.6.2.2 for nonprestressed RC beams only."""

    if required_shear_reinforcement_strength_lb < 0:
        raise ValueError("Required shear reinforcement strength cannot be negative.")
    if web_width_in <= 0 or effective_depth_in <= 0:
        raise ValueError("Web width and effective depth must be positive.")

    sqrt_fc = sqrt_concrete_strength_for_shear(
        concrete_strength_psi,
        allow_above_100=allow_sqrt_fc_above_100,
    )
    threshold = 4.0 * sqrt_fc * web_width_in * effective_depth_in
    if required_shear_reinforcement_strength_lb <= threshold:
        max_spacing = min(effective_depth_in / 2.0, 24.0)
        expression = "lesser of d/2 and 24 in."
    else:
        max_spacing = min(effective_depth_in / 4.0, 12.0)
        expression = "lesser of d/4 and 12 in."

    return ACIShearSpacingLimit(
        required_shear_reinforcement_strength_lb=required_shear_reinforcement_strength_lb,
        threshold_lb=threshold,
        effective_depth_in=effective_depth_in,
        max_spacing_in=max_spacing,
        limit_expression=expression,
    )


def design_perpendicular_stirrup_spacing(
    required_shear_reinforcement_strength_lb: float,
    area_in2: float,
    yield_strength_psi: float,
    effective_depth_in: float,
    concrete_strength_psi: float,
    web_width_in: float,
    *,
    allow_sqrt_fc_above_100: bool = False,
) -> ACIPerpendicularStirrupSpacingDesign:
    """Combine ACI 22.5.10.5.3 with Table 9.7.6.2.2 for vertical stirrup spacing."""

    calculated_spacing = perpendicular_stirrup_spacing_for_required_vs(
        area_in2=area_in2,
        yield_strength_psi=yield_strength_psi,
        effective_depth_in=effective_depth_in,
        required_shear_reinforcement_strength_lb=required_shear_reinforcement_strength_lb,
    )
    spacing_limit = max_shear_reinforcement_spacing_nonprestressed_beam(
        required_shear_reinforcement_strength_lb=required_shear_reinforcement_strength_lb,
        concrete_strength_psi=concrete_strength_psi,
        web_width_in=web_width_in,
        effective_depth_in=effective_depth_in,
        allow_sqrt_fc_above_100=allow_sqrt_fc_above_100,
    )
    return ACIPerpendicularStirrupSpacingDesign(
        required_shear_reinforcement_strength_lb=required_shear_reinforcement_strength_lb,
        area_in2=area_in2,
        yield_strength_psi=yield_strength_psi,
        effective_depth_in=effective_depth_in,
        calculated_spacing_in=calculated_spacing,
        spacing_limit=spacing_limit,
    )


def required_area_per_spacing_for_perpendicular_stirrups(
    required_shear_reinforcement_strength_lb: float,
    yield_strength_psi: float,
    effective_depth_in: float,
) -> float:
    """Report helper from R22.5.10.5: Av/s = (Vu - phi Vc)/(phi fyt d)."""

    if required_shear_reinforcement_strength_lb < 0:
        raise ValueError("Required shear reinforcement strength cannot be negative.")
    if yield_strength_psi <= 0 or effective_depth_in <= 0:
        raise ValueError("Yield strength and effective depth must be positive.")
    return required_shear_reinforcement_strength_lb / (yield_strength_psi * effective_depth_in)


def _validate_transverse_inputs(
    area_in2: float,
    yield_strength_psi: float,
    effective_depth_in: float,
    spacing_in: float,
) -> None:
    if area_in2 < 0:
        raise ValueError("Area cannot be negative.")
    if yield_strength_psi <= 0:
        raise ValueError("Yield strength must be positive.")
    if effective_depth_in <= 0:
        raise ValueError("Effective depth must be positive.")
    if spacing_in <= 0:
        raise ValueError("Spacing must be positive.")
