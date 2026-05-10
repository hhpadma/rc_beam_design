from beam_design.assemblies.base import RuleAssembly
from beam_design.core.interfaces import DesignRule


class DetailingDesign(RuleAssembly):
    scope = "detailing"

    def rules(self) -> tuple[DesignRule, ...]:
        return self.code.detailing_rules()
