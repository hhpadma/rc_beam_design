from dataclasses import dataclass

from beam_design.core.actions import ActionComponent, ActionSet, ActionType


@dataclass(frozen=True)
class ACIMomentCoefficient:
    """Moment coefficient in the form M = sign * w * ln^2 / divisor."""

    divisor: float
    label: str
    sign: float = 1.0

    def __post_init__(self) -> None:
        if self.divisor <= 0:
            raise ValueError("Moment coefficient divisor must be positive.")


@dataclass(frozen=True)
class ACIShearCoefficient:
    """Shear coefficient in the form V = factor * w * ln."""

    factor: float
    label: str


@dataclass(frozen=True)
class ACICoefficientBeamActionBuilder:
    """Convert line-load actions into beam moment/shear actions.

    The coefficient values are supplied by the calling code/check because ACI
    approximate coefficients depend on continuity, span location, and load
    pattern. This class enforces the process: line-load actions are converted
    to actions first, and only then combined by ACI load combinations.
    """

    span_ft: float

    def __post_init__(self) -> None:
        if self.span_ft <= 0:
            raise ValueError("Span length must be positive.")

    def moment_actions(
        self,
        line_actions: ActionSet,
        coefficient: ACIMomentCoefficient,
        label: str = "ACI coefficient moment actions",
    ) -> ActionSet:
        self._validate_line_actions(line_actions)
        return ActionSet(
            components=tuple(
                ActionComponent(
                    source=component.source,
                    value=coefficient.sign * component.value * self.span_ft**2 / coefficient.divisor,
                    action_type=ActionType.MOMENT,
                    label=f"{component.label}: {coefficient.label}".strip(": "),
                )
                for component in line_actions.components
            ),
            action_type=ActionType.MOMENT,
            label=label,
        )

    def shear_actions(
        self,
        line_actions: ActionSet,
        coefficient: ACIShearCoefficient,
        label: str = "ACI coefficient shear actions",
    ) -> ActionSet:
        self._validate_line_actions(line_actions)
        return ActionSet(
            components=tuple(
                ActionComponent(
                    source=component.source,
                    value=coefficient.factor * component.value * self.span_ft,
                    action_type=ActionType.SHEAR,
                    label=f"{component.label}: {coefficient.label}".strip(": "),
                )
                for component in line_actions.components
            ),
            action_type=ActionType.SHEAR,
            label=label,
        )

    def _validate_line_actions(self, actions: ActionSet) -> None:
        if actions.action_type != ActionType.LINE_LOAD:
            raise ValueError("ACI coefficient method requires line-load actions as input.")
