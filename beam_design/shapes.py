from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
import math


# ---- ShapeType Enum ----
class ShapeType(Enum):
    RECTANGULAR = "Rectangular"
    # Additional shapes can be added here in the future


# ---- Abstract Base Shape ----
@dataclass
class Shape(ABC):
    b: float   # width (in)
    h: float   # height (in)

    @abstractmethod
    def area(self) -> float:
        """Gross cross-sectional area (in^2)."""
        pass

    @abstractmethod
    def inertia_XX(self) -> float:
        """Moment of inertia about 22-axis (in^4)."""
        pass

    @abstractmethod
    def inertia_YY(self) -> float:
        """Moment of inertia about 33-axis (in^4)."""
        pass

    @abstractmethod
    def shape_type(self) -> ShapeType:
        pass

    # ---- Derived common properties ----
    def section_modulus_22(self) -> float:
        return self.inertia_XX() / (self.h / 2)

    def section_modulus_33(self) -> float:
        return self.inertia_YY() / (self.b / 2)

    def plastic_modulus_22(self) -> float:
        return (self.b * self.h**2) / 4

    def plastic_modulus_33(self) -> float:
        return (self.h * self.b**2) / 4

    def radius_of_gyration_22(self) -> float:
        return math.sqrt(self.inertia_XX() / self.area())

    def radius_of_gyration_33(self) -> float:
        return math.sqrt(self.inertia_YY() / self.area())

    def torsion_constant(self) -> float:
        """Approximate torsional constant J for rectangles."""
        b, h = max(self.b, self.h), min(self.b, self.h)
        return (b * h**3) * (1/3 - 0.21*(h/b)*(1 - (h**4)/(12*b**4)))

    def summary(self) -> dict:
        """Return dictionary of all key shape properties."""
        return {
            "Shape Type": self.shape_type().value,
            "Area (in^2)": self.area(),
            "IXX (in^4)": self.inertia_XX(),
            "IYY (in^4)": self.inertia_YY(),
            "SXX (in^3)": self.section_modulus_22(),
            "SYY (in^3)": self.section_modulus_33(),
            "ZXX (in^3)": self.plastic_modulus_22(),
            "ZYY (in^3)": self.plastic_modulus_33(),
            "RXX (in)": self.radius_of_gyration_22(),
            "RYY (in)": self.radius_of_gyration_33(),
            "J (in^4)": self.torsion_constant(),
            "CG Offset": (0, 0),
            "PNA Offset": (0, 0)
        }


# ---- Rectangular Shape ----
@dataclass
class RectangularShape(Shape):

    def area(self) -> float:
        return self.b * self.h

    def inertia_XX(self) -> float:
        """Inertia about axis parallel to width (b)."""
        return (self.b * self.h**3) / 12.0

    def inertia_YY(self) -> float:
        """Inertia about axis parallel to depth (h)."""
        return (self.h * self.b**3) / 12.0

    def shape_type(self) -> ShapeType:
        return ShapeType.RECTANGULAR


# Example usage
if __name__ == "__main__":
    shape = RectangularShape(b=15, h=24)
    props = shape.summary()
    for k, v in props.items():
        if isinstance(v, tuple):
            print(f"{k:20s} = {v}")
        else:
            print(f"{k:20s} = {v:.4f}")
