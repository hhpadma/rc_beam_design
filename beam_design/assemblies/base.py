from beam_design.core.interfaces import DesignCode, DesignRule
from beam_design.core.model import BeamDesignContext
from beam_design.core.result import DesignResult
from beam_design.core.runner import DesignRunner


class RuleAssembly:
    """Base class for workflow assemblies."""

    scope = "generic"

    def __init__(self, code: DesignCode):
        self.code = code

    def rules(self) -> tuple[DesignRule, ...]:
        raise NotImplementedError

    def run(self, context: BeamDesignContext) -> DesignResult:
        return DesignRunner(
            code_name=self.code.name,
            scope=self.scope,
            rules=self.rules(),
        ).run(context)
