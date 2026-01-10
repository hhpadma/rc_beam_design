from dataclasses import dataclass
from math import pi


@dataclass
class LineSegment:
    start: tuple
    end: tuple


@dataclass
class ArcSegment:
    center: tuple
    radius: float
    start_angle: float
    end_angle: float


class StirrupGeometry:
    """
    Pure geometry model of a rectangular stirrup with hooks
    (ACI-compliant, no drawing code)
    """

    def __init__(self, bw, bh, db, hook_angle=135):
        self.bw = bw
        self.bh = bh
        self.db = db
        self.hook_angle = hook_angle

        self.r = 2.0 * db  # inside bend radius (ACI 25.3.2)
        self.hook_length = max(6 * db, 3.0)

        self.lines = []
        self.arcs = []

        self._build_geometry()

    def _build_geometry(self):
        r = self.r
        bw = self.bw
        bh = self.bh

        # ---- Key points ----
        A = (r, 0)
        B = (bw - r, 0)
        C = (bw, r)
        D = (bw, bh - r)
        E = (bw - r, bh)
        F = (r, bh)
        G = (0, bh - r)
        H = (0, r)

        # ---- Straight segments ----
        self.lines.extend([
            LineSegment(A, B),
            LineSegment(C, D),
            LineSegment(E, F),
            LineSegment(G, H)
        ])

        # ---- Corner arcs (90° each) ----
        self.arcs.extend([
            ArcSegment(center=(bw - r, r), radius=r,
                       start_angle=-pi/2, end_angle=0),

            ArcSegment(center=(bw - r, bh - r), radius=r,
                       start_angle=0, end_angle=pi/2),

            ArcSegment(center=(r, bh - r), radius=r,
                       start_angle=pi/2, end_angle=pi),

            ArcSegment(center=(r, r), radius=r,
                       start_angle=pi, end_angle=3*pi/2),
        ])

        # ---- 135° Hook (top-left) ----
        theta = self.hook_angle * pi / 180

        hook_arc_start = 3*pi/2
        hook_arc_end = hook_arc_start + theta

        self.arcs.append(
            ArcSegment(
                center=(r, r),
                radius=r,
                start_angle=hook_arc_start,
                end_angle=hook_arc_end
            )
        )

        # Hook extension line
        hx = r - self.hook_length
        hy = 0 - self.hook_length

        self.lines.append(
            LineSegment(
                start=(r, 0),
                end=(hx, hy)
            )
        )

    def get_lines(self):
        return self.lines

    def get_arcs(self):
        return self.arcs
