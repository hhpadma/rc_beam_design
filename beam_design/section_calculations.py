from dataclasses import dataclass

from beam_design.core.actions import ActionComponent, ActionType
from beam_design.core.model import Section
from beam_design.section_assembler import SectionAssembly


@dataclass(frozen=True)
class SectionSelfWeightCalculator:
    """Calculate self-weight from the assembled section gross area."""

    unit_weight_pcf: float = 150.0
    source: str = "D"
    label: str = "section self-weight"

    def line_load_klf(self, section_source: SectionAssembly | Section) -> float:
        section = section_source.section if isinstance(section_source, SectionAssembly) else section_source
        return section.area / 144.0 * self.unit_weight_pcf / 1000.0

    def action(self, section_source: SectionAssembly | Section) -> ActionComponent:
        return ActionComponent(
            source=self.source,
            value=self.line_load_klf(section_source),
            action_type=ActionType.LINE_LOAD,
            label=self.label,
        )

    def apply(self, assembly: SectionAssembly, calculation_name: str = "self_weight_klf") -> SectionAssembly:
        return assembly.with_calculation(calculation_name, self.line_load_klf(assembly))
