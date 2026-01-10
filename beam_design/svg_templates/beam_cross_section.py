from base_template import SVGBase
from helpers import draw_dimension, draw_leader
from stirrups import draw_closed_stirrup


class BeamSectionSVG(SVGBase):
    def __init__(self, b, h, cover, scale=10):
        super().__init__(b+12, h+12, scale)
        self.b = b
        self.h = h
        self.cover = cover
        self.cx = self.width / 2
        self.cy = self.height / 2

        # arrow marker
        marker = self.dwg.marker(
            id="arrow",
            insert=(5, 5),
            size=(10, 10),
            orient="auto"
        )
        marker.add(self.dwg.path(d="M0,0 L10,5 L0,10 Z", fill="white"))
        self.dwg.defs.add(marker)

    def draw_concrete(self):
        self.layer_geom.add(self.dwg.rect(
            insert=(
                self.cx - self.b*self.scale/2,
                self.cy - self.h*self.scale/2
            ),
            size=(self.b*self.scale, self.h*self.scale),
            stroke_width=2
        ))

    def draw_longitudinal_bars(self, bars):
        for x, y, d in bars:
            self.layer_rebar.add(self.dwg.circle(
                center=(self.cx + x*self.scale,
                        self.cy - y*self.scale),
                r=(d/2)*self.scale
            ))

    def draw_stirrups(self, bar_dia):
        draw_closed_stirrup(
            self.dwg, self.layer_rebar,
            self.cx, self.cy,
            self.b, self.h,
            self.cover,
            bar_dia,
            self.scale
        )

    def draw_dimensions(self):
        draw_dimension(
            self.dwg, self.layer_geom,
            (self.cx - self.b*self.scale/2, self.cy + self.h*self.scale/2),
            (self.cx + self.b*self.scale/2, self.cy + self.h*self.scale/2),
            offset=20,
            text=f'{self.b}"'
        )

        draw_dimension(
            self.dwg, self.layer_geom,
            (self.cx - self.b*self.scale/2, self.cy - self.h*self.scale/2),
            (self.cx - self.b*self.scale/2, self.cy + self.h*self.scale/2),
            offset=20,
            text=f'{self.h}"'
        )


if __name__ == "__main__":

    beam = BeamSectionSVG(b=10, h=15, cover=1.5, scale=14)

    beam.draw_concrete()

    beam.draw_longitudinal_bars([
        (-3, -6, 0.63), (3, -6, 0.63),
        (-3, 6, 0.63),  (3, 6, 0.63)
    ])

    beam.draw_stirrups(bar_dia=0.375)  # Ø10 stirrup
    beam.draw_dimensions()

    beam.layer_text.add(beam.dwg.text(
        "Ø10 @ 5\" C/C",
        insert=(beam.cx + 90, beam.cy),
        fill="orange"
    ))

    beam.save("beam_section_detail.svg")
