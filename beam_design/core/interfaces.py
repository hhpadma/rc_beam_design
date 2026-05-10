from typing import Protocol

from beam_design.core.model import BeamDesignContext
from beam_design.core.result import CheckResult


class DesignRule(Protocol):
    check_id: str
    title: str

    def check(self, context: BeamDesignContext) -> CheckResult:
        ...


class DesignCode(Protocol):
    name: str

    def material_rules(self) -> tuple[DesignRule, ...]:
        ...

    def geometry_rules(self) -> tuple[DesignRule, ...]:
        ...

    def flexure_rules(self) -> tuple[DesignRule, ...]:
        ...

    def shear_rules(self) -> tuple[DesignRule, ...]:
        ...

    def bond_rules(self) -> tuple[DesignRule, ...]:
        ...

    def detailing_rules(self) -> tuple[DesignRule, ...]:
        ...
