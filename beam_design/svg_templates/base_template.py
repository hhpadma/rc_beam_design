import svgwrite


class SVGBase:
    def __init__(self, width, height, scale=10):
        self.scale = scale
        self.width = width * scale
        self.height = height * scale

        self.dwg = svgwrite.Drawing(
            size=(self.width, self.height),
            profile="full"
        )

        self.layer_geom = self.dwg.add(self.dwg.g(
            id="geometry", stroke="white", fill="none"))
        self.layer_rebar = self.dwg.add(self.dwg.g(
            id="rebar", stroke="red", fill="none"))
        self.layer_text = self.dwg.add(self.dwg.g(id="text"))

    def save(self, filename):
        self.dwg.saveas(filename)
