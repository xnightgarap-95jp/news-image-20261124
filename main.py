"""The World in One Day -- Tuesday 24 November 2026.

A one-page newspaper front page drawn from scratch with the Python
standard library only. Real DejaVu Serif type comes from fontdata.py
(glyph bitmaps rendered once with PIL on this machine; this program
itself needs no Pillow). The PNG is written by hand with zlib.

Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
Writes out/entry.png (1024x1024, deterministic, byte-identical).
"""
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fontdata import FONTS  # noqa: E402

W, H = 1024, 1024

PAPER = (247, 242, 231)
INK = (26, 26, 26)
RED = (176, 30, 36)
DARK = (18, 26, 38)
GREY = (112, 108, 98)
LIGHT = (232, 226, 212)
WHITE = (255, 255, 255)
BLACK = (10, 10, 10)
SEA = (38, 96, 138)
SKY = (168, 196, 220)
SAND = (214, 196, 158)
GREEN = (46, 125, 70)
GOLD = (198, 138, 20)
PURPLE = (123, 75, 166)
TEAL = (42, 122, 120)
BLUE = (31, 78, 156)
RUST = (163, 51, 39)
SLATE = (90, 107, 122)

REGION_COLORS = {
    "EUROPE": BLUE,
    "ASIA-PACIFIC": GOLD,
    "GLOBAL": SLATE,
    "MIDDLE EAST": RUST,
    "THE AMERICAS": PURPLE,
    "AFRICA": GREEN,
}


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg[0] for _ in range(w * h * 3))
        for i in range(w * h):
            self.px[i * 3:i * 3 + 3] = bytes(bg)

    def _clip(self, x0, y0, x1, y1, clip):
        if clip:
            x0 = max(x0, clip[0])
            y0 = max(y0, clip[1])
            x1 = min(x1, clip[0] + clip[2])
            y1 = min(y1, clip[1] + clip[3])
        x0 = max(x0, 0)
        y0 = max(y0, 0)
        x1 = min(x1, self.w)
        y1 = min(y1, self.h)
        return x0, y0, x1, y1

    def fill_rect(self, x, y, w, h, color, clip=None):
        x0, y0, x1, y1 = self._clip(x, y, x + w, y + h, clip)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            self.px[base:base + len(row)] = row

    def rect(self, x, y, w, h, color, t=1, clip=None):
        self.fill_rect(x, y, w, t, color, clip)
        self.fill_rect(x, y + h - t, w, t, color, clip)
        self.fill_rect(x, y, t, h, color, clip)
        self.fill_rect(x + w - t, y, t, h, color, clip)

    def hline(self, x0, x1, y, color, clip=None):
        if x1 < x0:
            x0, x1 = x1, x0
        self.fill_rect(x0, y, x1 - x0 + 1, 1, color, clip)

    def vline(self, x, y0, y1, color, clip=None):
        if y1 < y0:
            y0, y1 = y1, y0
        self.fill_rect(x, y0, 1, y1 - y0 + 1, color, clip)

    def line(self, x0, y0, x1, y1, color, clip=None):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            if 0 <= x0 < self.w and 0 <= y0 < self.h:
                if clip is None or (clip[0] <= x0 < clip[0] + clip[2]
                                    and clip[1] <= y0 < clip[1] + clip[3]):
                    base = (y0 * self.w + x0) * 3
                    self.px[base:base + 3] = bytes(color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, clip=None):
        for yy in range(cy - r, cy + r + 1):
            dx = int((r * r - (yy - cy) ** 2) ** 0.5) if abs(yy - cy) <= r else 0
            self.fill_rect(cx - dx, yy, dx * 2 + 1, 1, color, clip)

    def poly(self, pts, color, clip=None):
        # scanline fill for a simple polygon
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(min(ys), 0), min(max(ys), self.h - 1) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                    xs.append(x)
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[i]), y, int(xs[i + 1]) - int(xs[i]) + 1,
                               1, color, clip)

    # ------------------------------------------------------------ text
    def text_width(self, s, weight, size):
        font = FONTS[(weight, size)]
        total = 0
        for ch in s:
            g = font.get(ch)
            if g is None:
                g = font["?"]
            total += g[4]
        return total

    def draw_text(self, x, y, s, weight, size, color, clip=None):
        """Draw s with its baseline at y."""
        font = FONTS[(weight, size)]
        cx = x
        for ch in s:
            g = font.get(ch)
            if g is None:
                g = font["?"]
            w, h, yoff, rows, adv = g
            top = y + yoff
            for i, bits in enumerate(rows):
                yy = top + i
                if yy < 0 or yy >= self.h:
                    continue
                for xx in range(w):
                    if (bits >> (w - 1 - xx)) & 1:
                        px, py = cx + xx, yy
                        if 0 <= px < self.w and 0 <= py < self.h:
                            if clip is None or (clip[0] <= px < clip[0] + clip[2]
                                                and clip[1] <= py < clip[1] + clip[3]):
                                base = (py * self.w + px) * 3
                                self.px[base:base + 3] = bytes(color)
            cx += adv
        return cx

    def draw_text_center(self, cx, y, s, weight, size, color, clip=None):
        w = self.text_width(s, weight, size)
        return self.draw_text(cx - w // 2, y, s, weight, size, color, clip)

    def wrap(self, s, weight, size, maxw):
        words = s.split()
        lines, cur = [], ""
        for wd in words:
            trial = (cur + " " + wd).strip()
            if self.text_width(trial, weight, size) <= maxw or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines

    def paragraph(self, x, y, s, weight, size, maxw, leading, color, clip=None):
        for ln in self.wrap(s, weight, size, maxw):
            self.draw_text(x, y, ln, weight, size, color, clip)
            y += leading
        return y


# ---------------------------------------------------------------- scenes
def scene_box(c, x, y, w, h, bg):
    c.fill_rect(x, y, w, h, bg, clip=(x, y, w, h))
    c.rect(x, y, w, h, INK, 1)


def scene_hormuz(c, x, y, w, h):
    box = (x, y, w, h)
    scene_box(c, x, y, w, h, SKY)
    c.fill_rect(x, y + h * 55 // 100, w, h * 45 // 100, SEA, clip=box)
    # tanker hull
    c.fill_rect(x + w // 8, y + h * 52 // 100, w * 3 // 4, h * 16 // 100,
                (40, 40, 44), clip=box)
    c.fill_rect(x + w // 8, y + h * 40 // 100, w // 5, h * 12 // 100,
                (120, 40, 36), clip=box)
    # mine: spiky black circle
    mx, my, mr = x + w * 82 // 100, y + h * 68 // 100, 7
    for ang in range(0, 360, 45):
        import math as _m
        c.line(mx, my, mx + int(13 * _m.cos(_m.radians(ang))),
               my + int(13 * _m.sin(_m.radians(ang))), BLACK, clip=box)
    c.circle(mx, my, mr, BLACK, clip=box)
    # smoke puffs
    c.circle(x + w // 5, y + h * 30 // 100, 9, (200, 200, 195), clip=box)
    c.circle(x + w // 5 + 12, y + h * 24 // 100, 7, (215, 215, 210), clip=box)
    # dashed route
    for i in range(0, w, 14):
        c.hline(x + i, x + i + 7, y + h * 82 // 100, WHITE, clip=box)


def scene_nvidia(c, x, y, w, h):
    box = (x, y, w, h)
    scene_box(c, x, y, w, h, DARK)
    # chip
    cx, cy, cw, chh = x + w // 2 - 26, y + h // 2 - 22, 52, 44
    c.fill_rect(cx, cy, cw, chh, (28, 140, 70), clip=box)
    c.rect(cx, cy, cw, chh, (120, 220, 150), 1, clip=box)
    c.fill_rect(cx + 14, cy + 12, 24, 20, (16, 90, 46), clip=box)
    for i in range(5):
        c.vline(cx + 6 + i * 10, cy - 7, cy - 1, (160, 220, 170), clip=box)
        c.vline(cx + 6 + i * 10, cy + chh + 1, cy + chh + 7, (160, 220, 170),
                clip=box)
        c.hline(cx - 7, cx - 1, cy + 6 + i * 8, (160, 220, 170), clip=box)
        c.hline(cx + cw + 1, cx + cw + 7, cy + 6 + i * 8, (160, 220, 170),
                clip=box)
    # rising bars
    for i, bh in enumerate((14, 22, 30)):
        bx = x + w - 52 + i * 14
        c.fill_rect(bx, y + h - 12 - bh, 10, bh, (60, 200, 110), clip=box)


def scene_zaporizhzhia(c, x, y, w, h):
    box = (x, y, w, h)
    scene_box(c, x, y, w, h, (24, 30, 48))
    # apartment block
    bx, by, bw, bh = x + w // 6, y + h * 34 // 100, w * 3 // 5, h * 66 // 100
    c.fill_rect(bx, by, bw, bh, (120, 118, 110), clip=box)
    for r in range(3):
        for col in range(4):
            wx = bx + 8 + col * (bw // 4)
            wy = by + 8 + r * (bh // 3)
            colr = (250, 200, 80) if (r + col) % 3 == 0 else (40, 44, 54)
            c.fill_rect(wx, wy, bw // 5, bh // 5, colr, clip=box)
    # explosion burst
    ex, ey = x + w * 78 // 100, y + h * 30 // 100
    c.circle(ex, ey, 16, (250, 160, 40), clip=box)
    c.circle(ex, ey, 9, (250, 220, 90), clip=box)
    for ang in range(0, 360, 30):
        import math as _m
        c.line(ex, ey, ex + int(24 * _m.cos(_m.radians(ang))),
               ey + int(24 * _m.sin(_m.radians(ang))), (250, 180, 60), clip=box)
    # smoke
    c.circle(x + w // 4, y + h * 22 // 100, 8, (90, 90, 95), clip=box)


def scene_gaza(c, x, y, w, h):
    box = (x, y, w, h)
    scene_box(c, x, y, w, h, (196, 178, 140))
    for i, bh in enumerate((26, 40, 32, 46)):
        bx = x + 8 + i * (w // 4)
        c.fill_rect(bx, y + h - bh - 8, w // 5, bh, (90, 84, 76), clip=box)
    ex, ey = x + w * 72 // 100, y + h * 34 // 100
    c.circle(ex, ey, 12, (240, 120, 40), clip=box)
    c.circle(ex, ey, 6, (250, 210, 90), clip=box)
    c.circle(x + w // 3, y + h * 22 // 100, 7, (120, 112, 100), clip=box)


def scene_leak(c, x, y, w, h):
    box = (x, y, w, h)
    scene_box(c, x, y, w, h, (232, 226, 212))
    # stack of papers
    for k in range(3):
        px, py = x + 14 + k * 8, y + 10 + k * 7
        c.fill_rect(px, py, w - 60, h - 26, WHITE, clip=box)
        c.rect(px, py, w - 60, h - 26, INK, 1, clip=box)
        for r in range(3):
            c.hline(px + 6, px + w - 70, py + 8 + r * 7, GREY, clip=box)
    # red stamp
    sx, sy = x + w - 62, y + h - 30
    c.fill_rect(sx, sy, 48, 18, RED, clip=box)
    c.draw_text(sx + 6, sy + 13, "LEAK", "B", 11, WHITE, clip=box)


def scene_jets(c, x, y, w, h):
    box = (x, y, w, h)
    scene_box(c, x, y, w, h, SKY)
    # radar arcs
    cx, cy = x + 22, y + h - 12
    for r in (14, 26, 38):
        for ang in range(270, 361, 6):
            import math as _m
            px = cx + int(r * _m.cos(_m.radians(ang)))
            py = cy + int(r * _m.sin(_m.radians(ang)))
            if 0 <= px < W and 0 <= py < H:
                c.fill_rect(px, py, 1, 1, (60, 110, 70), clip=box)
    # jets: simple swept silhouettes
    for jx, jy, s in ((x + w // 2, y + 16, 1), (x + w * 3 // 4, y + 30, -1)):
        c.poly([(jx, jy), (jx + 26 * s, jy + 8), (jx + 8 * s, jy + 8),
                (jx + 2 * s, jy + 16)], (40, 44, 54), clip=box)


def scene_delta(c, x, y, w, h):
    box = (x, y, w, h)
    scene_box(c, x, y, w, h, DARK)
    # monitor
    mx, my, mw, mh = x + 10, y + 8, w - 20, h - 16
    c.fill_rect(mx, my, mw, mh, (16, 40, 30), clip=box)
    c.rect(mx, my, mw, mh, (90, 160, 140), 1, clip=box)
    import math as _m
    nodes = [(mx + 16, my + 12), (mx + mw - 20, my + 16),
             (mx + mw // 2, my + mh // 2), (mx + 22, my + mh - 14),
             (mx + mw - 26, my + mh - 12)]
    for i in range(len(nodes) - 1):
        c.line(nodes[i][0], nodes[i][1], nodes[i + 1][0], nodes[i + 1][1],
               (90, 200, 160), clip=box)
    for (nx, ny) in nodes:
        c.circle(nx, ny, 3, (250, 200, 80), clip=box)


def scene_court(c, x, y, w, h):
    box = (x, y, w, h)
    scene_box(c, x, y, w, h, (214, 204, 182))
    # courthouse: pediment + columns
    cx = x + w // 2
    c.poly([(cx - 52, y + 16), (cx + 52, y + 16), (cx, y + 4)], (120, 40, 36),
           clip=box)
    c.fill_rect(cx - 52, y + 16, 104, 5, (90, 84, 76), clip=box)
    for i in range(4):
        colx = cx - 44 + i * 28
        c.fill_rect(colx, y + 21, 8, h - 30, (240, 234, 220), clip=box)
    c.fill_rect(cx - 52, y + h - 10, 104, 5, (90, 84, 76), clip=box)


def scene_island(c, x, y, w, h):
    box = (x, y, w, h)
    scene_box(c, x, y, w, h, SKY)
    c.fill_rect(x, y + h * 62 // 100, w, h * 38 // 100, SEA, clip=box)
    # island
    c.poly([(x + w // 4, y + h * 62 // 100), (x + w * 3 // 4, y + h * 62 // 100),
            (x + w * 62 // 100, y + h * 52 // 100),
            (x + w * 38 // 100, y + h * 52 // 100)], SAND, clip=box)
    # palm
    px, py = x + w // 2, y + h * 52 // 100
    c.line(px, py, px + 2, py - 16, (90, 70, 40), clip=box)
    for dx in (-14, -7, 7, 14):
        c.line(px + 2, py - 16, px + 2 + dx, py - 22, GREEN, clip=box)
    # broken chain link
    c.circle(x + w - 26, y + 14, 6, (200, 200, 200), clip=box)
    c.circle(x + w - 14, y + 14, 6, (200, 200, 200), clip=box)
    c.line(x + w - 22, y + 8, x + w - 18, y + 20, RED, clip=box)


def scene_flags(c, x, y, w, h):
    box = (x, y, w, h)
    scene_box(c, x, y, w, h, (232, 226, 212))
    # two flags on poles
    for k, cols in enumerate((((200, 40, 40), WHITE, (40, 60, 160)),
                              ((255, 255, 255), (40, 60, 160)))):
        fx = x + 12 + k * (w // 2)
        c.vline(fx, y + 6, y + h - 8, INK, clip=box)
        fw, fh = w // 2 - 22, 20
        for s, col in enumerate(cols):
            c.fill_rect(fx + 1, y + 8 + s * (fh // len(cols)), fw,
                        fh // len(cols) + 1, col, clip=box)
        c.rect(fx + 1, y + 8, fw, fh, INK, 1, clip=box)
    # star of david-ish mark on second flag
    c.draw_text(x + w // 2 + 8, y + 26, "*", "B", 13, (40, 60, 160), clip=box)


def scene_quake(c, x, y, w, h):
    box = (x, y, w, h)
    scene_box(c, x, y, w, h, (226, 214, 190))
    # mountains
    c.poly([(x, y + h), (x + w // 4, y + 12), (x + w // 2, y + h)],
           (120, 116, 108), clip=box)
    c.poly([(x + w // 3, y + h), (x + w * 2 // 3, y + 6), (x + w, y + h)],
           (90, 88, 84), clip=box)
    c.poly([(x + w // 4 - 8, y + 12), (x + w // 4 + 8, y + 12),
            (x + w // 4, y + 22)], WHITE, clip=box)
    # seismograph zigzag
    pts = [(x + 8 + i * 9, y + h - 12 - ((i * 37) % 18)) for i in range(12)]
    for i in range(len(pts) - 1):
        c.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], RED, clip=box)


def scene_clinic(c, x, y, w, h):
    box = (x, y, w, h)
    scene_box(c, x, y, w, h, (214, 226, 200))
    # tent
    tx, ty = x + w // 2, y + h // 2
    c.poly([(tx - 34, ty + 14), (tx, ty - 16), (tx + 34, ty + 14)], WHITE,
           clip=box)
    c.poly([(tx - 34, ty + 14), (tx, ty + 2), (tx + 34, ty + 14)], (220, 60, 50),
           clip=box)
    # red cross sign
    c.fill_rect(tx - 4, ty - 12, 8, 20, RED, clip=box)
    c.fill_rect(tx - 10, ty - 6, 20, 8, RED, clip=box)


def scene_oil(c, x, y, w, h):
    box = (x, y, w, h)
    scene_box(c, x, y, w, h, (226, 214, 190))
    # derrick tower
    bx = x + w // 2
    c.poly([(bx - 26, y + h - 6), (bx - 8, y + 8), (bx + 8, y + 8),
            (bx + 26, y + h - 6)], (90, 84, 76), clip=box)
    c.line(bx - 18, y + h - 16, bx + 18, y + h - 16, (60, 56, 50), clip=box)
    c.line(bx - 12, y + h - 28, bx + 12, y + h - 28, (60, 56, 50), clip=box)
    # pumpjack arm + oil drop
    c.line(bx + 8, y + 8, bx + 30, y + 16, (40, 40, 44), clip=box)
    c.circle(bx + 30, y + 20, 3, BLACK, clip=box)
    c.poly([(bx + 34, y + 26), (bx + 38, y + 34), (bx + 30, y + 34)],
           BLACK, clip=box)
    # ground line
    c.hline(x + 6, x + w - 6, y + h - 6, (60, 56, 50), clip=box)


def scene_trade(c, x, y, w, h):
    box = (x, y, w, h)
    scene_box(c, x, y, w, h, (232, 226, 212))
    # EU flag: blue with circle of stars
    ex, ey, ew, eh = x + 10, y + 10, w // 2 - 16, h - 20
    c.fill_rect(ex, ey, ew, eh, BLUE, clip=box)
    import math as _m
    for k in range(8):
        ang = _m.radians(k * 45)
        sx = ex + ew // 2 + int(9 * _m.cos(ang))
        sy = ey + eh // 2 + int(9 * _m.sin(ang))
        c.circle(sx, sy, 1, (250, 220, 80), clip=box)
    # Indonesia flag: red over white
    ix = x + w // 2 + 6
    c.fill_rect(ix, ey, ew, eh // 2, (200, 40, 36), clip=box)
    c.fill_rect(ix, ey + eh // 2, ew, eh // 2, WHITE, clip=box)
    c.rect(ix, ey, ew, eh, INK, 1, clip=box)
    # arrow between
    c.line(ex + ew + 2, ey + eh // 2, ix - 2, ey + eh // 2, RED, clip=box)


SCENES = {
    "hormuz": scene_hormuz,
    "nvidia": scene_nvidia,
    "zaporizhzhia": scene_zaporizhzhia,
    "gaza": scene_gaza,
    "leak": scene_leak,
    "jets": scene_jets,
    "delta": scene_delta,
    "court": scene_court,
    "island": scene_island,
    "flags": scene_flags,
    "quake": scene_quake,
    "clinic": scene_clinic,
    "oil": scene_oil,
    "trade": scene_trade,
}


# ---------------------------------------------------------------- content
STATS = [
    ("4", "tankers mined\nin Hormuz"),
    ("490,000+", "Russian troops killed,\nleaked data says"),
    ("40", "wounded in the\nZaporizhzhia strike"),
    ("5.6", "magnitude of\nthe Nepal quake"),
    ("181", "Arya's record\nT20 score"),
    ("7.3m", "more people at risk\nof losing food aid"),
]

REGIONS = [("EUROPE", 8), ("ASIA-PACIFIC", 9), ("GLOBAL", 6),
           ("MIDDLE EAST", 6), ("THE AMERICAS", 4), ("AFRICA", 2)]

LEADS = [
    dict(n=1, scene="hormuz", banner="HORMUZ: TANKERS MINED",
         kicker="STRAIT OF HORMUZ \u00b7 IRAN WAR",
         head="Fourth tanker hits a mine as Iran shuts the Strait further",
         body="A fourth tanker hit a mine in the Strait of Hormuz, Iran's "
              "Guards said, as Tehran ordered the waterway shut \u201cfurther "
              "day by day\u201d. Qatar pressed for talks.",
         src="Middle East Eye, Euronews"),
    dict(n=2, scene="gaza", banner="GAZA: SECURITY CHIEF KILLED",
         kicker="GAZA CITY \u00b7 WAR",
         head="Israeli strike kills Hamas security chief",
         body="Naeem Abu Nahel, Hamas's internal security chief, was killed "
              "with six others, two of them police officers, in Israeli "
              "airstrikes on Gaza City on Tuesday.",
         src="Reuters, Dawn"),
    dict(n=3, scene="zaporizhzhia", banner="ZAPORIZHZHIA: NIGHT STRIKE",
         kicker="UKRAINE \u00b7 WAR",
         head="Two killed, 40 hurt as Russian strike hits flats",
         body="An overnight Russian attack on Zaporizhzhia killed two people "
              "and wounded 40, including four children, striking an "
              "apartment building, the governor said.",
         src="Just Security, AP"),
]

MEDIUMS = [
    dict(n=4, scene="court", banner="MEXICO: EL CHAPO ISIDRO TRIED",
         kicker="MEXICO \u00b7 CRIME",
         head="Mexico to try 'El Chapo Isidro' itself",
         body="Mexico will try 'El Chapo Isidro' for drug and weapons "
              "trafficking despite a US extradition request.",
         src="Horizon, La Mediterranee"),
    dict(n=5, scene="leak", banner="RUSSIA: DEATH TOLL LEAK",
         kicker="RUSSIA \u00b7 WAR",
         head="Leak puts Russian war dead past 490,000",
         body="Leaked data put Russian troops killed in Ukraine above "
              "490,000, one of the war's starkest counts yet.",
         src="10Things, La Mediterranee"),
    dict(n=6, scene="jets", banner="KOREA: JETS SCRAMBLED",
         kicker="SEOUL \u00b7 SECURITY",
         head="Russian jets enter Korea's defence zone",
         body="South Korea scrambled jets as Russian aircraft entered its "
              "air defence zone.",
         src="Just Security, Chanakya Lens"),
    dict(n=7, scene="delta", banner="GERMANY: DELTA ACCESS",
         kicker="BERLIN \u00b7 DEFENCE",
         head="Germany first in line for Ukraine's Delta system",
         body="Germany is set to become the first country to gain access "
              "to Ukraine's Delta battlefield system.",
         src="Kyiv Independent"),
    dict(n=8, scene="oil", banner="IRAQ: OILFIELDS SEIZED",
         kicker="BAGHDAD \u00b7 ENERGY",
         head="Iraq orders ministry to run Kurdish oilfields",
         body="Iraq's PM ordered the oil ministry to manage oilfields in "
              "areas under Kurdish security control.",
         src="Reuters, Al Arabiya"),
    dict(n=9, scene="island", banner="SOLOMONS: CHINA PACT ENDS",
         kicker="HONIARA \u00b7 DIPLOMACY",
         head="Solomon Islands to end China security pact",
         body="Honiara told Beijing it will not renew its security pact "
              "with China when the five-year deal expires in April.",
         src="10Things"),
    dict(n=10, scene="flags", banner="NETANYAHU: STRIKE IRAN",
         kicker="JERUSALEM \u00b7 DIPLOMACY",
         head="Netanyahu urges Trump to hit Iran again",
         body="Israel's PM urged Donald Trump to authorise renewed strikes "
              "on Iran.",
         src="10Things"),
    dict(n=11, scene="quake", banner="NEPAL: QUAKE 5.6",
         kicker="KOSHI \u00b7 DISASTER",
         head="Magnitude 5.6 quake shakes Nepal",
         body="A magnitude 5.6 earthquake struck Koshi province near the "
              "Chinese border.",
         src="Horizon, Chanakya Lens"),
    dict(n=12, scene="clinic", banner="CONGO: EBOLA TEAMS TRAPPED",
         kicker="ITURI \u00b7 HEALTH",
         head="Fighting traps Ebola responders in Ituri",
         body="Heavy fighting near a hospital in Ituri forced Ebola teams "
              "to take cover for over 24 hours.",
         src="UN News"),
    dict(n=13, scene="trade", banner="EU-INDONESIA: TRADE DEAL",
         kicker="BRUSSELS \u00b7 TRADE",
         head="EU and Indonesia sign tariff-slashing deal",
         body="The EU and Indonesia signed a trade deal eliminating most "
              "tariffs between them after years of talks.",
         src="Chanakya Lens"),
]

ALSO = [
    (14, "India–NZ Test drawn in Wellington", "IANS"),
    (15, "China sentences official in spy case", "Chanakya Lens"),
    (16, "Hasina: I'll return on 16 Dec", "Chanakya Lens"),
    (17, "Senate probes Vance-Vitol deal", "Chanakya Lens"),
    (18, "US targets Iran shadow banking", "Chanakya Lens"),
    (19, "US probes Iran tanker cyberattacks", "Chanakya Lens"),
    (20, "Thousands protest TV raid in Istanbul", "Chanakya Lens"),
    (21, "Germany tests kamikaze drones in Lithuania", "Chanakya Lens"),
    (22, "Thousands march in Lisbon over housing", "Chanakya Lens"),
    (23, "Latvia: war may hit tipping point next year", "Reuters"),
    (24, "Norway in talks with Ukraine on stability", "Just Security"),
    (25, "Oxfam: Gaza now a 'toxic land'", "Horizon"),
    (26, "Car bomb wrecks buildings in Villavicencio", "The Hindu"),
    (27, "Coach-truck crash kills 11 in UAE", "The National"),
    (28, "First foreign astronaut joins Tiangong", "Straits Times"),
    (29, "India women beat China 6-2 in hockey", "Apex Sports"),
    (30, "Arya smashes record 181 in T20 for Delhi", "IANS"),
    (31, "South Africa bowl Bangladesh out for 91", "IANS"),
    (32, "England beat Australia by 8 wickets in T20I", "ScoreZaap"),
    (33, "World Cup hosts named for 2031, 2035", "GalaxySports7"),
    (34, "Pennsylvania measles claims 9th death", "Horizon"),
    (35, "Wars put food aid for 7.3m at risk", "10Things"),
]

DATE_CHECK = ("Left out as other days' news: COP31's collapse (Sun 22 Nov) \u00b7 "
              "Nvidia brings Huang back (Mon 23 Nov) \u00b7 UK sanctions five "
              "Myanmar generals (Mon 23 Nov) \u00b7 Belgium's national strike "
              "(Mon 23 Nov) \u00b7 Shah\u2013Modi talks in Delhi (Mon 23 Nov) \u00b7 "
              "Brentford 4\u20130 Everton (Mon 23 Nov) \u00b7 Ukraine's Libya ship "
              "strikes confirmed (Mon 23 Nov).")

# map pins (fraction of map box) for stories 1-13; spread so no two overlap
PINS = {
    1: (0.68, 0.42), 2: (0.555, 0.42), 3: (0.56, 0.30),
    4: (0.20, 0.33), 5: (0.60, 0.20), 6: (0.84, 0.38),
    7: (0.50, 0.24), 8: (0.62, 0.46), 9: (0.93, 0.62),
    10: (0.57, 0.50), 11: (0.73, 0.43), 12: (0.52, 0.58),
    13: (0.46, 0.33),
}


# ---------------------------------------------------------------- layout
def draw_map(c, x, y, w, h):
    box = (x, y, w, h)
    c.fill_rect(x, y, w, h, (208, 226, 236), clip=box)
    c.rect(x, y, w, h, INK, 1)
    # rough continents, drawn as flat blobs
    land = (216, 202, 164)
    # North America
    c.poly([(x + 8, y + 34), (x + 70, y + 12), (x + 118, y + 22),
            (x + 108, y + 58), (x + 60, y + 66), (x + 18, y + 58)], land, clip=box)
    # South America
    c.poly([(x + 78, y + 92), (x + 108, y + 92), (x + 104, y + 140),
            (x + 88, y + 158), (x + 78, y + 118)], land, clip=box)
    # Europe
    c.poly([(x + 148, y + 22), (x + 178, y + 16), (x + 186, y + 40),
            (x + 162, y + 52), (x + 146, y + 40)], land, clip=box)
    # Africa
    c.poly([(x + 148, y + 62), (x + 182, y + 62), (x + 188, y + 96),
            (x + 172, y + 128), (x + 156, y + 100)], land, clip=box)
    # Asia
    c.poly([(x + 190, y + 16), (x + 268, y + 10), (x + 300, y + 34),
            (x + 282, y + 62), (x + 240, y + 66), (x + 210, y + 52),
            (x + 192, y + 38)], land, clip=box)
    # Australia
    c.poly([(x + 268, y + 118), (x + 296, y + 118), (x + 292, y + 138),
            (x + 270, y + 138)], land, clip=box)
    # pins
    for n, (fx, fy) in PINS.items():
        px, py = x + int(fx * w), y + int(fy * h)
        c.circle(px, py, 7, RED, clip=box)
        c.circle(px, py, 7, INK, clip=box)
        c.circle(px, py, 6, RED, clip=box)
        num = str(n)
        tw = c.text_width(num, "B", 9)
        c.draw_text(px - tw // 2, py + 3, num, "B", 9, WHITE, clip=box)


def main():
    c = Canvas(W, H, PAPER)
    mx = 28
    cw = W - 2 * mx  # 968

    # kicker
    c.draw_text(mx, 30, "THE WORLD IN ONE DAY", "B", 13, RED)
    right = "35 STORIES \u00b7 6 REGIONS \u00b7 EVERY ONE DATED TUESDAY 24 NOVEMBER 2026"
    c.draw_text(mx + cw - c.text_width(right, "R", 9), 28, right, "R", 9, GREY)
    c.hline(mx, mx + cw - 1, 38, INK)

    # headline
    c.draw_text_center(mx + cw // 2, 88, "Tuesday 24 November 2026", "B", 44, INK)
    c.draw_text_center(
        mx + cw // 2, 116,
        "Fourth tanker mined in Hormuz \u00b7 Hamas security chief killed \u00b7 "
        "Two killed in Zaporizhzhia flats",
        "R", 13, (60, 58, 52))
    c.hline(mx, mx + cw - 1, 124, INK)

    # stat strip
    sy = 130
    cell = cw // 6
    for i, (num, label) in enumerate(STATS):
        x = mx + i * cell
        if i:
            c.vline(x, sy + 4, sy + 44, GREY)
        c.draw_text(x + 8, sy + 26, num, "B", 24, INK)
        ly = sy + 38
        for ln in label.split("\n"):
            c.draw_text(x + 8, ly, ln, "R", 9, GREY)
            ly += 11
    c.hline(mx, mx + cw - 1, 184, INK)

    # region bar
    ry, rh = 190, 18
    total = sum(v for _, v in REGIONS)
    rx = mx
    for name, v in REGIONS:
        seg = int(cw * v / total)
        col = REGION_COLORS[name]
        c.fill_rect(rx, ry, seg, rh, col)
        label = "%s %d" % (name, v)
        tw = c.text_width(label, "B", 11)
        size = 11
        if tw >= seg - 4:
            size = 9
            tw = c.text_width(label, "B", 9)
        if tw < seg - 4:
            c.draw_text(rx + (seg - tw) // 2, ry + 13, label, "B", size, WHITE)
        rx += seg

    # leads
    ly = 214
    lw = (cw - 2 * 12) // 3
    for i, lead in enumerate(LEADS):
        x = mx + i * (lw + 12)
        SCENES[lead["scene"]](c, x, ly, lw, 100)
        by = ly + 100
        c.fill_rect(x, by, lw, 20, RED)
        c.draw_text(x + 6, by + 14, lead["banner"], "B", 11, WHITE)
        y = by + 34
        c.draw_text(x, y, "%d \u00b7 %s" % (lead["n"], lead["kicker"]), "B", 9, RED)
        y += 6
        y = c.paragraph(x, y + 16, lead["head"], "B", 16, lw, 19, INK)
        y += 2
        y = c.paragraph(x, y, lead["body"], "R", 11, lw, 13, (50, 48, 44))
        c.draw_text(x, y + 2, "(%s)" % lead["src"], "R", 9, GREY)

    # mediums: two rows of five
    my = 466
    mw = (cw - 4 * 10) // 5
    for row in range(2):
        for col in range(5):
            m = MEDIUMS[row * 5 + col]
            x = mx + col * (mw + 10)
            y = my + row * 118
            SCENES[m["scene"]](c, x, y, mw, 36)
            by = y + 36
            c.fill_rect(x, by, mw, 15, RED)
            c.draw_text(x + 4, by + 11, m["banner"], "B", 9, WHITE)
            yy = by + 26
            parts = m["kicker"].split(" \u00b7 ")
            kick = "%d \u00b7 %s \u00b7 %s" % (m["n"], parts[0], parts[1])
            src_short = "(" + m["src"].split(",")[0] + ")"
            if (c.text_width(kick, "B", 8)
                    + c.text_width(src_short, "R", 8) > mw - 4):
                kick = "%d \u00b7 %s" % (m["n"], parts[0])
            c.draw_text(x, yy, kick, "B", 8, RED)
            c.draw_text(x + mw - c.text_width(src_short, "R", 8), yy,
                        src_short, "R", 8, GREY)
            yy = c.paragraph(x, yy + 11, m["head"], "B", 11, mw, 12, INK)
            c.paragraph(x, yy + 1, m["body"], "R", 9, mw, 10,
                        (50, 48, 44))

    # map + also list
    ay = 710
    c.fill_rect(mx, ay, cw, 20, BLACK)
    c.draw_text(mx + 6, ay + 14, "WHERE IT HAPPENED \u00b7 numbered as the stories",
                "B", 11, WHITE)
    c.draw_text(mx + 352, ay + 14,
                "ALSO ON TUESDAY 24 NOVEMBER \u2014 22 MORE STORIES",
                "B", 11, WHITE)
    map_y = ay + 26
    draw_map(c, mx, map_y, 330, 188)
    c.draw_text(mx, map_y + 200,
                "Each number is the story with that number on this page.",
                "R", 9, GREY)
    # also items, two columns
    ax = mx + 352
    colw = (cw - 352) // 2 - 6
    for i, (n, text, src) in enumerate(ALSO):
        col = i // 11
        row = i % 11
        x = ax + col * (colw + 12)
        y = map_y + 12 + row * 18
        line = "%d %s (%s)" % (n, text, src)
        if c.text_width(line, "R", 10) > colw:
            line = "%d %s" % (n, text)
        c.draw_text(x, y, line, "R", 10, INK)

    # date check
    dy = 946
    c.rect(mx, dy, cw, 40, RED, 2)
    c.draw_text(mx + 8, dy + 15, "DATE CHECK", "B", 11, RED)
    c.paragraph(mx + 106, dy + 15, DATE_CHECK, "R", 10, cw - 114, 12, INK)

    # footer
    c.hline(mx, mx + cw - 1, 994, INK)
    c.draw_text(mx, 1008,
                "Every story here happened, or was first reported, on Tuesday "
                "24 November 2026. Officials' counts and claims are attributed.",
                "R", 9, GREY)
    c.draw_text(mx + cw - c.text_width("Sources named beside each story \u00b7 original drawings", "R", 9),
                1008, "Sources named beside each story \u00b7 original drawings",
                "R", 9, GREY)

    # ---- write PNG
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        base = yy * W * 3
        raw += c.px[base:base + W * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    print("wrote %s (%d bytes)" % (path, len(png)))


if __name__ == "__main__":
    main()
