from dataclasses import dataclass, field, replace
from typing import Any

from beam_design.core.model import BeamDesignContext, FactoredLoad, ReinforcementLayout, Section
from beam_design.core.reinforcement import LongitudinalLayerSpec, ReinforcementCage, TransverseReinforcementZone
from beam_design.core.section_shapes import (
    CompositeSectionShape,
    FlangeSide,
    l_shape,
    rectangular_shape,
    t_shape,
)
from beam_design.mat_concrete import Concrete
from beam_design.mat_steel import Steel
from beam_design.rebar import BarTag
from beam_design.reinforcement_assembler import PlacementRule, ReinforcementAssembler


@dataclass(frozen=True)
class SectionAssembly:
    """Complete physical beam section: cover, shape, and reinforcement."""

    section: Section
    reinforcement: ReinforcementLayout
    calculations: dict[str, float] = field(default_factory=dict)

    @property
    def shape(self) -> CompositeSectionShape:
        return self.section.shape

    @property
    def cage(self) -> ReinforcementCage | None:
        return self.reinforcement.cage

    @property
    def clear_cover(self) -> float:
        return self.section.cover

    @property
    def effective_depth(self) -> float:
        if self.reinforcement.tension_centroid_y_from_top is not None:
            return self.reinforcement.tension_centroid_y_from_top
        bar_radius = self.reinforcement.tension_bar_diameter / 2
        return self.section.depth - self.section.cover - bar_radius

    @property
    def gross_area(self) -> float:
        return self.section.area

    @property
    def web_width(self) -> float:
        return self.section.width

    def with_calculation(self, name: str, value: float) -> "SectionAssembly":
        updated = dict(self.calculations)
        updated[name] = value
        return replace(self, calculations=updated)

    def design_context(
        self,
        concrete: Concrete,
        steel: Steel,
        load: FactoredLoad | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> BeamDesignContext:
        context_metadata = {} if metadata is None else dict(metadata)
        if self.calculations:
            context_metadata.setdefault("section_calculations", self.calculations)

        return BeamDesignContext(
            section=self.section,
            concrete=concrete,
            steel=steel,
            reinforcement=self.reinforcement,
            load=FactoredLoad() if load is None else load,
            metadata=context_metadata,
        )


@dataclass(frozen=True)
class SectionAssembler:
    """Code-neutral factory for beam sections and complete section assemblies."""

    @staticmethod
    def rectangular(width: float, depth: float, cover: float = 1.5) -> Section:
        return Section(width=width, depth=depth, cover=cover, shape=rectangular_shape(width, depth))

    @staticmethod
    def t_beam(
        web_width: float,
        total_depth: float,
        flange_width: float,
        flange_thickness: float,
        cover: float = 1.5,
    ) -> Section:
        shape = t_shape(web_width, total_depth, flange_width, flange_thickness)
        return _section_from_shape(shape, cover)

    @staticmethod
    def l_beam(
        web_width: float,
        total_depth: float,
        flange_width: float,
        flange_thickness: float,
        flange_side: FlangeSide = FlangeSide.RIGHT,
        cover: float = 1.5,
    ) -> Section:
        shape = l_shape(web_width, total_depth, flange_width, flange_thickness, flange_side)
        return _section_from_shape(shape, cover)

    @staticmethod
    def assemble(
        shape: CompositeSectionShape,
        clear_cover: float,
        longitudinal_specs: tuple[LongitudinalLayerSpec, ...] = (),
        transverse_zones: tuple[TransverseReinforcementZone, ...] = (),
        stirrup_bar: BarTag | None = None,
        side_clear_spacing_min: float = 1.0,
        vertical_clear_spacing_min: float = 1.0,
        aggregate_size: float | None = None,
        placement_rules: tuple[PlacementRule, ...] = (),
    ) -> SectionAssembly:
        section = _section_from_shape(shape, clear_cover)
        reinforcement_assembler = ReinforcementAssembler(
            section=section,
            clear_cover=clear_cover,
            stirrup_bar=stirrup_bar,
            side_clear_spacing_min=side_clear_spacing_min,
            vertical_clear_spacing_min=vertical_clear_spacing_min,
            aggregate_size=aggregate_size,
            placement_rules=placement_rules,
        )
        cage = reinforcement_assembler.cage(
            longitudinal_specs=longitudinal_specs,
            transverse_zones=transverse_zones,
        )
        return SectionAssembly(section=section, reinforcement=ReinforcementLayout(cage=cage))

    @staticmethod
    def rectangular_assembly(
        width: float,
        depth: float,
        clear_cover: float,
        longitudinal_specs: tuple[LongitudinalLayerSpec, ...] = (),
        transverse_zones: tuple[TransverseReinforcementZone, ...] = (),
        stirrup_bar: BarTag | None = None,
        side_clear_spacing_min: float = 1.0,
        vertical_clear_spacing_min: float = 1.0,
        aggregate_size: float | None = None,
        placement_rules: tuple[PlacementRule, ...] = (),
    ) -> SectionAssembly:
        return SectionAssembler.assemble(
            shape=rectangular_shape(width, depth),
            clear_cover=clear_cover,
            longitudinal_specs=longitudinal_specs,
            transverse_zones=transverse_zones,
            stirrup_bar=stirrup_bar,
            side_clear_spacing_min=side_clear_spacing_min,
            vertical_clear_spacing_min=vertical_clear_spacing_min,
            aggregate_size=aggregate_size,
            placement_rules=placement_rules,
        )

    @staticmethod
    def t_beam_assembly(
        web_width: float,
        total_depth: float,
        flange_width: float,
        flange_thickness: float,
        clear_cover: float,
        longitudinal_specs: tuple[LongitudinalLayerSpec, ...] = (),
        transverse_zones: tuple[TransverseReinforcementZone, ...] = (),
        stirrup_bar: BarTag | None = None,
        side_clear_spacing_min: float = 1.0,
        vertical_clear_spacing_min: float = 1.0,
        aggregate_size: float | None = None,
        placement_rules: tuple[PlacementRule, ...] = (),
    ) -> SectionAssembly:
        return SectionAssembler.assemble(
            shape=t_shape(web_width, total_depth, flange_width, flange_thickness),
            clear_cover=clear_cover,
            longitudinal_specs=longitudinal_specs,
            transverse_zones=transverse_zones,
            stirrup_bar=stirrup_bar,
            side_clear_spacing_min=side_clear_spacing_min,
            vertical_clear_spacing_min=vertical_clear_spacing_min,
            aggregate_size=aggregate_size,
            placement_rules=placement_rules,
        )

    @staticmethod
    def l_beam_assembly(
        web_width: float,
        total_depth: float,
        flange_width: float,
        flange_thickness: float,
        clear_cover: float,
        flange_side: FlangeSide = FlangeSide.RIGHT,
        longitudinal_specs: tuple[LongitudinalLayerSpec, ...] = (),
        transverse_zones: tuple[TransverseReinforcementZone, ...] = (),
        stirrup_bar: BarTag | None = None,
        side_clear_spacing_min: float = 1.0,
        vertical_clear_spacing_min: float = 1.0,
        aggregate_size: float | None = None,
        placement_rules: tuple[PlacementRule, ...] = (),
    ) -> SectionAssembly:
        return SectionAssembler.assemble(
            shape=l_shape(web_width, total_depth, flange_width, flange_thickness, flange_side),
            clear_cover=clear_cover,
            longitudinal_specs=longitudinal_specs,
            transverse_zones=transverse_zones,
            stirrup_bar=stirrup_bar,
            side_clear_spacing_min=side_clear_spacing_min,
            vertical_clear_spacing_min=vertical_clear_spacing_min,
            aggregate_size=aggregate_size,
            placement_rules=placement_rules,
        )


def _section_from_shape(shape: CompositeSectionShape, cover: float) -> Section:
    return Section(width=shape.web_width, depth=shape.depth, cover=cover, shape=shape)
