from dataclasses import dataclass, field
from typing import Any

from beam_design.mat_concrete import Concrete
from beam_design.mat_steel import Steel
from beam_design.rebar import BarTag, RebarCatalog
from beam_design.core.section_shapes import CompositeSectionShape, rectangular_shape
from beam_design.core.reinforcement import ReinforcementCage


@dataclass(frozen=True)
class Section:
    """Code-neutral beam section geometry.

    ``width`` is the web width used by design checks. ``shape`` carries the
    full gross geometry and may be rectangular, T, or L.
    """

    width: float
    depth: float
    cover: float = 1.5
    shape: CompositeSectionShape | None = None

    def __post_init__(self) -> None:
        if self.width <= 0:
            raise ValueError("Section width must be positive.")
        if self.depth <= 0:
            raise ValueError("Section depth must be positive.")
        if self.cover < 0:
            raise ValueError("Section cover cannot be negative.")
        if self.shape is None:
            object.__setattr__(self, "shape", rectangular_shape(self.width, self.depth))

    @property
    def area(self) -> float:
        return self.shape.area

    @property
    def gross_width(self) -> float:
        return self.shape.width

    @property
    def centroid_y(self) -> float:
        return self.shape.centroid_y

    @property
    def inertia_x(self) -> float:
        return self.shape.inertia_x


@dataclass(frozen=True)
class ReinforcementLayout:
    """Code-neutral reinforcement description for a beam section.

    Prefer ``cage`` for new work. The simple fields remain as a small adapter
    for early rules and notebooks.
    """

    tension_bar: BarTag | None = None
    tension_bar_count: int = 0
    compression_bar: BarTag | None = None
    compression_bar_count: int = 0
    stirrup_bar: BarTag | None = None
    stirrup_spacing: float | None = None
    cage: ReinforcementCage | None = None

    @property
    def tension_area(self) -> float:
        if self.cage is not None:
            return self.cage.bottom_area
        if self.tension_bar is None:
            return 0.0
        return self.tension_bar_count * RebarCatalog.get(self.tension_bar).area_in2

    @property
    def tension_bar_diameter(self) -> float:
        if self.cage is not None:
            return self.cage.bottom_largest_bar_diameter
        if self.tension_bar is None:
            return 0.0
        return RebarCatalog.get(self.tension_bar).diameter_in

    @property
    def stirrup_area(self) -> float:
        if self.cage is not None and self.cage.first_transverse_zone is not None:
            return self.cage.first_transverse_zone.single_bar_area
        if self.stirrup_bar is None:
            return 0.0
        return RebarCatalog.get(self.stirrup_bar).area_in2

    @property
    def stirrup_legs(self) -> int:
        if self.cage is not None and self.cage.first_transverse_zone is not None:
            return self.cage.first_transverse_zone.legs
        return 2

    @property
    def governing_stirrup_spacing(self) -> float | None:
        if self.cage is not None and self.cage.first_transverse_zone is not None:
            return self.cage.first_transverse_zone.spacing
        return self.stirrup_spacing

    def transverse_zone_at(self, position: float):
        if self.cage is None:
            return None
        return self.cage.transverse_zone_at(position)

    def stirrup_area_at(self, position: float) -> float:
        zone = self.transverse_zone_at(position)
        if zone is not None:
            return zone.single_bar_area
        return self.stirrup_area

    def stirrup_legs_at(self, position: float) -> int:
        zone = self.transverse_zone_at(position)
        if zone is not None:
            return zone.legs
        return self.stirrup_legs

    def stirrup_spacing_at(self, position: float) -> float | None:
        zone = self.transverse_zone_at(position)
        if zone is not None:
            return zone.spacing
        return self.governing_stirrup_spacing

    @property
    def tension_centroid_y_from_top(self) -> float | None:
        if self.cage is None or not self.cage.bottom_layers:
            return None
        return self.cage.bottom_centroid_y_from_top


@dataclass(frozen=True)
class FactoredLoad:
    """Code-neutral demand values after a selected code handles combinations."""

    moment: float = 0.0
    shear: float = 0.0
    torsion: float = 0.0
    axial: float = 0.0
    label: str = "factored"


@dataclass(frozen=True)
class BeamDesignContext:
    """Single object passed to all rules and assemblies."""

    section: Section
    concrete: Concrete
    steel: Steel
    reinforcement: ReinforcementLayout = field(default_factory=ReinforcementLayout)
    load: FactoredLoad = field(default_factory=FactoredLoad)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def effective_depth(self) -> float:
        if self.reinforcement.tension_centroid_y_from_top is not None:
            return self.reinforcement.tension_centroid_y_from_top
        bar_radius = self.reinforcement.tension_bar_diameter / 2
        return self.section.depth - self.section.cover - bar_radius
