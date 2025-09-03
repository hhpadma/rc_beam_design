from dataclasses import dataclass


@dataclass
class Steel:
    fy: float  # yield strength (psi)
    Es: float = 29_000_000  # default modulus (psi)

    @property
    def epsilon_y(self) -> float:
        """Yield strain."""
        return self.fy / self.Es

    def stress(self, strain: float) -> float:
        """
        Bilinear elastic-perfectly plastic model.
        Extend later for nonlinear hardening models.
        """
        if strain * self.Es <= self.fy:
            return strain * self.Es
        else:
            return self.fy
