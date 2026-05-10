import pytest

from beam_design.codes.aci318.materials import (
    ACIAggregateConcreteType,
    ACIReinforcementApplication,
    ACIReinforcementProduct,
    ACIReinforcementUsage,
    LAMBDA_TABLE_19_2_4_2,
    lambda_factor,
    max_permitted_design_yield_strength,
)


def test_lambda_table_fixed_values_are_stored():
    assert lambda_factor(ACIAggregateConcreteType.ALL_LIGHTWEIGHT) == 0.75
    assert lambda_factor(ACIAggregateConcreteType.SAND_LIGHTWEIGHT) == 0.85
    assert lambda_factor(ACIAggregateConcreteType.NORMALWEIGHT) == 1.0
    assert LAMBDA_TABLE_19_2_4_2[ACIAggregateConcreteType.NORMALWEIGHT].fine_aggregate == "ASTM C33"


def test_lambda_blend_requires_explicit_interpolation_fraction():
    with pytest.raises(ValueError):
        lambda_factor(ACIAggregateConcreteType.LIGHTWEIGHT_FINE_BLEND)

    assert pytest.approx(
        lambda_factor(ACIAggregateConcreteType.LIGHTWEIGHT_FINE_BLEND, normalweight_aggregate_fraction=0.4)
    ) == 0.79
    assert pytest.approx(
        lambda_factor(ACIAggregateConcreteType.SAND_LIGHTWEIGHT_COARSE_BLEND, normalweight_aggregate_fraction=0.4)
    ) == 0.91


def test_reinforcement_strength_limit_table_for_shear_stirrups_and_flexure():
    assert (
        max_permitted_design_yield_strength(
            ACIReinforcementUsage.SHEAR,
            ACIReinforcementApplication.STIRRUPS_TIES_HOOPS,
            ACIReinforcementProduct.DEFORMED_BARS,
        )
        == 60_000
    )
    assert (
        max_permitted_design_yield_strength(
            ACIReinforcementUsage.SHEAR,
            ACIReinforcementApplication.STIRRUPS_TIES_HOOPS,
            ACIReinforcementProduct.WELDED_WIRE_REINFORCEMENT,
        )
        == 80_000
    )
    assert (
        max_permitted_design_yield_strength(
            ACIReinforcementUsage.FLEXURE_AXIAL_SHRINKAGE_TEMPERATURE,
            ACIReinforcementApplication.OTHER,
            ACIReinforcementProduct.DEFORMED_BARS,
        )
        == 80_000
    )
