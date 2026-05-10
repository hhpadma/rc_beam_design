from dataclasses import dataclass

from beam_design.core.model import BeamDesignContext
from beam_design.core.result import CheckResult
from beam_design.core.section_shapes import SectionShapeType


def is_flanged_section(context: BeamDesignContext) -> bool:
    return context.section.shape.shape_type in {SectionShapeType.T, SectionShapeType.L}


@dataclass(frozen=True)
class ACITBeamCompositeConstructionCheck:
    check_id: str = "aci318.t_beam.construction"
    title: str = "T-beam flange and web construction"

    def check(self, context: BeamDesignContext) -> CheckResult:
        if not is_flanged_section(context):
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "Section is not a T- or L-beam.",
            )

        monolithic = bool(context.metadata.get("aci_flange_and_web_monolithic", False))
        composite = bool(context.metadata.get("aci_flange_and_web_composite", False))
        kwargs = {
            "references": ("ACI 318-14 9.2.4.1", "ACI 318-14 16.4"),
            "data": {
                "flange_and_web_monolithic": monolithic,
                "flange_and_web_composite": composite,
            },
        }
        if monolithic or composite:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult.fail_result(
            self.check_id,
            self.title,
            message="T-beam flange and web concrete must be monolithic or made composite.",
            **kwargs,
        )


@dataclass(frozen=True)
class ACITBeamFlangeTransverseReinforcementCheck:
    check_id: str = "aci318.t_beam.flange_transverse_reinforcement"
    title: str = "T-beam flange transverse reinforcement"

    def check(self, context: BeamDesignContext) -> CheckResult:
        if not is_flanged_section(context):
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "Section is not a T- or L-beam.",
            )

        primary_parallel = bool(context.metadata.get("aci_primary_slab_reinforcement_parallel_to_beam", False))
        if not primary_parallel:
            return CheckResult.not_applicable(
                self.check_id,
                self.title,
                "Primary flexural slab reinforcement is not parallel to the beam.",
            )

        provided = bool(context.metadata.get("aci_flange_transverse_reinforcement_per_7_5_2_3", False))
        kwargs = {
            "references": ("ACI 318-14 9.2.4.3", "ACI 318-14 7.5.2.3"),
            "data": {
                "primary_slab_reinforcement_parallel_to_beam": primary_parallel,
                "flange_transverse_reinforcement_per_7_5_2_3": provided,
            },
        }
        if provided:
            return CheckResult.pass_result(self.check_id, self.title, **kwargs)
        return CheckResult.fail_result(
            self.check_id,
            self.title,
            message="Flange reinforcement perpendicular to the beam must satisfy ACI 7.5.2.3.",
            **kwargs,
        )
