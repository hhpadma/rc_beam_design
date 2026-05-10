from beam_design.assemblies.base import RuleAssembly
from beam_design.core.interfaces import DesignRule


class FlexureDesign(RuleAssembly):
    scope = "flexure"

    def rules(self) -> tuple[DesignRule, ...]:
        return self.code.flexure_rules()
