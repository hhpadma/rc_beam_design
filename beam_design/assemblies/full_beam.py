from dataclasses import dataclass

from beam_design.assemblies.bond import BondDesign
from beam_design.assemblies.detailing import DetailingDesign
from beam_design.assemblies.flexure import FlexureDesign
from beam_design.assemblies.geometry import GeometryDesign
from beam_design.assemblies.materials import MaterialDesign
from beam_design.assemblies.shear import ShearDesign
from beam_design.core.interfaces import DesignCode
from beam_design.core.model import BeamDesignContext
from beam_design.core.result import DesignResult


@dataclass(frozen=True)
class BeamDesign:
    code: DesignCode

    def run(self, context: BeamDesignContext) -> tuple[DesignResult, ...]:
        return (
            MaterialDesign(self.code).run(context),
            GeometryDesign(self.code).run(context),
            FlexureDesign(self.code).run(context),
            ShearDesign(self.code).run(context),
            BondDesign(self.code).run(context),
            DetailingDesign(self.code).run(context),
        )
