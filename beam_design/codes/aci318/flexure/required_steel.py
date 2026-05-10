from collections.abc import Callable
from dataclasses import dataclass


StressBlockDepthFunction = Callable[[float], float]


@dataclass(frozen=True)
class RequiredSteelResult:
    moment_ft_kip: float
    phi: float
    steel_yield_psi: float
    effective_depth_in: float
    required_area_in2: float
    stress_block_depth_in: float
    nominal_strength_ft_kip: float
    design_strength_ft_kip: float
    iterations: int


def solve_required_tension_area(
    moment_ft_kip: float,
    phi: float,
    steel_yield_psi: float,
    effective_depth_in: float,
    stress_block_depth: StressBlockDepthFunction,
    *,
    area_tolerance_in2: float = 1e-6,
    strength_tolerance_ft_kip: float = 1e-6,
    max_iterations: int = 100,
) -> RequiredSteelResult:
    """Solve required tension steel by bisection trial and error.

    The solver is intentionally small. Code modules provide the stress-block
    function; this routine only balances Mu against phi Mn.
    """

    if moment_ft_kip < 0:
        raise ValueError("Moment magnitude must be nonnegative.")
    if phi <= 0:
        raise ValueError("Strength reduction factor must be positive.")
    if steel_yield_psi <= 0 or effective_depth_in <= 0:
        raise ValueError("Steel strength and effective depth must be positive.")
    if moment_ft_kip == 0:
        return _result(moment_ft_kip, phi, steel_yield_psi, effective_depth_in, 0.0, stress_block_depth, 0)

    lower = 0.0
    upper = 1.0
    while _design_strength(upper, phi, steel_yield_psi, effective_depth_in, stress_block_depth) < moment_ft_kip:
        upper *= 2.0
        if upper > 1000:
            raise ValueError("Required tension steel area could not be bounded.")

    iterations = 0
    while iterations < max_iterations:
        iterations += 1
        trial = (lower + upper) / 2.0
        strength = _design_strength(trial, phi, steel_yield_psi, effective_depth_in, stress_block_depth)
        if abs(strength - moment_ft_kip) <= strength_tolerance_ft_kip or (upper - lower) <= area_tolerance_in2:
            return _result(moment_ft_kip, phi, steel_yield_psi, effective_depth_in, trial, stress_block_depth, iterations)
        if strength < moment_ft_kip:
            lower = trial
        else:
            upper = trial

    return _result(moment_ft_kip, phi, steel_yield_psi, effective_depth_in, (lower + upper) / 2.0, stress_block_depth, iterations)


def _design_strength(
    area_in2: float,
    phi: float,
    steel_yield_psi: float,
    effective_depth_in: float,
    stress_block_depth: StressBlockDepthFunction,
) -> float:
    return phi * _nominal_strength(area_in2, steel_yield_psi, effective_depth_in, stress_block_depth)


def _nominal_strength(
    area_in2: float,
    steel_yield_psi: float,
    effective_depth_in: float,
    stress_block_depth: StressBlockDepthFunction,
) -> float:
    a = stress_block_depth(area_in2)
    lever_arm = effective_depth_in - a / 2.0
    if lever_arm < 0:
        return -1.0
    return area_in2 * steel_yield_psi * lever_arm / 12000.0


def _result(
    moment_ft_kip: float,
    phi: float,
    steel_yield_psi: float,
    effective_depth_in: float,
    area_in2: float,
    stress_block_depth: StressBlockDepthFunction,
    iterations: int,
) -> RequiredSteelResult:
    a = stress_block_depth(area_in2)
    nominal_strength = _nominal_strength(area_in2, steel_yield_psi, effective_depth_in, stress_block_depth)
    return RequiredSteelResult(
        moment_ft_kip=moment_ft_kip,
        phi=phi,
        steel_yield_psi=steel_yield_psi,
        effective_depth_in=effective_depth_in,
        required_area_in2=area_in2,
        stress_block_depth_in=a,
        nominal_strength_ft_kip=nominal_strength,
        design_strength_ft_kip=phi * nominal_strength,
        iterations=iterations,
    )
