from dataclasses import dataclass
from enum import Enum

from beam_design.core.actions import ActionSet, ActionType


class CriticalLocationRole(Enum):
    LEFT_SUPPORT = "left_support"
    MIDSPAN = "midspan"
    RIGHT_SUPPORT = "right_support"
    LEFT_SHEAR = "left_shear"
    RIGHT_SHEAR = "right_shear"


@dataclass(frozen=True)
class CriticalSectionActions:
    """Factored design actions at a named beam location."""

    name: str
    moment: float
    shear: float
    torsion: float | None = None
    position_ft: float | None = None


@dataclass(frozen=True)
class CriticalActionRecord:
    """Single stored demand at a critical beam location.

    Flexure and shear are stored independently because their critical locations
    are often different. The design_group field links records that should be
    merged for constructibility, such as adjacent support faces.
    """

    id: str
    span_index: int
    role: CriticalLocationRole
    action_type: ActionType
    value: float
    position_ft: float
    local_position_ft: float
    design_group: str
    label: str = ""
    source: str = "U"

    @property
    def magnitude(self) -> float:
        return abs(self.value)


@dataclass(frozen=True)
class SpanActionTable:
    """Critical actions stored in a tabular, span-aware form."""

    span_lengths_ft: tuple[float, ...]
    records: tuple[CriticalActionRecord, ...] = ()
    label: str = "beam action table"

    def by_span(self, span_index: int) -> tuple[CriticalActionRecord, ...]:
        return tuple(record for record in self.records if record.span_index == span_index)

    def by_action_type(self, action_type: ActionType) -> tuple[CriticalActionRecord, ...]:
        return tuple(record for record in self.records if record.action_type == action_type)

    def design_groups(self, action_type: ActionType | None = None) -> dict[str, tuple[CriticalActionRecord, ...]]:
        groups: dict[str, list[CriticalActionRecord]] = {}
        for record in self.records:
            if action_type is not None and record.action_type != action_type:
                continue
            groups.setdefault(record.design_group, []).append(record)
        return {name: tuple(records) for name, records in groups.items()}

    def governing_by_group(self, action_type: ActionType | None = None) -> dict[str, CriticalActionRecord]:
        return {
            group: max(records, key=lambda record: record.magnitude)
            for group, records in self.design_groups(action_type).items()
        }

    def rows(self) -> tuple[dict[str, object], ...]:
        return tuple(
            {
                "id": record.id,
                "span": record.span_index + 1,
                "role": record.role.value,
                "action_type": record.action_type.value,
                "value": record.value,
                "position_ft": record.position_ft,
                "local_position_ft": record.local_position_ft,
                "design_group": record.design_group,
                "label": record.label,
            }
            for record in self.records
        )


@dataclass(frozen=True)
class BeamAnalysisResult:
    """Code-neutral result of beam analysis."""

    applicable: bool
    messages: tuple[str, ...]
    critical_sections: tuple[CriticalSectionActions, ...] = ()
    factored_line_load_klf: float | None = None
    governing_combination: str | None = None
    moment_actions: ActionSet | None = None
    shear_actions: ActionSet | None = None
    action_table: SpanActionTable | None = None
