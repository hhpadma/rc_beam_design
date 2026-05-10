from dataclasses import dataclass

from beam_design.core.model import BeamDesignContext
from beam_design.core.reinforcement import LongitudinalBarLayer, LongitudinalFace
from beam_design.core.result import CheckResult, CheckStatus
from beam_design.core.section_shapes import SectionShapeType


@dataclass(frozen=True)
class ACIFlexuralBarSpacingLimit:
    """ACI 318-14 Table 24.3.2 for nonprestressed RC beams with deformed bars."""

    service_steel_stress_psi: float
    clear_cover_to_tension_face_in: float
    limit_in: float
    limit_by_cover_in: float
    limit_by_stress_in: float


@dataclass(frozen=True)
class ACIFlangeTensionDistributionRequirement:
    effective_flange_width_in: float
    clear_span_in: float
    max_width_for_primary_tension_reinforcement_in: float
    outer_flange_reinforcement_required: bool

    @property
    def outer_flange_width_requiring_distribution_in(self) -> float:
        return max(
            self.effective_flange_width_in - self.max_width_for_primary_tension_reinforcement_in,
            0.0,
        )


@dataclass(frozen=True)
class ACIFlangePrimaryTensionBand:
    effective_flange_width_in: float
    clear_span_in: float
    web_width_in: float
    band_width_in: float
    overhang_each_side_of_web_in: float


def permitted_service_steel_stress(steel_yield_strength_psi: float) -> float:
    """ACI 318-14 24.3.2.1 permits fs = (2/3)fy for deformed reinforcement."""

    if steel_yield_strength_psi <= 0:
        raise ValueError("Steel yield strength must be positive.")
    return (2.0 / 3.0) * steel_yield_strength_psi


def max_deformed_bar_spacing_for_crack_control(
    service_steel_stress_psi: float,
    clear_cover_to_tension_face_in: float,
) -> ACIFlexuralBarSpacingLimit:
    """ACI 318-14 Table 24.3.2, deformed bars or wires row only."""

    if service_steel_stress_psi <= 0:
        raise ValueError("Service steel stress must be positive.")
    if clear_cover_to_tension_face_in < 0:
        raise ValueError("Clear cover to tension face cannot be negative.")

    stress_ratio = 40_000.0 / service_steel_stress_psi
    limit_by_cover = 15.0 * stress_ratio - 2.5 * clear_cover_to_tension_face_in
    limit_by_stress = 12.0 * stress_ratio
    return ACIFlexuralBarSpacingLimit(
        service_steel_stress_psi=service_steel_stress_psi,
        clear_cover_to_tension_face_in=clear_cover_to_tension_face_in,
        limit_in=min(limit_by_cover, limit_by_stress),
        limit_by_cover_in=limit_by_cover,
        limit_by_stress_in=limit_by_stress,
    )


def flange_tension_distribution_requirement(
    effective_flange_width_in: float,
    clear_span_in: float,
) -> ACIFlangeTensionDistributionRequirement:
    """ACI 318-14 24.3.4 for T-beam flanges in tension."""

    if effective_flange_width_in <= 0:
        raise ValueError("Effective flange width must be positive.")
    if clear_span_in <= 0:
        raise ValueError("Clear span must be positive.")

    limit = clear_span_in / 10.0
    return ACIFlangeTensionDistributionRequirement(
        effective_flange_width_in=effective_flange_width_in,
        clear_span_in=clear_span_in,
        max_width_for_primary_tension_reinforcement_in=min(effective_flange_width_in, limit),
        outer_flange_reinforcement_required=effective_flange_width_in > limit,
    )


def flange_primary_tension_band(
    effective_flange_width_in: float,
    clear_span_in: float,
    web_width_in: float,
) -> ACIFlangePrimaryTensionBand:
    """Primary flange tension reinforcement band from ACI 24.3.4.

    TODO: Verify the SP-17 design-aid convention for placing the bars outside
    the web. For now this helper only captures the ACI ln/10 primary band; the
    handbook's 11 in detail appears to be a center-to-center offset from the
    outer web bar, not a dimension from the web face.
    """

    if web_width_in <= 0:
        raise ValueError("Web width must be positive.")
    requirement = flange_tension_distribution_requirement(effective_flange_width_in, clear_span_in)
    band_width = requirement.max_width_for_primary_tension_reinforcement_in
    return ACIFlangePrimaryTensionBand(
        effective_flange_width_in=effective_flange_width_in,
        clear_span_in=clear_span_in,
        web_width_in=web_width_in,
        band_width_in=band_width,
        overhang_each_side_of_web_in=max((band_width - web_width_in) / 2.0, 0.0),
    )


def layer_center_spacing(layer: LongitudinalBarLayer) -> float | None:
    """Maximum center-to-center spacing between adjacent bars in one layer."""

    if len(layer.x_positions) < 2:
        return None
    positions = sorted(layer.x_positions)
    return max(right - left for left, right in zip(positions, positions[1:]))


def combined_layer_center_spacing(layers: tuple[LongitudinalBarLayer, ...]) -> float | None:
    """Maximum center-to-center spacing across same-elevation detailing groups."""

    positions = sorted(x for layer in layers for x in layer.x_positions)
    if len(positions) < 2:
        return None
    return max(right - left for left, right in zip(positions, positions[1:]))


def clear_cover_to_tension_face(
    section_depth_in: float,
    layer: LongitudinalBarLayer,
    tension_face: LongitudinalFace,
) -> float:
    """Least distance from bar surface to the concrete tension face, cc in Table 24.3.2."""

    if tension_face == LongitudinalFace.TOP:
        return layer.y_from_top - layer.bar_diameter / 2.0
    return section_depth_in - layer.y_from_top - layer.bar_diameter / 2.0


def least_clear_cover_to_tension_face(
    section_depth_in: float,
    layers: tuple[LongitudinalBarLayer, ...],
    tension_face: LongitudinalFace,
) -> float:
    if not layers:
        raise ValueError("At least one layer is required.")
    return min(clear_cover_to_tension_face(section_depth_in, layer, tension_face) for layer in layers)


def closest_layer_to_tension_face(
    layers: tuple[LongitudinalBarLayer, ...],
    tension_face: LongitudinalFace,
) -> LongitudinalBarLayer | None:
    tension_layers = tuple(layer for layer in layers if layer.face == tension_face)
    if not tension_layers:
        return None
    if tension_face == LongitudinalFace.TOP:
        return min(tension_layers, key=lambda layer: layer.y_from_top)
    return max(tension_layers, key=lambda layer: layer.y_from_top)


def closest_layers_to_tension_face(
    layers: tuple[LongitudinalBarLayer, ...],
    tension_face: LongitudinalFace,
    *,
    tolerance: float = 1e-6,
) -> tuple[LongitudinalBarLayer, ...]:
    """Return all detailing groups at the closest tension-face elevation."""

    closest = closest_layer_to_tension_face(layers, tension_face)
    if closest is None:
        return ()
    if tension_face == LongitudinalFace.TOP:
        return tuple(
            layer
            for layer in layers
            if layer.face == tension_face and abs(layer.y_from_top - closest.y_from_top) <= tolerance
        )
    return tuple(
        layer
        for layer in layers
        if layer.face == tension_face and abs(layer.y_from_top - closest.y_from_top) <= tolerance
    )


@dataclass(frozen=True)
class ACIFlexuralReinforcementDistributionCheck:
    check_id: str = "aci318.detailing.flexural_reinforcement_distribution"
    title: str = "Flexural reinforcement distribution"

    def check(self, context: BeamDesignContext) -> CheckResult:
        tension_face = _tension_face_from_metadata(context)
        if tension_face is None:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "Provide aci_tension_face for the beam section being checked.",
            )
        if context.reinforcement.cage is None:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "No reinforcement cage is defined.",
            )

        layers = closest_layers_to_tension_face(context.reinforcement.cage.longitudinal_layers, tension_face)
        if not layers:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                f"No longitudinal reinforcement is defined at the {tension_face.value} tension face.",
            )

        spacing = combined_layer_center_spacing(layers)
        if spacing is None:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "Only one bar is present at the closest tension-face elevation.",
            )

        fs = float(
            context.metadata.get(
                "aci_service_steel_stress_psi",
                permitted_service_steel_stress(context.steel.fy),
            )
        )
        cc = least_clear_cover_to_tension_face(context.section.depth, layers, tension_face)
        limit = max_deformed_bar_spacing_for_crack_control(fs, cc)
        kwargs = {
            "demand": spacing,
            "capacity": limit.limit_in,
            "ratio": spacing / limit.limit_in if limit.limit_in else None,
            "references": ("ACI 318-14 9.7.2.2", "ACI 318-14 24.3.2"),
            "data": {
                "tension_face": tension_face.value,
                "service_steel_stress_psi": fs,
                "cc_in": cc,
                "limit_by_cover_in": limit.limit_by_cover_in,
                "limit_by_stress_in": limit.limit_by_stress_in,
                "bar_tags": tuple(layer.bar_tag.value for layer in layers),
                "bar_count": sum(layer.count for layer in layers),
                "placement_labels": tuple(layer.placement_label for layer in layers),
                "x_positions": tuple(sorted(x for layer in layers for x in layer.x_positions)),
            },
        }
        if spacing <= limit.limit_in:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult.fail_result(self.check_id, self.title, **kwargs)


@dataclass(frozen=True)
class ACITBeamFlangeTensionDistributionCheck:
    check_id: str = "aci318.detailing.t_beam_flange_tension_distribution"
    title: str = "T-beam flange tension reinforcement distribution"

    def check(self, context: BeamDesignContext) -> CheckResult:
        tension_face = _tension_face_from_metadata(context)
        if tension_face != LongitudinalFace.TOP:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "The flange is not identified as the tension face.",
            )
        if context.section.shape.shape_type not in {SectionShapeType.T, SectionShapeType.L}:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "The section is not a T- or L-beam.",
            )

        clear_span = context.metadata.get("aci_clear_span_in", context.metadata.get("clear_span_in"))
        if clear_span is None:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "Provide aci_clear_span_in for the flange tension distribution check.",
            )

        effective_flange_width = float(
            context.metadata.get("aci_effective_flange_width_in", context.section.gross_width)
        )
        requirement = flange_tension_distribution_requirement(
            effective_flange_width_in=effective_flange_width,
            clear_span_in=float(clear_span),
        )
        data = {
            "effective_flange_width_in": requirement.effective_flange_width_in,
            "clear_span_in": requirement.clear_span_in,
            "clear_span_over_10_in": requirement.clear_span_in / 10.0,
            "max_width_for_primary_tension_reinforcement_in": requirement.max_width_for_primary_tension_reinforcement_in,
            "outer_flange_width_requiring_distribution_in": requirement.outer_flange_width_requiring_distribution_in,
            "outer_flange_reinforcement_required": requirement.outer_flange_reinforcement_required,
        }
        kwargs = {
            "demand": requirement.effective_flange_width_in,
            "capacity": requirement.clear_span_in / 10.0,
            "ratio": requirement.effective_flange_width_in / (requirement.clear_span_in / 10.0),
            "references": ("ACI 318-14 24.3.4",),
            "data": data,
        }
        if not requirement.outer_flange_reinforcement_required:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)

        provided = bool(context.metadata.get("aci_outer_flange_distribution_reinforcement_provided", False))
        if provided:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult(
            check_id=self.check_id,
            title=self.title,
            status=CheckStatus.WARNING,
            message="Additional bonded longitudinal reinforcement is required in the outer portions of the flange.",
            **kwargs,
        )


def _tension_face_from_metadata(context: BeamDesignContext) -> LongitudinalFace | None:
    value = context.metadata.get("aci_tension_face", context.metadata.get("tension_face"))
    if value is None:
        return None
    if isinstance(value, LongitudinalFace):
        return value
    return LongitudinalFace(str(value).lower())
