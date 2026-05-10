import pytest

from beam_design.codes.aci318.sections import aci_effective_depth
from beam_design.core.model import BeamDesignContext, ReinforcementLayout
from beam_design.core.reinforcement import LongitudinalFace, LongitudinalLayerSpec
from beam_design.mat_concrete import Concrete
from beam_design.mat_steel import Steel
from beam_design.rebar import BarTag
from beam_design.reinforcement_assembler import ReinforcementAssembler
from beam_design.section_assembler import SectionAssembler


def test_aci_effective_depth_uses_default_trial_bar_assumptions_before_reinforcement_exists():
    section = SectionAssembler.rectangular(width=18.0, depth=30.0, cover=1.5)
    context = BeamDesignContext(section=section, concrete=Concrete(fc=5000), steel=Steel(fy=60000))

    assert aci_effective_depth(context) == 27.5


def test_aci_effective_depth_uses_actual_cage_centroid_after_reinforcement_exists():
    section = SectionAssembler.rectangular(width=18.0, depth=30.0, cover=1.5)
    assembler = ReinforcementAssembler(section=section, stirrup_bar=BarTag.B10)
    cage = assembler.cage(
        longitudinal_specs=(LongitudinalLayerSpec(LongitudinalFace.BOTTOM, BarTag.B25, 2),)
    )
    context = BeamDesignContext(
        section=section,
        concrete=Concrete(fc=5000),
        steel=Steel(fy=60000),
        reinforcement=ReinforcementLayout(cage=cage),
    )

    assert pytest.approx(aci_effective_depth(context)) == cage.bottom_centroid_y_from_top
