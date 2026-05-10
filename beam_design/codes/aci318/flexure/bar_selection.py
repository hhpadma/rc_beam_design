from dataclasses import dataclass
from enum import Enum
from math import ceil

from beam_design.core.reinforcement import LongitudinalFace, LongitudinalLayerSpec
from beam_design.rebar import BarTag, RebarCatalog


class ACIBarSelectionMode(Enum):
    SAME_DIAMETER = "same_diameter"


@dataclass(frozen=True)
class ACIBarSelectionCandidate:
    bar_tag: BarTag
    count: int

    @property
    def provided_area_in2(self) -> float:
        return self.count * RebarCatalog.get(self.bar_tag).area_in2


@dataclass(frozen=True)
class ACIBarSelection:
    required_area_in2: float
    tension_face: LongitudinalFace
    candidates: tuple[ACIBarSelectionCandidate, ...]
    selected: ACIBarSelectionCandidate

    @property
    def provided_area_in2(self) -> float:
        return self.selected.provided_area_in2

    @property
    def provided_ratio(self) -> float:
        return self.provided_area_in2 / self.required_area_in2 if self.required_area_in2 else 0.0

    @property
    def layer_specs(self) -> tuple[LongitudinalLayerSpec, ...]:
        return (
            LongitudinalLayerSpec(
                face=self.tension_face,
                bar_tag=self.selected.bar_tag,
                count=self.selected.count,
            ),
        )


@dataclass(frozen=True)
class ACIBarSelector:
    available_bars: tuple[BarTag, ...] = tuple(bar.tag for bar in RebarCatalog.all())
    mode: ACIBarSelectionMode = ACIBarSelectionMode.SAME_DIAMETER
    preferred_bar: BarTag | None = None
    minimum_count: int = 1
    maximum_count: int | None = None

    def select(self, required_area_in2: float, tension_face: LongitudinalFace) -> ACIBarSelection:
        if required_area_in2 < 0:
            raise ValueError("Required steel area cannot be negative.")
        candidates = tuple(self._candidate(tag, required_area_in2) for tag in self.available_bars)
        candidates = tuple(candidate for candidate in candidates if self.maximum_count is None or candidate.count <= self.maximum_count)
        if not candidates:
            raise ValueError("No bar selection candidate satisfies the configured count limits.")

        if self.preferred_bar is not None:
            selected = self._candidate(self.preferred_bar, required_area_in2)
            if self.maximum_count is not None and selected.count > self.maximum_count:
                raise ValueError("Preferred bar exceeds the configured maximum count.")
        else:
            selected = min(candidates, key=lambda candidate: (candidate.provided_area_in2 - required_area_in2, candidate.count))

        return ACIBarSelection(
            required_area_in2=required_area_in2,
            tension_face=tension_face,
            candidates=candidates,
            selected=selected,
        )

    def _candidate(self, tag: BarTag, required_area_in2: float) -> ACIBarSelectionCandidate:
        tag = RebarCatalog.coerce_tag(tag)
        bar = RebarCatalog.get(tag)
        count = max(self.minimum_count, ceil(required_area_in2 / bar.area_in2)) if required_area_in2 else self.minimum_count
        return ACIBarSelectionCandidate(bar_tag=tag, count=count)
