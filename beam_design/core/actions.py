from dataclasses import dataclass
from enum import Enum


class ActionType(Enum):
    LINE_LOAD = "line_load"
    MOMENT = "moment"
    SHEAR = "shear"
    AXIAL = "axial"
    TORSION = "torsion"
    REACTION = "reaction"


@dataclass(frozen=True)
class ActionComponent:
    """Code-neutral scalar action generated from loads, forces, or analysis."""

    source: str
    value: float
    action_type: ActionType
    label: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.action_type, str):
            object.__setattr__(self, "action_type", ActionType(self.action_type))


@dataclass(frozen=True)
class ActionSet:
    """Collection of actions for a single response type and design location."""

    components: tuple[ActionComponent, ...] = ()
    action_type: ActionType = ActionType.LINE_LOAD
    label: str = "actions"

    def by_source(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for component in self.components:
            if component.action_type != self.action_type:
                raise ValueError("ActionSet components must have the same action type.")
            totals[component.source] = totals.get(component.source, 0.0) + component.value
        return totals


@dataclass(frozen=True)
class SurfaceLoad:
    source: str
    pressure_psf: float
    tributary_width_ft: float
    label: str = ""

    def to_line_action(self) -> ActionComponent:
        return ActionComponent(
            source=self.source,
            value=self.pressure_psf * self.tributary_width_ft / 1000.0,
            action_type=ActionType.LINE_LOAD,
            label=self.label,
        )


@dataclass(frozen=True)
class LineLoad:
    source: str
    value_klf: float
    label: str = ""

    def to_line_action(self) -> ActionComponent:
        return ActionComponent(
            source=self.source,
            value=self.value_klf,
            action_type=ActionType.LINE_LOAD,
            label=self.label,
        )


class ActionAssembler:
    """Code-neutral helpers that convert loads/forces into actions."""

    @staticmethod
    def line_load_actions(*loads: SurfaceLoad | LineLoad, label: str = "line load actions") -> ActionSet:
        return ActionSet(
            components=tuple(load.to_line_action() for load in loads),
            action_type=ActionType.LINE_LOAD,
            label=label,
        )
