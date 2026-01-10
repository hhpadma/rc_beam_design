from enum import Enum, IntEnum
from dataclasses import dataclass


class BarFunction(Enum):
    MAIN = "Main longitudinal bar"
    STIRRUP = "Stirrup or tie"


class BarStressState(Enum):
    TENSION = "tension"
    COMPRESSION = "compression"


class BarTag(IntEnum):
    B8 = 8
    B10 = 10
    B12 = 12
    B16 = 16
    B20 = 20
    B25 = 25
    B28 = 28
    B32 = 32
    B40 = 40


@dataclass(frozen=True)
class BarProperties:
    tag: BarTag
    diameter_in: float
    area_in2: float
    unit_weight_kg_per_in: float


class RebarCatalog:
    """
    Standard reinforcing bar properties.
    Units:
        - Diameter: inches
        - Area: in^2
        - Unit weight: kg/in
    """

    _bars = {
        BarTag.B8:  BarProperties(BarTag.B8,  0.31496063, 0.077965156, 0.010035569),
        BarTag.B10: BarProperties(BarTag.B10, 0.393700787, 0.121365243, 0.015675813),
        BarTag.B12: BarProperties(BarTag.B12, 0.472440945, 0.17515035,  0.022560976),
        BarTag.B16: BarProperties(BarTag.B16, 0.62992126,  0.311550623, 0.040142276),
        BarTag.B20: BarProperties(BarTag.B20, 0.787401575, 0.486700973, 0.062754065),
        BarTag.B25: BarProperties(BarTag.B25, 0.984251969, 0.761051522, 0.097815041),
        BarTag.B28: BarProperties(BarTag.B28, 1.102362205, 0.95480191,  0.123094512),
        BarTag.B32: BarProperties(BarTag.B32, 1.25984252,  1.246202492, 0.160315041),
        BarTag.B40: BarProperties(BarTag.B40, 1.57480315,  1.946803894, 0.25050813),
    }

    @classmethod
    def get(cls, tag: BarTag) -> BarProperties:
        try:
            return cls._bars[tag]
        except KeyError:
            raise ValueError(f"Bar tag {tag} not found in catalog")


if __name__ == "__main__":

    bar = RebarCatalog.get(BarTag.B16)
    print(bar)

    print(f"Bar Tag: {bar.tag}")
    print(f"Diameter: {bar.diameter_in:.4f} in")
    print(f"Area: {bar.area_in2:.4f} in²")
    print(f"Unit Weight: {bar.unit_weight_kg_per_in:.6f} kg/in")
