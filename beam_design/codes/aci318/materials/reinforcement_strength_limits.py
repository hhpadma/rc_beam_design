from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType


class ACIReinforcementUsage(Enum):
    FLEXURE_AXIAL_SHRINKAGE_TEMPERATURE = "flexure_axial_shrinkage_temperature"
    LATERAL_SUPPORT_OR_CONFINEMENT = "lateral_support_or_confinement"
    SHEAR = "shear"
    TORSION = "torsion"


class ACIReinforcementApplication(Enum):
    SPECIAL_SEISMIC_SYSTEMS = "special_seismic_systems"
    OTHER = "other"
    SPIRALS = "spirals"
    SHEAR_FRICTION = "shear_friction"
    STIRRUPS_TIES_HOOPS = "stirrups_ties_hoops"
    LONGITUDINAL_AND_TRANSVERSE = "longitudinal_and_transverse"


class ACIReinforcementProduct(Enum):
    DEFORMED_BARS = "deformed_bars"
    DEFORMED_WIRES = "deformed_wires"
    WELDED_WIRE_REINFORCEMENT = "welded_wire_reinforcement"
    WELDED_DEFORMED_BAR_MATS = "welded_deformed_bar_mats"


@dataclass(frozen=True)
class ACIReinforcementStrengthLimit:
    usage: ACIReinforcementUsage
    application: ACIReinforcementApplication
    max_yield_strength_psi: int
    permitted_products: tuple[ACIReinforcementProduct, ...]

    def permits(self, product: ACIReinforcementProduct | str) -> bool:
        return _coerce_product(product) in self.permitted_products


REINFORCEMENT_STRENGTH_LIMITS_20_2_2_4A = MappingProxyType(
    {
        (ACIReinforcementUsage.FLEXURE_AXIAL_SHRINKAGE_TEMPERATURE, ACIReinforcementApplication.SPECIAL_SEISMIC_SYSTEMS): (
            ACIReinforcementStrengthLimit(
                usage=ACIReinforcementUsage.FLEXURE_AXIAL_SHRINKAGE_TEMPERATURE,
                application=ACIReinforcementApplication.SPECIAL_SEISMIC_SYSTEMS,
                max_yield_strength_psi=60_000,
                permitted_products=(ACIReinforcementProduct.DEFORMED_BARS,),
            ),
        ),
        (ACIReinforcementUsage.FLEXURE_AXIAL_SHRINKAGE_TEMPERATURE, ACIReinforcementApplication.OTHER): (
            ACIReinforcementStrengthLimit(
                usage=ACIReinforcementUsage.FLEXURE_AXIAL_SHRINKAGE_TEMPERATURE,
                application=ACIReinforcementApplication.OTHER,
                max_yield_strength_psi=80_000,
                permitted_products=(
                    ACIReinforcementProduct.DEFORMED_BARS,
                    ACIReinforcementProduct.DEFORMED_WIRES,
                    ACIReinforcementProduct.WELDED_WIRE_REINFORCEMENT,
                    ACIReinforcementProduct.WELDED_DEFORMED_BAR_MATS,
                ),
            ),
        ),
        (ACIReinforcementUsage.LATERAL_SUPPORT_OR_CONFINEMENT, ACIReinforcementApplication.SPECIAL_SEISMIC_SYSTEMS): (
            ACIReinforcementStrengthLimit(
                usage=ACIReinforcementUsage.LATERAL_SUPPORT_OR_CONFINEMENT,
                application=ACIReinforcementApplication.SPECIAL_SEISMIC_SYSTEMS,
                max_yield_strength_psi=100_000,
                permitted_products=(
                    ACIReinforcementProduct.DEFORMED_BARS,
                    ACIReinforcementProduct.DEFORMED_WIRES,
                    ACIReinforcementProduct.WELDED_WIRE_REINFORCEMENT,
                ),
            ),
        ),
        (ACIReinforcementUsage.LATERAL_SUPPORT_OR_CONFINEMENT, ACIReinforcementApplication.SPIRALS): (
            ACIReinforcementStrengthLimit(
                usage=ACIReinforcementUsage.LATERAL_SUPPORT_OR_CONFINEMENT,
                application=ACIReinforcementApplication.SPIRALS,
                max_yield_strength_psi=100_000,
                permitted_products=(ACIReinforcementProduct.DEFORMED_BARS, ACIReinforcementProduct.DEFORMED_WIRES),
            ),
        ),
        (ACIReinforcementUsage.LATERAL_SUPPORT_OR_CONFINEMENT, ACIReinforcementApplication.OTHER): (
            ACIReinforcementStrengthLimit(
                usage=ACIReinforcementUsage.LATERAL_SUPPORT_OR_CONFINEMENT,
                application=ACIReinforcementApplication.OTHER,
                max_yield_strength_psi=80_000,
                permitted_products=(
                    ACIReinforcementProduct.DEFORMED_BARS,
                    ACIReinforcementProduct.DEFORMED_WIRES,
                    ACIReinforcementProduct.WELDED_WIRE_REINFORCEMENT,
                ),
            ),
        ),
        (ACIReinforcementUsage.SHEAR, ACIReinforcementApplication.SPECIAL_SEISMIC_SYSTEMS): (
            ACIReinforcementStrengthLimit(
                usage=ACIReinforcementUsage.SHEAR,
                application=ACIReinforcementApplication.SPECIAL_SEISMIC_SYSTEMS,
                max_yield_strength_psi=60_000,
                permitted_products=(
                    ACIReinforcementProduct.DEFORMED_BARS,
                    ACIReinforcementProduct.DEFORMED_WIRES,
                    ACIReinforcementProduct.WELDED_WIRE_REINFORCEMENT,
                ),
            ),
        ),
        (ACIReinforcementUsage.SHEAR, ACIReinforcementApplication.SPIRALS): (
            ACIReinforcementStrengthLimit(
                usage=ACIReinforcementUsage.SHEAR,
                application=ACIReinforcementApplication.SPIRALS,
                max_yield_strength_psi=60_000,
                permitted_products=(ACIReinforcementProduct.DEFORMED_BARS, ACIReinforcementProduct.DEFORMED_WIRES),
            ),
        ),
        (ACIReinforcementUsage.SHEAR, ACIReinforcementApplication.SHEAR_FRICTION): (
            ACIReinforcementStrengthLimit(
                usage=ACIReinforcementUsage.SHEAR,
                application=ACIReinforcementApplication.SHEAR_FRICTION,
                max_yield_strength_psi=60_000,
                permitted_products=(
                    ACIReinforcementProduct.DEFORMED_BARS,
                    ACIReinforcementProduct.DEFORMED_WIRES,
                    ACIReinforcementProduct.WELDED_WIRE_REINFORCEMENT,
                ),
            ),
        ),
        (ACIReinforcementUsage.SHEAR, ACIReinforcementApplication.STIRRUPS_TIES_HOOPS): (
            ACIReinforcementStrengthLimit(
                usage=ACIReinforcementUsage.SHEAR,
                application=ACIReinforcementApplication.STIRRUPS_TIES_HOOPS,
                max_yield_strength_psi=60_000,
                permitted_products=(
                    ACIReinforcementProduct.DEFORMED_BARS,
                    ACIReinforcementProduct.DEFORMED_WIRES,
                    ACIReinforcementProduct.WELDED_WIRE_REINFORCEMENT,
                ),
            ),
            ACIReinforcementStrengthLimit(
                usage=ACIReinforcementUsage.SHEAR,
                application=ACIReinforcementApplication.STIRRUPS_TIES_HOOPS,
                max_yield_strength_psi=80_000,
                permitted_products=(ACIReinforcementProduct.WELDED_WIRE_REINFORCEMENT,),
            ),
        ),
        (ACIReinforcementUsage.TORSION, ACIReinforcementApplication.LONGITUDINAL_AND_TRANSVERSE): (
            ACIReinforcementStrengthLimit(
                usage=ACIReinforcementUsage.TORSION,
                application=ACIReinforcementApplication.LONGITUDINAL_AND_TRANSVERSE,
                max_yield_strength_psi=60_000,
                permitted_products=(
                    ACIReinforcementProduct.DEFORMED_BARS,
                    ACIReinforcementProduct.DEFORMED_WIRES,
                    ACIReinforcementProduct.WELDED_WIRE_REINFORCEMENT,
                ),
            ),
        ),
    }
)


def reinforcement_strength_limits(
    usage: ACIReinforcementUsage | str,
    application: ACIReinforcementApplication | str,
) -> tuple[ACIReinforcementStrengthLimit, ...]:
    key = (_coerce_usage(usage), _coerce_application(application))
    return REINFORCEMENT_STRENGTH_LIMITS_20_2_2_4A[key]


def max_permitted_design_yield_strength(
    usage: ACIReinforcementUsage | str,
    application: ACIReinforcementApplication | str,
    product: ACIReinforcementProduct | str,
) -> int:
    product = _coerce_product(product)
    permitted = [limit.max_yield_strength_psi for limit in reinforcement_strength_limits(usage, application) if product in limit.permitted_products]
    if not permitted:
        raise ValueError(f"{product.value} is not permitted for {usage!r} / {application!r}.")
    return max(permitted)


def _coerce_usage(value: ACIReinforcementUsage | str) -> ACIReinforcementUsage:
    if isinstance(value, ACIReinforcementUsage):
        return value
    normalized = value.strip().lower()
    for item in ACIReinforcementUsage:
        if normalized in {item.value, item.name.lower()}:
            return item
    raise ValueError(f"{value!r} is not a valid reinforcement usage.")


def _coerce_application(value: ACIReinforcementApplication | str) -> ACIReinforcementApplication:
    if isinstance(value, ACIReinforcementApplication):
        return value
    normalized = value.strip().lower()
    for item in ACIReinforcementApplication:
        if normalized in {item.value, item.name.lower()}:
            return item
    raise ValueError(f"{value!r} is not a valid reinforcement application.")


def _coerce_product(value: ACIReinforcementProduct | str) -> ACIReinforcementProduct:
    if isinstance(value, ACIReinforcementProduct):
        return value
    normalized = value.strip().lower()
    for item in ACIReinforcementProduct:
        if normalized in {item.value, item.name.lower()}:
            return item
    raise ValueError(f"{value!r} is not a valid reinforcement product.")
