from dataclasses import dataclass


@dataclass
class Steel:
    yield_strength: float  # psi
    modulus_of_elasticity: float = 29_000_000  # psi
    ultimate_strain: float = 0.15
    poisson_ratio: float = 0.3
    unit_weight: float = 490/(12**3)  # lb/in³
    thermal_expansion: float = 6.5e-6

    @property
    def yield_strain(self) -> float:
        """Yield strain."""
        return self.yield_strength / self.modulus_of_elasticity

    @property
    def ultimate_stress(self) -> float:
        """Approximate ultimate stress (psi)."""
        return 1.1 * self.yield_strength


if __name__ == "__main__":
    steel = Steel(yield_strength=60000)
    print(f"Yield Strength: {steel.yield_strength} psi")
    print(f"Yield Strain: {steel.yield_strain:.6f}")
    print(f"Ultimate Strain: {steel.ultimate_strain:.4f}")
    print(f"Ultimate Stress: {steel.ultimate_stress:.2f} psi")
    print(f"Modulus of Elasticity: {steel.modulus_of_elasticity:.2f} psi")
    print(f"Poisson Ratio: {steel.poisson_ratio:.2f}")
    print(f"Unit Weight: {steel.unit_weight:.6f} lb/in³")
    print(f"Thermal Expansion: {steel.thermal_expansion:.2e}")
