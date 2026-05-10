from beam_design.codes.aci318.bond.development_length import ACIDevelopmentLengthCheck
from beam_design.codes.aci318.detailing.cover import ACIMinimumCoverCheck
from beam_design.codes.aci318.detailing.flexural_distribution import (
    ACIFlexuralReinforcementDistributionCheck,
    ACITBeamFlangeTensionDistributionCheck,
)
from beam_design.codes.aci318.detailing.spacing import ACILongitudinalBarClearSpacingCheck, ACIStirrupSpacingCheck
from beam_design.codes.aci318.flexure.strength import ACIFlexuralStrengthCheck
from beam_design.codes.aci318.flexure.strain_limit import ACITensionStrainLimitCheck
from beam_design.codes.aci318.flexure.steel_limits import (
    ACIMaximumTensionSteelCheck,
    ACIMinimumTensionSteelCheck,
)
from beam_design.codes.aci318.load_combinations import ACILoadCombinations
from beam_design.codes.aci318.materials.concrete_strength import ACIConcreteMinimumStrengthCheck
from beam_design.codes.aci318.sections.effective_flange_width import ACIFlangeWidthCheck
from beam_design.codes.aci318.sections.minimum_depth import ACIMinimumBeamDepthCheck
from beam_design.codes.aci318.sections.deflection import ACIDeflectionRequirementCheck
from beam_design.codes.aci318.sections.t_beam_construction import (
    ACITBeamCompositeConstructionCheck,
    ACITBeamFlangeTransverseReinforcementCheck,
)
from beam_design.codes.aci318.sections.torsion_flange import ACITorsionFlangeWidthCheck
from beam_design.codes.aci318.shear.strength import ACIShearStrengthCheck
from beam_design.codes.aci318.shear.requirements import (
    ACIAxialTensionCreepShrinkageShearEffectCheck,
    ACIConcreteShearSqrtStrengthLimitCheck,
    ACIShearReinforcementYieldStrengthLimitCheck,
    ACIShearSectionDimensionLimitCheck,
    ACIVariableDepthShearEffectCheck,
    ACIWebOpeningShearEffectCheck,
)
from beam_design.codes.aci318.stability import ACILateralStabilityCheck
from beam_design.core.interfaces import DesignRule


class ACI318:
    """Assembler for ACI 318 rule blocks."""

    name = "ACI 318"

    def load_combinations(self) -> ACILoadCombinations:
        return ACILoadCombinations()

    def material_rules(self) -> tuple[DesignRule, ...]:
        return (ACIConcreteMinimumStrengthCheck(),)

    def geometry_rules(self) -> tuple[DesignRule, ...]:
        return (
            ACIMinimumBeamDepthCheck(),
            ACIDeflectionRequirementCheck(),
            ACITBeamCompositeConstructionCheck(),
            ACIFlangeWidthCheck(),
            ACITBeamFlangeTransverseReinforcementCheck(),
            ACITorsionFlangeWidthCheck(),
        )

    def stability_rules(self) -> tuple[DesignRule, ...]:
        return (ACILateralStabilityCheck(),)

    def flexure_rules(self) -> tuple[DesignRule, ...]:
        return (
            ACIMinimumTensionSteelCheck(),
            ACIMaximumTensionSteelCheck(),
            ACITensionStrainLimitCheck(),
            ACIFlexuralStrengthCheck(),
        )

    def shear_rules(self) -> tuple[DesignRule, ...]:
        return (
            ACIShearSectionDimensionLimitCheck(),
            ACIConcreteShearSqrtStrengthLimitCheck(),
            ACIShearReinforcementYieldStrengthLimitCheck(),
            ACIWebOpeningShearEffectCheck(),
            ACIAxialTensionCreepShrinkageShearEffectCheck(),
            ACIVariableDepthShearEffectCheck(),
            ACIShearStrengthCheck(),
            ACIStirrupSpacingCheck(),
        )

    def bond_rules(self) -> tuple[DesignRule, ...]:
        return (ACIDevelopmentLengthCheck(),)

    def detailing_rules(self) -> tuple[DesignRule, ...]:
        return (
            ACIMinimumCoverCheck(),
            ACILongitudinalBarClearSpacingCheck(),
            ACIFlexuralReinforcementDistributionCheck(),
            ACITBeamFlangeTensionDistributionCheck(),
            ACIStirrupSpacingCheck(),
        )

    def all_rules(self) -> tuple[DesignRule, ...]:
        return (
            *self.material_rules(),
            *self.stability_rules(),
            *self.geometry_rules(),
            *self.flexure_rules(),
            *self.shear_rules(),
            *self.bond_rules(),
            *self.detailing_rules(),
        )
