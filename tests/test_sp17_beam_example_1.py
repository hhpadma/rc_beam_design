import pytest

from tests.sp17_examples import SP17_BEAM_EXAMPLE_1


def test_sp17_beam_example_1_given_values_are_recorded():
    example = SP17_BEAM_EXAMPLE_1

    assert example.service_additional_dead_load_psf == 15
    assert example.service_live_load_psf == 65
    assert example.concrete_strength_psi == 5000
    assert example.steel_yield_strength_psi == 60000
    assert example.lambda_factor == 1.0
    assert example.span_ft == 36
    assert example.beam_width_in == 18
    assert example.slab_thickness_in == 7
    assert example.column_width_in == 24
    assert example.column_depth_in == 24
    assert example.tributary_width_ft == 14


def test_sp17_beam_example_1_service_line_loads_from_visible_data():
    example = SP17_BEAM_EXAMPLE_1

    assert example.service_additional_dead_line_load_plf == 210
    assert example.service_live_line_load_plf == 910
    assert pytest.approx(example.slab_self_weight_psf) == 87.5
    assert pytest.approx(example.slab_self_weight_line_load_plf) == 1093.75
    assert pytest.approx(example.beam_self_weight_klf) == 0.5625
    assert pytest.approx(example.slab_self_weight_klf) == 1.09375
    assert pytest.approx(example.additional_dead_load_klf) == 0.21
    assert pytest.approx(example.live_load_klf) == 0.91
    assert pytest.approx(example.total_dead_load_klf) == 1.86625
    assert pytest.approx(example.factored_dead_only_load_klf) == 2.61275
    assert pytest.approx(example.factored_dead_live_load_klf) == 3.6955


def test_sp17_beam_example_1_aci_interior_t_beam_effective_width_target():
    example = SP17_BEAM_EXAMPLE_1

    assert example.clear_span_in / 8 == 51
    assert 8 * example.slab_thickness_in == 56
    assert example.clear_distance_to_next_beam_in / 2 == 84
    assert example.aci_interior_t_beam_clear_span_overhang_limit_in == 51
    assert example.aci_example_effective_flange_width_in == 120


def test_sp17_beam_example_1_material_objects_match_given_values():
    example = SP17_BEAM_EXAMPLE_1

    assert example.concrete().compressive_strength == 5000
    assert example.steel().yield_strength == 60000


def test_sp17_beam_example_1_generates_line_load_actions():
    example = SP17_BEAM_EXAMPLE_1
    actions = example.line_load_actions()
    totals = actions.by_source()

    assert pytest.approx(totals["D"]) == example.total_dead_load_klf
    assert pytest.approx(totals["L"]) == example.live_load_klf
