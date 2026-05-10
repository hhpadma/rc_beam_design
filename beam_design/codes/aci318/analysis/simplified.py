from dataclasses import dataclass
from enum import Enum

from beam_design.codes.aci318.load_combinations import ACILoadCombinations, ActionPattern
from beam_design.core.analysis import (
    BeamAnalysisResult,
    CriticalActionRecord,
    CriticalLocationRole,
    CriticalSectionActions,
    SpanActionTable,
)
from beam_design.core.actions import ActionComponent, ActionSet, ActionType


class ACIApproximateMomentCase(Enum):
    POSITIVE_END_SPAN_INTEGRAL = "positive_end_span_integral"
    POSITIVE_END_SPAN_UNRESTRAINED = "positive_end_span_unrestrained"
    POSITIVE_INTERIOR_SPAN = "positive_interior_span"
    NEGATIVE_EXTERIOR_SUPPORT_SPANDREL = "negative_exterior_support_spandrel"
    NEGATIVE_EXTERIOR_SUPPORT_COLUMN = "negative_exterior_support_column"
    NEGATIVE_FIRST_INTERIOR_SUPPORT_TWO_SPANS = "negative_first_interior_support_two_spans"
    NEGATIVE_FIRST_INTERIOR_SUPPORT_MORE_THAN_TWO_SPANS = "negative_first_interior_support_more_than_two_spans"
    NEGATIVE_OTHER_SUPPORTS = "negative_other_supports"
    NEGATIVE_STIFF_SUPPORTS = "negative_stiff_supports"


class ACIApproximateShearCase(Enum):
    EXTERIOR_FACE_FIRST_INTERIOR_SUPPORT = "exterior_face_first_interior_support"
    FACE_ALL_OTHER_SUPPORTS = "face_all_other_supports"


class ACIBeamLoadApplicationLocation(Enum):
    TOP = "top"
    BOTTOM = "bottom"
    UNKNOWN = "unknown"


class ACIShearCriticalPlane(Enum):
    FACE_OF_SUPPORT = "face_of_support"
    EFFECTIVE_DEPTH_FROM_FACE = "effective_depth_from_face"


_MOMENT_DIVISORS: dict[ACIApproximateMomentCase, tuple[float, float, str]] = {
    ACIApproximateMomentCase.POSITIVE_END_SPAN_INTEGRAL: (14.0, 1.0, "positive end span, integral support"),
    ACIApproximateMomentCase.POSITIVE_END_SPAN_UNRESTRAINED: (11.0, 1.0, "positive end span, unrestrained"),
    ACIApproximateMomentCase.POSITIVE_INTERIOR_SPAN: (16.0, 1.0, "positive interior span"),
    ACIApproximateMomentCase.NEGATIVE_EXTERIOR_SUPPORT_SPANDREL: (24.0, -1.0, "negative exterior support, spandrel beam"),
    ACIApproximateMomentCase.NEGATIVE_EXTERIOR_SUPPORT_COLUMN: (16.0, -1.0, "negative exterior support, column"),
    ACIApproximateMomentCase.NEGATIVE_FIRST_INTERIOR_SUPPORT_TWO_SPANS: (9.0, -1.0, "negative first interior support, two spans"),
    ACIApproximateMomentCase.NEGATIVE_FIRST_INTERIOR_SUPPORT_MORE_THAN_TWO_SPANS: (10.0, -1.0, "negative first interior support, more than two spans"),
    ACIApproximateMomentCase.NEGATIVE_OTHER_SUPPORTS: (11.0, -1.0, "negative face of other supports"),
    ACIApproximateMomentCase.NEGATIVE_STIFF_SUPPORTS: (12.0, -1.0, "negative stiff supports"),
}

_SHEAR_FACTORS: dict[ACIApproximateShearCase, tuple[float, str]] = {
    ACIApproximateShearCase.EXTERIOR_FACE_FIRST_INTERIOR_SUPPORT: (1.15 / 2.0, "exterior face of first interior support"),
    ACIApproximateShearCase.FACE_ALL_OTHER_SUPPORTS: (1.0 / 2.0, "face of all other supports"),
}


@dataclass(frozen=True)
class ACISimplifiedAnalysisInput:
    """Inputs and assumptions for ACI 318-14 simplified analysis."""

    line_actions: ActionSet
    clear_spans_ft: tuple[float, ...]
    current_span_index: int = 0
    prismatic: bool = True
    uniformly_distributed: bool = True
    minimum_span_count: int = 2
    supports_integral: bool = True
    longer_adjacent_span_limit: float = 1.2
    include_lateral: bool = False
    default_column_support: bool = True
    load_application_location: ACIBeamLoadApplicationLocation = ACIBeamLoadApplicationLocation.TOP
    concentrated_load_between_face_and_d: bool | None = None
    effective_depth_ft: float | None = None
    shear_critical_plane: ACIShearCriticalPlane | None = None

    def __post_init__(self) -> None:
        if isinstance(self.load_application_location, str):
            object.__setattr__(
                self,
                "load_application_location",
                ACIBeamLoadApplicationLocation(self.load_application_location.lower()),
            )
        if isinstance(self.shear_critical_plane, str):
            object.__setattr__(self, "shear_critical_plane", ACIShearCriticalPlane(self.shear_critical_plane.lower()))
        if self.line_actions.action_type != ActionType.LINE_LOAD:
            raise ValueError("Simplified analysis requires distributed line-load actions.")
        if len(self.clear_spans_ft) < 1:
            raise ValueError("At least one clear span must be provided.")
        if not 0 <= self.current_span_index < len(self.clear_spans_ft):
            raise ValueError("Current span index is outside the clear span list.")
        if any(span <= 0 for span in self.clear_spans_ft):
            raise ValueError("Clear spans must be positive.")
        if self.effective_depth_ft is not None and self.effective_depth_ft <= 0:
            raise ValueError("Effective depth must be positive when provided.")

    @property
    def current_span_ft(self) -> float:
        return self.clear_spans_ft[self.current_span_index]


ACISimplifiedAnalysisResult = BeamAnalysisResult


class ACISimplifiedBeamAnalysis:
    """ACI 318-14 Section 6.5 simplified analysis for continuous beams."""

    def __init__(self, combinations: ACILoadCombinations | None = None):
        self.combinations = ACILoadCombinations() if combinations is None else combinations

    def validate(self, data: ACISimplifiedAnalysisInput) -> tuple[str, ...]:
        messages: list[str] = []
        if not data.prismatic:
            messages.append("Members are not prismatic.")
        if not data.uniformly_distributed:
            messages.append("Loads are not uniformly distributed.")
        if len(data.clear_spans_ft) < data.minimum_span_count:
            messages.append(f"At least {data.minimum_span_count} spans are required.")
        if not data.supports_integral:
            messages.append("Members are not built integrally with supports.")
        if not self._live_load_not_more_than_three_dead(data.line_actions):
            messages.append("Live load exceeds three times dead load.")
        if not self._adjacent_spans_within_limit(data.clear_spans_ft, data.longer_adjacent_span_limit):
            messages.append("Longer adjacent span exceeds the shorter span by more than 20 percent.")
        return tuple(messages)

    def analyze(
        self,
        data: ACISimplifiedAnalysisInput,
        moment_cases: tuple[ACIApproximateMomentCase, ...] | None = None,
        shear_cases: tuple[ACIApproximateShearCase, ...] | None = None,
    ) -> ACISimplifiedAnalysisResult:
        messages = self.validate(data)
        if messages:
            return ACISimplifiedAnalysisResult(applicable=False, messages=messages)

        envelope = self.combinations.action_envelope(
            ActionPattern.from_action_set(data.line_actions),
            include_lateral=data.include_lateral,
        )
        governing = envelope.governing
        wu = governing.value
        moment_actions = self.moment_actions(
            factored_line_load_klf=wu,
            span_ft=data.current_span_ft,
            cases=self._default_moment_cases(data) if moment_cases is None else moment_cases,
        )
        shear_actions = self.shear_actions(
            factored_line_load_klf=wu,
            span_ft=data.current_span_ft,
            cases=self._default_shear_cases() if shear_cases is None else shear_cases,
        )
        critical_sections = self.critical_sections(moment_actions, shear_actions)
        action_table = self.action_table(data, wu)
        return ACISimplifiedAnalysisResult(
            applicable=True,
            messages=("ACI 318-14 simplified analysis is applicable.",),
            critical_sections=critical_sections,
            factored_line_load_klf=wu,
            governing_combination=governing.label,
            moment_actions=moment_actions,
            shear_actions=shear_actions,
            action_table=action_table,
        )

    def action_table(self, data: ACISimplifiedAnalysisInput, factored_line_load_klf: float) -> SpanActionTable:
        records: list[CriticalActionRecord] = []
        station = 0.0
        support_stations = [0.0]
        for span in data.clear_spans_ft:
            station += span
            support_stations.append(station)

        for span_index, span_ft in enumerate(data.clear_spans_ft):
            left = support_stations[span_index]
            right = support_stations[span_index + 1]
            mid = left + span_ft / 2.0
            left_shear_position, left_shear_local = self._shear_position(data, span_index, CriticalLocationRole.LEFT_SHEAR, left, right)
            right_shear_position, right_shear_local = self._shear_position(data, span_index, CriticalLocationRole.RIGHT_SHEAR, left, right)
            records.extend(
                (
                    self._moment_record(data, factored_line_load_klf, span_index, CriticalLocationRole.LEFT_SUPPORT, left, 0.0),
                    self._moment_record(data, factored_line_load_klf, span_index, CriticalLocationRole.MIDSPAN, mid, span_ft / 2.0),
                    self._moment_record(data, factored_line_load_klf, span_index, CriticalLocationRole.RIGHT_SUPPORT, right, span_ft),
                    self._shear_record(
                        data,
                        factored_line_load_klf,
                        span_index,
                        CriticalLocationRole.LEFT_SHEAR,
                        left_shear_position,
                        left_shear_local,
                    ),
                    self._shear_record(
                        data,
                        factored_line_load_klf,
                        span_index,
                        CriticalLocationRole.RIGHT_SHEAR,
                        right_shear_position,
                        right_shear_local,
                    ),
                )
            )
        return SpanActionTable(
            span_lengths_ft=data.clear_spans_ft,
            records=tuple(records),
            label="ACI 318-14 simplified analysis critical action table",
        )

    def critical_sections(self, moment_actions: ActionSet, shear_actions: ActionSet) -> tuple[CriticalSectionActions, ...]:
        shear_by_label = {component.label: component.value for component in shear_actions.components}
        default_shear = max((abs(component.value) for component in shear_actions.components), default=0.0)
        sections: list[CriticalSectionActions] = []
        for component in moment_actions.components:
            shear = shear_by_label.get(component.label, default_shear)
            sections.append(
                CriticalSectionActions(
                    name=component.label,
                    moment=component.value,
                    shear=shear,
                )
            )
        if not sections:
            sections.extend(
                CriticalSectionActions(name=component.label, moment=0.0, shear=component.value)
                for component in shear_actions.components
            )
        return tuple(sections)

    def moment_actions(
        self,
        factored_line_load_klf: float,
        span_ft: float,
        cases: tuple[ACIApproximateMomentCase, ...],
    ) -> ActionSet:
        return ActionSet(
            components=tuple(
                self._moment_component(factored_line_load_klf, span_ft, case)
                for case in cases
            ),
            action_type=ActionType.MOMENT,
            label="ACI 318-14 Table 6.5.2 approximate moments",
        )

    def shear_actions(
        self,
        factored_line_load_klf: float,
        span_ft: float,
        cases: tuple[ACIApproximateShearCase, ...],
    ) -> ActionSet:
        return ActionSet(
            components=tuple(
                self._shear_component(factored_line_load_klf, span_ft, case)
                for case in cases
            ),
            action_type=ActionType.SHEAR,
            label="ACI 318-14 Table 6.5.4 approximate shears",
        )

    def _moment_component(self, wu: float, span_ft: float, case: ACIApproximateMomentCase) -> ActionComponent:
        divisor, sign, label = _MOMENT_DIVISORS[case]
        return ActionComponent(
            source="U",
            value=sign * wu * span_ft**2 / divisor,
            action_type=ActionType.MOMENT,
            label=label,
        )

    def _shear_component(self, wu: float, span_ft: float, case: ACIApproximateShearCase) -> ActionComponent:
        factor, label = _SHEAR_FACTORS[case]
        return ActionComponent(
            source="U",
            value=factor * wu * span_ft,
            action_type=ActionType.SHEAR,
            label=label,
        )

    def _moment_record(
        self,
        data: ACISimplifiedAnalysisInput,
        wu: float,
        span_index: int,
        role: CriticalLocationRole,
        position_ft: float,
        local_position_ft: float,
    ) -> CriticalActionRecord:
        span_ft = data.clear_spans_ft[span_index]
        if role == CriticalLocationRole.MIDSPAN:
            divisor = 14.0 if span_index in (0, len(data.clear_spans_ft) - 1) else 16.0
            value = wu * span_ft**2 / divisor
            group = f"span-{span_index + 1}-positive-flexure"
            label = "positive end span" if divisor == 14.0 else "positive interior span"
        else:
            support_index = span_index if role == CriticalLocationRole.LEFT_SUPPORT else span_index + 1
            divisor = self._negative_support_divisor(data, span_index, support_index)
            support_span_ft = self._negative_support_span(data.clear_spans_ft, span_index, support_index)
            value = -wu * support_span_ft**2 / divisor
            group = f"support-{support_index}-negative-flexure"
            label = f"negative support {support_index}"

        return CriticalActionRecord(
            id=f"S{span_index + 1}-{role.value}-M",
            span_index=span_index,
            role=role,
            action_type=ActionType.MOMENT,
            value=value,
            position_ft=position_ft,
            local_position_ft=local_position_ft,
            design_group=group,
            label=label,
        )

    def _shear_record(
        self,
        data: ACISimplifiedAnalysisInput,
        wu: float,
        span_index: int,
        role: CriticalLocationRole,
        position_ft: float,
        local_position_ft: float,
    ) -> CriticalActionRecord:
        span_ft = data.clear_spans_ft[span_index]
        support_index = span_index if role == CriticalLocationRole.LEFT_SHEAR else span_index + 1
        factor = self._shear_factor_for_span_face(data, span_index, role)
        sign = 1.0 if role == CriticalLocationRole.LEFT_SHEAR else -1.0
        shear_at_face = factor * wu * span_ft
        plane = self._resolved_shear_critical_plane(data)
        if plane == ACIShearCriticalPlane.EFFECTIVE_DEPTH_FROM_FACE:
            shear_magnitude = max(shear_at_face - wu * self._shear_offset_from_face_ft(data), 0.0)
            plane_label = "at d from face of support"
        else:
            shear_magnitude = shear_at_face
            plane_label = "at face of support"
        return CriticalActionRecord(
            id=f"S{span_index + 1}-{role.value}-V",
            span_index=span_index,
            role=role,
            action_type=ActionType.SHEAR,
            value=sign * shear_magnitude,
            position_ft=position_ft,
            local_position_ft=local_position_ft,
            design_group=f"support-{support_index}-shear",
            label=f"shear support {support_index}, {plane_label}",
        )

    def _resolved_shear_critical_plane(self, data: ACISimplifiedAnalysisInput) -> ACIShearCriticalPlane:
        if data.shear_critical_plane is not None:
            return data.shear_critical_plane
        if (
            data.supports_integral
            and data.load_application_location == ACIBeamLoadApplicationLocation.TOP
            and data.concentrated_load_between_face_and_d is False
            and data.effective_depth_ft is not None
        ):
            return ACIShearCriticalPlane.EFFECTIVE_DEPTH_FROM_FACE
        return ACIShearCriticalPlane.FACE_OF_SUPPORT

    def _shear_offset_from_face_ft(self, data: ACISimplifiedAnalysisInput) -> float:
        if self._resolved_shear_critical_plane(data) != ACIShearCriticalPlane.EFFECTIVE_DEPTH_FROM_FACE:
            return 0.0
        if data.effective_depth_ft is None:
            return 0.0
        return data.effective_depth_ft

    def _shear_position(
        self,
        data: ACISimplifiedAnalysisInput,
        span_index: int,
        role: CriticalLocationRole,
        left: float,
        right: float,
    ) -> tuple[float, float]:
        span_ft = data.clear_spans_ft[span_index]
        offset = self._shear_offset_from_face_ft(data)
        if role == CriticalLocationRole.LEFT_SHEAR:
            return left + offset, offset
        return right - offset, span_ft - offset

    def _negative_support_divisor(
        self,
        data: ACISimplifiedAnalysisInput,
        span_index: int,
        support_index: int,
    ) -> float:
        span_count = len(data.clear_spans_ft)
        if support_index in (0, span_count):
            return 16.0 if data.default_column_support else 24.0
        first_interior_divisor = 9.0 if span_count == 2 else 10.0
        if support_index == 1 and span_index == 0:
            return first_interior_divisor
        if support_index == span_count - 1 and span_index == span_count - 1:
            return first_interior_divisor
        return 11.0

    def _negative_support_span(self, spans: tuple[float, ...], span_index: int, support_index: int) -> float:
        if support_index == 0 or support_index == len(spans):
            return spans[span_index]
        return (spans[support_index - 1] + spans[support_index]) / 2.0

    def _shear_factor_for_span_face(
        self,
        data: ACISimplifiedAnalysisInput,
        span_index: int,
        role: CriticalLocationRole,
    ) -> float:
        span_count = len(data.clear_spans_ft)
        if role == CriticalLocationRole.RIGHT_SHEAR and span_index == 0:
            return 1.15 / 2.0
        if role == CriticalLocationRole.LEFT_SHEAR and span_index == span_count - 1:
            return 1.15 / 2.0
        return 1.0 / 2.0

    def _default_moment_cases(self, data: ACISimplifiedAnalysisInput) -> tuple[ACIApproximateMomentCase, ...]:
        exterior_case = (
            ACIApproximateMomentCase.NEGATIVE_EXTERIOR_SUPPORT_COLUMN
            if data.default_column_support
            else ACIApproximateMomentCase.NEGATIVE_EXTERIOR_SUPPORT_SPANDREL
        )
        first_interior_case = (
            ACIApproximateMomentCase.NEGATIVE_FIRST_INTERIOR_SUPPORT_TWO_SPANS
            if len(data.clear_spans_ft) == 2
            else ACIApproximateMomentCase.NEGATIVE_FIRST_INTERIOR_SUPPORT_MORE_THAN_TWO_SPANS
        )
        return (
            ACIApproximateMomentCase.POSITIVE_INTERIOR_SPAN,
            exterior_case,
            first_interior_case,
            ACIApproximateMomentCase.NEGATIVE_OTHER_SUPPORTS,
        )

    def _default_shear_cases(self) -> tuple[ACIApproximateShearCase, ...]:
        return (
            ACIApproximateShearCase.EXTERIOR_FACE_FIRST_INTERIOR_SUPPORT,
            ACIApproximateShearCase.FACE_ALL_OTHER_SUPPORTS,
        )

    def _live_load_not_more_than_three_dead(self, line_actions: ActionSet) -> bool:
        totals = line_actions.by_source()
        dead = totals.get("D", 0.0)
        live = totals.get("L", 0.0)
        if dead <= 0:
            return live <= 0
        return live <= 3.0 * dead

    def _adjacent_spans_within_limit(self, spans: tuple[float, ...], limit: float) -> bool:
        return all(max(a, b) / min(a, b) <= limit for a, b in zip(spans, spans[1:]))
