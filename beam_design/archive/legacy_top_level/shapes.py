from beam_design.core.section_shapes import (
    CompositeSectionShape,
    FlangeSide,
    RectanglePart,
    SectionShapeType,
    l_shape,
    rectangular_shape,
    t_shape,
)

Shape = CompositeSectionShape
ShapeType = SectionShapeType


def RectangularShape(b: float | None = None, h: float | None = None, *, width: float | None = None, depth: float | None = None):
    return rectangular_shape(width if width is not None else b, depth if depth is not None else h)


def TShape(
    bw: float | None = None,
    h: float | None = None,
    bf: float | None = None,
    hf: float | None = None,
    *,
    web_width: float | None = None,
    total_depth: float | None = None,
    flange_width: float | None = None,
    flange_thickness: float | None = None,
):
    return t_shape(
        web_width if web_width is not None else bw,
        total_depth if total_depth is not None else h,
        flange_width if flange_width is not None else bf,
        flange_thickness if flange_thickness is not None else hf,
    )


def LShape(
    bw: float | None = None,
    h: float | None = None,
    bf: float | None = None,
    hf: float | None = None,
    *,
    web_width: float | None = None,
    total_depth: float | None = None,
    flange_width: float | None = None,
    flange_thickness: float | None = None,
    flange_side: FlangeSide = FlangeSide.RIGHT,
):
    return l_shape(
        web_width if web_width is not None else bw,
        total_depth if total_depth is not None else h,
        flange_width if flange_width is not None else bf,
        flange_thickness if flange_thickness is not None else hf,
        flange_side,
    )

__all__ = [
    "CompositeSectionShape",
    "FlangeSide",
    "LShape",
    "RectanglePart",
    "RectangularShape",
    "SectionShapeType",
    "Shape",
    "ShapeType",
    "TShape",
    "l_shape",
    "rectangular_shape",
    "t_shape",
]
