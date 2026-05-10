from dataclasses import dataclass
from enum import Enum
from math import sqrt
from typing import Protocol


class SectionShapeType(Enum):
    RECTANGULAR = "rectangular"
    T = "t"
    L = "l"


class FlangeSide(Enum):
    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True)
class RectanglePart:
    width: float
    depth: float
    x_left: float
    y_top: float

    def __post_init__(self) -> None:
        if self.width <= 0:
            raise ValueError("Rectangle part width must be positive.")
        if self.depth <= 0:
            raise ValueError("Rectangle part depth must be positive.")

    @property
    def area(self) -> float:
        return self.width * self.depth

    @property
    def centroid_x(self) -> float:
        return self.x_left + self.width / 2

    @property
    def centroid_y(self) -> float:
        return self.y_top + self.depth / 2

    @property
    def inertia_x_centroid(self) -> float:
        return self.width * self.depth**3 / 12

    @property
    def inertia_y_centroid(self) -> float:
        return self.depth * self.width**3 / 12


class BeamSectionShape(Protocol):
    shape_type: SectionShapeType
    depth: float
    web_width: float
    parts: tuple[RectanglePart, ...]

    @property
    def width(self) -> float:
        ...

    @property
    def area(self) -> float:
        ...

    @property
    def centroid_x(self) -> float:
        ...

    @property
    def centroid_y(self) -> float:
        ...

    @property
    def inertia_x(self) -> float:
        ...

    @property
    def inertia_y(self) -> float:
        ...


@dataclass(frozen=True)
class CompositeSectionShape:
    shape_type: SectionShapeType
    web_width: float
    depth: float
    parts: tuple[RectanglePart, ...]

    def __post_init__(self) -> None:
        if self.web_width <= 0:
            raise ValueError("Web width must be positive.")
        if self.depth <= 0:
            raise ValueError("Section depth must be positive.")
        if not self.parts:
            raise ValueError("At least one rectangle part is required.")

    @property
    def width(self) -> float:
        return max(part.x_left + part.width for part in self.parts) - min(part.x_left for part in self.parts)

    @property
    def area(self) -> float:
        return sum(part.area for part in self.parts)

    @property
    def centroid_x(self) -> float:
        return sum(part.area * part.centroid_x for part in self.parts) / self.area

    @property
    def centroid_y(self) -> float:
        return sum(part.area * part.centroid_y for part in self.parts) / self.area

    @property
    def inertia_x(self) -> float:
        centroid_y = self.centroid_y
        return sum(
            part.inertia_x_centroid + part.area * (part.centroid_y - centroid_y) ** 2
            for part in self.parts
        )

    @property
    def inertia_y(self) -> float:
        centroid_x = self.centroid_x
        return sum(
            part.inertia_y_centroid + part.area * (part.centroid_x - centroid_x) ** 2
            for part in self.parts
        )

    @property
    def section_modulus_top(self) -> float:
        return self.inertia_x / self.centroid_y

    @property
    def section_modulus_bottom(self) -> float:
        return self.inertia_x / (self.depth - self.centroid_y)

    @property
    def radius_of_gyration_x(self) -> float:
        return sqrt(self.inertia_x / self.area)

    @property
    def radius_of_gyration_y(self) -> float:
        return sqrt(self.inertia_y / self.area)

    def summary(self) -> dict[str, float | str]:
        return {
            "shape_type": self.shape_type.value,
            "width": self.width,
            "web_width": self.web_width,
            "depth": self.depth,
            "area": self.area,
            "centroid_x": self.centroid_x,
            "centroid_y": self.centroid_y,
            "inertia_x": self.inertia_x,
            "inertia_y": self.inertia_y,
            "section_modulus_top": self.section_modulus_top,
            "section_modulus_bottom": self.section_modulus_bottom,
        }


def rectangular_shape(width: float, depth: float) -> CompositeSectionShape:
    return CompositeSectionShape(
        shape_type=SectionShapeType.RECTANGULAR,
        web_width=width,
        depth=depth,
        parts=(RectanglePart(width=width, depth=depth, x_left=0.0, y_top=0.0),),
    )


def t_shape(web_width: float, total_depth: float, flange_width: float, flange_thickness: float) -> CompositeSectionShape:
    _validate_flanged_dimensions(web_width, total_depth, flange_width, flange_thickness)
    web_depth = total_depth - flange_thickness
    web_left = (flange_width - web_width) / 2
    return CompositeSectionShape(
        shape_type=SectionShapeType.T,
        web_width=web_width,
        depth=total_depth,
        parts=(
            RectanglePart(width=flange_width, depth=flange_thickness, x_left=0.0, y_top=0.0),
            RectanglePart(width=web_width, depth=web_depth, x_left=web_left, y_top=flange_thickness),
        ),
    )


def l_shape(
    web_width: float,
    total_depth: float,
    flange_width: float,
    flange_thickness: float,
    flange_side: FlangeSide = FlangeSide.RIGHT,
) -> CompositeSectionShape:
    _validate_flanged_dimensions(web_width, total_depth, flange_width, flange_thickness)
    if isinstance(flange_side, str):
        flange_side = FlangeSide(flange_side.lower())

    web_depth = total_depth - flange_thickness
    web_left = 0.0 if flange_side == FlangeSide.RIGHT else flange_width - web_width
    return CompositeSectionShape(
        shape_type=SectionShapeType.L,
        web_width=web_width,
        depth=total_depth,
        parts=(
            RectanglePart(width=flange_width, depth=flange_thickness, x_left=0.0, y_top=0.0),
            RectanglePart(width=web_width, depth=web_depth, x_left=web_left, y_top=flange_thickness),
        ),
    )


def _validate_flanged_dimensions(
    web_width: float,
    total_depth: float,
    flange_width: float,
    flange_thickness: float,
) -> None:
    if web_width <= 0:
        raise ValueError("Web width must be positive.")
    if total_depth <= 0:
        raise ValueError("Total depth must be positive.")
    if flange_width <= 0:
        raise ValueError("Flange width must be positive.")
    if flange_thickness <= 0:
        raise ValueError("Flange thickness must be positive.")
    if flange_width < web_width:
        raise ValueError("Flange width cannot be less than web width.")
    if flange_thickness >= total_depth:
        raise ValueError("Flange thickness must be less than total depth.")
