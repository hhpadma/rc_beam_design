from dataclasses import dataclass

from beam_design.core.analysis import CriticalSectionActions
from beam_design.core.model import Section
from beam_design.section_assembler import SectionAssembly


@dataclass(frozen=True)
class SectionDesignInput:
    """Actions required to design or review a beam section."""

    moment: float
    shear: float
    torsion: float | None = None
    label: str = "section design actions"

    @classmethod
    def from_critical_section(cls, critical: CriticalSectionActions) -> "SectionDesignInput":
        return cls(
            moment=critical.moment,
            shear=critical.shear,
            torsion=critical.torsion,
            label=critical.name,
        )


@dataclass(frozen=True)
class SectionDesigner:
    """Read-only design helper for an assembled physical beam section.

    Code-specific effective flange rules and detailing checks should still live
    in code packages. This class exposes code-neutral section facts.
    """

    assembly: SectionAssembly | Section

    @property
    def section(self) -> Section:
        if isinstance(self.assembly, Section):
            return self.assembly
        return self.assembly.section

    @property
    def shape_summary(self) -> dict[str, float | str]:
        return self.section.shape.summary()

    @property
    def reinforcement_summary(self) -> dict[str, float | int | None]:
        if isinstance(self.assembly, Section):
            return {}

        cage = self.assembly.cage
        if cage is None:
            return {}

        return {
            "bottom_area": cage.bottom_area,
            "top_area": cage.top_area,
            "bottom_layers": len(cage.bottom_layers),
            "top_layers": len(cage.top_layers),
            "transverse_zones": len(cage.transverse_zones),
            "effective_depth": self.assembly.effective_depth,
        }

    @property
    def summary(self) -> dict[str, object]:
        return {
            "shape": self.shape_summary,
            "reinforcement": self.reinforcement_summary,
        }
