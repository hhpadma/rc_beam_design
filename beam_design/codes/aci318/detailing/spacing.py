from dataclasses import dataclass

from beam_design.core.model import BeamDesignContext
from beam_design.core.reinforcement import LongitudinalBarLayer
from beam_design.core.result import CheckResult


@dataclass(frozen=True)
class ACIStirrupSpacingCheck:
    check_id: str = "aci318.detailing.stirrup_spacing"
    title: str = "Stirrup spacing"

    def check(self, context: BeamDesignContext) -> CheckResult:
        position = float(context.metadata.get("transverse_position", 0.0))
        spacing = context.reinforcement.stirrup_spacing_at(position)
        if spacing is None:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "No stirrup spacing is defined.",
            )

        limit = min(context.effective_depth / 2, 24.0)
        kwargs = {
            "demand": spacing,
            "capacity": limit,
            "ratio": spacing / limit if limit else None,
            "references": ("ACI 318 stirrup spacing requirements",),
        }
        if spacing <= limit:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult.fail_result(self.check_id, self.title, **kwargs)


@dataclass(frozen=True)
class ACILongitudinalLayerFit:
    available_width_in: float
    required_width_in: float
    clear_spacing_in: float | None
    minimum_clear_spacing_in: float
    bar_count: int
    bar_diameter_in: float

    @property
    def fits(self) -> bool:
        return self.available_width_in >= self.required_width_in


def minimum_longitudinal_clear_spacing(
    bar_diameter_in: float,
    *,
    nominal_max_aggregate_size_in: float | None = None,
    clear_spacing_floor_in: float = 1.0,
) -> float:
    """ACI 318-14 25.2.1 clear spacing for parallel longitudinal bars."""

    if bar_diameter_in <= 0:
        raise ValueError("Bar diameter must be positive.")
    if clear_spacing_floor_in <= 0:
        raise ValueError("Clear spacing floor must be positive.")
    values = [clear_spacing_floor_in, bar_diameter_in]
    if nominal_max_aggregate_size_in is not None:
        if nominal_max_aggregate_size_in <= 0:
            raise ValueError("Nominal maximum aggregate size must be positive.")
        values.append(4.0 * nominal_max_aggregate_size_in / 3.0)
    return max(values)


def longitudinal_layer_required_width(
    bar_count: int,
    bar_diameter_in: float,
    minimum_clear_spacing_in: float,
    *,
    clear_cover_in: float,
    transverse_bar_diameter_in: float = 0.0,
    side_bar_center_offset_inside_transverse_in: float = 0.75,
) -> float:
    """SP-17-style required web width demonstration for one bar layer."""

    if bar_count <= 0:
        raise ValueError("Bar count must be positive.")
    _validate_nonnegative(
        bar_diameter_in=bar_diameter_in,
        minimum_clear_spacing_in=minimum_clear_spacing_in,
        clear_cover_in=clear_cover_in,
        transverse_bar_diameter_in=transverse_bar_diameter_in,
        side_bar_center_offset_inside_transverse_in=side_bar_center_offset_inside_transverse_in,
    )
    if bar_count == 1:
        return 2.0 * (clear_cover_in + transverse_bar_diameter_in + side_bar_center_offset_inside_transverse_in)
    return (
        2.0 * (clear_cover_in + transverse_bar_diameter_in + side_bar_center_offset_inside_transverse_in)
        + (bar_count - 1) * bar_diameter_in
        + (bar_count - 1) * minimum_clear_spacing_in
    )


def longitudinal_layer_fit(
    web_width_in: float,
    bar_count: int,
    bar_diameter_in: float,
    minimum_clear_spacing_in: float,
    *,
    clear_cover_in: float,
    transverse_bar_diameter_in: float = 0.0,
    side_bar_center_offset_inside_transverse_in: float = 0.75,
) -> ACILongitudinalLayerFit:
    """Check if one longitudinal layer fits inside the web."""

    if web_width_in <= 0:
        raise ValueError("Web width must be positive.")
    required = longitudinal_layer_required_width(
        bar_count=bar_count,
        bar_diameter_in=bar_diameter_in,
        minimum_clear_spacing_in=minimum_clear_spacing_in,
        clear_cover_in=clear_cover_in,
        transverse_bar_diameter_in=transverse_bar_diameter_in,
        side_bar_center_offset_inside_transverse_in=side_bar_center_offset_inside_transverse_in,
    )
    clear_spacing = None
    if bar_count > 1:
        clear_spacing = (
            web_width_in
            - 2.0 * (clear_cover_in + transverse_bar_diameter_in + side_bar_center_offset_inside_transverse_in)
        ) / (bar_count - 1) - bar_diameter_in
    return ACILongitudinalLayerFit(
        available_width_in=web_width_in,
        required_width_in=required,
        clear_spacing_in=clear_spacing,
        minimum_clear_spacing_in=minimum_clear_spacing_in,
        bar_count=bar_count,
        bar_diameter_in=bar_diameter_in,
    )


@dataclass(frozen=True)
class ACILongitudinalBarClearSpacingCheck:
    check_id: str = "aci318.detailing.longitudinal_bar_clear_spacing"
    title: str = "Longitudinal bar clear spacing"

    def check(self, context: BeamDesignContext) -> CheckResult:
        if context.reinforcement.cage is None:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "No reinforcement cage is defined.",
            )

        aggregate_size = context.metadata.get("aci_nominal_max_aggregate_size_in")
        checked: list[dict[str, object]] = []
        failing: list[dict[str, object]] = []
        for layer in context.reinforcement.cage.longitudinal_layers:
            if layer.clear_spacing is None:
                continue
            required = minimum_longitudinal_clear_spacing(
                layer.bar_diameter,
                nominal_max_aggregate_size_in=float(aggregate_size) if aggregate_size is not None else None,
            )
            row = _layer_spacing_row(layer, required)
            checked.append(row)
            if layer.clear_spacing < required:
                failing.append(row)

        if not checked:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "No multi-bar longitudinal layers are available to check.",
            )

        governing = min(checked, key=lambda row: row["ratio"])
        kwargs = {
            "demand": governing["clear_spacing_in"],
            "capacity": governing["required_clear_spacing_in"],
            "ratio": governing["ratio"],
            "references": ("ACI 318-14 25.2.1",),
            "data": {
                "layers": checked,
                "failing_layers": failing,
            },
        }
        if failing:
            return CheckResult.fail_result(self.check_id, self.title, **kwargs)
        return CheckResult.pass_result(self.check_id, self.title, **kwargs)


def _layer_spacing_row(layer: LongitudinalBarLayer, required_spacing_in: float) -> dict[str, object]:
    return {
        "face": layer.face.value,
        "bar_tag": layer.bar_tag.value,
        "bar_count": layer.count,
        "placement_label": layer.placement_label,
        "clear_spacing_in": layer.clear_spacing,
        "required_clear_spacing_in": required_spacing_in,
        "ratio": layer.clear_spacing / required_spacing_in if required_spacing_in else None,
    }


def _validate_nonnegative(**values: float) -> None:
    for name, value in values.items():
        if value < 0:
            raise ValueError(f"{name} cannot be negative.")
