import pytest

from beam_design.codes.aci318.load_combinations import (
    ACIActionSource,
    ACILoadCombinations,
    ActionPattern,
)
from tests.sp17_examples import SP17_BEAM_EXAMPLE_1


def test_aci_load_combinations_include_table_5_3_1_equations():
    equations = ACILoadCombinations().equations()

    assert [equation.equation for equation in equations] == [
        "5.3.1a",
        "5.3.1b",
        "5.3.1c",
        "5.3.1d",
        "5.3.1e",
        "5.3.1f",
        "5.3.1g",
    ]


def test_sp17_example_dead_only_load_combination():
    example = SP17_BEAM_EXAMPLE_1
    actions = example.line_load_actions()
    pattern = ActionPattern.from_action_set(actions)
    results = ACILoadCombinations().combine(pattern, include_lateral=False)
    dead_only = next(result for result in results if result.equation == "5.3.1a")

    assert dead_only.primary_source == ACIActionSource.DEAD
    assert pytest.approx(dead_only.value) == example.factored_dead_only_load_klf


def test_sp17_example_gravity_envelope_governs_by_dead_plus_live():
    example = SP17_BEAM_EXAMPLE_1
    pattern = ActionPattern.from_action_set(example.line_load_actions())
    envelope = ACILoadCombinations().action_envelope(pattern, include_lateral=False)
    governing = envelope.governing

    assert governing.equation == "5.3.1b"
    assert governing.primary_source == ACIActionSource.LIVE
    assert pytest.approx(governing.value) == example.factored_dead_live_load_klf


def test_sp17_handbook_rounded_display_values_match_example_page():
    pattern = ActionPattern.from_action_set(SP17_BEAM_EXAMPLE_1.rounded_handbook_line_load_actions())
    governing = ACILoadCombinations().action_envelope(
        pattern,
        include_lateral=False,
    ).governing

    assert governing.equation == "5.3.1b"
    assert pytest.approx(1.4 * pattern.total_by_source()[ACIActionSource.DEAD], abs=0.05) == 2.6
    assert pytest.approx(governing.value, abs=0.05) == 3.7


def test_action_effects_use_same_combination_engine_for_any_scalar_response():
    pattern = ActionPattern.from_values(D=10.0, L=6.0, W=-3.0)
    envelope = ACILoadCombinations().action_envelope(pattern)

    assert abs(envelope.governing.value) == max(
        abs(result.value) for result in envelope.results
    )
