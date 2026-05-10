from beam_design.assemblies.base import RuleAssembly
from beam_design.core.interfaces import DesignRule


class ShearDesign(RuleAssembly):
    scope = "shear"

    def rules(self) -> tuple[DesignRule, ...]:
        return self.code.shear_rules()
