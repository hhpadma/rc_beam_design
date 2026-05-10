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

    @property
    def mark(self) -> str:
        return f"D{self.tag.value}"


class RebarCatalog:
    """
    Standard reinforcing bar properties.
    Units:
        - Diameter: inches
        - Area: in^2
        - Unit weight: kg/in
    """

    _bars = {
        BarTag.B8:  BarProperties(BarTag.B8,  0.31496063, 0.077965, 0.010036),
        BarTag.B10: BarProperties(BarTag.B10, 0.39370079, 0.121365, 0.015676),
        BarTag.B12: BarProperties(BarTag.B12, 0.47244094, 0.175130, 0.022561),
        BarTag.B16: BarProperties(BarTag.B16, 0.62992126, 0.311551, 0.040142),
        BarTag.B20: BarProperties(BarTag.B20, 0.78740157, 0.486701, 0.062754),
        BarTag.B25: BarProperties(BarTag.B25, 0.98425197, 0.761052, 0.097815),
        BarTag.B28: BarProperties(BarTag.B28, 1.10236220, 0.954802, 0.123095),
        BarTag.B32: BarProperties(BarTag.B32, 1.25984252, 1.246202, 0.160315),
        BarTag.B40: BarProperties(BarTag.B40, 1.57480315, 1.946804, 0.250508),
    }

    @classmethod
    def get(cls, tag: BarTag | int | str) -> BarProperties:
        tag = cls.coerce_tag(tag)
        try:
            return cls._bars[tag]
        except KeyError:
            raise ValueError(f"Bar tag {tag} not found in catalog")

    @classmethod
    def coerce_tag(cls, tag: BarTag | int | str) -> BarTag:
        if isinstance(tag, BarTag):
            return tag
        if isinstance(tag, int):
            return BarTag(tag)
        if isinstance(tag, str):
            normalized = tag.strip().upper().replace("#", "").replace("D", "").replace("B", "")
            if normalized.startswith("Ø"):
                normalized = normalized[1:]
            return BarTag(int(normalized))
        raise TypeError(f"Unsupported bar tag type: {type(tag)!r}")

    @classmethod
    def all(cls) -> tuple[BarProperties, ...]:
        return tuple(cls._bars[tag] for tag in sorted(cls._bars))


if __name__ == "__main__":

    bar = RebarCatalog.get(BarTag.B16)
    print(bar)

    print(f"Bar Tag: {bar.tag}")
    print(f"Diameter: {bar.diameter_in:.4f} in")
    print(f"Area: {bar.area_in2:.4f} in²")
    print(f"Unit Weight: {bar.unit_weight_kg_per_in:.6f} kg/in")
