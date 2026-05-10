from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from types import MappingProxyType


class ACIStrengthReductionCategory(Enum):
    MOMENT_AXIAL = "moment_axial"
    SHEAR = "shear"
    TORSION = "torsion"
    BEARING = "bearing"
    POST_TENSIONED_ANCHORAGE_ZONE = "post_tensioned_anchorage_zone"
    BRACKET_OR_CORBEL = "bracket_or_corbel"
    STRUT_AND_TIE = "strut_and_tie"
    PRECAST_CONNECTION_YIELDING_STEEL = "precast_connection_yielding_steel"
    PLAIN_CONCRETE = "plain_concrete"
    ANCHOR_IN_CONCRETE = "anchor_in_concrete"


class ACITransverseReinforcementType(Enum):
    SPIRAL = "spiral"
    OTHER = "other"


class ACIStrainControlRegion(Enum):
    COMPRESSION_CONTROLLED = "compression_controlled"
    TRANSITION = "transition"
    TENSION_CONTROLLED = "tension_controlled"


@dataclass(frozen=True)
class ACIStrengthReductionFactor:
    category: ACIStrengthReductionCategory
    phi: float | None = None
    min_phi: float | None = None
    max_phi: float | None = None
    reference: str = "ACI 318-14 Table 21.2.1"
    note: str = ""

    @property
    def is_range(self) -> bool:
        return self.phi is None


PHI_TABLE_21_2_1 = MappingProxyType(
    {
        ACIStrengthReductionCategory.MOMENT_AXIAL: ACIStrengthReductionFactor(
            category=ACIStrengthReductionCategory.MOMENT_AXIAL,
            min_phi=0.65,
            max_phi=0.90,
            note="Use ACI 318-14 Table 21.2.2.",
        ),
        ACIStrengthReductionCategory.SHEAR: ACIStrengthReductionFactor(
            category=ACIStrengthReductionCategory.SHEAR,
            phi=0.75,
            note="Additional requirements may apply for seismic force-resisting systems.",
        ),
        ACIStrengthReductionCategory.TORSION: ACIStrengthReductionFactor(
            category=ACIStrengthReductionCategory.TORSION,
            phi=0.75,
        ),
        ACIStrengthReductionCategory.BEARING: ACIStrengthReductionFactor(
            category=ACIStrengthReductionCategory.BEARING,
            phi=0.65,
        ),
        ACIStrengthReductionCategory.POST_TENSIONED_ANCHORAGE_ZONE: ACIStrengthReductionFactor(
            category=ACIStrengthReductionCategory.POST_TENSIONED_ANCHORAGE_ZONE,
            phi=0.85,
        ),
        ACIStrengthReductionCategory.BRACKET_OR_CORBEL: ACIStrengthReductionFactor(
            category=ACIStrengthReductionCategory.BRACKET_OR_CORBEL,
            phi=0.75,
        ),
        ACIStrengthReductionCategory.STRUT_AND_TIE: ACIStrengthReductionFactor(
            category=ACIStrengthReductionCategory.STRUT_AND_TIE,
            phi=0.75,
        ),
        ACIStrengthReductionCategory.PRECAST_CONNECTION_YIELDING_STEEL: ACIStrengthReductionFactor(
            category=ACIStrengthReductionCategory.PRECAST_CONNECTION_YIELDING_STEEL,
            phi=0.90,
        ),
        ACIStrengthReductionCategory.PLAIN_CONCRETE: ACIStrengthReductionFactor(
            category=ACIStrengthReductionCategory.PLAIN_CONCRETE,
            phi=0.60,
        ),
        ACIStrengthReductionCategory.ANCHOR_IN_CONCRETE: ACIStrengthReductionFactor(
            category=ACIStrengthReductionCategory.ANCHOR_IN_CONCRETE,
            min_phi=0.45,
            max_phi=0.75,
            reference="ACI 318-14 Chapter 17",
        ),
    }
)


def strength_reduction_factor(category: ACIStrengthReductionCategory | str) -> ACIStrengthReductionFactor:
    category = coerce_strength_reduction_category(category)
    return PHI_TABLE_21_2_1[category]


def fixed_phi(category: ACIStrengthReductionCategory | str) -> float:
    record = strength_reduction_factor(category)
    if record.phi is None:
        raise ValueError(f"{record.category.value} requires a context-specific strength reduction factor.")
    return record.phi


@lru_cache(maxsize=None)
def compression_controlled_strain_limit(fy_psi: float, es_psi: float, grade60_deformed: bool = True) -> float:
    if fy_psi <= 0 or es_psi <= 0:
        raise ValueError("fy and Es must be positive.")
    if grade60_deformed and abs(fy_psi - 60000.0) < 1e-9:
        return 0.002
    return fy_psi / es_psi


@lru_cache(maxsize=None)
def phi_for_moment_axial(
    net_tensile_strain: float,
    fy_psi: float = 60000.0,
    es_psi: float = 29000000.0,
    transverse_reinforcement: ACITransverseReinforcementType | str = ACITransverseReinforcementType.OTHER,
    grade60_deformed: bool = True,
) -> float:
    transverse = coerce_transverse_reinforcement_type(transverse_reinforcement)
    ety = compression_controlled_strain_limit(fy_psi, es_psi, grade60_deformed)
    if net_tensile_strain <= ety:
        return 0.75 if transverse == ACITransverseReinforcementType.SPIRAL else 0.65
    if net_tensile_strain >= 0.005:
        return 0.90

    transition_fraction = (net_tensile_strain - ety) / (0.005 - ety)
    if transverse == ACITransverseReinforcementType.SPIRAL:
        return 0.75 + 0.15 * transition_fraction
    return 0.65 + 0.25 * transition_fraction


def strain_control_region(
    net_tensile_strain: float,
    fy_psi: float = 60000.0,
    es_psi: float = 29000000.0,
    grade60_deformed: bool = True,
) -> ACIStrainControlRegion:
    ety = compression_controlled_strain_limit(fy_psi, es_psi, grade60_deformed)
    if net_tensile_strain <= ety:
        return ACIStrainControlRegion.COMPRESSION_CONTROLLED
    if net_tensile_strain >= 0.005:
        return ACIStrainControlRegion.TENSION_CONTROLLED
    return ACIStrainControlRegion.TRANSITION


def coerce_strength_reduction_category(value: ACIStrengthReductionCategory | str) -> ACIStrengthReductionCategory:
    if isinstance(value, ACIStrengthReductionCategory):
        return value
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    return ACIStrengthReductionCategory(normalized)


def coerce_transverse_reinforcement_type(value: ACITransverseReinforcementType | str) -> ACITransverseReinforcementType:
    if isinstance(value, ACITransverseReinforcementType):
        return value
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    return ACITransverseReinforcementType(normalized)
