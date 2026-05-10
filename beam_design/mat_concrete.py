from dataclasses import dataclass
import math


@dataclass(init=False)
class Concrete:
    compressive_strength: float
    poisson_ratio: float = 0.2
    ultimate_compressive_strain: float = 0.003
    strain_at_ultimate_compressive_stress: float = 0.002
    unit_weight: float = 150/(12**3)
    thermal_expansion: float = 6e-6

    def __init__(
        self,
        compressive_strength: float | None = None,
        *,
        fc: float | None = None,
        poisson_ratio: float = 0.2,
        ultimate_compressive_strain: float = 0.003,
        strain_at_ultimate_compressive_stress: float = 0.002,
        unit_weight: float = 150/(12**3),
        thermal_expansion: float = 6e-6,
    ):
        if compressive_strength is None:
            compressive_strength = fc
        if compressive_strength is None:
            raise TypeError("Concrete requires compressive_strength or fc.")

        self.compressive_strength = compressive_strength
        self.poisson_ratio = poisson_ratio
        self.ultimate_compressive_strain = ultimate_compressive_strain
        self.strain_at_ultimate_compressive_stress = strain_at_ultimate_compressive_stress
        self.unit_weight = unit_weight
        self.thermal_expansion = thermal_expansion

    @property
    def fc(self) -> float:
        return self.compressive_strength

    @property
    def modulus_of_elasticity(self) -> float:
        """ACI 318 empirical modulus of elasticity in psi."""
        return 57000 * math.sqrt(self.compressive_strength)

    @property
    def Ec(self) -> float:
        return self.modulus_of_elasticity

    @property
    def shear_modulus(self) -> float:
        return self.modulus_of_elasticity / (2 * (1 + self.poisson_ratio))

    @property
    def tensile_strength(self) -> float:
        return 0.1 * self.compressive_strength

    @property
    def tensile_strain(self) -> float:
        return self.tensile_strength / self.modulus_of_elasticity

    @property
    def modulus_of_rupture(self) -> float:
        return 7.5 * math.sqrt(self.compressive_strength)

    @property
    def beta1_factor(self) -> float:
        if self.compressive_strength <= 4000:
            return 0.85
        if self.compressive_strength >= 8000:
            return 0.65
        return 0.85 - 0.05 * ((self.compressive_strength - 4000) / 1000)

    @property
    def beta1(self) -> float:
        return self.beta1_factor
