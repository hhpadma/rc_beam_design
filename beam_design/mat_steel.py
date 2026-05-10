from dataclasses import dataclass


@dataclass(init=False)
class Steel:
    yield_strength: float
    modulus_of_elasticity: float = 29_000_000
    ultimate_strain: float = 0.15
    poisson_ratio: float = 0.3
    unit_weight: float = 490/(12**3)
    thermal_expansion: float = 6.5e-6

    def __init__(
        self,
        yield_strength: float | None = None,
        *,
        fy: float | None = None,
        modulus_of_elasticity: float = 29_000_000,
        ultimate_strain: float = 0.15,
        poisson_ratio: float = 0.3,
        unit_weight: float = 490/(12**3),
        thermal_expansion: float = 6.5e-6,
    ):
        if yield_strength is None:
            yield_strength = fy
        if yield_strength is None:
            raise TypeError("Steel requires yield_strength or fy.")

        self.yield_strength = yield_strength
        self.modulus_of_elasticity = modulus_of_elasticity
        self.ultimate_strain = ultimate_strain
        self.poisson_ratio = poisson_ratio
        self.unit_weight = unit_weight
        self.thermal_expansion = thermal_expansion

    @property
    def fy(self) -> float:
        return self.yield_strength

    @property
    def Es(self) -> float:
        return self.modulus_of_elasticity

    @property
    def yield_strain(self) -> float:
        return self.yield_strength / self.modulus_of_elasticity

    @property
    def epsilon_y(self) -> float:
        return self.yield_strain

    @property
    def ultimate_stress(self) -> float:
        return 1.1 * self.yield_strength

    def stress(self, strain: float) -> float:
        elastic_stress = strain * self.modulus_of_elasticity
        sign = 1 if strain >= 0 else -1
        return sign * min(abs(elastic_stress), self.yield_strength)
