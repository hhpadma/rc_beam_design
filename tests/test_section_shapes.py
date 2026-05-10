import pytest

from beam_design.core.section_shapes import FlangeSide, SectionShapeType, l_shape, rectangular_shape, t_shape
from beam_design.core.reinforcement import LongitudinalFace, LongitudinalLayerSpec
from beam_design.mat_concrete import Concrete
from beam_design.mat_steel import Steel
from beam_design.rebar import BarTag
from beam_design.section_assembler import SectionAssembler
from beam_design.section_designer import SectionDesigner


def test_rectangular_shape_properties():
    shape = rectangular_shape(width=12, depth=24)

    assert shape.shape_type == SectionShapeType.RECTANGULAR
    assert shape.area == 288
    assert shape.centroid_y == 12
    assert shape.inertia_x == 12 * 24**3 / 12
    assert shape.inertia_y == 24 * 12**3 / 12


def test_t_shape_area_and_centered_centroid_x():
    shape = t_shape(web_width=12, total_depth=24, flange_width=48, flange_thickness=4)

    assert shape.shape_type == SectionShapeType.T
    assert shape.area == 48 * 4 + 12 * 20
    assert shape.centroid_x == 24
    assert shape.width == 48
    assert shape.web_width == 12


def test_l_shape_centroid_moves_toward_web_side():
    right = l_shape(
        web_width=12,
        total_depth=24,
        flange_width=48,
        flange_thickness=4,
        flange_side=FlangeSide.RIGHT,
    )
    left = l_shape(
        web_width=12,
        total_depth=24,
        flange_width=48,
        flange_thickness=4,
        flange_side=FlangeSide.LEFT,
    )

    assert right.shape_type == SectionShapeType.L
    assert right.centroid_x < 24
    assert left.centroid_x > 24
    assert pytest.approx(right.centroid_y) == left.centroid_y


def test_flanged_shape_rejects_bad_dimensions():
    with pytest.raises(ValueError):
        t_shape(web_width=18, total_depth=24, flange_width=12, flange_thickness=4)

    with pytest.raises(ValueError):
        t_shape(web_width=12, total_depth=24, flange_width=48, flange_thickness=24)


def test_section_assembler_creates_shape_backed_section():
    section = SectionAssembler.t_beam(
        web_width=12,
        total_depth=24,
        flange_width=48,
        flange_thickness=4,
        cover=2,
    )

    assert section.width == 12
    assert section.depth == 24
    assert section.cover == 2
    assert section.gross_width == 48
    assert section.area == 48 * 4 + 12 * 20


def test_section_assembler_creates_complete_rectangular_assembly():
    assembly = SectionAssembler.rectangular_assembly(
        width=16,
        depth=30,
        clear_cover=1.5,
        stirrup_bar=BarTag.B10,
        longitudinal_specs=(
            LongitudinalLayerSpec(LongitudinalFace.BOTTOM, BarTag.B25, 3),
            LongitudinalLayerSpec(LongitudinalFace.TOP, BarTag.B20, 2),
        ),
    )

    assert assembly.clear_cover == 1.5
    assert assembly.section.width == 16
    assert assembly.shape.shape_type == SectionShapeType.RECTANGULAR
    assert assembly.cage.bottom_area > 0
    assert assembly.cage.top_area > 0
    assert assembly.effective_depth == assembly.cage.bottom_centroid_y_from_top


def test_section_assembly_creates_design_context():
    assembly = SectionAssembler.t_beam_assembly(
        web_width=12,
        total_depth=24,
        flange_width=48,
        flange_thickness=4,
        clear_cover=1.5,
        stirrup_bar=BarTag.B10,
        longitudinal_specs=(
            LongitudinalLayerSpec(LongitudinalFace.BOTTOM, BarTag.B20, 3),
        ),
    )
    context = assembly.design_context(
        concrete=Concrete(fc=4000),
        steel=Steel(fy=60000),
        metadata={"aci_exposure_classes": ("F1",)},
    )

    assert context.section is assembly.section
    assert context.reinforcement is assembly.reinforcement
    assert context.effective_depth == assembly.effective_depth


def test_section_designer_reports_shape_and_reinforcement_summary():
    assembly = SectionAssembler.l_beam_assembly(
        web_width=12,
        total_depth=24,
        flange_width=48,
        flange_thickness=4,
        clear_cover=1.5,
        stirrup_bar=BarTag.B10,
        longitudinal_specs=(
            LongitudinalLayerSpec(LongitudinalFace.BOTTOM, BarTag.B20, 3),
        ),
    )
    summary = SectionDesigner(assembly).summary

    assert summary["shape"]["shape_type"] == "l"
    assert summary["reinforcement"]["bottom_layers"] == 1
    assert summary["reinforcement"]["effective_depth"] == assembly.effective_depth
