from beam_design.assemblies.base import RuleAssembly
from beam_design.core.interfaces import DesignRule


class GeometryDesign(RuleAssembly):
    scope = "geometry"

    def rules(self) -> tuple[DesignRule, ...]:
        return self.code.geometry_rules()
