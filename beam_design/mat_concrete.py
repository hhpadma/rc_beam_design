from dataclasses import dataclass
import math


@dataclass
class Concrete:
    fc: float  # compressive strength (psi)

    @property
    def Ec(self) -> float:
        """ACI 318 empirical modulus of elasticity (psi)."""
        return 57000 * math.sqrt(self.fc)

    @property
    def beta1(self) -> float:
        """
        ACI 318-19, Section 22.2.2.4.3
        Factor for Whitney stress block depth.
        """
        if self.fc <= 4000:
            return 0.85
        elif self.fc >= 8000:
            return 0.65
        else:
            # Linear interpolation
            return 0.85 - 0.05 * ((self.fc - 4000) / 1000)

    def stress_block(self, a: float, b: float) -> float:
        """
        Placeholder for nonlinear stress block calculation (expand later).
        """
        return 0.85 * self.fc * a * b
