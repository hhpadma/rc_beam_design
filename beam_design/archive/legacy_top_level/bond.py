from math import sqrt
from functools import cached_property
from abc import ABC, abstractmethod
from beam_design.rebar import BarFunction, BarStressState, BarTag, RebarCatalog
from beam_design.mat_concrete import Concrete
from beam_design.mat_steel import Steel


class HookRule(ABC):
    """
    Abstract base class for hook and bend rules defined by a design code.
    """

    def __init__(
        self,
        bar_diameter: float,
        hook_angle_deg: int,
        bar_function: BarFunction
    ):
        self.db = bar_diameter
        self.angle = hook_angle_deg
        self.function = bar_function

    @property
    @abstractmethod
    def hook_length(self) -> float:
        """Straight extension beyond bend (in)."""
        pass

    @property
    @abstractmethod
    def inside_bend_diameter(self) -> float:
        """Inside diameter of bend (in)."""
        pass


class DevelopmentLengthRule(ABC):
    """
    Abstract base class for development length rules defined by a design code.
    """

    @abstractmethod
    def development_length(self) -> float:
        """Development length (in)."""
        pass


class DevelopmentLengthRuleACI(DevelopmentLengthRule):
    """
    ACI-318 Development length rule implementation for reinforcing bars.
    This class computes required development lengths ( in inches) for reinforcing bars
    per ACI 318 provisions. It supports tension(straight and hooked) and
    compression cases and applies ACI modification factors for top casting,
    epoxy coating, concrete cover, and confinement.
    Parameters
    ----------
    concrete: Concrete
        Concrete material object with attribute `compressive_strength` (concrete compressive
        strength in psi).
    steel: Steel
        Steel material object with attribute `yield_strength` (specified yield strength
        in psi).
    bar_tag: BarTag
        Enum/flag indicating standard rebar size(tag) from `RebarCatalog`.
    stress_state: BarStressState
        Enum/flag indicating bar stress state(tension or compression).
    hooked: bool, optional
        True if bar is anchored with a hook; affects tension development checks.
        Default: False.
    top_cast: bool, optional
        True if bar is located in top-cast concrete(affects psi_t). Default: False.
    epoxy_coated: bool, optional
        True if bar is epoxy-coated(affects psi_e). Default: False.
    confinement: bool or numeric, optional
        Indicates whether adequate confinement is present(affects psi_r).
        Default: False.
    cover: bool or numeric, optional
        Indicates concrete cover condition(affects psi_c). Default: False.
    Attributes
    ----------
    fc: float
        Concrete compressive strength(psi), copied from `concrete.compressive_strength`.
    fy: float
        Steel yield strength(psi), copied from `steel.yield_strength`.
    db: float
        Bar diameter(inches).
    stress_state: BarStressState
        Stored stress state.
    hook: bool
        Hooked anchor flag.
    top_cast: bool
        Top-cast modifier flag.
        True: For more than 12 in. of fresh concrete is placed below horizontal reinforcement
    epoxy: bool
        Epoxy-coating modifier flag.
        True: For epoxy-coated bars
    confinement: bool
        Confinement modifier flag.
        True: For 90° hooks of No. 11 and smaller bars that are either (1) enclosed along ℓ_dh within ties or stirrups perpendicular to ℓ_dh at s ≤ 3d_b or
        (2) enclosed along the bar extension beyond hook including the bend within ties or stirrups perpendicular to the tail extension of
        the hook at s ≤ 3d_b : 0.8 For 180-degree hooks of No. 11 and smaller bars enclosed along
        ℓ_dh within ties or stirrups perpendicular to ℓ_dh at s ≤ 3d_b
    cover: bool
        Concrete cover modifier flag. 
        True: For No. 11 bar and smaller hooks with side cover (normal to plane
        of hook) ≥ 2.5 in. and for 90 ° hooks with cover on bar extension beyond hook ≥ 2 in.
    Notes
    -----
    - All inputs and outputs are in imperial units: psi for stresses, inches for
      lengths.
    - The implementation uses the ACI expressions:
        straight/hooked tension nominal length:
            ld = (3/40) * (fy / sqrt(fc)) * db * psi_t * psi_e * psi_s
          and enforces the minimum: max(ld, max(12.0, 40 * db))
        compression nominal length:
            ldc = 0.02 * (fy / sqrt(fc)) * db
          and enforces the minimum: max(ldc, max(8.0, 20 * db))
    - psi_t, psi_e, psi_c, and psi_r are implemented as method helpers:
        psi_t = 1.3 if top_cast else 1.0
        psi_e = 1.2 if epoxy_coated else 1.0
        psi_c = 0.7 if cover <= 1.0 else 1.0
        psi_r = 0.7 if confinement <= 1.0 else 1.0
    - psi_s (bar surface condition factor) is expected to be provided by the
      DevelopmentLengthRule base class or another mixin; it represents surface
      condition (e.g., plain vs deformed) and is included in the tension formulas.
    Returns
    -------
    float
        Required development length in inches as determined by ACI rules.
    Example
    -------
    >>> rule = DevelopmentLengthRuleACI(concrete, steel, 0.75, BarStressState.TENSION,
    ...                                hooked=False, top_cast=True, epoxy_coated=False)
    >>> ld_in = rule.calculate()
    """

    def __init__(
        self,
        concrete: Concrete,
        steel: Steel,
        bar_tag: BarTag,
        stress_state: BarStressState = BarStressState.TENSION,
        lw_factor: float = 1.0,
        hooked: bool = False,
        top_cast: bool = False,
        epoxy_coated: bool = False,
        confinement: bool = False,
        cover: bool = False
    ):
        self.fc = concrete.compressive_strength
        self.fy = steel.yield_strength
        self.db = RebarCatalog.get(bar_tag).diameter_in
        self.stress_state = stress_state
        self.lw_factor = lw_factor
        self.hook = hooked
        self.top_cast = top_cast
        self.epoxy = epoxy_coated
        self.confinement = confinement
        self.cover = cover

    # -------------------------
    # Modification factors
    # -------------------------
    def psi_t(self):
        return 1.3 if self.top_cast else 1.0

    def psi_e(self):
        return 1.2 if self.epoxy else 1.0

    def psi_c(self):
        return 0.7 if self.cover else 1.0

    def psi_r(self):
        return 0.7 if self.confinement else 1.0

    # -------------------------
    # Main API
    # -------------------------
    def calculate(self) -> float:
        if self.stress_state == BarStressState.COMPRESSION:
            return self._compression_development()
        else:
            if self.hook:
                return self._hooked_tension_development()
            else:
                return self._straight_tension_development()

    # -------------------------
    # Internal calculations
    # -------------------------
    def _straight_tension_development(self):
        frac_ld = (
            self.fy / (self.lw_factor*sqrt(self.fc))
            * self.db
            * self.psi_t()
            * self.psi_e()
        )
        return frac_ld/20 if self.db > 0.9 else frac_ld/25

    def _hooked_tension_development(self):
        ld = (
            self.fy / (self.lw_factor*sqrt(self.fc))
            * self.db
            * self.psi_e()
            * self.psi_c()
            * self.psi_r()
        )/50
        return ld

    def _compression_development(self):
        ldc = (
            self.fy / (self.lw_factor*sqrt(self.fc))
            * self.db
            * self.psi_r()
        )/50
        return max(ldc, 0.0003*self.fy*self.db)


class HookRuleACI(HookRule):
    """
    ACI 318 hook and bend requirements for reinforcing bars.
    """

    @cached_property
    def hook_length(self) -> float:

        if self.function == BarFunction.MAIN:
            return self._main_bar_hook_length()

        elif self.function == BarFunction.STIRRUP:
            return self._stirrup_hook_length()

        raise ValueError("Unsupported bar function")

    def _main_bar_hook_length(self) -> float:
        if self.angle == 90:
            return max(12 * self.db, 6.0)
        elif self.angle == 180:
            return max(4 * self.db, 2.5)
        else:
            raise ValueError("Unsupported hook angle for main bars")

    def _stirrup_hook_length(self) -> float:
        if self.angle == 90 and self.db <= 0.63:  # #3, #4, #5
            return max(6 * self.db, 3.0)
        elif self.angle == 90 and self.db <= 1:  # #3, #4, #5
            return 12 * self.db
        elif self.angle == 135 and self.db <= 1:
            return max(6 * self.db, 3.0)
        elif self.angle == 180 and self.db <= 1:
            return max(4 * self.db, 2.5)
        else:
            raise ValueError("Unsupported hook angle for stirrups")

    @cached_property
    def inside_bend_diameter(self) -> float:
        """
        ACI 318:
        - Main bars: varies by bar size
        - Stirrups/ties (No. 5 and smaller): 4db
        """

        if self.function == BarFunction.STIRRUP:
            return 4.0 * self.db

        elif self.function == BarFunction.MAIN:
            if self.db <= 0.63:       # ~ No. 5
                return 3.0 * self.db
            elif self.db <= 1.41:      # ~ No. 11
                return 4.0 * self.db
            else:
                return 5.0 * self.db
        else:
            raise ValueError("Unsupported bar function")


if __name__ == "__main__":
    bar = RebarCatalog.get(BarTag.B20)

    hook = HookRuleACI(
        bar_diameter=bar.diameter_in,
        hook_angle_deg=180,
        bar_function=BarFunction.MAIN
    )
    db = bar.diameter_in
    bend_d = hook.inside_bend_diameter
    print(f"Bar Diameter: {db:.3f} in")
    print(f"Hook Angle: {hook.angle} degrees")
    print(f"Hook Length: {hook.hook_length:.3f} in")
    print(f"Inside Bend Diameter: {bend_d:.3f} in")
