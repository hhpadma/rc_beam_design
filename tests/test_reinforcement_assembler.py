import pytest

from beam_design import (
    ACI318,
    BeamDesignContext,
    Concrete,
    FactoredLoad,
    LongitudinalFace,
    LongitudinalLayerSpec,
    ReinforcementAssembler,
    ReinforcementLayout,
    SectionAssembler,
    Steel,
    TransverseZoneKind,
)
from beam_design.codes.aci318.shear.strength import ACIShearStrengthCheck
from beam_design.rebar import BarTag, RebarCatalog


def test_aci_bar_catalog_uses_expected_fps_dataset():
    bar = RebarCatalog.get("D25")

    assert bar.tag == BarTag.B25
    assert bar.mark == "D25"
    assert pytest.approx(bar.diameter_in) == 0.98425197
    assert pytest.approx(bar.area_in2) == 0.761052
    assert pytest.approx(bar.unit_weight_kg_per_in) == 0.097815


def test_bar_catalog_accepts_symbol_style_tags():
    assert RebarCatalog.get("Ø40").tag == BarTag.B40
    assert RebarCatalog.get("B20").tag == BarTag.B20
    assert RebarCatalog.get(16).tag == BarTag.B16


def test_longitudinal_bottom_layer_positions_and_effective_depth():
    section = SectionAssembler.rectangular(width=16, depth=30, cover=1.5)
    assembler = ReinforcementAssembler(section=section, stirrup_bar=BarTag.B10)
    cage = assembler.cage(
        longitudinal_specs=(
            LongitudinalLayerSpec(
                face=LongitudinalFace.BOTTOM,
                bar_tag=BarTag.B25,
                count=3,
            ),
        )
    )
    layer = cage.bottom_layers[0]

    assert len(layer.x_positions) == 3
    assert layer.x_positions[0] < layer.x_positions[1] < layer.x_positions[2]
    assert pytest.approx(cage.bottom_centroid_y_from_top) == layer.y_from_top
    assert cage.bottom_centroid_y_from_top < section.depth


def test_multiple_bottom_layers_stack_toward_neutral_axis():
    section = SectionAssembler.rectangular(width=18, depth=32, cover=1.5)
    assembler = ReinforcementAssembler(section=section, stirrup_bar=BarTag.B10)
    cage = assembler.cage(
        longitudinal_specs=(
            LongitudinalLayerSpec(LongitudinalFace.BOTTOM, BarTag.B25, 2),
            LongitudinalLayerSpec(LongitudinalFace.BOTTOM, BarTag.B20, 2),
        )
    )
    first, second = cage.bottom_layers

    assert second.y_from_top < first.y_from_top
    assert cage.bottom_centroid_y_from_top < first.y_from_top


def test_lap_splice_is_considered_in_clear_spacing_fit():
    section = SectionAssembler.rectangular(width=12, depth=24, cover=1.5)
    assembler = ReinforcementAssembler(section=section, stirrup_bar=BarTag.B10)

    with pytest.raises(ValueError):
        assembler.cage(
            longitudinal_specs=(
                LongitudinalLayerSpec(
                    face=LongitudinalFace.BOTTOM,
                    bar_tag=BarTag.B25,
                    count=4,
                    lap_splice_bar_tag=BarTag.B25,
                ),
            )
        )


def test_two_zone_transverse_layout_creates_support_and_midspan_zones():
    section = SectionAssembler.rectangular(width=12, depth=24, cover=1.5)
    assembler = ReinforcementAssembler(section=section)
    zones = assembler.two_zone_transverse(
        span_length=240,
        support_zone_length=48,
        support_bar=BarTag.B10,
        support_spacing=4,
        midspan_bar=BarTag.B10,
        midspan_spacing=8,
    )

    assert [zone.kind for zone in zones] == [
        TransverseZoneKind.LEFT_SUPPORT,
        TransverseZoneKind.MIDSPAN,
        TransverseZoneKind.RIGHT_SUPPORT,
    ]
    assert zones[0].spacing == 4
    assert zones[1].spacing == 8


def test_cage_bridges_to_existing_shear_check_with_actual_legs_and_spacing():
    section = SectionAssembler.rectangular(width=12, depth=24, cover=1.5)
    assembler = ReinforcementAssembler(section=section, stirrup_bar=BarTag.B10)
    cage = assembler.cage(
        longitudinal_specs=(
            LongitudinalLayerSpec(LongitudinalFace.BOTTOM, BarTag.B20, 3),
        ),
        transverse_zones=(
            assembler.transverse_zone(0, 60, BarTag.B10, spacing=5, legs=4),
        ),
    )
    context = BeamDesignContext(
        section=section,
        concrete=Concrete(fc=4000),
        steel=Steel(fy=60000),
        reinforcement=ReinforcementLayout(cage=cage),
        load=FactoredLoad(shear=10_000),
    )
    result = ACIShearStrengthCheck().check(context)

    assert result.data["Vs"] > 0
    assert result.capacity > 10_000
    assert context.effective_depth == cage.bottom_centroid_y_from_top


def test_explicit_longitudinal_layers_allow_nonuniform_t_beam_flange_detailing():
    section = SectionAssembler.t_beam(
        web_width=18,
        total_depth=30,
        flange_width=120,
        flange_thickness=7,
        cover=1.5,
    )
    assembler = ReinforcementAssembler(section=section, stirrup_bar=BarTag.B10)
    top_distance = 1.5 + RebarCatalog.get(BarTag.B10).diameter_in + RebarCatalog.get(BarTag.B25).diameter_in / 2

    web_bars = assembler.explicit_longitudinal_layer(
        face=LongitudinalFace.TOP,
        bar_tag=BarTag.B25,
        x_positions=(55.0, 57.5, 60.0, 62.5, 65.0),
        distance_from_face=top_distance,
        placement_label="web main top bars",
    )
    ln_over_10_bars = assembler.explicit_longitudinal_layer(
        face=LongitudinalFace.TOP,
        bar_tag=BarTag.B25,
        x_positions=(44.0, 76.0),
        distance_from_face=top_distance,
        placement_label="ln/10 distribution main top bars",
    )
    outer_flange_bars = assembler.explicit_longitudinal_layer(
        face=LongitudinalFace.TOP,
        bar_tag=BarTag.B16,
        x_positions=(10.0, 20.0, 30.0, 90.0, 100.0, 110.0),
        distance_from_face=top_distance,
        placement_label="outer flange crack-control bars",
    )
    cage = assembler.cage(
        explicit_longitudinal_layers=(web_bars, ln_over_10_bars, outer_flange_bars)
    )

    assert len(cage.top_layers) == 3
    assert cage.top_layers[0].placement_label == "web main top bars"
    assert cage.top_layers[1].placement_label == "ln/10 distribution main top bars"
    assert cage.top_layers[2].placement_label == "outer flange crack-control bars"
    assert cage.top_layers[0].y_from_top == cage.top_layers[1].y_from_top == cage.top_layers[2].y_from_top
    assert pytest.approx(cage.top_layers[0].x_positions[0] - cage.top_layers[1].x_positions[0]) == 11.0
    assert pytest.approx(cage.top_layers[1].x_positions[1] - cage.top_layers[0].x_positions[-1]) == 11.0
    assert pytest.approx(cage.top_layers[1].width) == 32.0
    assert cage.top_area == pytest.approx(7 * RebarCatalog.get(BarTag.B25).area_in2 + 6 * RebarCatalog.get(BarTag.B16).area_in2)


def test_explicit_bar_positions_are_checked_against_gross_section_width():
    section = SectionAssembler.t_beam(
        web_width=18,
        total_depth=30,
        flange_width=120,
        flange_thickness=7,
        cover=1.5,
    )
    assembler = ReinforcementAssembler(section=section)

    with pytest.raises(ValueError):
        assembler.explicit_longitudinal_layer(
            face=LongitudinalFace.TOP,
            bar_tag=BarTag.B25,
            x_positions=(10.0, 125.0),
        )


def test_transverse_zone_is_selected_by_section_location():
    section = SectionAssembler.rectangular(width=12, depth=24, cover=1.5)
    assembler = ReinforcementAssembler(section=section, stirrup_bar=BarTag.B10)
    cage = assembler.cage(
        longitudinal_specs=(
            LongitudinalLayerSpec(LongitudinalFace.BOTTOM, BarTag.B20, 3),
        ),
        transverse_zones=assembler.two_zone_transverse(
            span_length=240,
            support_zone_length=48,
            support_bar=BarTag.B10,
            support_spacing=4,
            midspan_bar=BarTag.B10,
            midspan_spacing=10,
        ),
    )
    support_context = BeamDesignContext(
        section=section,
        concrete=Concrete(fc=4000),
        steel=Steel(fy=60000),
        reinforcement=ReinforcementLayout(cage=cage),
        load=FactoredLoad(shear=10_000),
        metadata={"transverse_position": 12},
    )
    midspan_context = BeamDesignContext(
        section=section,
        concrete=Concrete(fc=4000),
        steel=Steel(fy=60000),
        reinforcement=ReinforcementLayout(cage=cage),
        load=FactoredLoad(shear=10_000),
        metadata={"transverse_position": 120},
    )

    support_vs = ACIShearStrengthCheck().check(support_context).data["Vs"]
    midspan_vs = ACIShearStrengthCheck().check(midspan_context).data["Vs"]

    assert support_vs > midspan_vs


def test_aci_full_beam_accepts_cage_reinforcement():
    section = SectionAssembler.rectangular(width=12, depth=24, cover=1.5)
    assembler = ReinforcementAssembler(section=section, stirrup_bar=BarTag.B10)
    cage = assembler.cage(
        longitudinal_specs=(
            LongitudinalLayerSpec(LongitudinalFace.BOTTOM, BarTag.B20, 3),
        ),
        transverse_zones=(
            assembler.transverse_zone(0, 60, BarTag.B10, spacing=6, legs=2),
        ),
    )
    context = BeamDesignContext(
        section=section,
        concrete=Concrete(fc=5000),
        steel=Steel(fy=60000),
        reinforcement=ReinforcementLayout(cage=cage),
        load=FactoredLoad(moment=100_000, shear=10_000),
        metadata={
            "aci_exposure_classes": ("F3",),
            "development_length_provided": 30,
        },
    )

    results = ACI318().all_rules()

    assert results
    assert context.reinforcement.tension_area == cage.bottom_area
