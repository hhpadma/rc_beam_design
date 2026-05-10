from dataclasses import dataclass

from beam_design.core.model import BeamDesignContext
from beam_design.core.result import CheckResult
from beam_design.core.section_shapes import SectionShapeType


def torsion_overhanging_flange_limit(
    slab_thickness_in: float,
    projection_above_slab_in: float,
    projection_below_slab_in: float,
) -> float:
    if slab_thickness_in <= 0:
        raise ValueError("Slab thickness must be positive.")
    return min(max(projection_above_slab_in, projection_below_slab_in), 4.0 * slab_thickness_in)


@dataclass(frozen=True)
class ACITorsionFlangeWidthCheck:
    check_id: str = "aci318.t_beam.torsion_flange_width"
    title: str = "Torsion overhanging flange width"

    def check(self, context: BeamDesignContext) -> CheckResult:
        if not bool(context.metadata.get("aci_torsion_design_required", False)):
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "Torsional design is not required.",
            )
        if context.section.shape.shape_type not in {SectionShapeType.T, SectionShapeType.L}:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "Section is not a T- or L-beam.",
            )

        required = (
            "aci_slab_thickness_in",
            "aci_torsion_projection_above_slab_in",
            "aci_torsion_projection_below_slab_in",
        )
        missing = tuple(key for key in required if key not in context.metadata)
        if missing:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                f"Missing metadata: {', '.join(missing)}.",
            )

        slab_thickness = float(context.metadata["aci_slab_thickness_in"])
        projection_above = float(context.metadata["aci_torsion_projection_above_slab_in"])
        projection_below = float(context.metadata["aci_torsion_projection_below_slab_in"])
        allowed_overhang = torsion_overhanging_flange_limit(slab_thickness, projection_above, projection_below)
        actual_overhang = (context.section.gross_width - context.section.width) / (
            2.0 if context.section.shape.shape_type == SectionShapeType.T else 1.0
        )
        acp_with_flanges = context.metadata.get("aci_torsion_acp2_over_pcp_with_flanges")
        acp_without_flanges = context.metadata.get("aci_torsion_acp2_over_pcp_without_flanges")
        flanges_included = bool(context.metadata.get("aci_torsion_flanges_included", True))
        must_neglect = (
            acp_with_flanges is not None
            and acp_without_flanges is not None
            and float(acp_with_flanges) < float(acp_without_flanges)
        )
        kwargs = {
            "demand": actual_overhang,
            "capacity": allowed_overhang,
            "ratio": actual_overhang / allowed_overhang if allowed_overhang else None,
            "references": ("ACI 318-14 9.2.4.4", "ACI 318-14 22.7"),
            "data": {
                "actual_overhang_in": actual_overhang,
                "allowed_overhang_in": allowed_overhang,
                "flanges_included": flanges_included,
                "torsion_parameter_requires_neglecting_flanges": must_neglect,
            },
        }
        if actual_overhang > allowed_overhang:
            return CheckResult.fail_result(
                self.check_id,
                self.title,
                message="Overhanging flange width used for torsion exceeds ACI 9.2.4.4(a).",
                **kwargs,
            )
        if flanges_included and must_neglect:
            return CheckResult.fail_result(
                self.check_id,
                self.title,
                message="Overhanging flanges must be neglected for torsion per ACI 9.2.4.4(b).",
                **kwargs,
            )
        return CheckResult.pass_result(self.check_id, self.title, **kwargs)
