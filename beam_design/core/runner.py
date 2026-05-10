from collections.abc import Iterable

from beam_design.core.interfaces import DesignRule
from beam_design.core.model import BeamDesignContext
from beam_design.core.result import CheckResult, DesignResult


class DesignRunner:
    """Generic rule runner. It has no knowledge of any design code."""

    def __init__(self, code_name: str, scope: str, rules: Iterable[DesignRule]):
        self.code_name = code_name
        self.scope = scope
        self.rules = tuple(rules)

    def run(self, context: BeamDesignContext) -> DesignResult:
        results: list[CheckResult] = []
        for rule in self.rules:
            results.append(rule.check(context))
        return DesignResult(code=self.code_name, scope=self.scope, checks=tuple(results))
