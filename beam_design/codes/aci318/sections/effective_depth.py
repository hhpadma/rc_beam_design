from beam_design.codes.aci318.flexure.assumptions import effective_depth_one_layer
from beam_design.core.model import BeamDesignContext


DEFAULT_TRIAL_TRANSVERSE_BAR_DIAMETER_IN = 0.5
DEFAULT_TRIAL_LONGITUDINAL_BAR_DIAMETER_IN = 1.0


def aci_effective_depth(
    context: BeamDesignContext,
    *,
    trial_transverse_bar_diameter_in: float = DEFAULT_TRIAL_TRANSVERSE_BAR_DIAMETER_IN,
    trial_longitudinal_bar_diameter_in: float = DEFAULT_TRIAL_LONGITUDINAL_BAR_DIAMETER_IN,
) -> float:
    """Return actual section d when bars exist, otherwise an ACI trial d."""

    if context.reinforcement.tension_centroid_y_from_top is not None:
        return context.effective_depth

    transverse_diameter = float(
        context.metadata.get("aci_trial_transverse_bar_diameter_in", trial_transverse_bar_diameter_in)
    )
    longitudinal_diameter = float(
        context.metadata.get("aci_trial_longitudinal_bar_diameter_in", trial_longitudinal_bar_diameter_in)
    )
    return effective_depth_one_layer(
        total_depth_in=context.section.depth,
        clear_cover_in=context.section.cover,
        transverse_bar_diameter_in=transverse_diameter,
        longitudinal_bar_diameter_in=longitudinal_diameter,
    )
