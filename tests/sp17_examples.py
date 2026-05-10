from dataclasses import dataclass

from beam_design.beam_loads import BeamLineActionBuilder
from beam_design.core.actions import ActionAssembler, ActionSet, LineLoad, SurfaceLoad
from beam_design.mat_concrete import Concrete
from beam_design.mat_steel import Steel
from beam_design.section_assembler import SectionAssembler, SectionAssembly
from beam_design.section_calculations import SectionSelfWeightCalculator


@dataclass(frozen=True)
class SP17BeamExample1:
    """SP-17 7.7 Beam Example 1: continuous interior beam.

    Only values visible in the provided example statement are included here.
    Missing design selections, such as beam total depth and reinforcement, are
    intentionally not assumed.
    """

    service_additional_dead_load_psf: float = 15.0
    service_live_load_psf: float = 65.0
    concrete_strength_psi: float = 5000.0
    steel_yield_strength_psi: float = 60000.0
    lambda_factor: float = 1.0
    span_ft: float = 36.0
    beam_width_in: float = 18.0
    slab_thickness_in: float = 7.0
    column_width_in: float = 24.0
    column_depth_in: float = 24.0
    tributary_width_ft: float = 14.0
    normalweight_concrete_unit_weight_pcf: float = 150.0
    selected_beam_depth_in: float = 30.0

    @property
    def span_in(self) -> float:
        return self.span_ft * 12.0

    @property
    def clear_span_in(self) -> float:
        return self.span_in - self.column_width_in

    @property
    def tributary_width_in(self) -> float:
        return self.tributary_width_ft * 12.0

    @property
    def service_additional_dead_line_load_plf(self) -> float:
        return self.service_additional_dead_load_psf * self.tributary_width_ft

    @property
    def service_live_line_load_plf(self) -> float:
        return self.service_live_load_psf * self.tributary_width_ft

    @property
    def slab_self_weight_psf(self) -> float:
        return self.normalweight_concrete_unit_weight_pcf * self.slab_thickness_in / 12.0

    @property
    def slab_self_weight_line_load_plf(self) -> float:
        slab_width_ft = self.tributary_width_ft - self.beam_width_in / 12.0
        return self.slab_self_weight_psf * slab_width_ft

    @property
    def beam_self_weight_klf(self) -> float:
        return (
            self.beam_width_in
            * self.selected_beam_depth_in
            / 144.0
            * self.normalweight_concrete_unit_weight_pcf
            / 1000.0
        )

    @property
    def slab_self_weight_klf(self) -> float:
        return self.slab_self_weight_line_load_plf / 1000.0

    @property
    def additional_dead_load_klf(self) -> float:
        return self.service_additional_dead_line_load_plf / 1000.0

    @property
    def live_load_klf(self) -> float:
        return self.service_live_line_load_plf / 1000.0

    @property
    def total_dead_load_klf(self) -> float:
        return self.beam_self_weight_klf + self.slab_self_weight_klf + self.additional_dead_load_klf

    @property
    def factored_dead_only_load_klf(self) -> float:
        return 1.4 * self.total_dead_load_klf

    @property
    def factored_dead_live_load_klf(self) -> float:
        return 1.2 * self.total_dead_load_klf + 1.6 * self.live_load_klf

    @property
    def clear_distance_to_next_beam_in(self) -> float:
        return self.tributary_width_in

    @property
    def aci_interior_t_beam_overhang_limit_in(self) -> float:
        return min(
            self.clear_span_in / 8.0,
            8.0 * self.slab_thickness_in,
            self.clear_distance_to_next_beam_in / 2.0,
        )

    @property
    def aci_interior_t_beam_clear_span_overhang_limit_in(self) -> float:
        return min(
            self.clear_span_in / 8.0,
            8.0 * self.slab_thickness_in,
            self.clear_distance_to_next_beam_in / 2.0,
        )

    @property
    def aci_example_effective_flange_width_in(self) -> float:
        return self.beam_width_in + 2.0 * self.aci_interior_t_beam_clear_span_overhang_limit_in

    @property
    def aci_minimum_depth_one_end_continuous_in(self) -> float:
        return self.span_in / 18.5

    @property
    def aci_interior_t_beam_effective_flange_width_in(self) -> float:
        return self.beam_width_in + 2.0 * self.aci_interior_t_beam_overhang_limit_in

    def concrete(self) -> Concrete:
        return Concrete(fc=self.concrete_strength_psi)

    def steel(self) -> Steel:
        return Steel(fy=self.steel_yield_strength_psi)

    def rectangular_beam_assembly(self) -> SectionAssembly:
        return SectionAssembler.rectangular_assembly(
            width=self.beam_width_in,
            depth=self.selected_beam_depth_in,
            clear_cover=1.5,
        )

    def section_self_weight_action(self):
        return SectionSelfWeightCalculator(
            unit_weight_pcf=self.normalweight_concrete_unit_weight_pcf,
            source="D",
            label="beam self-weight",
        ).action(self.rectangular_beam_assembly())

    def line_load_actions(self) -> ActionSet:
        slab_width_ft = self.tributary_width_ft - self.beam_width_in / 12.0
        return BeamLineActionBuilder(
            default_section=self.rectangular_beam_assembly(),
            self_weight=SectionSelfWeightCalculator(
                unit_weight_pcf=self.normalweight_concrete_unit_weight_pcf,
                source="D",
                label="beam self-weight",
            ),
            surface_loads=(
                SurfaceLoad(
                    source="D",
                    pressure_psf=self.slab_self_weight_psf,
                    tributary_width_ft=slab_width_ft,
                    label="slab self-weight",
                ),
                SurfaceLoad(
                    source="D",
                    pressure_psf=self.service_additional_dead_load_psf,
                    tributary_width_ft=self.tributary_width_ft,
                    label="additional dead load",
                ),
                SurfaceLoad(
                    source="L",
                    pressure_psf=self.service_live_load_psf,
                    tributary_width_ft=self.tributary_width_ft,
                    label="live load",
                ),
            ),
            label="SP-17 Beam Example 1 line-load actions",
        ).line_actions()

    def rounded_handbook_line_load_actions(self) -> ActionSet:
        return ActionAssembler.line_load_actions(
            LineLoad(source="D", value_klf=2.6 / 1.4, label="rounded service dead action"),
            LineLoad(source="L", value_klf=self.live_load_klf, label="service live action"),
            label="SP-17 rounded display line-load actions",
        )


SP17_BEAM_EXAMPLE_1 = SP17BeamExample1()
