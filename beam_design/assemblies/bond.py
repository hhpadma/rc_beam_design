from beam_design.assemblies.base import RuleAssembly
from beam_design.core.interfaces import DesignRule


class BondDesign(RuleAssembly):
    scope = "bond"

    def rules(self) -> tuple[DesignRule, ...]:
        return self.code.bond_rules()
