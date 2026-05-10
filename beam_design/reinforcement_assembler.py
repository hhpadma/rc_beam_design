from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from itertools import groupby

from beam_design.core.model import Section
from beam_design.core.reinforcement import (
    LongitudinalBarLayer,
    LongitudinalFace,
    LongitudinalLayerSpec,
    ReinforcementCage,
    TransversePurpose,
    TransverseReinforcementZone,
    TransverseZoneKind,
)
from beam_design.rebar import BarTag, RebarCatalog


PlacementRule = Callable[["ReinforcementAssembler", tuple[LongitudinalLayerSpec, ...]], None]


@dataclass(frozen=True)
class ReinforcementAssembler:
    section: Section
    clear_cover: float | None = None
    stirrup_bar: BarTag | None = None
    side_clear_spacing_min: float = 1.0
    vertical_clear_spacing_min: float = 1.0
    aggregate_size: float | None = None
    placement_rules: tuple[PlacementRule, ...] = ()

    @property
    def cover(self) -> float:
        return self.section.cover if self.clear_cover is None else self.clear_cover

    @property
    def stirrup_diameter(self) -> float:
        if self.stirrup_bar is None:
            return 0.0
        return RebarCatalog.get(self.stirrup_bar).diameter_in

    def longitudinal_layers(self, specs: tuple[LongitudinalLayerSpec, ...]) -> tuple[LongitudinalBarLayer, ...]:
        for rule in self.placement_rules:
            rule(self, specs)

        layers: list[LongitudinalBarLayer] = []
        indexed_specs = tuple(enumerate(specs))
        ordered_specs = sorted(indexed_specs, key=lambda item: (item[1].face.value, item[0]))

        for face, grouped_specs in groupby(ordered_specs, key=lambda item: item[1].face):
            distance_from_face = 0.0
            previous_diameter: float | None = None
            for _, spec in grouped_specs:
                distance_from_face = self._next_layer_distance_from_face(
                    spec.bar_diameter,
                    previous_diameter,
                    distance_from_face,
                )
                y = self._layer_y(face, distance_from_face)
                x_positions, clear_spacing = self._bar_x_positions(spec)
                self._check_horizontal_spacing(spec, clear_spacing)
                layers.append(
                    LongitudinalBarLayer(
                        face=face,
                        bar_tag=spec.bar_tag,
                        count=spec.count,
                        y_from_top=y,
                        x_positions=x_positions,
                        clear_spacing=clear_spacing,
                        lap_splice_bar_tag=spec.lap_splice_bar_tag,
                    )
                )
                previous_diameter = spec.bar_diameter

        return tuple(layers)

    def cage(
        self,
        longitudinal_specs: tuple[LongitudinalLayerSpec, ...] = (),
        explicit_longitudinal_layers: tuple[LongitudinalBarLayer, ...] = (),
        transverse_zones: tuple[TransverseReinforcementZone, ...] = (),
    ) -> ReinforcementCage:
        return ReinforcementCage(
            longitudinal_layers=(
                *self.longitudinal_layers(longitudinal_specs),
                *explicit_longitudinal_layers,
            ),
            transverse_zones=transverse_zones,
        )

    def explicit_longitudinal_layer(
        self,
        face: LongitudinalFace,
        bar_tag: BarTag,
        x_positions: tuple[float, ...],
        *,
        y_from_top: float | None = None,
        distance_from_face: float | None = None,
        clear_spacing: float | None = None,
        lap_splice_bar_tag: BarTag | None = None,
        placement_label: str | None = None,
    ) -> LongitudinalBarLayer:
        """Create a bar layer from explicit section x-coordinates.

        Use this for detailing cases where bars are not uniformly distributed
        across the web, such as top bars extending into a T-beam flange.
        Coordinates are measured from the left edge of the gross section.
        """

        if isinstance(face, str):
            face = LongitudinalFace(face.lower())
        bar_tag = RebarCatalog.coerce_tag(bar_tag)
        if not x_positions:
            raise ValueError("At least one bar position is required.")
        width = self.section.gross_width
        if any(x < 0 or x > width for x in x_positions):
            raise ValueError("Explicit bar positions must lie within the gross section width.")
        if y_from_top is not None and distance_from_face is not None:
            raise ValueError("Use either y_from_top or distance_from_face, not both.")
        bar_diameter = RebarCatalog.get(bar_tag).diameter_in
        if y_from_top is None:
            if distance_from_face is None:
                distance_from_face = self.cover + self.stirrup_diameter + bar_diameter / 2.0
            y_from_top = self._layer_y(face, distance_from_face)
        if y_from_top < 0 or y_from_top > self.section.depth:
            raise ValueError("Layer y-coordinate must lie within the section depth.")

        positions = tuple(sorted(float(x) for x in x_positions))
        spacing = clear_spacing
        if spacing is None and len(positions) > 1:
            spacing = min(
                right - left - bar_diameter
                for left, right in zip(positions, positions[1:])
            )
        if spacing is not None and spacing < 0:
            raise ValueError("Explicit bar positions overlap.")

        return LongitudinalBarLayer(
            face=face,
            bar_tag=bar_tag,
            count=len(positions),
            y_from_top=float(y_from_top),
            x_positions=positions,
            clear_spacing=spacing,
            lap_splice_bar_tag=lap_splice_bar_tag,
            placement_label=placement_label,
        )

    def transverse_zone(
        self,
        start: float,
        end: float,
        bar_tag: BarTag,
        spacing: float,
        legs: int = 2,
        kind: TransverseZoneKind = TransverseZoneKind.CUSTOM,
        purposes: tuple[TransversePurpose, ...] = (TransversePurpose.SHEAR,),
        hook_angle: int = 135,
    ) -> TransverseReinforcementZone:
        return TransverseReinforcementZone(
            start=start,
            end=end,
            bar_tag=bar_tag,
            spacing=spacing,
            legs=legs,
            kind=kind,
            purposes=purposes,
            hook_angle=hook_angle,
        )

    def two_zone_transverse(
        self,
        span_length: float,
        support_zone_length: float,
        support_bar: BarTag,
        support_spacing: float,
        midspan_bar: BarTag,
        midspan_spacing: float,
        legs: int = 2,
        right_support_zone_length: float | None = None,
        purposes: tuple[TransversePurpose, ...] = (TransversePurpose.SHEAR,),
    ) -> tuple[TransverseReinforcementZone, ...]:
        if span_length <= 0:
            raise ValueError("Span length must be positive.")
        if support_zone_length <= 0:
            raise ValueError("Support zone length must be positive.")
        right_support_zone_length = support_zone_length if right_support_zone_length is None else right_support_zone_length
        if support_zone_length + right_support_zone_length >= span_length:
            raise ValueError("Support zones must leave a positive midspan zone.")

        return (
            self.transverse_zone(
                start=0.0,
                end=support_zone_length,
                bar_tag=support_bar,
                spacing=support_spacing,
                legs=legs,
                kind=TransverseZoneKind.LEFT_SUPPORT,
                purposes=purposes,
            ),
            self.transverse_zone(
                start=support_zone_length,
                end=span_length - right_support_zone_length,
                bar_tag=midspan_bar,
                spacing=midspan_spacing,
                legs=legs,
                kind=TransverseZoneKind.MIDSPAN,
                purposes=purposes,
            ),
            self.transverse_zone(
                start=span_length - right_support_zone_length,
                end=span_length,
                bar_tag=support_bar,
                spacing=support_spacing,
                legs=legs,
                kind=TransverseZoneKind.RIGHT_SUPPORT,
                purposes=purposes,
            ),
        )

    def _bar_x_positions(self, spec: LongitudinalLayerSpec) -> tuple[tuple[float, ...], float | None]:
        available_width = self.section.width - 2 * (self.cover + self.stirrup_diameter)
        if available_width <= 0:
            raise ValueError("No horizontal space remains inside cover and stirrup.")

        occupied_width = spec.count * spec.placement_width_per_bar
        if spec.count == 1:
            return (self.section.width / 2,), None

        clear_spacing = (available_width - occupied_width) / (spec.count - 1)
        if clear_spacing < 0:
            raise ValueError("Bars do not fit within the available section width.")

        start_x = self.cover + self.stirrup_diameter + spec.placement_width_per_bar / 2
        pitch = spec.placement_width_per_bar + clear_spacing
        return tuple(start_x + i * pitch for i in range(spec.count)), clear_spacing

    def _next_layer_distance_from_face(
        self,
        bar_diameter: float,
        previous_diameter: float | None,
        previous_distance_from_face: float,
    ) -> float:
        if previous_diameter is None:
            return self.cover + self.stirrup_diameter + bar_diameter / 2
        return previous_distance_from_face + previous_diameter / 2 + self.vertical_clear_spacing_min + bar_diameter / 2

    def _layer_y(self, face: LongitudinalFace, distance_from_face: float) -> float:
        if face == LongitudinalFace.TOP:
            return distance_from_face
        return self.section.depth - distance_from_face

    def _check_horizontal_spacing(self, spec: LongitudinalLayerSpec, clear_spacing: float | None) -> None:
        if clear_spacing is None:
            return
        required = self.minimum_longitudinal_clear_spacing(spec)
        if clear_spacing < required:
            raise ValueError(
                f"Clear spacing {clear_spacing:.3f} in is less than required {required:.3f} in "
                f"for {spec.count} D{spec.bar_tag.value} bars."
            )

    def minimum_longitudinal_clear_spacing(self, spec: LongitudinalLayerSpec) -> float:
        values = [self.side_clear_spacing_min, spec.bar_diameter]
        if self.aggregate_size is not None:
            values.append(4 * self.aggregate_size / 3)
        if spec.lap_splice_bar_tag is not None:
            values.append(RebarCatalog.get(spec.lap_splice_bar_tag).diameter_in)
        return max(values)
