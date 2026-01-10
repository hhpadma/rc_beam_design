import svgwrite
from math import cos, sin, pi
from stirrup_geometry import LineSegment, ArcSegment, StirrupGeometry


class StirrupSVGAdapter:
    """
    Converts StirrupGeometry into SVG path
    """

    def __init__(self, geometry: StirrupGeometry, scale=10.0):
        self.geom = geometry
        self.scale = scale

    def _s(self, value):
        """Scale inches → SVG units (px)"""
        return value * self.scale

    def _point(self, p):
        return (self._s(p[0]), self._s(p[1]))

    def _arc_endpoint(self, center, radius, angle):
        x = center[0] + radius * cos(angle)
        y = center[1] + radius * sin(angle)
        return self._point((x, y))

    def build_path(self, dwg: svgwrite.Drawing):
        path = dwg.path(
            fill="none",
            stroke="red",
            stroke_width=1.5
        )

        started = False

        # ---- Lines ----
        for seg in self.geom.get_lines():
            p1 = self._point(seg.start)
            p2 = self._point(seg.end)

            if not started:
                path.push(f"M {p1[0]},{p1[1]}")
                started = True

            path.push(f"L {p2[0]},{p2[1]}")

        # ---- Arcs ----
        for arc in self.geom.get_arcs():
            r = self._s(arc.radius)

            start = self._arc_endpoint(
                arc.center, arc.radius, arc.start_angle
            )
            end = self._arc_endpoint(
                arc.center, arc.radius, arc.end_angle
            )

            delta = arc.end_angle - arc.start_angle
            large_arc = 1 if abs(delta) > pi else 0
            sweep = 1 if delta > 0 else 0

            if not started:
                path.push(f"M {start[0]},{start[1]}")
                started = True
            else:
                path.push(f"L {start[0]},{start[1]}")

            path.push_arc(
                target=end,
                r=(r, r),
                rotation=0,
                large_arc=bool(large_arc),
                angle_dir='+' if sweep == 1 else '-'
            )

        dwg.add(path)
        return path


if __name__ == "__main__":

    dwg = svgwrite.Drawing("stirrup_clean.svg", size=("400px", "400px"))

    geom = StirrupGeometry(
        bw=6.0,
        bh=10.0,
        db=0.375,   # #3 bar
        hook_angle=135
    )

    adapter = StirrupSVGAdapter(geom, scale=25)
    adapter.build_path(dwg)

    dwg.save()
