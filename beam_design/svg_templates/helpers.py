import svgwrite


def draw_dimension(dwg, layer, p1, p2, offset=10, text=""):
    """Draws a linear dimension with arrows."""
    (x1, y1), (x2, y2) = p1, p2

    # extension lines
    layer.add(dwg.line((x1, y1), (x1, y1 - offset), stroke="white"))
    layer.add(dwg.line((x2, y2), (x2, y2 - offset), stroke="white"))

    # dimension line
    layer.add(dwg.line((x1, y1 - offset), (x2, y2 - offset),
                       stroke="white",
                       marker_start="url(#arrow)",
                       marker_end="url(#arrow)"))

    # text
    layer.add(dwg.text(
        text,
        insert=((x1 + x2) / 2, y1 - offset - 4),
        fill="orange",
        text_anchor="middle"
    ))


def draw_leader(dwg, layer, start, elbow, end, text):
    """Draws leader line with elbow."""
    layer.add(dwg.polyline(
        [start, elbow, end],
        fill="none",
        stroke="white"
    ))
    layer.add(dwg.text(
        text,
        insert=(end[0] + 5, end[1]),
        fill="orange"
    ))
