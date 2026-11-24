#!/usr/bin/env python3
"""Draw one newspaper front page summing up Tuesday 24 November 2026.

Stdlib only, no network. Writes a 1024x1024 PNG to $MAKEFUN_OUTPUT_DIR
(or /output) as entry.png. Every run writes identical bytes: the picture is
drawn from fixed data with a hand-made 5x7 bitmap font and a hand-rolled
PNG encoder, so there is no clock, no randomness and no file input.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font ----
# A 5x7 bitmap font, one glyph per line: seven rows of five bits, rows
# joined with "/". Only the characters the page needs are defined.
FONT = {
    "A": "01110/10001/10001/11111/10001/10001/10001",
    "B": "11110/10001/10001/11110/10001/10001/11110",
    "C": "01110/10001/10000/10000/10000/10001/01110",
    "D": "11110/10001/10001/10001/10001/10001/11110",
    "E": "11111/10000/10000/11110/10000/10000/11111",
    "F": "11111/10000/10000/11110/10000/10000/10000",
    "G": "01110/10001/10000/10111/10001/10001/01111",
    "H": "10001/10001/10001/11111/10001/10001/10001",
    "I": "01110/00100/00100/00100/00100/00100/01110",
    "J": "00111/00010/00010/00010/00010/10010/01100",
    "K": "10001/10010/10100/11000/10100/10010/10001",
    "L": "10000/10000/10000/10000/10000/10000/11111",
    "M": "10001/11011/10101/10101/10001/10001/10001",
    "N": "10001/11001/10101/10011/10001/10001/10001",
    "O": "01110/10001/10001/10001/10001/10001/01110",
    "P": "11110/10001/10001/11110/10000/10000/10000",
    "Q": "01110/10001/10001/10001/10101/10010/01101",
    "R": "11110/10001/10001/11110/10100/10010/10001",
    "S": "01111/10000/10000/01110/00001/00001/11110",
    "T": "11111/00100/00100/00100/00100/00100/00100",
    "U": "10001/10001/10001/10001/10001/10001/01110",
    "V": "10001/10001/10001/10001/10001/01010/00100",
    "W": "10001/10001/10001/10101/10101/11011/10001",
    "X": "10001/10001/01010/00100/01010/10001/10001",
    "Y": "10001/10001/01010/00100/00100/00100/00100",
    "Z": "11111/00001/00010/00100/01000/10000/11111",
    "a": "00000/00000/01110/00001/01111/10001/01111",
    "b": "10000/10000/10000/11110/10001/10001/11110",
    "c": "00000/00000/01110/10001/10000/10001/01110",
    "d": "00001/00001/00001/01111/10001/10001/01111",
    "e": "00000/00000/01110/10001/11111/10000/01110",
    "f": "00110/01001/01000/11110/01000/01000/01000",
    "g": "00000/01111/10001/10001/01111/00001/01110",
    "h": "10000/10000/10000/11110/10001/10001/10001",
    "i": "00100/00000/01100/00100/00100/00100/01110",
    "j": "00010/00000/00110/00010/00010/10010/01100",
    "k": "10000/10000/10010/10100/11000/10100/10010",
    "l": "01100/00100/00100/00100/00100/00100/01110",
    "m": "00000/00000/11010/10101/10101/10101/10101",
    "n": "00000/00000/11110/10001/10001/10001/10001",
    "o": "00000/00000/01110/10001/10001/10001/01110",
    "p": "00000/11110/10001/10001/11110/10000/10000",
    "q": "00000/01111/10001/10001/01111/00001/00001",
    "r": "00000/00000/10110/11001/10000/10000/10000",
    "s": "00000/00000/01111/10000/01110/00001/11110",
    "t": "00100/00100/11111/00100/00100/00100/00011",
    "u": "00000/00000/10001/10001/10001/10011/01101",
    "v": "00000/00000/10001/10001/10001/01010/00100",
    "w": "00000/00000/10001/10001/10101/10101/01010",
    "x": "00000/00000/10001/01010/00100/01010/10001",
    "y": "00000/00000/10001/10001/01111/00001/01110",
    "z": "00000/00000/11111/00010/00100/01000/11111",
    "0": "01110/10001/10011/10101/11001/10001/01110",
    "1": "00100/01100/00100/00100/00100/00100/01110",
    "2": "01110/10001/00001/00110/01000/10000/11111",
    "3": "11110/00001/00001/01110/00001/00001/11110",
    "4": "00010/00110/01010/10010/11111/00010/00010",
    "5": "11111/10000/11110/00001/00001/10001/01110",
    "6": "00110/01000/10000/11110/10001/10001/01110",
    "7": "11111/00001/00010/00100/01000/01000/01000",
    "8": "01110/10001/10001/01110/10001/10001/01110",
    "9": "01110/10001/10001/01111/00001/00010/01100",
    " ": "00000/00000/00000/00000/00000/00000/00000",
    ".": "00000/00000/00000/00000/00000/01100/01100",
    ",": "00000/00000/00000/00000/01100/00100/01000",
    ":": "00000/01100/01100/00000/01100/01100/00000",
    ";": "00000/01100/01100/00000/01100/00100/01000",
    "'": "00100/00100/01000/00000/00000/00000/00000",
    "-": "00000/00000/00000/01110/00000/00000/00000",
    "/": "00001/00010/00010/00100/01000/01000/10000",
    "(": "00010/00100/01000/01000/01000/00100/00010",
    ")": "01000/00100/00010/00010/00010/00100/01000",
    "$": "00100/01111/10100/01110/00101/11110/00100",
    "%": "11001/11010/00010/00100/01000/01011/10011",
    "+": "00000/00100/00100/11111/00100/00100/00000",
    "&": "01100/10010/10100/01000/10101/10010/01101",
    "!": "00100/00100/00100/00100/00100/00000/00100",
    "?": "01110/10001/00001/00110/00100/00000/00100",
    '"': "01010/01010/00000/00000/00000/00000/00000",
    "=": "00000/00000/11111/00000/11111/00000/00000",
    "*": "00000/10101/01110/10101/00000/00000/00000",
    "_": "00000/00000/00000/00000/00000/00000/11111",
}


def text_width(text, scale):
    """Pixel width of text at the given scale (6 px per glyph, 1 px gap)."""
    return len(text) * 6 * scale - scale


def wrap_text(text, scale, max_px):
    """Greedy word wrap; returns a list of lines that fit in max_px."""
    limit = max(1, max_px // (6 * scale))
    words = text.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if len(trial) <= limit:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            # A single over-long word is hard-split.
            while len(word) > limit:
                lines.append(word[:limit])
                word = word[limit:]
            cur = word
    if cur:
        lines.append(cur)
    return lines


# -------------------------------------------------------------- canvas ----
class Canvas:
    """An RGB canvas with a few drawing primitives."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def put(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = color

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.put(xx, yy, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err, x, y = dx - dy, x0, y0
        half = thick // 2
        while True:
            for ty in range(y - half, y + half + 1):
                for tx in range(x - half, x + half + 1):
                    self.put(tx, ty, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.put(xx, yy, color)

    def ring(self, cx, cy, r, color, thick=2):
        for yy in range(cy - r - thick, cy + r + thick + 1):
            for xx in range(cx - r - thick, cx + r + thick + 1):
                d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                if r - thick / 2 <= d <= r + thick / 2:
                    self.put(xx, yy, color)

    def ellipse(self, cx, cy, rx, ry, color, thick=2):
        for deg in range(0, 360):
            import math
            a = math.radians(deg)
            x = int(cx + rx * math.cos(a))
            y = int(cy + ry * math.sin(a))
            for ty in range(y - thick // 2, y + thick // 2 + 1):
                for tx in range(x - thick // 2, x + thick // 2 + 1):
                    self.put(tx, ty, color)

    def poly(self, points, color):
        """Fill a simple polygon by scanlines."""
        ys = [p[1] for p in points]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for x in range(int(xs[k]), int(xs[k + 1]) + 1):
                    self.put(x, y, color)

    def glyph(self, ch, x, y, scale, color):
        rows = FONT.get(ch)
        if rows is None:
            rows = FONT["?"]
        for ry, row in enumerate(rows.split("/")):
            for rx, bit in enumerate(row):
                if bit == "1":
                    self.rect(x + rx * scale, y + ry * scale,
                              scale, scale, color)

    def text(self, s, x, y, scale, color):
        for ch in s:
            self.glyph(ch, x, y, scale, color)
            x += 6 * scale
        return x

    def text_center(self, s, cx, y, scale, color):
        self.text(s, cx - text_width(s, scale) // 2, y, scale, color)

    def block(self, lines, x, y, scale, color, leading=3):
        for line in lines:
            self.text(line, x, y, scale, color)
            y += 7 * scale + leading
        return y


# ------------------------------------------------------------------ png ----
def png_bytes(canvas):
    """Encode the canvas as PNG bytes (fixed filter 0, level 9)."""
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    header = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


# ------------------------------------------------------------ pictograms ----
# Each draws a small scene inside a 116x116 box at (x, y) in one accent.

def pic_chip(c, x, y, col):
    c.rect(x + 28, y + 28, 60, 60, col)
    c.rect(x + 42, y + 42, 32, 32, (247, 242, 231))
    c.rect(x + 52, y + 52, 12, 12, col)
    for i in range(4):
        px = x + 34 + i * 15
        c.rect(px, y + 14, 6, 14, col)
        c.rect(px, y + 88, 6, 14, col)
        c.rect(x + 14, y + 34 + i * 15, 14, 6, col)
        c.rect(x + 88, y + 34 + i * 15, 14, 6, col)
    c.line(x + 84, y + 34, x + 104, y + 14, col, 4)
    c.line(x + 104, y + 14, x + 92, y + 14, col, 4)
    c.line(x + 104, y + 14, x + 104, y + 26, col, 4)


def pic_shield(c, x, y, col):
    pts = [(x + 58, y + 12), (x + 96, y + 26), (x + 96, y + 60),
           (x + 58, y + 104), (x + 20, y + 60), (x + 20, y + 26)]
    c.poly(pts, col)
    c.poly([(x + 58, y + 22), (x + 86, y + 32), (x + 86, y + 58),
            (x + 58, y + 92), (x + 30, y + 58), (x + 30, y + 32)],
           (247, 242, 231))
    c.line(x + 40, y + 58, x + 54, y + 74, (179, 32, 44), 5)
    c.line(x + 54, y + 74, x + 80, y + 40, (179, 32, 44), 5)


def pic_drone(c, x, y, col):
    c.rect(x + 44, y + 50, 28, 16, col)
    c.disc(x + 58, y + 58, 6, (247, 242, 231))
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        ax, ay = x + 58 + dx * 26, y + 58 + dy * 26
        c.line(x + 58, y + 58, ax, ay, col, 4)
        c.ring(ax, ay, 12, col, 3)
        c.line(ax - 12, ay, ax + 12, ay, col, 3)
    c.disc(x + 58, y + 58, 3, col)


def pic_flats(c, x, y, col):
    c.rect(x + 22, y + 30, 72, 76, col)
    for row in range(3):
        for cnum in range(3):
            wx = x + 32 + cnum * 22
            wy = y + 40 + row * 24
            c.rect(wx, wy, 12, 12, (247, 242, 231))
    c.line(x + 58, y + 30, x + 50, y + 52, (247, 242, 231), 3)
    c.line(x + 50, y + 52, x + 62, y + 70, (247, 242, 231), 3)
    c.line(x + 62, y + 70, x + 54, y + 90, (247, 242, 231), 3)
    for bx, by in ((x + 14, y + 14), (x + 96, y + 20), (x + 100, y + 88)):
        c.line(bx - 8, by, bx + 8, by, col, 3)
        c.line(bx, by - 8, bx, by + 8, col, 3)


def pic_satellite(c, x, y, col):
    c.rect(x + 46, y + 48, 24, 20, col)
    c.disc(x + 58, y + 58, 5, (247, 242, 231))
    for sx in (x + 8, x + 74):
        c.rect(sx, y + 50, 28, 16, col)
        c.line(sx + 7, y + 50, sx + 7, y + 66, (247, 242, 231), 2)
        c.line(sx + 14, y + 50, sx + 14, y + 66, (247, 242, 231), 2)
        c.line(sx + 21, y + 50, sx + 21, y + 66, (247, 242, 231), 2)
    c.line(x + 46, y + 58, x + 36, y + 58, col, 3)
    c.line(x + 70, y + 58, x + 74, y + 58, col, 3)
    c.ellipse(x + 58, y + 58, 52, 20, col, 2)
    c.disc(x + 102, y + 44, 4, col)


def pic_spy(c, x, y, col):
    c.rect(x + 24, y + 22, 52, 72, col)
    for i in range(4):
        c.rect(x + 32, y + 34 + i * 14, 36, 5, (247, 242, 231))
    c.ring(x + 74, y + 66, 22, col, 6)
    c.line(x + 90, y + 82, x + 106, y + 98, col, 6)
    c.disc(x + 74, y + 66, 4, col)


PICS = [pic_chip, pic_shield, pic_drone, pic_flats, pic_satellite, pic_spy]

# -------------------------------------------------------------- stories ----
# Six verified stories of the 24 November 2026 news cycle, each with the
# wire service that reported it. All were reported on 24 November in at
# least one time zone; the first two were announced late on 23 November
# US time and led every 24 November edition worldwide.
STORIES = [
    ("LEAD STORY - TECH, USA", "HUANG IS BACK AT NVIDIA",
     "Board reinstates Jensen Huang as CEO after Trump stepped in; "
     "shares jump 31% and the Nasdaq soars.",
     "REUTERS", (29, 78, 137)),
    ("BUSINESS - CYBER", "CROWDSTRIKE BUYS ZSCALER",
     "$43.9bn all-stock deal, the biggest cyber takeover ever, "
     "unites two security giants.",
     "REUTERS", (179, 32, 44)),
    ("AMERICAS - MEXICO", "US DRONE HELPED NAB CARTEL BOSS",
     "Mexico captures FBI most-wanted 'El Chapo Isidro' in Sinaloa; "
     "20 die in gun battles.",
     "AP", (0, 110, 80)),
    ("WAR - UKRAINE", "14 KILLED IN KYIV REGION STRIKES",
     "Russian missiles hit flats and a shop near Kyiv; Zelenskyy "
     "pleads for Patriot missiles.",
     "AFP", (120, 60, 20)),
    ("SECURITY - SPACE", "NATO VOWS TO DEFEND SPACE",
     "Allies warn Russia may launch a nuclear-armed satellite "
     "within weeks, Berlin media say.",
     "REUTERS", (90, 40, 120)),
    ("ASIA - CHINA", "CHINA DEATH SENTENCE FOR SPYING",
     "Official 'Ma' condemned for leaking 35 state secrets to a "
     "foreign agency for $150,000.",
     "REUTERS", (150, 100, 0)),
]

PAPER = (247, 242, 231)
INK = (17, 17, 17)
GREY = (110, 104, 90)
RULE = (17, 17, 17)
CELL_BG = (255, 253, 247)


def draw_page():
    c = Canvas(W, H, PAPER)
    # Masthead.
    c.text_center("THE WORLD TODAY", W // 2, 26, 6, INK)
    c.rect(24, 84, W - 48, 4, INK)
    c.rect(24, 92, W - 48, 2, INK)
    c.text_center("TUESDAY 24 NOVEMBER 2026", W // 2, 106, 3, (179, 32, 44))
    c.text_center("SIX STORIES THAT SHAPED THE DAY - FROM EVERY CORNER "
                  "OF THE GLOBE", W // 2, 136, 2, GREY)
    c.rect(24, 164, W - 48, 2, INK)

    # Grid: 2 columns x 3 rows.
    margin, gap = 24, 16
    cell_w = (W - 2 * margin - gap) // 2
    cell_h = 258
    top = 180
    for idx, (kicker, headline, summary, source, accent) in enumerate(STORIES):
        col, row = idx % 2, idx // 2
        x = margin + col * (cell_w + gap)
        y = top + row * (cell_h + gap)
        c.rect(x, y, cell_w, cell_h, CELL_BG)
        c.rect(x, y, cell_w, 2, accent)
        c.rect(x, y, cell_w, 30, accent)
        c.text(kicker, x + 12, y + 8, 2, (255, 255, 255))
        # Pictogram on a tinted square, headline beside it.
        px, py = x + 14, y + 44
        c.rect(px, py, 116, 116, PAPER)
        c.rect(px, py, 116, 116, accent)  # frame painted over below
        c.rect(px + 3, py + 3, 110, 110, PAPER)
        PICS[idx](c, px, py, accent)
        hx = px + 130
        hw = cell_w - 130 - 28
        lines = wrap_text(headline, 3, hw)
        c.block(lines[:3], hx, py + 4, 3, INK, leading=4)
        # Summary across the full cell width.
        sy = y + 172
        slines = wrap_text(summary, 2, cell_w - 28)
        c.block(slines[:3], x + 14, sy, 2, INK, leading=4)
        c.text("SOURCE: " + source, x + 14, y + cell_h - 24, 2, GREY)

    # Footer.
    fy = top + 3 * cell_h + 2 * gap + 8
    c.rect(24, fy, W - 48, 2, INK)
    c.text_center("DRAWN FROM REPORTS OF 24 NOVEMBER 2026 - SOURCES: "
                  "REUTERS - AP - AFP", W // 2, fy + 10, 2, GREY)
    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(draw_page())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
