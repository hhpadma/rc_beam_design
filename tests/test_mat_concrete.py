import pytest
from beam_design.concrete import Concrete


def test_ec_calculation():
    c = Concrete(fc=4000)
    assert pytest.approx(c.Ec, rel=0.01) == 57000 * (4000 ** 0.5)


def test_beta1_limits():
    c1 = Concrete(fc=3000)
    c2 = Concrete(fc=6000)
    c3 = Concrete(fc=9000)
    assert c1.beta1 == 0.85
    assert 0.65 < c2.beta1 < 0.85
    assert c3.beta1 == 0.65
