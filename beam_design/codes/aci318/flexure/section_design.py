from dataclasses import dataclass

from beam_design.codes.aci318.flexure.assumptions import compression_block_depth_from_tension, effective_depth_one_layer
from beam_design.codes.aci318.flexure.bar_selection import ACIBarSelection, ACIBarSelector
from beam_design.codes.aci318.flexure.minimum_reinforcement import (
    ACIMinimumFlexuralReinforcement,
    minimum_flexural_reinforcement_area,
)
from beam_design.codes.aci318.flexure.required_steel import RequiredSteelResult, solve_required_tension_area
from beam_design.codes.aci318.flexure.strain import ACIFlexuralStrainResult, evaluate_flexural_strain
from beam_design.core.actions import ActionType
from beam_design.core.analysis import CriticalActionRecord, CriticalLocationRole, SpanActionTable
from beam_design.core.reinforcement import LongitudinalFace
from beam_design.core.section_shapes import SectionShapeType
from beam_design.mat_concrete import Concrete
from beam_design.mat_steel import Steel
from beam_design.rebar import BarTag, RebarCatalog
from beam_design.reinforcement_assembler import PlacementRule
from beam_design.section_assembler import SectionAssembler, SectionAssembly


@dataclass(frozen=True)
class ACIFlexuralDesignSection:
    design_group: str
    governing_record: CriticalActionRecord
    records: tuple[CriticalActionRecord, ...]
    tension_face: LongitudinalFace
    compression_width_in: float
    effective_depth_in: float
    required: RequiredSteelResult
    minimum_required: ACIMinimumFlexuralReinforcement
    bar_selection: ACIBarSelection
    strain: ACIFlexuralStrainResult
    assembly: SectionAssembly

    @property
    def provided_bar(self) -> BarTag:
        return self.bar_selection.selected.bar_tag

    @property
    def provided_count(self) -> int:
        return self.bar_selection.selected.count

    @property
    def provided_area_in2(self) -> float:
        return self.bar_selection.provided_area_in2

    @property
    def provided_strength_ratio(self) -> float:
        return self.bar_selection.provided_ratio

    @property
    def governing_required_area_in2(self) -> float:
        return self.bar_selection.required_area_in2

    @property
    def minimum_reinforcement_controls(self) -> bool:
        return self.minimum_required.required_area_in2 > self.required.required_area_in2


@dataclass(frozen=True)
class ACIFlexuralSectionBuilder:
    """Thin coordinator from moment design groups to partial section assemblies."""

    base_section: SectionAssembly
    concrete: Concrete
    steel: Steel
    bar_selector: ACIBarSelector = ACIBarSelector()
    preferred_bar: BarTag | None = None
    phi_assumption: float = 0.90
    stirrup_bar: BarTag | None = None
    side_clear_spacing_min: float = 1.0
    vertical_clear_spacing_min: float = 1.0
    aggregate_size: float | None = None
    placement_rules: tuple[PlacementRule, ...] = ()

    def design_from_action_table(self, table: SpanActionTable) -> tuple[ACIFlexuralDesignSection, ...]:
        designs: list[ACIFlexuralDesignSection] = []
        for group, records in table.design_groups(ActionType.MOMENT).items():
            governing = max(records, key=lambda record: record.magnitude)
            designs.append(self.design_group(group, records, governing))
        return tuple(designs)

    def design_group(
        self,
        design_group: str,
        records: tuple[CriticalActionRecord, ...],
        governing_record: CriticalActionRecord,
    ) -> ACIFlexuralDesignSection:
        tension_face = tension_face_for_moment(governing_record)
        compression_width = self.compression_width(governing_record)
        effective_depth = self.effective_depth_for_trial_bar()
        required = solve_required_tension_area(
            moment_ft_kip=governing_record.magnitude,
            phi=self.phi_assumption,
            steel_yield_psi=self.steel.yield_strength,
            effective_depth_in=effective_depth,
            stress_block_depth=lambda area: compression_block_depth_from_tension(
                tension_area_in2=area,
                steel_stress_psi=self.steel.yield_strength,
                concrete_strength_psi=self.concrete.compressive_strength,
                compression_width_in=compression_width,
            ),
        )
        minimum_required = minimum_flexural_reinforcement_area(
            concrete_strength_psi=self.concrete.compressive_strength,
            steel_yield_psi=self.steel.yield_strength,
            web_width_in=self.base_section.web_width,
            effective_depth_in=effective_depth,
        )
        governing_required_area = max(required.required_area_in2, minimum_required.required_area_in2)
        selection = self._bar_selector().select(governing_required_area, tension_face)
        strain = evaluate_flexural_strain(
            provided_area_in2=selection.provided_area_in2,
            concrete_strength_psi=self.concrete.compressive_strength,
            steel_yield_psi=self.steel.yield_strength,
            steel_modulus_psi=self.steel.modulus_of_elasticity,
            compression_width_in=compression_width,
            effective_depth_in=effective_depth,
            ultimate_concrete_strain=self.concrete.ultimate_compressive_strain,
        )
        assembly = SectionAssembler.assemble(
            shape=self.base_section.shape,
            clear_cover=self.base_section.clear_cover,
            longitudinal_specs=selection.layer_specs,
            stirrup_bar=self.stirrup_bar,
            side_clear_spacing_min=self.side_clear_spacing_min,
            vertical_clear_spacing_min=self.vertical_clear_spacing_min,
            aggregate_size=self.aggregate_size,
            placement_rules=self.placement_rules,
        )
        return ACIFlexuralDesignSection(
            design_group=design_group,
            governing_record=governing_record,
            records=records,
            tension_face=tension_face,
            compression_width_in=compression_width,
            effective_depth_in=effective_depth,
            required=required,
            minimum_required=minimum_required,
            bar_selection=selection,
            strain=strain,
            assembly=assembly,
        )

    def compression_width(self, record: CriticalActionRecord) -> float:
        shape = self.base_section.shape
        if record.value > 0 and shape.shape_type in {SectionShapeType.T, SectionShapeType.L}:
            return self.base_section.section.gross_width
        return self.base_section.web_width

    def effective_depth_for_trial_bar(self) -> float:
        selector = self._bar_selector()
        if selector.preferred_bar is None:
            bar_diameter = 1.0
        else:
            bar_diameter = RebarCatalog.get(selector.preferred_bar).diameter_in
        stirrup_diameter = 0.5 if self.stirrup_bar is None else RebarCatalog.get(self.stirrup_bar).diameter_in
        return effective_depth_one_layer(
            total_depth_in=self.base_section.section.depth,
            clear_cover_in=self.base_section.clear_cover,
            transverse_bar_diameter_in=stirrup_diameter,
            longitudinal_bar_diameter_in=bar_diameter,
        )

    def _bar_selector(self) -> ACIBarSelector:
        if self.preferred_bar is None:
            return self.bar_selector
        return ACIBarSelector(
            available_bars=self.bar_selector.available_bars,
            mode=self.bar_selector.mode,
            preferred_bar=self.preferred_bar,
            minimum_count=self.bar_selector.minimum_count,
            maximum_count=self.bar_selector.maximum_count,
        )


def tension_face_for_moment(record: CriticalActionRecord) -> LongitudinalFace:
    if record.value < 0 or record.role in {CriticalLocationRole.LEFT_SUPPORT, CriticalLocationRole.RIGHT_SUPPORT}:
        return LongitudinalFace.TOP
    return LongitudinalFace.BOTTOM


ACIFlexuralSectionDesigner = ACIFlexuralSectionBuilder
ACIRequiredFlexuralReinforcement = RequiredSteelResult


def required_flexural_reinforcement(
    moment_ft_kip: float,
    phi: float,
    concrete_strength_psi: float,
    steel_yield_psi: float,
    compression_width_in: float,
    effective_depth_in: float,
) -> RequiredSteelResult:
    return solve_required_tension_area(
        moment_ft_kip=moment_ft_kip,
        phi=phi,
        steel_yield_psi=steel_yield_psi,
        effective_depth_in=effective_depth_in,
        stress_block_depth=lambda area: compression_block_depth_from_tension(
            tension_area_in2=area,
            steel_stress_psi=steel_yield_psi,
            concrete_strength_psi=concrete_strength_psi,
            compression_width_in=compression_width_in,
        ),
    )
