from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class ACIDesignAssumption:
    clause: str
    title: str
    statement: str
    report_note: str = ""


@dataclass(frozen=True)
class ACIEquivalentRectangularStressBlock:
    concrete_strength_psi: float
    beta1: float
    alpha1: float = 0.85
    ultimate_concrete_strain: float = 0.003
    tensile_strength_neglected: bool = True

    @property
    def equivalent_concrete_stress_psi(self) -> float:
        return self.alpha1 * self.concrete_strength_psi

    def equivalent_depth(self, neutral_axis_depth_in: float) -> float:
        if neutral_axis_depth_in <= 0:
            raise ValueError("Neutral axis depth must be positive.")
        return self.beta1 * neutral_axis_depth_in

    def compression_force(self, width_in: float, compression_block_depth_in: float) -> float:
        if width_in <= 0:
            raise ValueError("Compression width must be positive.")
        if compression_block_depth_in <= 0:
            raise ValueError("Compression block depth must be positive.")
        return self.equivalent_concrete_stress_psi * width_in * compression_block_depth_in


ACI_MOMENT_AXIAL_ASSUMPTIONS = (
    ACIDesignAssumption(
        clause="22.2.1.1",
        title="Equilibrium",
        statement="Equilibrium shall be satisfied at each section.",
        report_note="Nominal flexural strength is solved by balancing internal compression and tension forces.",
    ),
    ACIDesignAssumption(
        clause="22.2.1.2",
        title="Linear strain distribution",
        statement="Concrete and nonprestressed reinforcement strain is proportional to distance from the neutral axis.",
        report_note="Plane sections are assumed to remain plane at nominal strength.",
    ),
    ACIDesignAssumption(
        clause="22.2.2.1",
        title="Maximum concrete strain",
        statement="Maximum strain at the extreme concrete compression fiber is 0.003.",
    ),
    ACIDesignAssumption(
        clause="22.2.2.2",
        title="Concrete tensile strength neglected",
        statement="Tensile strength of concrete is neglected in flexural and axial strength calculations.",
    ),
    ACIDesignAssumption(
        clause="22.2.2.4.1",
        title="Equivalent concrete stress",
        statement="Concrete stress of 0.85fc' is uniformly distributed over the equivalent compression zone.",
    ),
    ACIDesignAssumption(
        clause="22.2.2.4.1",
        title="Equivalent compression block depth",
        statement="Equivalent compression block depth is a = beta1 c.",
    ),
    ACIDesignAssumption(
        clause="22.2.2.4.3",
        title="Beta1 factor",
        statement="Beta1 is selected from ACI 318-14 Table 22.2.2.4.3.",
    ),
)


ACI_MOMENT_AXIAL_ASSUMPTIONS_BY_CLAUSE = MappingProxyType(
    {assumption.clause: assumption for assumption in ACI_MOMENT_AXIAL_ASSUMPTIONS}
)


def beta1_factor(concrete_strength_psi: float) -> float:
    if concrete_strength_psi <= 0:
        raise ValueError("Concrete compressive strength must be positive.")
    if concrete_strength_psi <= 4000.0:
        return 0.85
    if concrete_strength_psi >= 8000.0:
        return 0.65
    return 0.85 - 0.05 * ((concrete_strength_psi - 4000.0) / 1000.0)


def equivalent_rectangular_stress_block(concrete_strength_psi: float) -> ACIEquivalentRectangularStressBlock:
    return ACIEquivalentRectangularStressBlock(
        concrete_strength_psi=concrete_strength_psi,
        beta1=beta1_factor(concrete_strength_psi),
    )


def compression_block_depth_from_tension(
    tension_area_in2: float,
    steel_stress_psi: float,
    concrete_strength_psi: float,
    compression_width_in: float,
) -> float:
    if tension_area_in2 < 0:
        raise ValueError("Tension steel area cannot be negative.")
    if steel_stress_psi < 0:
        raise ValueError("Steel stress cannot be negative.")
    if compression_width_in <= 0:
        raise ValueError("Compression width must be positive.")
    block = equivalent_rectangular_stress_block(concrete_strength_psi)
    return tension_area_in2 * steel_stress_psi / (block.equivalent_concrete_stress_psi * compression_width_in)


def effective_depth_one_layer(
    total_depth_in: float,
    clear_cover_in: float,
    transverse_bar_diameter_in: float,
    longitudinal_bar_diameter_in: float,
) -> float:
    if total_depth_in <= 0:
        raise ValueError("Total depth must be positive.")
    if min(clear_cover_in, transverse_bar_diameter_in, longitudinal_bar_diameter_in) < 0:
        raise ValueError("Cover and bar diameters cannot be negative.")
    return total_depth_in - clear_cover_in - transverse_bar_diameter_in - longitudinal_bar_diameter_in / 2.0


def flexural_assumption_report_rows() -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "clause": assumption.clause,
            "title": assumption.title,
            "statement": assumption.statement,
            "report_note": assumption.report_note,
        }
        for assumption in ACI_MOMENT_AXIAL_ASSUMPTIONS
    )
