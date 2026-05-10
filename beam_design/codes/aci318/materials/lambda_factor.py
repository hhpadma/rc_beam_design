from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType


class ACIAggregateConcreteType(Enum):
    ALL_LIGHTWEIGHT = "all_lightweight"
    LIGHTWEIGHT_FINE_BLEND = "lightweight_fine_blend"
    SAND_LIGHTWEIGHT = "sand_lightweight"
    SAND_LIGHTWEIGHT_COARSE_BLEND = "sand_lightweight_coarse_blend"
    NORMALWEIGHT = "normalweight"


@dataclass(frozen=True)
class ACILambdaFactorRecord:
    concrete_type: ACIAggregateConcreteType
    lambda_min: float
    lambda_max: float
    fine_aggregate: str
    coarse_aggregate: str
    interpolation_basis: str | None = None

    @property
    def is_range(self) -> bool:
        return self.lambda_min != self.lambda_max


LAMBDA_TABLE_19_2_4_2 = MappingProxyType(
    {
        ACIAggregateConcreteType.ALL_LIGHTWEIGHT: ACILambdaFactorRecord(
            concrete_type=ACIAggregateConcreteType.ALL_LIGHTWEIGHT,
            lambda_min=0.75,
            lambda_max=0.75,
            fine_aggregate="ASTM C330",
            coarse_aggregate="ASTM C330",
        ),
        ACIAggregateConcreteType.LIGHTWEIGHT_FINE_BLEND: ACILambdaFactorRecord(
            concrete_type=ACIAggregateConcreteType.LIGHTWEIGHT_FINE_BLEND,
            lambda_min=0.75,
            lambda_max=0.85,
            fine_aggregate="Combination of ASTM C330 and ASTM C33",
            coarse_aggregate="ASTM C330",
            interpolation_basis="normalweight fine aggregate fraction",
        ),
        ACIAggregateConcreteType.SAND_LIGHTWEIGHT: ACILambdaFactorRecord(
            concrete_type=ACIAggregateConcreteType.SAND_LIGHTWEIGHT,
            lambda_min=0.85,
            lambda_max=0.85,
            fine_aggregate="ASTM C33",
            coarse_aggregate="ASTM C330",
        ),
        ACIAggregateConcreteType.SAND_LIGHTWEIGHT_COARSE_BLEND: ACILambdaFactorRecord(
            concrete_type=ACIAggregateConcreteType.SAND_LIGHTWEIGHT_COARSE_BLEND,
            lambda_min=0.85,
            lambda_max=1.0,
            fine_aggregate="ASTM C33",
            coarse_aggregate="Combination of ASTM C330 and ASTM C33",
            interpolation_basis="normalweight coarse aggregate fraction",
        ),
        ACIAggregateConcreteType.NORMALWEIGHT: ACILambdaFactorRecord(
            concrete_type=ACIAggregateConcreteType.NORMALWEIGHT,
            lambda_min=1.0,
            lambda_max=1.0,
            fine_aggregate="ASTM C33",
            coarse_aggregate="ASTM C33",
        ),
    }
)


def lambda_factor(
    concrete_type: ACIAggregateConcreteType | str,
    *,
    normalweight_aggregate_fraction: float | None = None,
) -> float:
    record = LAMBDA_TABLE_19_2_4_2[_coerce_concrete_type(concrete_type)]
    if not record.is_range:
        return record.lambda_min
    if normalweight_aggregate_fraction is None:
        raise ValueError(f"{record.interpolation_basis} is required for {record.concrete_type.value}.")
    if not 0.0 <= normalweight_aggregate_fraction <= 1.0:
        raise ValueError("Normalweight aggregate fraction must be between 0 and 1.")
    return record.lambda_min + (record.lambda_max - record.lambda_min) * normalweight_aggregate_fraction


def _coerce_concrete_type(value: ACIAggregateConcreteType | str) -> ACIAggregateConcreteType:
    if isinstance(value, ACIAggregateConcreteType):
        return value
    normalized = value.strip().lower()
    for item in ACIAggregateConcreteType:
        if normalized in {item.value, item.name.lower()}:
            return item
    raise ValueError(f"{value!r} is not a valid ACI aggregate concrete type.")
