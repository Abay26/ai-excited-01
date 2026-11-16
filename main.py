#!/usr/bin/env python3
"""ai-excited-01 entry: a humpback whale breaching out of a smartphone.

Pure standard library (zlib + struct write the PNG bytes by hand). Renders one
1024x1024 image to $MAKEFUN_OUTPUT_DIR/entry.png (or /output/entry.png).
Fully deterministic: fixed constants only, no randomness, no timestamps.
"""
import math
import os
import struct
import zlib

W = 1024
H = 1024
img = bytearray(W * H * 3)

NAVY = (13, 42, 90)
WHALE = (18, 58, 107)
WHALE_DARK = (10, 40, 80)
BELLY = (238, 246, 255)
FOAM = (235, 245, 255)
SPRAY = (210, 235, 255)
SKY_TOP = (125, 205, 250)
SKY_BOT = (28, 128, 220)
SEA_TOP = (13, 71, 161)
SEA_BOT = (4, 30, 70)
SUN = (255, 213, 79)
SUN_GLOW = (255, 235, 150)
PHONE = (15, 23, 42)
SCREEN = (178, 235, 255)
HALO = (90, 190, 255)
ORANGE = (255, 140, 60)
YELLOW = (255, 205, 40)
WHITE = (255, 255, 255)
WAVE = (90, 165, 235)
BUBBLE = (170, 215, 250)


def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        img[i] = c[0]
        img[i + 1] = c[1]
        img[i + 2] = c[2]


def fill_rect(x0, y0, x1, y1, c):
    x0 = max(0, int(x0))
    y0 = max(0, int(y0))
    x1 = min(W - 1, int(x1))
    y1 = min(H - 1, int(y1))
    if x1 < x0 or y1 < y0:
        return
    row = bytes(c) * (x1 - x0 + 1)
    for y in range(y0, y1 + 1):
        i = (y * W + x0) * 3
        img[i:i + (x1 - x0 + 1) * 3] = row


def lerp_color(c0, c1, t):
    return tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3))


def vgrad(y0, y1, c0, c1):
    for y in range(max(0, y0), min(H - 1, y1) + 1):
        t = (y - y0) / max(1, y1 - y0)
        c = lerp_color(c0, c1, t)
        img[y * W * 3:(y + 1) * W * 3] = bytes(c) * W


def disc(cx, cy, r, c):
    cx = int(cx)
    cy = int(cy)
    r = int(r)
    if r <= 0:
        return
    for y in range(max(0, cy - r), min(H - 1, cy + r) + 1):
        dy = y - cy
        dx = int(math.sqrt(max(0, r * r - dy * dy)))
        x0 = max(0, cx - dx)
        x1 = min(W - 1, cx + dx)
        i = (y * W + x0) * 3
        img[i:i + (x1 - x0 + 1) * 3] = bytes(c) * (x1 - x0 + 1)


def ellipse(cx, cy, rx, ry, c):
    rx = int(rx)
    ry = int(ry)
    if rx <= 0 or ry <= 0:
        return
    for y in range(max(0, cy - ry), min(H - 1, cy + ry) + 1):
        dy = (y - cy) / ry
        dx = int(rx * math.sqrt(max(0.0, 1.0 - dy * dy)))
        x0 = max(0, cx - dx)
        x1 = min(W - 1, cx + dx)
        i = (y * W + x0) * 3
        img[i:i + (x1 - x0 + 1) * 3] = bytes(c) * (x1 - x0 + 1)


def polygon(pts, c):
    ys = [p[1] for p in pts]
    y0 = max(0, int(min(ys)))
    y1 = min(H - 1, int(max(ys)))
    n = len(pts)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x0, ya = pts[i]
            x1, yb = pts[(i + 1) % n]
            if (ya <= y < yb) or (yb <= y < ya):
                t = (y - ya) / (yb - ya)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            xa = max(0, int(xs[i]))
            xb = min(W - 1, int(xs[i + 1]))
            if xb >= xa:
                ii = (y * W + xa) * 3
                img[ii:ii + (xb - xa + 1) * 3] = bytes(c) * (xb - xa + 1)


def line(x0, y0, x1, y1, c, w=1):
    steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    r = max(1, w // 2)
    for i in range(steps + 1):
        t = i / max(1, steps)
        disc(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t), r, c)


def rrect(x, y, w, h, r, c):
    polygon([(x + r, y), (x + w - r, y), (x + w, y + r), (x + w, y + h - r),
             (x + w - r, y + h), (x + r, y + h), (x, y + h - r), (x, y + r)], c)
    for cx, cy in [(x + r, y + r), (x + w - r, y + r),
                   (x + w - r, y + h - r), (x + r, y + h - r)]:
        disc(cx, cy, r, c)


def rot_pt(x, y, cx, cy, ang):
    ca = math.cos(ang)
    sa = math.sin(ang)
    dx = x - cx
    dy = y - cy
    return (cx + dx * ca - dy * sa, cy + dx * sa + dy * ca)


def rotated_rrect(cx, cy, w, h, ang, r, c):
    outer = [rot_pt(cx - w / 2, cy - h / 2, cx, cy, ang),
             rot_pt(cx + w / 2, cy - h / 2, cx, cy, ang),
             rot_pt(cx + w / 2, cy + h / 2, cx, cy, ang),
             rot_pt(cx - w / 2, cy + h / 2, cx, cy, ang)]
    polygon(outer, c)
    for dx, dy in [(-w / 2 + r, -h / 2 + r), (w / 2 - r, -h / 2 + r),
                   (w / 2 - r, h / 2 - r), (-w / 2 + r, h / 2 - r)]:
        px, py = rot_pt(cx + dx, cy + dy, cx, cy, ang)
        disc(int(px), int(py), r, c)


# 5x7 pixel font, only the glyphs "HI, JUDGE!" needs.
FONT = {
    'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'I': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    ',': [".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."],
    'J': ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    'U': ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'D': ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    'G': [".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."],
    'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    '!': ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    ' ': [".....", ".....", ".....", ".....", ".....", ".....", "....."],
}


def draw_text(x, y, s, scale, c):
    cx = x
    for ch in s:
        g = FONT.get(ch, FONT[' '])
        for r, row in enumerate(g):
            for col, bit in enumerate(row):
                if bit == '#':
                    fill_rect(cx + col * scale, y + r * scale,
                              cx + col * scale + scale - 1,
                              y + r * scale + scale - 1, c)
        cx += 6 * scale


def draw_sky_and_sea():
    vgrad(0, 470, SKY_TOP, SKY_BOT)
    vgrad(470, H - 1, SEA_TOP, SEA_BOT)
    # sun with glow and rays, top-left
    for x, y in [(150, 140)]:
        disc(x, y, 130, (255, 244, 190))
        disc(x, y, 95, SUN_GLOW)
        for k in range(12):
            a = k * math.pi / 6 + 0.26
            line(x + int(105 * math.cos(a)), y + int(105 * math.sin(a)),
                 x + int(165 * math.cos(a)), y + int(165 * math.sin(a)), SUN, 7)
        disc(x, y, 58, SUN)
        disc(x + 14, y - 14, 30, (255, 230, 130))
    # sparkles in the sky
    for sx, sy, sr in [(300, 90, 12), (470, 60, 9), (620, 130, 10), (880, 60, 11),
                       (950, 210, 9), (90, 300, 10), (760, 240, 8)]:
        line(sx - sr, sy, sx + sr, sy, WHITE, 3)
        line(sx, sy - sr, sx, sy + sr, WHITE, 3)
    # horizon shimmer
    for x in range(0, W, 26):
        disc(x, 470 + int(3 * math.sin(x / 60.0)), 5, (150, 205, 245))
    # rolling waves in the sea
    for base, phase in [(560, 0.0), (660, 1.3), (800, 2.6), (920, 0.9)]:
        prev = None
        for x in range(0, W + 1, 8):
            y = base + int(7 * math.sin(x / 55.0 + phase))
            if prev is not None:
                line(prev[0], prev[1], x, y, WAVE, 4)
            prev = (x, y)


def quad_bezier(p0, c, p2, t):
    u = 1.0 - t
    return (u * u * p0[0] + 2 * u * t * c[0] + t * t * p2[0],
            u * u * p0[1] + 2 * u * t * c[1] + t * t * p2[1])


def quad_tangent(p0, c, p2, t):
    return (2 * (1 - t) * (c[0] - p0[0]) + 2 * t * (p2[0] - c[0]),
            2 * (1 - t) * (c[1] - p0[1]) + 2 * t * (p2[1] - c[1]))


def draw_phone():
    cx, cy = 512, 730
    ang = -0.18
    # glow halo behind the phone
    rotated_rrect(cx, cy, 404, 624, ang, 46, HALO)
    # phone body and screen
    rotated_rrect(cx, cy, 360, 580, ang, 42, PHONE)
    rotated_rrect(cx, cy, 318, 538, ang, 30, SCREEN)
    # light streak across the screen
    p1 = rot_pt(cx - 170, cy - 200, cx, cy, ang)
    p2 = rot_pt(cx + 60, cy - 200, cx, cy, ang)
    p3 = rot_pt(cx + 170, cy + 200, cx, cy, ang)
    p4 = rot_pt(cx - 60, cy + 200, cx, cy, ang)
    polygon([p1, p2, p3, p4], (220, 248, 255))
    # notch at the top of the screen
    nx, ny = rot_pt(cx, cy - 258, cx, cy, ang)
    disc(int(nx), int(ny), 12, PHONE)
    # app icons on the lower half of the screen
    icons = [(255, 140, 60), (120, 200, 90), (255, 205, 40),
             (150, 120, 230), (90, 165, 235), (255, 110, 130)]
    k = 0
    for row in range(2):
        for col in range(3):
            lx = -100 + col * 100
            ly = 130 + row * 95
            ix, iy = rot_pt(cx + lx, cy + ly, cx, cy, ang)
            rrect(int(ix) - 22, int(iy) - 22, 44, 44, 10, icons[k])
            k += 1
    # home indicator bar
    hx, hy = rot_pt(cx, cy + 255, cx, cy, ang)
    rrect(int(hx) - 55, int(hy) - 5, 110, 10, 5, (60, 90, 130))


def draw_whale():
    p0 = (640.0, 520.0)   # tail base, just out of the phone screen
    pc = (700.0, 150.0)   # control point: the arch of the leap
    p2 = (330.0, 290.0)   # head, upper left
    # tail flukes first, so the body overlaps the joint
    polygon([(640, 520), (745, 430), (760, 480), (665, 535)], WHALE)
    polygon([(640, 520), (750, 580), (720, 615), (660, 540)], WHALE)
    # body: discs along the curve, radius tapering at both ends
    pts = []
    for i in range(91):
        t = i / 90.0
        pt = quad_bezier(p0, pc, p2, t)
        r = 55 + 45 * math.sin(math.pi * math.pow(t, 0.9))
        pts.append((pt, r, t))
        disc(int(pt[0]), int(pt[1]), int(r), WHALE)
    # white belly: discs offset to the underside of the curve
    for pt, r, t in pts:
        if 0.08 <= t <= 0.92:
            tx, ty = quad_tangent(p0, pc, p2, t)
            n = math.hypot(tx, ty) or 1.0
            nx, ny = ty / n, -tx / n
            if ny < 0:  # belly must face down (positive y)
                nx, ny = -nx, -ny
            disc(int(pt[0] + nx * 0.45 * r), int(pt[1] + ny * 0.45 * r),
                 int(0.45 * r), BELLY)
    # dorsal fin on the back, near the tail
    pt, r, t = pts[11]
    tx, ty = quad_tangent(p0, pc, p2, t)
    n = math.hypot(tx, ty) or 1.0
    bx, by = -ty / n, tx / n
    if by > 0:
        bx, by = -bx, -by
    base = (pt[0] + bx * 0.7 * r, pt[1] + by * 0.7 * r)
    tip = (pt[0] + bx * 1.25 * r, pt[1] + by * 1.25 * r)
    polygon([(base[0] - 14, base[1] + 10), (tip[0], tip[1]),
             (base[0] + 16, base[1] - 4)], WHALE_DARK)
    # (no pectoral fin: on this arc it reads as a dark arrow through the belly)
    # eye and smile near the head
    head = quad_bezier(p0, pc, p2, 0.92)
    disc(int(head[0] + 12), int(head[1] - 16), 10, WHITE)
    disc(int(head[0] + 12), int(head[1] - 16), 5, (10, 15, 30))
    line(int(head[0] - 30), int(head[1] + 28), int(head[0] + 55),
         int(head[1] + 12), WHALE_DARK, 4)
    # blowhole spray above the head
    for sx, sy, sr in [(385, 190, 8), (405, 168, 6), (360, 180, 6), (425, 195, 7),
                       (340, 205, 5), (415, 145, 5), (375, 155, 4)]:
        disc(sx, sy, sr, SPRAY)
    line(390, 215, 380, 175, SPRAY, 3)
    line(405, 210, 415, 170, SPRAY, 3)


def draw_splash():
    # foam where the whale bursts out of the screen
    for sx, sy, sr, c in [
            (600, 470, 26, FOAM), (560, 480, 20, FOAM), (650, 480, 22, FOAM),
            (520, 500, 16, FOAM), (690, 500, 15, SPRAY), (600, 440, 18, FOAM),
            (575, 455, 12, SPRAY), (630, 450, 13, FOAM), (545, 460, 10, SPRAY),
            (665, 460, 11, SPRAY), (600, 500, 24, (200, 230, 255))]:
        disc(sx, sy, sr, c)
    # droplets flying up around the breach
    for sx, sy, sr in [(520, 420, 8), (680, 430, 9), (560, 390, 7), (700, 480, 6),
                       (480, 470, 7), (720, 440, 5), (540, 360, 5), (640, 380, 6)]:
        disc(sx, sy, sr, SPRAY)


def draw_bubble():
    # tail first, then the bubble body, then the text
    polygon([(700, 195), (640, 275), (770, 195)], NAVY)
    rrect(588, 63, 379, 134, 26, NAVY)
    polygon([(712, 193), (662, 262), (755, 193)], WHITE)
    rrect(592, 67, 371, 126, 22, WHITE)
    draw_text(625, 118, "HI, JUDGE!", 5, NAVY)


def draw_fish_and_bubbles():
    def fish(cx, cy, s, flip, c):
        ellipse(cx, cy, int(22 * s), int(9 * s), c)
        d = -1 if flip else 1
        polygon([(cx + d * 20 * s, cy), (cx + d * 34 * s, cy - 10 * s),
                 (cx + d * 34 * s, cy + 10 * s)], c)
        disc(int(cx - d * 10 * s), int(cy - 2 * s), max(2, int(2 * s)), WHITE)
    fish(200, 830, 1.0, False, ORANGE)
    fish(850, 880, 1.1, True, ORANGE)
    fish(300, 960, 0.8, False, YELLOW)
    fish(150, 700, 0.7, False, YELLOW)
    # bubbles rising from the phone
    for bx, by, br in [(300, 640, 12), (280, 590, 9), (260, 540, 7),
                       (740, 660, 11), (770, 610, 8), (800, 565, 6)]:
        disc(bx, by, br, BUBBLE)
        sea = lerp_color(SEA_TOP, SEA_BOT, (by - 470) / 554.0)
        disc(bx, by, max(2, br - 3), sea)


def draw_scene():
    draw_sky_and_sea()
    draw_phone()
    draw_whale()
    draw_splash()
    draw_bubble()
    draw_fish_and_bubbles()


def png_chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(path):
    raw = b"".join(b"\x00" + bytes(img[y * W * 3:(y + 1) * W * 3])
                   for y in range(H))
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr)
            + png_chunk(b"IDAT", zlib.compress(raw, 6))
            + png_chunk(b"IEND", b""))
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


def main():
    draw_scene()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    path = os.path.join(out_dir, "entry.png")
    n = write_png(path)
    print("wrote %s (%d bytes)" % (path, n))


if __name__ == "__main__":
    main()
