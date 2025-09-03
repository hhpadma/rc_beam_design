import pytest
from beam_design.steel import Steel


def test_yield_strain():
    s = Steel(fy=60000)
    assert pytest.approx(s.epsilon_y, rel=0.01) == 60000 / 29_000_000


def test_stress_elastic():
    s = Steel(fy=60000)
    strain = 0.001
    assert pytest.approx(s.stress(strain)) == strain * s.Es


def test_stress_yield_plateau():
    s = Steel(fy=60000)
    strain = 0.01
    assert s.stress(strain) == 60000
