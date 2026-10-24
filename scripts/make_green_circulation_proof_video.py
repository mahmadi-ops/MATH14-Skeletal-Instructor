#!/usr/bin/env python3
"""Render, with Manim, the animation explaining the idea behind the proof of
Green's theorem in its circulation-curl (tangential) form,

    oint_C M dx + N dy  =  iint_R (dN/dx - dM/dy) dA.

The video argues the theorem, it does not compute it, in the manner of
scripts/make_stokes_proof_idea_video.py.  The chain of ideas:

  1.  the statement: the counterclockwise circulation of F = <M, N> around
      C against the integral of (curl F) . k over the region R inside;
  2.  one tiny rectangle: its bottom and top edges together give
      -(dM/dy) dA (the top is travelled backwards, which is where the minus
      sign comes from), its right and left edges give (dN/dx) dA, so
      (curl F) . k is circulation per unit area;
  3.  cover R with such rectangles; along C some of them stick out of R;
  4.  add the circulation around every rectangle;
  5.  every interior edge is travelled twice, once in each direction, so
      the inside cancels in pairs, and only a staircase hugging C is left;
  6.  so the circulation around C is approximately the sum over the
      rectangles; as their number increases, less sticks out of R and the
      approximation improves; in the limit the staircase becomes C, the
      sum becomes the double integral, and the theorem follows;
  7.  on a curved surface the same argument is Stokes' theorem.

No numbers appear: the region, the rectangles and the field are generic.

Styling follows the other videos in the book: black background, Computer
Modern text in white, blue boundary, orange and purple for the M- and
N-parts, red field, gold for what sticks out of R.

Output: assets/videos/green_circulation_proof_1080p.mp4 (1920x1080, 30 fps,
silent).

Run with:  python3 scripts/make_green_circulation_proof_video.py
           python3 scripts/make_green_circulation_proof_video.py --out FILE
           python3 scripts/make_green_circulation_proof_video.py --still BEAT
"""

import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
from manim import *

OUT_FILE = Path(__file__).resolve().parents[1] / "assets" / "videos" / \
    "green_circulation_proof_1080p.mp4"

# the palette of the other videos in the book
INK = "#ffffff"
CURVE = "#2e9aff"          # the boundary curve C
REGION = "#1d5e8c"         # the region R
REGION_SOLID = "#10344d"   # REGION at 55% on black, opaque so that what lies behind R is hidden
STICK = "#e0b84a"          # the parts of the rectangles sticking out of R
MCOL = "#ff862f"           # the M-part: horizontal edges
NCOL = "#c77dff"           # the N-part: vertical edges
FIELD = "#fc6255"          # the field F
GRIDC = "#7fb8e6"          # the rectangles
DIM = "#5a5a5a"

TPL = TexTemplate(preamble=r"\usepackage{amsmath}" "\n" r"\usepackage{amssymb}")

# ------------------------------------------------------------------ region
CENTER = np.array([0.0, -0.15, 0.0])


def blob(t):
    """The boundary C of R, counterclockwise as t increases."""
    r = 2.05 + 0.26 * np.sin(2 * t + 0.6) + 0.13 * np.cos(3 * t)
    return CENTER + np.array([1.3 * r * np.cos(t), 0.86 * r * np.sin(t), 0.0])


TS = np.linspace(0, 2 * np.pi, 400, endpoint=False)
BOUNDARY = np.array([blob(t) for t in TS])


def region_polygon(**kw):
    return Polygon(*BOUNDARY, **kw)


def oriented_C(width=6, tips=(0.35, 2.45, 4.4)):
    """The curve C, with arrowheads showing the counterclockwise direction."""
    curve = VMobject(stroke_color=CURVE, stroke_width=width)
    curve.set_points_smoothly([blob(t) for t in np.linspace(0, 2 * np.pi, 160)])
    arrows = VGroup(*[
        Arrow(blob(t0), blob(t0 + 0.13), buff=0, color=CURVE,
              stroke_width=width, max_tip_length_to_length_ratio=1.2,
              tip_length=0.24)
        for t0 in tips
    ])
    return VGroup(curve, arrows)


def inside(p):
    """Point-in-region test against the polygon BOUNDARY."""
    x, y = p[0], p[1]
    c = False
    P = BOUNDARY
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        if (a[1] > y) != (b[1] > y):
            if x < a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]):
                c = not c
    return c


def region_area():
    x, y = BOUNDARY[:, 0], BOUNDARY[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def cover(h):
    """The squares of side h, on the lattice through CENTER, that meet R, as
    index pairs (i, j): the square with lower-left corner CENTER + (i h, j h).
    A square meets R when its centre is inside or C passes through it."""
    xmin, xmax = BOUNDARY[:, 0].min(), BOUNDARY[:, 0].max()
    ymin, ymax = BOUNDARY[:, 1].min(), BOUNDARY[:, 1].max()
    cells = set()
    for i in range(int(np.floor((xmin - CENTER[0]) / h)), int(np.ceil((xmax - CENTER[0]) / h)) + 1):
        for j in range(int(np.floor((ymin - CENTER[1]) / h)), int(np.ceil((ymax - CENTER[1]) / h)) + 1):
            x, y = CENTER[0] + i * h, CENTER[1] + j * h
            hit = np.any((BOUNDARY[:, 0] >= x) & (BOUNDARY[:, 0] <= x + h) &
                         (BOUNDARY[:, 1] >= y) & (BOUNDARY[:, 1] <= y + h))
            if hit or inside([x + h / 2, y + h / 2]):
                cells.add((i, j))
    return cells


def corner(i, j, h):
    return np.array([CENTER[0] + i * h, CENTER[1] + j * h, 0.0])


def cover_grid(h, cells, color=GRIDC, width=2):
    """The outlines of the covering squares."""
    return VGroup(*[
        Square(side_length=h, stroke_color=color, stroke_width=width)
        .move_to(corner(i, j, h) + [h / 2, h / 2, 0])
        for i, j in sorted(cells)
    ]).set_z_index(2)


def cover_stick(h, cells):
    """The squares that C passes through, filled gold and kept behind the
    opaque region, so that only the parts sticking out of R show."""
    group = VGroup()
    for i, j in sorted(cells):
        x, y = corner(i, j, h)[:2]
        if np.any((BOUNDARY[:, 0] >= x) & (BOUNDARY[:, 0] <= x + h) &
                  (BOUNDARY[:, 1] >= y) & (BOUNDARY[:, 1] <= y + h)) or not inside([x + h / 2, y + h / 2]):
            group.add(Square(side_length=h, stroke_width=0, fill_color=STICK, fill_opacity=0.45)
                      .move_to(corner(i, j, h) + [h / 2, h / 2, 0]))
    return group.set_z_index(-1)


def stick_area(h, cells):
    return len(cells) * h * h - region_area()


def staircase(h, cells, color=INK, width=5):
    """The outer boundary of the union of the covering squares, traced
    counterclockwise: the edges whose neighbour across them is not in the
    cover."""
    nxt = {}
    for i, j in cells:
        for a, b, nb in [((i, j), (i + 1, j), (i, j - 1)), ((i + 1, j), (i + 1, j + 1), (i + 1, j)),
                         ((i + 1, j + 1), (i, j + 1), (i, j + 1)), ((i, j + 1), (i, j), (i - 1, j))]:
            if nb not in cells:
                nxt.setdefault(a, []).append(b)
    start = min(nxt)
    path, v = [start], start
    while True:
        outs = nxt[v]
        v = outs.pop(0)
        if v == start:
            break
        path.append(v)
    if any(nxt.values()):
        raise ValueError("the cover is not bounded by a single staircase")
    stair = VMobject(stroke_color=color, stroke_width=width)
    stair.set_points_as_corners([corner(i, j, h) for i, j in path + [start]])
    return stair.set_z_index(4)


def swirls(h, cells, color=MCOL, width=2.4):
    """A small counterclockwise circulation arrow in every covering square."""
    group = VGroup()
    tip = 0.09 * h / 0.62
    for i, j in sorted(cells):
        c = corner(i, j, h) + [h / 2, h / 2, 0]
        arc = Arc(radius=0.27 * h, start_angle=-0.6 * PI, angle=1.55 * PI,
                  arc_center=c, stroke_color=color, stroke_width=width)
        arc.add_tip(tip_length=tip, tip_width=tip)
        group.add(arc)
    return group.set_z_index(3)


class GreenCirculationProof(Scene):
    only = None

    # -------------------------------------------------------------- helpers
    def caption(self, *lines, edge=UP, buff=0.45, size=40):
        block = VGroup(*[
            Tex(line, tex_template=TPL, font_size=size, color=INK)
            for line in lines
        ]).arrange(DOWN, buff=0.2).to_edge(edge, buff=buff)
        return block

    def formula(self, tex, edge=DOWN, buff=0.55, size=46, color=INK, **kw):
        f = MathTex(tex, tex_template=TPL, font_size=size, color=color, **kw)
        return f.to_edge(edge, buff=buff)

    def clear(self, *mobs, run_time=0.6):
        self.play(*[FadeOut(m) for m in mobs if m is not None], run_time=run_time)

    def construct(self):
        self.camera.background_color = "#000000"
        for name, beat in (("statement", self.beat_statement),
                           ("cell", self.beat_one_cell),
                           ("chop", self.beat_chop),
                           ("add", self.beat_add),
                           ("cancel", self.beat_cancel),
                           ("limit", self.beat_limit),
                           ("stokes", self.beat_stokes)):
            beat()
            if self.only == name:
                return

    # 1 ---------------------------------------------------------------------
    def beat_statement(self):
        self.region = region_polygon(fill_color=REGION_SOLID, fill_opacity=1,
                                     stroke_width=0)
        self.C = oriented_C().set_z_index(5)
        title = self.caption(r"Green's Theorem (circulation--curl form)", size=50)
        self.play(FadeIn(title))
        self.play(FadeIn(self.region), run_time=1.2)
        self.play(Create(self.C[0]), run_time=1.6)
        self.play(*[GrowArrow(a) for a in self.C[1]], run_time=0.6)

        r_lab = MathTex("R", tex_template=TPL, font_size=56, color=INK).move_to(CENTER + [-0.2, 0.3, 0])
        c_lab = MathTex("C", tex_template=TPL, font_size=50, color=CURVE).move_to(blob(0.95) + [0.35, 0.3, 0])
        self.play(FadeIn(r_lab), FadeIn(c_lab))

        # a field F = <M, N>, faint, over the whole picture
        def F(p):
            x, y = (p - CENTER)[:2]
            return np.array([-0.55 * y + 0.25 * x + 0.35, 0.55 * x - 0.1 * y + 0.15, 0.0])
        field = VGroup()
        for x in np.arange(-6.3, 6.4, 0.9):
            for y in np.arange(-1.8, 1.9, 0.9):
                p = np.array([x, y, 0])
                v = F(p)
                v = 0.5 * v / max(np.linalg.norm(v), 1e-6)
                field.add(Arrow(p - v / 2, p + v / 2, buff=0, color=FIELD,
                                stroke_width=3, max_tip_length_to_length_ratio=0.3,
                                stroke_opacity=0.6, fill_opacity=0.6))
        f_lab = MathTex(r"\mathbf{F}=\langle M,N\rangle", tex_template=TPL,
                        font_size=42, color=FIELD).move_to([5.5, 2.25, 0])
        f_lab.add_background_rectangle(opacity=0.85, buff=0.08)
        self.play(FadeIn(field, lag_ratio=0.02), FadeIn(f_lab), run_time=1.4)
        self.wait(1.0)
        self.clear(title)

        eq = self.formula(
            r"\oint_C M\,dx+N\,dy\;=\;\iint_R\left(\frac{\partial N}{\partial x}"
            r"-\frac{\partial M}{\partial y}\right)dA",
            edge=UP, buff=0.4, size=46)
        self.play(Write(eq), run_time=2.0)
        ask = self.caption(r"Circulation around $C$ on the left, the curl inside $R$ on the right.",
                           r"Why should they be equal?", edge=DOWN, size=38)
        self.play(FadeIn(ask))
        self.wait(2.6)
        self.clear(ask, eq, field, f_lab, r_lab, c_lab)
        self.labels = None

    # 2 ---------------------------------------------------------------------
    def beat_one_cell(self):
        """What one tiny rectangle says: (curl F).k is circulation per unit area."""
        head = self.caption(r"Idea 1: the circulation around one tiny rectangle", size=44)
        self.play(FadeIn(head), FadeOut(self.region), FadeOut(self.C))

        # the rectangle, on the left of the screen
        w, hgt = 2.6, 2.1
        o = np.array([-6.1, -1.2, 0])                     # its corner (x, y)
        bl, br, tr, tl = o, o + [w, 0, 0], o + [w, hgt, 0], o + [0, hgt, 0]
        cell = Polygon(bl, br, tr, tl, stroke_width=0, fill_color=REGION, fill_opacity=0.6)
        bottom = Arrow(bl, br, buff=0.05, color=MCOL, stroke_width=6, max_tip_length_to_length_ratio=0.12)
        top = Arrow(tr, tl, buff=0.05, color=MCOL, stroke_width=6, max_tip_length_to_length_ratio=0.12)
        right = Arrow(br, tr, buff=0.05, color=NCOL, stroke_width=6, max_tip_length_to_length_ratio=0.16)
        left = Arrow(tl, bl, buff=0.05, color=NCOL, stroke_width=6, max_tip_length_to_length_ratio=0.16)
        corner = Dot(bl, color=INK, radius=0.06)
        lab_o = MathTex("(x,y)", tex_template=TPL, font_size=34, color=INK).next_to(bl, DOWN, buff=0.15)
        lab_dx = MathTex(r"\Delta x", tex_template=TPL, font_size=36, color=INK).next_to(bottom, DOWN, buff=0.12).shift(RIGHT * 0.5)
        lab_dy = MathTex(r"\Delta y", tex_template=TPL, font_size=36, color=INK).next_to(left, LEFT, buff=0.12)
        self.play(FadeIn(cell), FadeIn(corner), FadeIn(lab_o), FadeIn(lab_dx), FadeIn(lab_dy))

        col = dict(tex_template=TPL, font_size=38)
        x0 = -2.6
        # bottom and top: the M-part
        m1 = MathTex(r"M(x,y)\,\Delta x", color=MCOL, **col)
        m2 = MathTex(r"-\,M(x,y+\Delta y)\,\Delta x", color=MCOL, **col)
        m3 = MathTex(r"\approx\;-\frac{\partial M}{\partial y}\,\Delta A", color=MCOL, **col)
        row1 = VGroup(m1, m2, m3).arrange(RIGHT, buff=0.22).move_to([0, 1.25, 0], aligned_edge=LEFT).shift(RIGHT * x0)
        n1 = MathTex(r"N(x+\Delta x,y)\,\Delta y", color=NCOL, **col)
        n2 = MathTex(r"-\,N(x,y)\,\Delta y", color=NCOL, **col)
        n3 = MathTex(r"\approx\;\frac{\partial N}{\partial x}\,\Delta A", color=NCOL, **col)
        row2 = VGroup(n1, n2, n3).arrange(RIGHT, buff=0.22).move_to([0, -0.35, 0], aligned_edge=LEFT).shift(RIGHT * x0)

        note = self.caption(r"Along the bottom, $\mathbf{F}\cdot d\mathbf{r}\approx M\,\Delta x$.",
                            edge=DOWN, size=36)
        self.play(GrowArrow(bottom), FadeIn(note))
        self.play(Write(m1), run_time=1.0)
        self.wait(0.8)
        note2 = self.caption(r"The top is travelled backwards, from right to left:",
                             r"that is where the minus sign comes from.", edge=DOWN, size=36)
        self.play(GrowArrow(top), FadeOut(note), FadeIn(note2))
        self.play(Write(m2), run_time=1.2)
        self.wait(1.6)
        self.play(Write(m3), run_time=1.2)
        self.wait(1.0)
        note3 = self.caption(r"Up the right side and down the left, $\mathbf{F}\cdot d\mathbf{r}\approx \pm N\,\Delta y$.",
                             edge=DOWN, size=36)
        self.play(GrowArrow(right), GrowArrow(left), FadeOut(note2), FadeIn(note3))
        self.play(Write(n1), run_time=1.0)
        self.play(Write(n2), run_time=1.0)
        self.wait(0.8)
        self.play(Write(n3), run_time=1.2)
        self.wait(1.2)

        total = MathTex(r"\oint_{\text{rectangle}}\mathbf{F}\cdot d\mathbf{r}\;\approx\;"
                        r"\left(\frac{\partial N}{\partial x}-\frac{\partial M}{\partial y}\right)\Delta A",
                        tex_template=TPL, font_size=42, color=INK)
        total.move_to([0, -1.95, 0], aligned_edge=LEFT).shift(RIGHT * x0)
        box = SurroundingRectangle(total, color=INK, buff=0.15, stroke_width=2)
        self.play(FadeOut(note3))
        self.play(Write(total), run_time=1.6)
        self.play(Create(box))
        note4 = self.caption(r"$\dfrac{\partial N}{\partial x}-\dfrac{\partial M}{\partial y}=(\operatorname{curl}\mathbf{F})\cdot\mathbf{k}$"
                             r" is circulation per unit area \quad ($\Delta A=\Delta x\,\Delta y$).",
                             edge=DOWN, buff=0.35, size=34)
        self.play(FadeIn(note4))
        self.wait(3.0)
        self.clear(head, note4, cell, bottom, top, right, left, corner, lab_o, lab_dx, lab_dy,
                   row1, row2, total, box)
        self.play(FadeIn(self.region), FadeIn(self.C))

    # 3 ---------------------------------------------------------------------
    def beat_chop(self):
        head = self.caption(r"Idea 2: cover $R$ with tiny rectangles", size=46)
        self.play(FadeIn(head))
        self.h = 0.62
        self.cells = cover(self.h)
        self.grid = cover_grid(self.h, self.cells)
        self.stick = cover_stick(self.h, self.cells)
        self.play(Create(self.grid, lag_ratio=0.02), run_time=2.0)
        note = self.caption(r"Along $C$ some of the rectangles stick out of $R$.",
                            edge=DOWN, size=40)
        self.play(FadeIn(note), FadeIn(self.stick))
        self.wait(2.4)
        self.clear(note, head)

    # 4 ---------------------------------------------------------------------
    def beat_add(self):
        head = self.caption(r"Idea 3: add up the circulation around every rectangle", size=44)
        self.play(FadeIn(head))
        self.sw = swirls(self.h, self.cells)
        self.play(LaggedStart(*[Create(a) for a in self.sw], lag_ratio=0.015, run_time=2.6))
        self.summ = self.formula(
            r"\sum_k \oint_{\partial R_k}\mathbf{F}\cdot d\mathbf{r}\;\approx\;"
            r"\sum_k\left(\frac{\partial N}{\partial x}-\frac{\partial M}{\partial y}\right)\Delta A_k",
            edge=DOWN, buff=0.4, size=42)
        self.play(Write(self.summ), run_time=2.0)
        self.wait(2.0)
        self.clear(head)

    # 5 ---------------------------------------------------------------------
    def beat_cancel(self):
        head = self.caption(r"Idea 4: the inside cancels", size=46)
        self.play(FadeIn(head), FadeOut(self.summ))

        # two neighbouring rectangles, enlarged in a card
        card = self.two_cell_card()
        card["card"].move_to([0, -0.2, 0]).set_z_index(10)
        self.play(FadeIn(card["card"]), run_time=0.9)
        note = self.caption(r"Two rectangles share an edge,",
                            r"and each one travels it the opposite way.", edge=DOWN, size=38)
        self.play(FadeIn(note))
        self.wait(1.4)
        self.play(Indicate(card["shared"], color=INK, scale_factor=1.15), run_time=1.2)
        self.clear(note, run_time=0.5)
        self.play(FadeOut(card["shared"], scale=0.4), run_time=1.2)
        gone = self.caption(r"Their contributions cancel.", edge=DOWN, size=42)
        self.play(FadeIn(gone))
        self.wait(1.4)
        self.clear(gone, card["card"])

        # everywhere at once
        note2 = self.caption(r"Every interior edge is shared by two rectangles,",
                             r"so every interior edge cancels.", edge=DOWN, size=38)
        self.play(FadeIn(note2))
        self.wait(1.6)
        self.stair = staircase(self.h, self.cells)
        self.play(FadeOut(self.grid), FadeOut(self.sw), Create(self.stair), run_time=2.0)
        self.clear(note2, run_time=0.5)
        note3 = self.caption(r"Only the outer edges are left: a staircase that hugs $C$.",
                             edge=DOWN, size=40)
        self.play(FadeIn(note3))
        self.wait(2.2)
        self.clear(note3, head)

    def two_cell_card(self):
        box = RoundedRectangle(width=8.0, height=4.2, corner_radius=0.15, stroke_color=DIM,
                               stroke_width=2, fill_color="#000000", fill_opacity=1.0)
        s = 1.5

        def cell(centre, drop_right=False, drop_left=False):
            c = np.array(centre)
            corners = {"bl": c + [-s / 2, -s / 2, 0], "br": c + [s / 2, -s / 2, 0],
                       "tr": c + [s / 2, s / 2, 0], "tl": c + [-s / 2, s / 2, 0]}
            group, shared = VGroup(), None
            for a, b in [("bl", "br"), ("br", "tr"), ("tr", "tl"), ("tl", "bl")]:
                colr = MCOL if a in ("bl", "tr") else NCOL
                arr = Arrow(corners[a], corners[b], buff=0.06, color=colr, stroke_width=5,
                            max_tip_length_to_length_ratio=0.16)
                if (drop_right and (a, b) == ("br", "tr")) or (drop_left and (a, b) == ("tl", "bl")):
                    shared = arr
                else:
                    group.add(arr)
            return group, shared

        left, shared_l = cell([-0.95, 0, 0], drop_right=True)
        right, shared_r = cell([0.95, 0, 0], drop_left=True)
        shared_l.shift(LEFT * 0.07)
        shared_r.shift(RIGHT * 0.07)
        shared = VGroup(shared_l, shared_r)
        labs = VGroup(MathTex("R_1", tex_template=TPL, color=INK, font_size=40).move_to([-0.95, 0, 0]),
                      MathTex("R_2", tex_template=TPL, color=INK, font_size=40).move_to([0.95, 0, 0]))
        inner = VGroup(left, right, shared, labs)
        return {"card": VGroup(box, inner), "shared": shared}

    # 6 ---------------------------------------------------------------------
    def beat_limit(self):
        head = self.caption(r"So the sum over the rectangles is the circulation around the staircase",
                            size=40)
        self.play(FadeIn(head))
        chain = self.formula(r"\sum_k\oint_{\partial R_k}\mathbf{F}\cdot d\mathbf{r}\;=\;"
                             r"\oint_{\text{staircase}}\mathbf{F}\cdot d\mathbf{r}",
                             edge=DOWN, buff=0.45, size=44)
        self.play(Write(chain), run_time=1.6)
        self.wait(2.2)

        # the staircase hugs C, and with Idea 3: the circulation around C is
        # approximately a sum over the rectangles
        dfrac = r"\left(\frac{\partial N}{\partial x}-\frac{\partial M}{\partial y}\right)"
        approx = MathTex(r"\oint_C M\,dx+N\,dy", r"\;\approx\;", r"\sum_k" + dfrac + r"\Delta A_k",
                         tex_template=TPL, font_size=44, color=INK).to_edge(DOWN, buff=0.45)
        head_b = self.caption(r"The staircase hugs $C$, so by Idea 3 the circulation around $C$",
                              r"is approximately a sum over the rectangles.", size=40)
        self.play(FadeOut(head), FadeIn(head_b), FadeOut(chain, shift=UP * 0.3),
                  FadeIn(approx, shift=UP * 0.3), run_time=1.2)
        self.wait(2.4)

        # as the number of rectangles grows, less sticks out and the approximation improves
        head2 = self.caption(r"As the number of rectangles increases, less sticks out of $R$",
                             r"and the approximation improves.", size=42)
        H = 3.0
        track = Rectangle(width=0.55, height=H, stroke_color=INK, stroke_opacity=0.6,
                          stroke_width=2).move_to([5.3, -0.35, 0])
        level = ValueTracker(0.0)

        def make_bar():
            b = Rectangle(width=0.55, height=max(H * level.get_value(), 1e-3), stroke_width=0,
                          fill_color=FIELD, fill_opacity=0.85)
            return b.move_to(track.get_bottom(), aligned_edge=DOWN)

        bar = always_redraw(make_bar)
        g_lab = Tex(r"error in $\approx$", tex_template=TPL, font_size=34,
                    color=INK).next_to(track, UP, buff=0.2)
        # the bar follows the area sticking out of R
        sizes = [self.h, self.h / 2, self.h / 4]
        covers = [self.cells, cover(sizes[1]), cover(sizes[2])]
        levels = [stick_area(hh, cc) / stick_area(sizes[0], covers[0]) for hh, cc in zip(sizes, covers)]
        layers = [VGroup(self.stick, cover_grid(self.h, self.cells), self.stair)]
        for hh, cc, w in zip(sizes[1:], covers[1:], (1.5, 1.0)):
            layers.append(VGroup(cover_stick(hh, cc), cover_grid(hh, cc, width=w),
                                 staircase(hh, cc, width=w + 2)))
        self.add(bar)
        self.play(FadeOut(head_b), FadeIn(head2), FadeIn(track), FadeIn(g_lab),
                  Create(layers[0][1], lag_ratio=0.02), level.animate.set_value(levels[0]),
                  run_time=1.8)
        self.wait(1.4)
        for prev, layer, lv in zip(layers, layers[1:], levels[1:]):
            self.play(FadeOut(prev), FadeIn(layer[0]), Create(layer[1], lag_ratio=0.005),
                      Create(layer[2]), level.animate.set_value(lv), run_time=2.2)
            self.wait(1.6)

        # in the limit the approximation becomes exact
        head3 = self.caption(r"In the limit the staircase becomes $C$",
                             r"and the sum becomes the double integral.", size=40)
        self.play(FadeOut(head2), FadeIn(head3))
        self.play(FadeOut(layers[-1]), level.animate.set_value(0.0), run_time=1.6)
        final = MathTex(r"\oint_C M\,dx+N\,dy", r"\;=\;", r"\iint_R" + dfrac + r"dA",
                        tex_template=TPL, font_size=44, color=INK).to_edge(DOWN, buff=0.45)
        self.play(ReplacementTransform(approx[0], final[0]), ReplacementTransform(approx[1], final[1]),
                  FadeTransform(approx[2], final[2]), run_time=1.8)
        self.wait(2.0)
        bar.clear_updaters()
        self.play(FadeOut(head3), FadeOut(track), FadeOut(bar), FadeOut(g_lab),
                  final.animate.scale(48 / 44).to_edge(UP, buff=0.4), run_time=1.4)
        frame = SurroundingRectangle(final, color=CURVE, buff=0.18, stroke_width=3)
        self.play(Create(frame))
        self.wait(2.0)
        self.final = VGroup(final, frame)

    # 7 ---------------------------------------------------------------------
    def beat_stokes(self):
        note = self.caption(r"On a curved surface the same argument, patch by patch,",
                            r"is Stokes' theorem.", edge=DOWN, size=40)
        self.play(FadeIn(note))
        self.wait(2.8)
        self.play(FadeOut(note), FadeOut(self.final), FadeOut(self.region), FadeOut(self.C),
                  run_time=1.2)
        self.wait(0.4)


def main(argv):
    out = OUT_FILE
    if "--out" in argv:
        out = Path(argv[argv.index("--out") + 1]).resolve()
    still = argv[argv.index("--still") + 1] if "--still" in argv else None

    tmp = Path(tempfile.mkdtemp(prefix="green-manim-"))
    config.media_dir = str(tmp)
    config.pixel_width, config.pixel_height = 1920, 1080
    config.frame_rate = 30
    config.background_color = "#000000"
    config.output_file = "green_circulation_proof_1080p"
    config.disable_caching = True

    if still:
        config.save_last_frame = True
        config.write_to_movie = False
        GreenCirculationProof.only = still
        GreenCirculationProof().render()
        png = next(tmp.rglob("*.png"))
        dst = Path.cwd() / f"green_{still}.png"
        shutil.move(str(png), str(dst))
        print(f"wrote {dst}")
        return

    GreenCirculationProof().render()
    produced = next(tmp.rglob("green_circulation_proof_1080p.mp4"))
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(produced), str(out))
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
