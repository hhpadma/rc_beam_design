from dataclasses import dataclass

from beam_design.core.actions import ActionComponent, ActionSet, ActionType, LineLoad, SurfaceLoad
from beam_design.core.model import Section
from beam_design.section_assembler import SectionAssembly
from beam_design.section_calculations import SectionSelfWeightCalculator


SectionSource = SectionAssembly | Section


@dataclass(frozen=True)
class BeamLineActionBuilder:
    """Convert beam loads to line-load actions before analysis.

    The builder is code-neutral. It may include self-weight from an explicit
    review section, or from a configured default section during early design.
    """

    surface_loads: tuple[SurfaceLoad, ...] = ()
    line_loads: tuple[LineLoad, ...] = ()
    default_section: SectionSource | None = None
    self_weight: SectionSelfWeightCalculator | None = None
    include_self_weight: bool = True
    label: str = "beam line-load actions"

    def line_actions(self, section: SectionSource | None = None) -> ActionSet:
        components: list[ActionComponent] = []
        self_weight_section = section if section is not None else self.default_section
        if self.include_self_weight:
            if self_weight_section is None:
                raise ValueError("Self-weight requires either an explicit section or a default section.")
            calculator = self.self_weight or SectionSelfWeightCalculator()
            components.append(calculator.action(self_weight_section))

        components.extend(load.to_line_action() for load in self.line_loads)
        components.extend(load.to_line_action() for load in self.surface_loads)
        return ActionSet(
            components=tuple(components),
            action_type=ActionType.LINE_LOAD,
            label=self.label,
        )
