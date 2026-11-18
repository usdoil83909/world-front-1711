import os
import struct
import zlib
import math


WIDTH = 1024
HEIGHT = 1024
LEFT, RIGHT, BOTTOM = 20, 1004, 966
PAPER = (246, 243, 234)
INK = (24, 22, 22)
GREY = (70, 68, 66)
WHITE = (255, 255, 255)
LIGHT_GREY = (218, 218, 218)
PALE_GREY = (232, 232, 232)
MID_GREY = (164, 164, 164)
MAP_GREY = (206, 206, 206)
RED = (170, 40, 36)


FONT = {
    "A": (14, 17, 17, 31, 17, 17, 17),
    "B": (30, 17, 17, 30, 17, 17, 30),
    "C": (14, 17, 16, 16, 16, 17, 14),
    "D": (30, 17, 17, 17, 17, 17, 30),
    "E": (31, 16, 16, 30, 16, 16, 31),
    "F": (31, 16, 16, 30, 16, 16, 16),
    "G": (14, 17, 16, 23, 17, 17, 15),
    "H": (17, 17, 17, 31, 17, 17, 17),
    "I": (14, 4, 4, 4, 4, 4, 14),
    "J": (7, 2, 2, 2, 18, 18, 12),
    "K": (17, 18, 20, 24, 20, 18, 17),
    "L": (16, 16, 16, 16, 16, 16, 31),
    "M": (17, 27, 21, 21, 17, 17, 17),
    "N": (17, 25, 21, 19, 17, 17, 17),
    "O": (14, 17, 17, 17, 17, 17, 14),
    "P": (30, 17, 17, 30, 16, 16, 16),
    "Q": (14, 17, 17, 17, 21, 18, 13),
    "R": (30, 17, 17, 30, 20, 18, 17),
    "S": (15, 16, 16, 14, 1, 1, 30),
    "T": (31, 4, 4, 4, 4, 4, 4),
    "U": (17, 17, 17, 17, 17, 17, 14),
    "V": (17, 17, 17, 17, 17, 10, 4),
    "W": (17, 17, 17, 21, 21, 21, 10),
    "X": (17, 17, 10, 4, 10, 17, 17),
    "Y": (17, 17, 10, 4, 4, 4, 4),
    "Z": (31, 1, 2, 4, 8, 16, 31),
    "0": (14, 17, 19, 21, 25, 17, 14),
    "1": (4, 12, 4, 4, 4, 4, 14),
    "2": (14, 17, 1, 2, 4, 8, 31),
    "3": (30, 1, 1, 14, 1, 1, 30),
    "4": (2, 6, 10, 18, 31, 2, 2),
    "5": (31, 16, 16, 30, 1, 1, 30),
    "6": (14, 16, 16, 30, 17, 17, 14),
    "7": (31, 1, 2, 4, 8, 8, 8),
    "8": (14, 17, 17, 14, 17, 17, 14),
    "9": (14, 17, 17, 15, 1, 1, 14),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 12, 12),
    ",": (0, 0, 0, 0, 4, 4, 8),
    "'": (4, 4, 8, 0, 0, 0, 0),
    "-": (0, 0, 0, 31, 0, 0, 0),
    ":": (0, 12, 12, 0, 12, 12, 0),
    ";": (0, 12, 12, 0, 4, 4, 8),
    "%": (17, 2, 4, 8, 16, 17, 0),
    "$": (4, 15, 20, 14, 5, 30, 4),
    "(": (2, 4, 8, 8, 8, 4, 2),
    ")": (8, 4, 2, 2, 2, 4, 8),
    "/": (1, 2, 2, 4, 8, 8, 16),
    "!": (4, 4, 4, 4, 4, 0, 4),
    "?": (14, 17, 1, 2, 4, 0, 4),
    "&": (12, 18, 20, 8, 21, 18, 13),
    "+": (0, 4, 4, 31, 4, 4, 0),
}


def text_width(text, scale):
    return (len(text) * 6 - 1) * scale if text else 0


def fill_rect(canvas, x, y, width, height, colour):
    """Reject misplaced ink rather than silently cropping it at the page edge."""
    if width <= 0 or height <= 0:
        return
    assert LEFT <= x and x + width <= RIGHT, (x, width)
    assert 0 <= y and y + height <= BOTTOM, (y, height)
    span = bytes(colour) * width
    for row in range(y, y + height):
        canvas[row][x * 3:(x + width) * 3] = span


def draw_text(canvas, x, y, text, scale, colour):
    assert x >= LEFT and x + text_width(text, scale) <= RIGHT
    assert y >= 0 and y + 7 * scale <= BOTTOM
    for index, character in enumerate(text.upper()):
        assert character in FONT, character
        for row, bits in enumerate(FONT[character]):
            for column in range(5):
                if bits & (1 << (4 - column)):
                    fill_rect(canvas, x + (index * 6 + column) * scale,
                              y + row * scale, scale, scale, colour)


def fitted_centered_text(canvas, y, text, scale, colour,
                         left=LEFT, right=RIGHT, margin=20):
    available = right - left - 2 * margin
    while scale > 1 and text_width(text, scale) > available:
        scale -= 1
    width = text_width(text, scale)
    assert width <= available, text
    x = left + (right - left - width) // 2
    draw_text(canvas, x, y, text, scale, colour)
    return x, width, scale


def wrap(text, px_width, scale):
    lines, current = [], ""
    for word in text.split():
        assert text_width(word, scale) <= px_width, word
        candidate = word if not current else current + " " + word
        if current and text_width(candidate, scale) > px_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def draw_rule(canvas, x, y, width, thickness=1):
    fill_rect(canvas, x, y, width, thickness, INK)


def draw_frame(canvas, x, y, width, height, colour=INK, thickness=1):
    fill_rect(canvas, x, y, width, thickness, colour)
    fill_rect(canvas, x, y + height - thickness, width, thickness, colour)
    fill_rect(canvas, x, y, thickness, height, colour)
    fill_rect(canvas, x + width - thickness, y, thickness, height, colour)


def draw_line(canvas, x0, y0, x1, y1, colour=INK, thickness=1):
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    error, radius = dx + dy, thickness // 2
    while True:
        fill_rect(canvas, x0 - radius, y0 - radius, thickness, thickness, colour)
        if x0 == x1 and y0 == y1:
            break
        doubled = 2 * error
        if doubled >= dy:
            error += dy
            x0 += sx
        if doubled <= dx:
            error += dx
            y0 += sy


def draw_polyline(canvas, points, colour=INK, thickness=1, closed=False):
    for first, second in zip(points, points[1:]):
        draw_line(canvas, *first, *second, colour, thickness)
    if closed and len(points) > 1:
        draw_line(canvas, *points[-1], *points[0], colour, thickness)


def fill_polygon(canvas, points, fill_colour=MAP_GREY, outline_colour=INK):
    assert len(points) >= 3
    for y in range(min(p[1] for p in points), max(p[1] for p in points) + 1):
        crossings = []
        for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
            if min(y1, y2) <= y < max(y1, y2):
                crossings.append(x1 + (y - y1) * (x2 - x1) // (y2 - y1))
        crossings.sort()
        for left, right in zip(crossings[::2], crossings[1::2]):
            fill_rect(canvas, left, y, right - left + 1, 1, fill_colour)
    if outline_colour is not None:
        draw_polyline(canvas, points, outline_colour, closed=True)


def fill_circle(canvas, center_x, center_y, radius, colour):
    for dy in range(-radius, radius + 1):
        dx = math.isqrt(radius * radius - dy * dy)
        fill_rect(canvas, center_x - dx, center_y + dy, 2 * dx + 1, 1, colour)


def draw_ellipse(canvas, cx, cy, rx, ry, colour=INK, steps=72):
    points = []
    for index in range(steps + 1):
        angle = 2 * math.pi * index / steps
        point = (round(cx + rx * math.cos(angle)), round(cy + ry * math.sin(angle)))
        if not points or point != points[-1]:
            points.append(point)
    draw_polyline(canvas, points, colour)


def dotted_route(canvas, points, colour=RED, spacing=5):
    """Carry the dot spacing continuously around each bend of the route."""
    travelled, next_dot = 0.0, 0.0
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        length = math.hypot(x1 - x0, y1 - y0)
        if length == 0:
            continue
        while next_dot <= travelled + length:
            fraction = (next_dot - travelled) / length
            x, y = round(x0 + fraction * (x1 - x0)), round(y0 + fraction * (y1 - y0))
            fill_circle(canvas, x, y, 1, colour)
            next_dot += spacing
        travelled += length


def draw_condensed_text(canvas, x, y, text, colour=INK):
    for index, character in enumerate(text.upper()):
        assert character in FONT, character
        for row, bits in enumerate(FONT[character]):
            for column in range(5):
                if bits & (1 << (4 - column)):
                    fill_rect(canvas, x + index * 5 + column * 4 // 5,
                              y + row * 2, 1, 2, colour)


def wrap_condensed(text, px_width):
    lines, current = [], ""
    for word in text.split():
        candidate = word if not current else current + " " + word
        if current and len(candidate) * 5 - 1 > px_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def draw_lead_panel(canvas, y, headline, dek, dek_scale=2):
    x, width = 32, 960
    dek_lines = wrap(dek, 930, dek_scale)
    assert 1 <= len(dek_lines) <= 2
    assert " ".join(dek_lines) == dek
    # The specified panel heights determine the lead band's exact boundaries.
    # Keep the final dek clear of the three-pixel bottom rule.
    height = 80 if len(dek_lines) == 2 else 66
    draw_frame(canvas, x, y, width, height, INK, 3)
    assert text_width(headline, 2) <= 930
    draw_text(canvas, x + 12, y + 6, headline, 2, INK)
    for index, line in enumerate(dek_lines):
        assert y + 38 + 18 * index + 7 * dek_scale <= y + height - 3
        draw_text(canvas, x + 12, y + 38 + 18 * index, line, dek_scale, GREY)
    return height


# Coastlines use geographic longitude/latitude, with 25--35 vertices each.
# Separate islands below supply detail without distorting the mainland shapes.
CONTINENTS = {
    "NORTH AMERICA": [
        (-168, 65), (-162, 70), (-146, 71), (-137, 69), (-129, 71),
        (-116, 73), (-103, 72), (-91, 70), (-81, 66), (-77, 59),
        (-65, 60), (-55, 53), (-60, 47), (-68, 45), (-72, 41),
        (-76, 36), (-81, 29), (-80, 25), (-83, 26), (-86, 30),
        (-91, 29), (-97, 26), (-96, 21), (-90, 19), (-87, 21),
        (-87, 16), (-83, 14), (-78, 9), (-84, 10), (-94, 16),
        (-105, 23), (-117, 32), (-126, 49), (-139, 60), (-153, 59),
    ],
    "SOUTH AMERICA": [
        (-81, 12), (-76, 10), (-71, 12), (-65, 10), (-61, 8),
        (-57, 6), (-52, 4), (-50, 0), (-45, -2), (-39, -5),
        (-35, -8), (-36, -14), (-39, -19), (-41, -23), (-46, -25),
        (-49, -29), (-52, -33), (-54, -36), (-59, -40), (-64, -44),
        (-66, -49), (-68, -55), (-72, -53), (-74, -47), (-75, -40),
        (-73, -31), (-71, -22), (-75, -15), (-79, -7), (-81, 1),
    ],
    "EUROPE": [
        (-10, 36), (-10, 43), (-4, 44), (-1, 48), (-5, 49),
        (1, 51), (6, 54), (9, 55), (8, 58), (5, 59),
        (5, 63), (10, 68), (19, 71), (26, 70), (30, 66),
        (25, 60), (22, 57), (28, 59), (36, 62), (44, 62),
        (48, 54), (42, 48), (37, 46), (30, 45), (28, 41),
        (24, 40), (24, 37), (21, 37), (19, 41), (16, 44),
        (18, 40), (15, 38), (12, 43), (7, 44), (0, 39),
    ],
    "AFRICA": [
        (-17, 28), (-13, 32), (-7, 35), (0, 36), (7, 37),
        (11, 34), (18, 32), (25, 32), (32, 31), (34, 27),
        (36, 22), (40, 16), (44, 12), (51, 12), (48, 7),
        (43, 1), (41, -7), (40, -13), (36, -19), (35, -25),
        (30, -30), (25, -34), (19, -35), (16, -29), (13, -23),
        (12, -15), (9, -5), (9, 3), (2, 5), (-7, 5),
        (-15, 11), (-17, 20),
    ],
    "ASIA": [
        (44, 62), (54, 69), (76, 73), (100, 77), (122, 73),
        (143, 72), (164, 66), (178, 66), (170, 58), (158, 51),
        (150, 59), (141, 53), (135, 44), (128, 40), (129, 35),
        (122, 39), (121, 30), (113, 22), (108, 21), (110, 12),
        (104, 1), (99, 8), (97, 17), (90, 22), (82, 16),
        (78, 7), (73, 17), (68, 25), (60, 25), (53, 16),
        (44, 13), (35, 30), (35, 37), (44, 42), (48, 54),
    ],
    "AUSTRALIA": [
        (113, -22), (114, -19), (119, -17), (123, -16), (126, -14),
        (129, -15), (130, -12), (133, -12), (136, -13), (137, -16),
        (140, -17), (142, -11), (144, -14), (145, -19), (149, -22),
        (151, -25), (153, -28), (153, -31), (150, -35), (147, -38),
        (143, -39), (140, -37), (137, -35), (134, -33), (130, -32),
        (126, -33), (122, -34), (117, -35), (114, -31), (113, -26),
    ],
}


def project(longitude, latitude):
    return round(40 + (longitude + 180) * 440 / 360), round(420 + (80 - latitude) * 1.37)


def boxes_overlap(first, second):
    return (first[0] < second[2] and second[0] < first[2]
            and first[1] < second[3] and second[1] < first[3])


def draw_world_map(canvas):
    draw_frame(canvas, 20, 380, 480, 268, INK, 2)
    fill_rect(canvas, 22, 382, 476, 27, INK)
    draw_text(canvas, 30, 388, "THE DAY ON THE MAP", 2, WHITE)
    for y in range(420, 646, 18):
        draw_line(canvas, 23, y, 496, y, LIGHT_GREY)

    for coastline in CONTINENTS.values():
        assert 25 <= len(coastline) <= 35
        fill_polygon(canvas, [project(*point) for point in coastline])
    islands = (
        [(-53, 60), (-44, 61), (-30, 70), (-24, 79), (-40, 83),
         (-56, 80), (-62, 72)],
        [(-8, 50), (-5, 55), (-6, 59), (-2, 58), (1, 52)],
        [(-10, 51), (-10, 55), (-7, 55), (-6, 52)],
        [(-84, 22), (-79, 23), (-74, 20), (-79, 20)],
        [(-74, 20), (-69, 20), (-68, 18), (-73, 18)],
        [(130, 32), (134, 34), (138, 37), (142, 42), (145, 44),
         (144, 39), (140, 35), (135, 33)],
        [(120, 19), (123, 17), (122, 14), (126, 9), (124, 6),
         (121, 10), (119, 12)],
        [(96, 5), (101, 1), (106, -6), (103, -5)],
        [(108, -7), (114, -7), (118, -9), (112, -9)],
        [(109, 6), (118, 7), (118, 0), (112, -3), (109, 1)],
        [(132, -3), (141, -3), (150, -7), (145, -9), (137, -7)],
        [(47, -13), (50, -16), (47, -25), (44, -24)],
        [(145, -41), (149, -41), (148, -44), (145, -43)],
        [(173, -35), (177, -38), (174, -41), (171, -43), (168, -46),
         (166, -45), (170, -41)],
    )
    for island in islands:
        fill_polygon(canvas, [project(*point) for point in island])

    # Location, geographic point, and carefully reserved label origin.
    markers = (
        (1, "KERCH", 36.5, 45.4, 315, 451),
        (2, "BAHRAIN", 50.5, 26.0, 335, 487),
        (3, "MANILA", 121.0, 14.6, 430, 530),
        (4, "SHENZHEN", 114.0, 22.5, 410, 476),
        (5, "ANTALYA", 30.7, 36.9, 257, 500),
        (6, "GENEVA", 6.1, 46.2, 235, 444),
        (7, "DR CONGO", 23.7, -3.0, 305, 550),
        (8, "PORT-AU-PRINCE", -72.3, 18.5, 104, 520),
        (9, "ANCHORAGE", -149.9, 61.2, 49, 422),
        (10, "NEW YORK", -74.0, 40.7, 185, 464),
    )
    label_boxes, marker_boxes = [], []
    for number, label, longitude, latitude, lx, ly in markers:
        mx, my = project(longitude, latitude)
        radius = 8 if number == 10 else 6
        box = (lx - 2, ly - 2, lx + text_width(label, 1) + 2, ly + 9)
        assert 23 <= box[0] < box[2] <= 497 and 411 <= box[1] < box[3] <= 645
        label_boxes.append(box)
        marker_boxes.append((mx - radius, my - radius, mx + radius + 1, my + radius + 1))
    for index, box in enumerate(label_boxes):
        assert not any(boxes_overlap(box, other) for other in label_boxes[index + 1:])
        assert not any(boxes_overlap(box, other) for other in marker_boxes)
    for index, first in enumerate(markers):
        ax, ay = project(first[2], first[3])
        first_radius = 8 if first[0] == 10 else 6
        for second in markers[index + 1:]:
            bx, by = project(second[2], second[3])
            second_radius = 8 if second[0] == 10 else 6
            assert math.hypot(ax - bx, ay - by) > first_radius + second_radius + 1

    manila, shenzhen, anchorage = project(121, 14.6), project(114, 22.5), project(-149.9, 61.2)
    dotted_route(canvas, [(428, 533), (419, 522), manila, shenzhen, (406, 486), (416, 483)])
    dotted_route(canvas, [shenzhen, (384, 457), (350, 432), (300, 422),
                          (240, 422), (190, 426), (146, 433), (111, 441),
                          anchorage, (78, 431)])

    # Leaders sit below the paper backplates; no route crosses a letter.
    for number, label, longitude, latitude, lx, ly in markers:
        mx, my = project(longitude, latitude)
        end_x = max(lx, min(mx, lx + text_width(label, 1) - 1))
        end_y = ly + (7 if my > ly else 0)
        draw_line(canvas, mx, my, end_x, end_y, GREY)
    for marker, box in zip(markers, label_boxes):
        number, label, longitude, latitude, lx, ly = marker
        fill_rect(canvas, box[0], box[1], box[2] - box[0], box[3] - box[1], PAPER)
        draw_text(canvas, lx, ly, label, 1, INK)
    for number, label, longitude, latitude, lx, ly in markers:
        mx, my = project(longitude, latitude)
        fill_circle(canvas, mx, my, 8 if number == 10 else 6, RED)
        draw_text(canvas, mx - text_width(str(number), 1) // 2, my - 3, str(number), 1, WHITE)

    draw_line(canvas, 33, 613, 486, 613, MID_GREY)
    dotted_route(canvas, [(35, 627), (62, 627)])
    draw_text(canvas, 71, 624, "MANILA / SHENZHEN / ANCHORAGE", 1, GREY)


def draw_bridge(canvas):
    # Engraved sky and quiet shoreline, all inside the first picture frame.
    for y in range(430, 451, 5):
        for x in range(534 + (y % 3) * 3, 667, 23):
            draw_line(canvas, x, y, min(x + 12, 669), y, LIGHT_GREY)
    draw_polyline(canvas, [(531, 520), (544, 517), (559, 519), (575, 516),
                           (592, 521), (628, 519), (647, 516), (670, 519)], MID_GREY)
    # Mirror the towers and the broken deck in compressed, rippled water.
    reflection = [(535, 490), (587, 490), (603, 503), (616, 505), (628, 489), (665, 489)]
    reflected = [(x, 529 + (526 - y) // 2) for x, y in reflection]
    draw_polyline(canvas, reflected, MID_GREY)
    for x in (535, 587, 665):
        draw_line(canvas, x, 530, x + 2, 551, MID_GREY)
        draw_line(canvas, x - 2, 538, x + 4, 538, LIGHT_GREY)
    for y in range(529, 560, 5):
        for x in range(531 + (y % 4) * 2, 669, 27):
            draw_line(canvas, x, y, min(x + 18, 671), y, LIGHT_GREY)

    left_arch = [(535, 486), (547, 469), (560, 458), (576, 454), (587, 462), (596, 487)]
    right_arch = [(626, 488), (634, 473), (648, 460), (657, 468), (665, 486)]
    draw_polyline(canvas, left_arch, INK, 2)
    draw_polyline(canvas, right_arch, INK, 2)
    for x, top in ((535, 486), (587, 462), (665, 486)):
        draw_line(canvas, x, top, x, 526, INK, 2)
        draw_line(canvas, x - 3, 526, x + 3, 526, INK)
    draw_line(canvas, 535, 486, 596, 487, INK, 2)
    draw_line(canvas, 535, 493, 596, 494, INK)
    draw_line(canvas, 626, 488, 665, 486, INK, 2)
    draw_line(canvas, 626, 495, 665, 493, INK)
    # Closely spaced deck trusses and vertical arch hangers.
    for start, stop, top in ((536, 590, 486), (628, 658, 487)):
        for x in range(start, stop, 9):
            draw_polyline(canvas, [(x, top + 1), (x + 4, top + 7), (x + 8, top + 1)], GREY)
    for x, top in ((547, 469), (560, 458), (576, 454), (587, 462), (634, 473), (648, 460), (657, 468)):
        draw_line(canvas, x, top, x, 486, GREY)
    draw_polyline(canvas, [(596, 487), (605, 500), (616, 504), (626, 488)], INK, 2)
    draw_polyline(canvas, [(597, 493), (606, 505), (615, 509), (625, 495)], GREY)
    for x, y in ((606, 537), (621, 546), (642, 535)):
        draw_line(canvas, x, y, x + 7, y - 3, GREY, 2)
    fill_polygon(canvas, [(605, 485), (609, 474), (613, 481), (617, 476), (616, 487)], RED, RED)
    draw_polyline(canvas, [(611, 474), (607, 468), (612, 462), (608, 456)], GREY, 2)


def draw_drone(canvas, cx, cy, size):
    points = [(cx - size, cy), (cx + size, cy - size // 2),
              (cx + size // 3, cy + size // 3), (cx, cy + size),
              (cx - size // 3, cy + size // 3), (cx - size - 3, cy + 3)]
    fill_polygon(canvas, points, INK, INK)
    draw_line(canvas, cx - size // 2, cy + 1, cx + size // 2, cy - size // 5, WHITE)


def draw_drone_scene(canvas):
    for y in range(432, 555, 13):
        draw_line(canvas, 691, y, 826, y, PALE_GREY)
    for x in range(698, 829, 22):
        draw_line(canvas, x, 427, x, 555, PALE_GREY)
    draw_drone(canvas, 733, 452, 15)
    draw_drone(canvas, 802, 443, 8)
    dotted_route(canvas, [(702, 500), (712, 485), (730, 477), (752, 472), (776, 469)], GREY, 6)
    # A target reticle surrounds open sky below the smaller drone.
    draw_ellipse(canvas, 802, 478, 12, 12, RED)
    draw_ellipse(canvas, 802, 478, 5, 5, MID_GREY)
    for x0, y0, x1, y1 in ((785, 478, 795, 478), (809, 478, 819, 478),
                             (802, 461, 802, 471), (802, 485, 802, 495)):
        draw_line(canvas, x0, y0, x1, y1, RED)
    for rx, ry, colour in ((41, 20, LIGHT_GREY), (29, 14, MID_GREY), (17, 8, GREY)):
        draw_ellipse(canvas, 779, 526, rx, ry, colour)
    draw_line(canvas, 779, 526, 807, 513, RED)
    draw_line(canvas, 779, 526, 779, 547, INK, 2)
    draw_line(canvas, 769, 548, 789, 548, INK, 2)
    draw_line(canvas, 766, 551, 792, 551, GREY)
    for x, height in ((696, 13), (707, 21), (718, 9), (728, 16)):
        fill_rect(canvas, x, 555 - height, 7, height, MID_GREY)
        draw_line(canvas, x + 2, 555 - height - 4, x + 2, 555 - height, GREY)


def draw_chart(canvas):
    left, top, right, bottom = 859, 449, 981, 542
    draw_text(canvas, 853, 428, "S&P 500", 1, INK)
    value = "-1.1%"
    draw_text(canvas, right - text_width(value, 1), 442, value, 1, RED)
    stock_points = [(863, 459), (873, 464), (883, 461), (894, 475),
                    (905, 472), (916, 486), (927, 482), (938, 499),
                    (949, 495), (960, 515), (970, 521), (979, 535)]
    fill_polygon(canvas, stock_points + [(979, bottom - 1), (863, bottom - 1)], LIGHT_GREY, None)
    for y in (458, 479, 500, 521):
        draw_line(canvas, left + 1, y, right, y, MID_GREY)
        draw_line(canvas, left - 3, y, left, y, GREY)
    for x in (879, 899, 919, 939, 959, 979):
        draw_line(canvas, x, top + 4, x, bottom - 1, PALE_GREY)
        draw_line(canvas, x, bottom, x, bottom - 3, INK)
    draw_line(canvas, left, top, left, bottom, INK)
    draw_line(canvas, left, bottom, right, bottom, INK)
    draw_text(canvas, 859, 549, "OPEN", 1, GREY)
    draw_text(canvas, right - text_width("CLOSE", 1), 549, "CLOSE", 1, GREY)
    draw_polyline(canvas, stock_points, RED, 2)
    fill_circle(canvas, 979, 535, 2, RED)


def draw_day_in_pictures(canvas):
    draw_frame(canvas, 516, 380, 488, 268, INK, 2)
    fill_rect(canvas, 518, 382, 484, 27, INK)
    draw_text(canvas, 526, 388, "THE DAY IN PICTURES", 2, WHITE)
    frames = ((526, 419), (684, 419), (842, 419))
    for x, y in frames:
        draw_frame(canvas, x, y, 150, 143)
    # Local raster surfaces make panel containment an executable invariant.
    for (x, y), painter in zip(frames, (draw_bridge, draw_drone_scene, draw_chart)):
        layer = [bytearray(row) for row in canvas]
        painter(layer)
        for row in range(HEIGHT):
            if y < row < y + 142:
                assert layer[row][:3 * (x + 1)] == canvas[row][:3 * (x + 1)]
                assert layer[row][3 * (x + 149):] == canvas[row][3 * (x + 149):]
            else:
                assert layer[row] == canvas[row]
        for row in range(y + 1, y + 142):
            canvas[row][3 * (x + 1):3 * (x + 149)] = layer[row][3 * (x + 1):3 * (x + 149)]
    captions = (
        "KERCH BRIDGE HIT, TRAFFIC HALTED",
        "IRAN DRONES ON US RADAR",
        "AI STOCKS SLIDE AGAIN",
    )
    for (x, y), caption in zip(frames, captions):
        lines = wrap(caption, 144, 1)
        assert len(lines) <= 2 and " ".join(lines) == caption
        for index, line in enumerate(lines):
            draw_text(canvas, x + 3, 568 + index * 10, line, 1, INK)


def draw_lower_panels(canvas):
    source = [bytearray(row) for row in canvas]
    paper_row = bytes(PAPER) * WIDTH
    for y in range(388, 432):
        source[y] = bytearray(paper_row)
    draw_world_map(source)
    draw_day_in_pictures(source)
    source_top, source_height = 380, 268
    target_top, target_height = 432, 216
    for y in range(target_height):
        # Include both outer rules when fitting the complete panels to the band.
        source_y = source_top + round(y * (source_height - 1) / (target_height - 1))
        canvas[target_top + y][20 * 3:1004 * 3] = source[source_y][20 * 3:1004 * 3]


def draw_brief_columns(canvas):
    columns = (
        ("EUROPE", (
            "KERCH BRIDGE HIT BY DRONES AND MISSILES",
            "ZELENSKY HAILS 'UNPRECEDENTED' RAID",
            "RUSSIA REPORTS RECORD DRONE KILLS",
            "MOSCOW ADMITS BRIDGE DAMAGED",
            "UN: 2026 UKRAINE CIVILIAN TOLL WORST YET",
            "FIVE EU STATES PLAN RWANDA RETURN HUB",
            "COP31 IN ANTALYA ENTERS FINAL DAYS",
            "ROCKSTROM WARNS ON CLIMATE TIPPING POINTS",
            "FOUR NATIONS PLEDGE $200M TO GREEN FUNDS",
            "KYIV AND ALLIES MEET ON INTERCEPTORS",
        )),
        ("MIDDLE EAST AND AFRICA", (
            "IRAN DRONES HIT US RADAR IN BAHRAIN",
            "MANAMA INTERCEPTS THIRD RAID IN DAYS",
            "ROOSEVELT CARRIER GROUP REACHES GULF",
            "US FIRES AT IRANIAN TARGETS AT SEA",
            "EBOLA CASES DOUBLE IN DR CONGO",
            "11,000 CASES AND 5,400 DEATHS",
            "OUTBREAK NOW IN 67 HEALTH ZONES",
            "WHO CHIEF WARNS OF WIDER SPREAD",
            "HAITI GANGS COMMIT 'ATROCIOUS ABUSES'",
            "UN URGES CIVILIAN PROTECTION",
        )),
        ("ASIA-PACIFIC", (
            "TRUMP ARRIVES IN MANILA FOR TRADE TALKS",
            "THREE-WAY NUCLEAR TALKS SET IN CHINA",
            "XI AND PUTIN TO JOIN TRUMP IN SHENZHEN",
            "TRUMP HINTS AT MEETING KIM JONG UN",
            "CHINA BACKS UNCLOS SEA CODE",
            "QUAD ADDS NAVAL DRILL AND CABLE PACT",
            "INDIA BUS CRASH KILLS NINE",
            "AUSTRALIA SANCTIONS THREE SETTLERS",
            "JAPAN PM FACES CHINA RIFT",
            "UN WARNS SOUTH SUDAN OVER POLLS",
        )),
        ("AMERICAS AND THE WORLD", (
            "US LOSES ITS MEASLES-FREE STATUS",
            "MEXICO AND BOLIVIA ALSO STRIPPED",
            "PAHO WARNS OF 30-YEAR HIGH",
            "PELTOLA WINS ALASKA SENATE RACE",
            "FEMA RUNS EMERGENCY ALERT TEST",
            "DOW FALLS 779 POINTS",
            "S&P 500 DOWN 1.1 PCT",
            "NASDAQ DOWN 1.5 PCT",
            "NVIDIA SHARES SWING WILDLY AGAIN",
            "TIGER WOODS TO RETURN IN BAHAMAS",
        )),
    )
    width = 228
    for column, (label, briefs) in enumerate(columns):
        x = LEFT + column * (width + 20)
        assert len(label) * 5 - 1 <= width - 10
        fill_rect(canvas, x, 660, width, 22, INK)
        draw_condensed_text(canvas, x + 5, 664, label, WHITE)
        y = 689
        for headline in briefs:
            lines = wrap_condensed(headline, width - 8)
            assert len(lines) <= 2 and " ".join(lines) == headline
            for line in lines:
                assert len(line) * 5 - 1 <= width - 8 and y + 14 <= 925
                draw_condensed_text(canvas, x + 4, y, line, INK)
                y += 14
            y += 8


def png_chunk(kind, data):
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xffffffff)


def write_png(path, canvas):
    raw = bytearray()
    for row in canvas:
        raw.append(0)
        raw.extend(row)
    ihdr = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr)
           + png_chunk(b"IDAT", zlib.compress(bytes(raw), 1)) + png_chunk(b"IEND", b""))
    assert 50000 <= len(png) <= 1048576, len(png)
    with open(path, "wb") as output:
        output.write(png)


def main():
    canvas = [bytearray(bytes(PAPER) * WIDTH) for _ in range(HEIGHT)]
    fitted_centered_text(canvas, 18, "THE WORLD", 12, INK)
    draw_rule(canvas, LEFT, 104, RIGHT - LEFT, 3)
    draw_rule(canvas, LEFT, 110, RIGHT - LEFT)

    fitted_centered_text(canvas, 117, "TUESDAY 17 NOVEMBER 2026", 3, INK)
    draw_text(canvas, 32, 125, "VOL. XI  No. 323", 1, INK)
    right = "ONE PAGE OF THE DAY'S NEWS"
    draw_text(canvas, RIGHT - 12 - text_width(right, 1), 125, right, 1, INK)

    panels = (
        ("KERCH BRIDGE STRUCK BY DRONES AND MISSILES IN UNPRECEDENTED RAID",
         "Zelensky hails a masterstroke after weeks wearing down Russian air defences; Moscow admits damage.", 2),
        ("IRAN DRONES HIT US RADAR IN BAHRAIN, THIRD ATTACK IN DAYS",
         "Manama says its defences intercepted the raid as the Roosevelt carrier group arrives.", 1),
        ("TRUMP IN MANILA: TRADE DEALS, THEN THREE-WAY TALKS WITH XI AND PUTIN",
         "Historic nuclear summit planned in China; the US leader hints he may also meet Kim Jong Un.", 2),
    )
    y = 150
    for expected_top, (headline, dek, dek_scale) in zip((150, 238, 312), panels):
        assert y == expected_top
        height = draw_lead_panel(canvas, y, headline, dek, dek_scale)
        y += height + 8
    assert y - 8 == 392

    fill_rect(canvas, LEFT, 396, RIGHT - LEFT, 32, INK)
    strip = "S&P 500 -1.1%  DOW -779  NASDAQ -1.5%  NVIDIA SWINGS  OIL UP"
    assert text_width(strip, 2) <= RIGHT - LEFT - 40
    fitted_centered_text(canvas, 403, strip, 2, WHITE)

    draw_lower_panels(canvas)
    draw_brief_columns(canvas)
    draw_rule(canvas, LEFT, 928, RIGHT - LEFT)
    footer = "COMPILED FROM WIRE REPORTS OF TUESDAY 17 NOVEMBER 2026 - DRAWN BY A PROGRAM - MAKE.FUN"
    fitted_centered_text(canvas, 958, footer, 1, INK)

    # Resolve relative output paths from the repository directory.
    repository = os.path.dirname(os.path.realpath(__file__))
    requested = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if requested is None:
        output_dir = os.path.join(repository, "out")
    elif os.path.isabs(requested):
        output_dir = requested
    else:
        output_dir = os.path.join(repository, requested)
    output_path = os.path.join(output_dir, "entry.png")
    os.makedirs(output_dir, exist_ok=True)
    write_png(output_path, canvas)
    print("wrote entry.png")


if __name__ == "__main__":
    main()
