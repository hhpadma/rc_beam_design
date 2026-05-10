from beam_design.assemblies.base import RuleAssembly
from beam_design.core.interfaces import DesignRule


class MaterialDesign(RuleAssembly):
    scope = "materials"

    def rules(self) -> tuple[DesignRule, ...]:
        return self.code.material_rules()
