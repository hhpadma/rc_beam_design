from dataclasses import dataclass

from sections import Section
from mat_concrete import Concrete
from mat_steel import Steel

# Singly Reinforced Rectangular Beam Flexure Design

# balanced steel ratio
# ρ_b = 0.85 * β1 * f'c / fy * (ε_c / (ε_c + ε_y))

@dataclass
class Flexure:
    section: Section
    concrete: Concrete
    steel: Steel

    @property
    def depth_steel(self) -> float:
        """Distance from extreme compression fiber to centroid of tension reinforcement (in)."""
        return self.section.depth - self.section.cover - self.section.bar_diameter / 2

    @property
    def depth_neutral_axis(self) -> float:
        """Depth of neutral axis from extreme compression fiber (in)."""
        a_s = self.area_steel
        f_y = self.steel.yield_strength
        f_c = self.concrete.compressive_strength
        b = self.section.width
        beta1 = self.concrete.beta1_factor

        return (a_s * f_y) / (0.85 * f_c * b * beta1)

    @property
    def moment_capacity(self) -> float:
        """Nominal moment capacity (in-lb)."""
        a_s = self.area_steel
        f_y = self.steel.yield_strength
        d = self.depth_steel
        c = self.depth_neutral_axis
        beta1 = self.concrete.beta1_factor

        a = beta1 * c  # depth of equivalent rectangular stress block

        # Check if steel yields
        epsilon_y = self.steel.yield_strain
        epsilon_cu = self.concrete.ultimate_compressive_strain

        epsilon_s = epsilon_cu * (d - c) / c  # strain in tension steel

        if epsilon_s < epsilon_y:
            # Steel does not yield, use elastic stress in steel
            f_s = epsilon_s * self.steel.modulus_of_elasticity
            if f_s > f_y:
                f_s = f_y  # Cap at yield strength
        else:
            f_s = f_y  # Steel yields

        # Calculate nominal moment capacity
        c_c = a / 2  # centroid of compression block from extreme fiber
        moment_capacity = a_s * f_s * (d - c_c)

        return moment_capacity