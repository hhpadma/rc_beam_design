from dataclasses import dataclass
from enum import Enum

from beam_design.rebar import BarTag, RebarCatalog


class LongitudinalFace(Enum):
    TOP = "top"
    BOTTOM = "bottom"


class TransverseZoneKind(Enum):
    LEFT_SUPPORT = "left_support"
    MIDSPAN = "midspan"
    RIGHT_SUPPORT = "right_support"
    CUSTOM = "custom"


class TransversePurpose(Enum):
    SHEAR = "shear"
    TORSION = "torsion"
    DUCTILITY = "ductility"
    CONFINEMENT = "confinement"


@dataclass(frozen=True)
class LongitudinalLayerSpec:
    face: LongitudinalFace
    bar_tag: BarTag
    count: int
    lap_splice_bar_tag: BarTag | None = None

    def __post_init__(self) -> None:
        if isinstance(self.face, str):
            object.__setattr__(self, "face", LongitudinalFace(self.face.lower()))
        object.__setattr__(self, "bar_tag", RebarCatalog.coerce_tag(self.bar_tag))
        if self.lap_splice_bar_tag is not None:
            object.__setattr__(self, "lap_splice_bar_tag", RebarCatalog.coerce_tag(self.lap_splice_bar_tag))
        if self.count <= 0:
            raise ValueError("Longitudinal layer count must be positive.")

    @property
    def bar_diameter(self) -> float:
        return RebarCatalog.get(self.bar_tag).diameter_in

    @property
    def bar_area(self) -> float:
        return RebarCatalog.get(self.bar_tag).area_in2

    @property
    def area(self) -> float:
        return self.count * self.bar_area

    @property
    def placement_width_per_bar(self) -> float:
        if self.lap_splice_bar_tag is None:
            return self.bar_diameter
        return self.bar_diameter + RebarCatalog.get(self.lap_splice_bar_tag).diameter_in


@dataclass(frozen=True)
class LongitudinalBarLayer:
    face: LongitudinalFace
    bar_tag: BarTag
    count: int
    y_from_top: float
    x_positions: tuple[float, ...]
    clear_spacing: float | None
    lap_splice_bar_tag: BarTag | None = None
    placement_label: str | None = None

    @property
    def bar_diameter(self) -> float:
        return RebarCatalog.get(self.bar_tag).diameter_in

    @property
    def bar_area(self) -> float:
        return RebarCatalog.get(self.bar_tag).area_in2

    @property
    def area(self) -> float:
        return self.count * self.bar_area

    @property
    def centroid_y_from_top(self) -> float:
        return self.y_from_top

    @property
    def width(self) -> float:
        if not self.x_positions:
            return 0.0
        return max(self.x_positions) - min(self.x_positions)


@dataclass(frozen=True)
class TransverseReinforcementZone:
    start: float
    end: float
    bar_tag: BarTag
    spacing: float
    legs: int = 2
    kind: TransverseZoneKind = TransverseZoneKind.CUSTOM
    purposes: tuple[TransversePurpose, ...] = (TransversePurpose.SHEAR,)
    hook_angle: int = 135

    def __post_init__(self) -> None:
        if isinstance(self.kind, str):
            object.__setattr__(self, "kind", TransverseZoneKind(self.kind.lower()))
        object.__setattr__(self, "bar_tag", RebarCatalog.coerce_tag(self.bar_tag))
        object.__setattr__(
            self,
            "purposes",
            tuple(TransversePurpose(p.lower()) if isinstance(p, str) else p for p in self.purposes),
        )
        if self.start < 0:
            raise ValueError("Transverse zone start cannot be negative.")
        if self.end <= self.start:
            raise ValueError("Transverse zone end must be greater than start.")
        if self.spacing <= 0:
            raise ValueError("Transverse spacing must be positive.")
        if self.legs <= 0:
            raise ValueError("Transverse reinforcement must have at least one leg.")

    @property
    def bar_diameter(self) -> float:
        return RebarCatalog.get(self.bar_tag).diameter_in

    @property
    def single_bar_area(self) -> float:
        return RebarCatalog.get(self.bar_tag).area_in2

    @property
    def area_per_set(self) -> float:
        return self.legs * self.single_bar_area

    def contains(self, position: float) -> bool:
        return self.start <= position <= self.end


@dataclass(frozen=True)
class ReinforcementCage:
    longitudinal_layers: tuple[LongitudinalBarLayer, ...] = ()
    transverse_zones: tuple[TransverseReinforcementZone, ...] = ()

    @property
    def bottom_layers(self) -> tuple[LongitudinalBarLayer, ...]:
        return tuple(layer for layer in self.longitudinal_layers if layer.face == LongitudinalFace.BOTTOM)

    @property
    def top_layers(self) -> tuple[LongitudinalBarLayer, ...]:
        return tuple(layer for layer in self.longitudinal_layers if layer.face == LongitudinalFace.TOP)

    @property
    def bottom_area(self) -> float:
        return sum(layer.area for layer in self.bottom_layers)

    @property
    def top_area(self) -> float:
        return sum(layer.area for layer in self.top_layers)

    @property
    def bottom_centroid_y_from_top(self) -> float:
        return _weighted_y(self.bottom_layers)

    @property
    def top_centroid_y_from_top(self) -> float:
        return _weighted_y(self.top_layers)

    @property
    def bottom_largest_bar_diameter(self) -> float:
        return max((layer.bar_diameter for layer in self.bottom_layers), default=0.0)

    @property
    def first_transverse_zone(self) -> TransverseReinforcementZone | None:
        return self.transverse_zones[0] if self.transverse_zones else None

    def transverse_zone_at(self, position: float) -> TransverseReinforcementZone | None:
        for zone in self.transverse_zones:
            if zone.contains(position):
                return zone
        return None


def _weighted_y(layers: tuple[LongitudinalBarLayer, ...]) -> float:
    area = sum(layer.area for layer in layers)
    if area <= 0:
        return 0.0
    return sum(layer.area * layer.centroid_y_from_top for layer in layers) / area
