from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CheckStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    title: str
    status: CheckStatus
    message: str = ""
    demand: float | None = None
    capacity: float | None = None
    ratio: float | None = None
    references: tuple[str, ...] = ()
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def pass_result(cls, check_id: str, title: str, **kwargs: Any) -> "CheckResult":
        return cls(check_id=check_id, title=title, status=CheckStatus.PASS, **kwargs)

    @classmethod
    def fail_result(cls, check_id: str, title: str, **kwargs: Any) -> "CheckResult":
        return cls(check_id=check_id, title=title, status=CheckStatus.FAIL, **kwargs)

    @classmethod
    def not_applicable(cls, check_id: str, title: str, message: str = "") -> "CheckResult":
        return cls(
            check_id=check_id,
            title=title,
            status=CheckStatus.NOT_APPLICABLE,
            message=message,
        )


@dataclass(frozen=True)
class DesignResult:
    code: str
    scope: str
    checks: tuple[CheckResult, ...]

    @property
    def passed(self) -> bool:
        return all(result.status in {CheckStatus.PASS, CheckStatus.NOT_APPLICABLE} for result in self.checks)

    @property
    def failures(self) -> tuple[CheckResult, ...]:
        return tuple(result for result in self.checks if result.status == CheckStatus.FAIL)
