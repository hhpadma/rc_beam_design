from dataclasses import dataclass
import math


@dataclass
class Concrete:
    compressive_strength: float
    poisson_ratio: float = 0.2
    ultimate_compressive_strain: float = 0.003
    strain_at_ultimate_compressive_stress: float = 0.002
    unit_weight: float = 150/(12**3)  # lb/in³
    thermal_expansion: float = 6e-6

    @property
    def modulus_of_elasticity(self) -> float:
        """ACI 318 empirical modulus of elasticity (psi)."""
        return 57000 * math.sqrt(self.compressive_strength)

    @property
    def shear_modulus(self) -> float:
        """Approximate shear modulus (psi)."""
        return self.modulus_of_elasticity / (2 * (1 + self.poisson_ratio))

    @property
    def tensile_strength(self) -> float:
        """Approximate tensile strength (psi)."""
        return 0.1*self.compressive_strength

    @property
    def tensile_strain(self) -> float:
        """Approximate tensile strain."""
        return self.tensile_strength / self.modulus_of_elasticity

    @property
    def modulus_of_rupture(self) -> float:
        """Approximate modulus of rupture (psi)."""
        return 7.5 * math.sqrt(self.compressive_strength)

    @property
    def beta1_factor(self) -> float:
        """
        ACI 318-19, Section 22.2.2.4.3
        Factor for Whitney stress block depth.
        """
        if self.compressive_strength <= 4000:
            return 0.85
        elif self.compressive_strength >= 8000:
            return 0.65
        else:
            # Linear interpolation
            return 0.85 - 0.05 * ((self.compressive_strength - 4000) / 1000)


if __name__ == "__main__":
    conc = Concrete(compressive_strength=4000)
    print(f"Compressive Strength: {conc.compressive_strength} psi")
    print(f"Tensile Strength: {conc.tensile_strength:.2f} psi")
    print(f"Tensile Strain: {conc.tensile_strain:.6f}")
    print(f"Modulus of Elasticity: {conc.modulus_of_elasticity:.2f} psi")
    print(f"Beta1 Factor: {conc.beta1_factor:.2f}")
    print(
        f"Ultimate Compressive Strain: {conc.ultimate_compressive_strain:.4f}")
    print(f"Shear Modulus: {conc.shear_modulus:.2f} psi")
    print(f"Poisson Ratio: {conc.poisson_ratio:.2f}")
    print(
        f"Strain at Ultimate Compressive Stress: {conc.strain_at_ultimate_compressive_stress:.4f}")
    print(f"Unit Weight: {conc.unit_weight:.6f} lb/in³")
    print(f"Thermal Expansion: {conc.thermal_expansion:.6e}")
    print(f"Modulus of Rupture: {conc.modulus_of_rupture:.2f} psi")
