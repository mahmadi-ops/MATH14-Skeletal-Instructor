#!/usr/bin/env python3
"""Render the animation behind the first formula of the triple-integral
section: the mass of a block whose density varies from point to point,

    M = iiint_B rho(x,y,z) dV.

The video is about the idea only.  No numbers appear anywhere: the block is
a generic B, the density is a generic rho(x,y,z), and the partition is only
ever "small blocks", never "n blocks".  The beats:

  1.  the block B, shaded by its density rho (darker means denser), and the
      question: mass = density x volume needs a constant density, and rho
      is not constant;
  2.  divide the x, y and z directions into n, m and p divisions: tiny
      blocks B_ijk of volume Delta V = Delta x Delta y Delta z;
  3.  one tiny block, magnified: its density hardly changes, so its mass is
      about rho(x_i, y_j, z_k) Delta V = rho(x_i, y_j, z_k) Dx Dy Dz;
  4.  add the tiny masses: the triple Riemann sum, an estimate in which
      each tiny block was given a single density;
  5.  refine the partition (n, m, p grow): the piecewise-constant picture
      approaches the true shading, and the estimate improves;
  6.  the limit as n, m, p -> infinity is the exact mass, and that limit is
      the triple integral, iiint_B rho dV = iiint_B rho dx dy dz;
  7.  the general form, iiint_E f(x,y,z) dV, of which this is one
      application.

This is the storyboard of the instructor's GeoGebra page "Triple Integrals"
(geogebra.org/m/fwma3ksy), in the notation of the book: rho for the density
(mass per unit volume), the sample point (x_i, y_j, z_k) as in the
double-integral section, and Delta V = Delta x Delta y Delta z as in the
triple-integral section.

Styling follows the other videos in the book: black background, Computer
Modern text in white, blue for the solid, orange highlight, thin grey axes.

Output: assets/videos/block_mass_1080p.mp4 (1920x1080, 30 fps, silent).

Run with:  python3 scripts/make_block_mass_video.py
           python3 scripts/make_block_mass_video.py --still chop
                   (one PNG of the last frame of that beat, for checking)
"""

import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
from manim import *

OUT_FILE = Path(__file__).resolve().parents[1] / "assets" / "videos" / \
    "block_mass_1080p.mp4"

# the palette of the other videos in the book
INK = "#ffffff"
HILITE = "#ff862f"         # the small block under discussion
AXESC = "#9a9a9a"
DIM = "#5a5a5a"
GRID = "#000000"           # the cuts between the small blocks
PALE = "#eaf4ff"           # least dense
DENSE = "#123f6d"          # most dense

# Computer Modern, as in the LaTeX-set text of the other videos
TPL = TexTemplate(preamble=r"\usepackage{amsmath}" "\n" r"\usepackage{amssymb}")

# ------------------------------------------------------------------ the block
# B = [X0,X1] x [Y0,Y1] x [Z0,Z1].  With the camera at theta = -45 degrees
# the three faces that show are x = X1, y = Y0 and z = Z1.
X0, X1 = -2.0, 2.0
Y0, Y1 = -1.5, 1.5
Z0, Z1 = -1.1, 1.1
NSMOOTH = 22               # fine enough to pass for a continuous shading


def rho(x, y, z):
    """A generic smooth density: heavier towards one upper corner, lighter
    towards the opposite one.  Only its shape matters."""
    u = (x - X0) / (X1 - X0)
    v = (y - Y0) / (Y1 - Y0)
    w = (z - Z0) / (Z1 - Z0)
    return 0.35 * u + 0.25 * (1 - v) + 0.4 * w * w + 0.3 * np.exp(
        -((u - 0.8) ** 2 + (v - 0.2) ** 2 + (w - 0.85) ** 2) / 0.12)


_RHO_MIN, _RHO_MAX = None, None


def rho_color(x, y, z):
    global _RHO_MIN, _RHO_MAX
    if _RHO_MIN is None:
        g = np.linspace(0, 1, 25)
        vals = [rho(X0 + a * (X1 - X0), Y0 + b * (Y1 - Y0), Z0 + c * (Z1 - Z0))
                for a in g for b in g for c in g]
        _RHO_MIN, _RHO_MAX = min(vals), max(vals)
    t = (rho(x, y, z) - _RHO_MIN) / (_RHO_MAX - _RHO_MIN)
    return interpolate_color(ManimColor(PALE), ManimColor(DENSE),
                             float(np.clip(t, 0, 1)))


def partition(n, m=None, p=None, stroke_width=1.6, stroke_color=GRID):
    """The three visible faces of B after the x, y and z directions are
    divided into n, m and p pieces.  Each face rectangle is the exposed
    side of one tiny block B_ijk, filled with the density at that block's
    centre.

    Returns a VGroup of the face rectangles, and a dict mapping the
    (i, j, k) index of a tiny block to its visible face rectangles."""
    m = n if m is None else m
    p = n if p is None else p
    xs = np.linspace(X0, X1, n + 1)
    ys = np.linspace(Y0, Y1, m + 1)
    zs = np.linspace(Z0, Z1, p + 1)
    faces = VGroup()
    by_block = {}

    def add(pts, i, j, k):
        cx = 0.5 * (xs[i] + xs[i + 1])
        cy = 0.5 * (ys[j] + ys[j + 1])
        cz = 0.5 * (zs[k] + zs[k + 1])
        col = rho_color(cx, cy, cz)
        poly = Polygon(*[np.array(p, dtype=float) for p in pts],
                       fill_color=col, fill_opacity=1.0,
                       stroke_color=stroke_color if stroke_width else col,
                       stroke_width=stroke_width or 0.6)
        faces.add(poly)
        by_block.setdefault((i, j, k), VGroup()).add(poly)

    # the top face z = Z1 (all blocks with k = p-1)
    for i in range(n):
        for j in range(m):
            add([(xs[i], ys[j], Z1), (xs[i + 1], ys[j], Z1),
                 (xs[i + 1], ys[j + 1], Z1), (xs[i], ys[j + 1], Z1)],
                i, j, p - 1)
    # the front face y = Y0 (j = 0)
    for i in range(n):
        for k in range(p):
            add([(xs[i], Y0, zs[k]), (xs[i + 1], Y0, zs[k]),
                 (xs[i + 1], Y0, zs[k + 1]), (xs[i], Y0, zs[k + 1])],
                i, 0, k)
    # the right face x = X1 (i = n-1)
    for j in range(m):
        for k in range(p):
            add([(X1, ys[j], zs[k]), (X1, ys[j + 1], zs[k]),
                 (X1, ys[j + 1], zs[k + 1]), (X1, ys[j], zs[k + 1])],
                n - 1, j, k)
    return faces, by_block


def smooth_block():
    faces, _ = partition(NSMOOTH, NSMOOTH, NSMOOTH, stroke_width=0)
    return faces


def grid_lines(n, m, p, color=GRID, width=2.0):
    """Only the cuts, drawn over the smooth block: how B is divided."""
    xs = np.linspace(X0, X1, n + 1)
    ys = np.linspace(Y0, Y1, m + 1)
    zs = np.linspace(Z0, Z1, p + 1)
    lines = VGroup()

    def seg(a, b):
        lines.add(Line(np.array(a, dtype=float), np.array(b, dtype=float),
                       stroke_color=color, stroke_width=width))

    for x in xs:                              # cuts x = const
        seg((x, Y0, Z1), (x, Y1, Z1))         # on the top
        seg((x, Y0, Z0), (x, Y0, Z1))         # on the front
    for y in ys:                              # cuts y = const
        seg((X0, y, Z1), (X1, y, Z1))         # on the top
        seg((X1, y, Z0), (X1, y, Z1))         # on the right
    for z in zs:                              # cuts z = const
        seg((X0, Y0, z), (X1, Y0, z))         # on the front
        seg((X1, Y0, z), (X1, Y1, z))         # on the right
    return lines


# ----------------------------------------------------------- the small block
def small_block_card(color):
    """A flat close-up of one small block: its three visible faces, its
    dimensions, and the point at which the density is sampled."""
    s = 1.55                      # the front edges
    d = np.array([0.72, 0.5, 0])  # the receding edge, on screen
    O = ORIGIN
    front = Polygon(O, O + s * RIGHT, O + s * RIGHT + s * UP, O + s * UP)
    top = Polygon(O + s * UP, O + s * RIGHT + s * UP,
                  O + s * RIGHT + s * UP + d, O + s * UP + d)
    right = Polygon(O + s * RIGHT, O + s * RIGHT + d,
                    O + s * RIGHT + s * UP + d, O + s * RIGHT + s * UP)
    cube = VGroup(front, top, right)
    for f in cube:
        f.set_fill(color, opacity=1.0)
        f.set_stroke(HILITE, width=5)

    dx = MathTex(r"\Delta x", tex_template=TPL, color=INK, font_size=40)
    dx.next_to(front, DOWN, buff=0.18)
    dz = MathTex(r"\Delta z", tex_template=TPL, color=INK, font_size=40)
    dz.next_to(front, LEFT, buff=0.18)
    dy = MathTex(r"\Delta y", tex_template=TPL, color=INK, font_size=40)
    dy.move_to(O + s * RIGHT + 0.5 * d + np.array([0.55, -0.1, 0]))

    pt = Dot(O + np.array([0.5 * s, 0.5 * s, 0]) + 0.35 * d, radius=0.075,
             color=HILITE)
    pt_lab = MathTex(r"(x_i,\,y_j,\,z_k)", tex_template=TPL, color=HILITE,
                     font_size=38)
    pt_lab.next_to(pt, UP, buff=0.14).shift(0.55 * RIGHT)

    name = MathTex(r"B_{ijk}", tex_template=TPL, color=INK, font_size=44)
    name.next_to(top, UP, buff=0.3).shift(0.2 * LEFT)

    card = VGroup(cube, dx, dz, dy, pt, pt_lab, name)
    ring = Circle(radius=0.5 * max(card.width, card.height) + 0.5,
                  stroke_color=HILITE, stroke_width=3,
                  fill_color="#000000", fill_opacity=0.92)
    ring.move_to(card.get_center())
    return VGroup(ring, card)


class BlockMass(ThreeDScene):
    only = None                 # set by --still: render up to this beat

    # -------------------------------------------------------------- helpers
    def caption(self, *lines, edge=UP, buff=0.45, size=40):
        """A block of LaTeX prose, fixed to the frame."""
        block = VGroup(*[
            Tex(line, tex_template=TPL, font_size=size, color=INK)
            for line in lines
        ]).arrange(DOWN, buff=0.22).to_edge(edge, buff=buff)
        self.add_fixed_in_frame_mobjects(block)
        return block

    def formula(self, tex, edge=DOWN, buff=0.6, size=46, color=INK):
        f = MathTex(tex, tex_template=TPL, font_size=size, color=color)
        f.to_edge(edge, buff=buff)
        self.add_fixed_in_frame_mobjects(f)
        return f

    def clear_fixed(self, *mobs, run_time=0.6):
        self.play(*[FadeOut(m) for m in mobs if m is not None],
                  run_time=run_time)

    def stop_after(self, name):
        return self.only == name

    # ------------------------------------------------------------ the video
    def construct(self):
        self.camera.background_color = "#000000"
        for name, beat in (("question", self.beat_question),
                           ("chop", self.beat_chop),
                           ("one", self.beat_one_small_block),
                           ("sum", self.beat_add_them_up),
                           ("refine", self.beat_refine),
                           ("limit", self.beat_limit)):
            beat()
            if self.stop_after(name):
                return

    # 1 ---------------------------------------------------------------------
    def beat_question(self):
        self.set_camera_orientation(phi=64 * DEGREES, theta=-47 * DEGREES,
                                    zoom=0.7)
        self.block_shift = np.array([0.0, 0.0, 1.25])
        axes = ThreeDAxes(
            x_range=[-3, 3, 1], y_range=[-3, 3, 1], z_range=[-2, 2, 1],
            x_length=6, y_length=6, z_length=4,
            axis_config={"stroke_color": AXESC, "stroke_width": 1.6,
                         "include_ticks": False, "include_tip": False},
        ).shift(self.block_shift)
        self.smooth = smooth_block().shift(self.block_shift)

        title = self.caption(r"The Mass of a Block with Variable Density",
                             size=50)
        self.play(Create(axes, run_time=1.0), FadeIn(title))
        self.play(FadeIn(self.smooth), run_time=1.6)

        b_lab = MathTex(r"B", tex_template=TPL, color=INK, font_size=60)
        b_lab.move_to(np.array([-3.1, 1.7, 0.0]))
        self.add_fixed_in_frame_mobjects(b_lab)
        self.play(FadeIn(b_lab))

        intro = self.caption(
            r"A solid block $B$ whose density $\rho(x,y,z)$, the mass per"
            r" unit volume,",
            r"varies from point to point.  Darker means denser.",
            edge=DOWN, size=38,
        )
        self.play(FadeIn(intro))
        self.wait(3.0)
        self.clear_fixed(intro)

        const = self.formula(
            r"\text{If } \rho \text{ were constant:}\qquad"
            r" M = \rho \cdot (\text{volume of } B).",
            edge=DOWN, buff=1.35, size=42,
        )
        self.play(Write(const), run_time=1.4)
        self.wait(1.6)
        ask = self.caption(
            r"But $\rho$ changes from point to point.  What is the mass"
            r" $M$ of $B$?",
            edge=DOWN, buff=0.5, size=38,
        )
        self.play(FadeIn(ask))
        self.wait(2.6)
        self.clear_fixed(ask, const, title)
        self.axes, self.b_lab = axes, b_lab

    # 2 ---------------------------------------------------------------------
    def beat_chop(self):
        head = self.caption(r"Divide $B$ into tiny blocks", size=46)
        self.play(FadeIn(head))

        self.coarse_nmp = (5, 7, 4)
        self.cuts = grid_lines(*self.coarse_nmp).shift(self.block_shift)
        how = self.caption(
            r"Divide the $x$, $y$ and $z$ directions into $n$, $m$ and $p$"
            r" divisions.",
            edge=DOWN, buff=1.35, size=38,
        )
        self.play(FadeIn(how), Create(self.cuts), run_time=2.2)
        self.wait(1.4)
        self.clear_fixed(how)

        note = self.caption(
            r"This cuts $B$ into tiny blocks $B_{ijk}$, each $\Delta x$ by"
            r" $\Delta y$ by $\Delta z$, of volume",
            edge=DOWN, buff=1.35, size=38,
        )
        dv = self.formula(r"\Delta V = \Delta x\,\Delta y\,\Delta z.",
                          edge=DOWN, buff=0.55, size=46)
        self.play(FadeIn(note), Write(dv), run_time=1.4)
        self.wait(2.4)
        self.clear_fixed(note, dv, head)

    # 3 ---------------------------------------------------------------------
    def beat_one_small_block(self):
        head = self.caption(r"One tiny block $B_{ijk}$", size=46)
        self.play(FadeIn(head))

        n, m, p = self.coarse_nmp
        _, by_block = partition(n, m, p, stroke_width=0)
        idx = (n - 2, 0, p - 1)           # on the top front edge, fully visible
        chosen = by_block[idx].shift(self.block_shift)
        for f in chosen:
            f.set_stroke(HILITE, width=6)
        self.play(FadeIn(chosen), run_time=0.8)

        # a ring around it on screen, and a line to the magnified copy
        centre = self.camera.project_point(chosen.get_center())
        ring = Circle(radius=0.42, stroke_color=HILITE, stroke_width=3)
        ring.move_to(centre)
        self.add_fixed_in_frame_mobjects(ring)
        self.play(Create(ring), run_time=0.6)

        colour = chosen[0].get_fill_color()
        card = small_block_card(colour)
        card.scale(0.92).to_edge(RIGHT, buff=0.35).shift(DOWN * 0.25)
        lead = Line(ring.get_center() + 0.42 * normalize(
            card[0].get_center() - ring.get_center()),
            card[0].get_center() - card[0].radius * normalize(
                card[0].get_center() - ring.get_center()),
            stroke_color=HILITE, stroke_width=3)
        self.add_fixed_in_frame_mobjects(lead, card)
        self.play(Create(lead), FadeIn(card), run_time=1.0)
        self.wait(0.6)

        note = self.caption(
            r"On a block this tiny the density hardly changes,",
            r"so treat it as constant: its value at a point"
            r" $(x_i,\,y_j,\,z_k)$ of $B_{ijk}$.",
            edge=DOWN, buff=1.35, size=36,
        )
        self.play(FadeIn(note))
        self.wait(2.2)
        dm = self.formula(
            r"\text{mass of } B_{ijk} \;\approx\;"
            r" \rho(x_i,\,y_j,\,z_k)\,\Delta V"
            r" \;=\; \rho(x_i,\,y_j,\,z_k)\,\Delta x\,\Delta y\,\Delta z",
            edge=DOWN, buff=0.5, size=42,
        )
        self.play(Write(dm), run_time=1.8)
        self.wait(3.0)
        self.clear_fixed(note, dm, head, card, lead, ring)
        self.play(FadeOut(chosen), run_time=0.5)

    # 4 ---------------------------------------------------------------------
    def beat_add_them_up(self):
        head = self.caption(r"Add the masses of all the tiny blocks",
                            size=46)
        self.play(FadeIn(head))

        coarse, _ = partition(*self.coarse_nmp)
        coarse.shift(self.block_shift)
        self.play(FadeOut(self.cuts), FadeOut(self.smooth),
                  FadeIn(coarse), run_time=1.4)
        self.wait(0.6)

        rsum = self.formula(
            r"M \;\approx\; \sum_{k=1}^{p}\sum_{j=1}^{m}\sum_{i=1}^{n}"
            r" \rho(x_i,\,y_j,\,z_k)\,\Delta V",
            edge=DOWN, buff=0.55, size=46,
        )
        self.play(Write(rsum), run_time=2.0)
        name = self.caption(r"a \emph{triple Riemann sum}", edge=DOWN,
                            buff=2.0, size=40)
        self.play(FadeIn(name))
        self.wait(2.0)
        self.clear_fixed(name)
        note = self.caption(
            r"Only an estimate: inside each tiny block the true density",
            r"was replaced by a single value, the one at its sample point.",
            edge=DOWN, buff=2.0, size=36,
        )
        self.play(FadeIn(note))
        self.wait(3.0)
        self.clear_fixed(note, head)
        self.rsum, self.coarse = rsum, coarse

    # 5 ---------------------------------------------------------------------
    def beat_refine(self):
        head = self.caption(r"More divisions: $n$, $m$, $p$ grow", size=46)
        self.play(FadeIn(head))
        note = self.caption(
            r"The tiny blocks shrink ($\Delta x,\ \Delta y,\ \Delta z"
            r" \to 0$), the sum grows longer,",
            r"and the estimate gets better and better.",
            edge=DOWN, buff=2.0, size=36,
        )
        self.play(FadeIn(note))

        current = self.coarse
        for nmp, w in (((7, 10, 6), 1.5), ((10, 14, 8), 1.2),
                       ((15, 20, 12), 1.0), ((NSMOOTH,) * 3, 0.7)):
            finer, _ = partition(*nmp, stroke_width=w)
            finer.shift(self.block_shift)
            self.play(FadeOut(current), FadeIn(finer), run_time=0.9)
            self.wait(0.9)
            current = finer
        self.wait(1.2)
        self.clear_fixed(note, head)
        self.current = current

    # 6 ---------------------------------------------------------------------
    def beat_limit(self):
        head = self.caption(r"In the limit, the estimate becomes exact",
                            size=46)
        self.play(FadeIn(head))

        self.play(FadeOut(self.current), FadeIn(self.smooth), run_time=1.0)

        lim = MathTex(
            r"M \;=\; \lim_{n,\,m,\,p\to\infty}\;"
            r"\sum_{k=1}^{p}\sum_{j=1}^{m}\sum_{i=1}^{n}"
            r" \rho(x_i,\,y_j,\,z_k)\,\Delta V",
            tex_template=TPL, font_size=44, color=INK,
        ).to_edge(DOWN, buff=0.55)
        self.add_fixed_in_frame_mobjects(lim)
        self.play(FadeOut(self.rsum), FadeIn(lim), run_time=1.2)
        self.wait(2.2)

        final = MathTex(
            r"M \;=\; \iiint_B \rho(x,y,z)\,dV"
            r" \;=\; \iiint_B \rho(x,y,z)\,dx\,dy\,dz",
            tex_template=TPL, font_size=48, color=INK,
        ).to_edge(DOWN, buff=0.55)
        self.add_fixed_in_frame_mobjects(final)
        self.play(FadeOut(head), lim.animate.to_edge(UP, buff=0.45),
                  run_time=0.8)
        self.play(Write(final), run_time=1.6)
        self.wait(1.0)

        gloss = self.caption(
            r"The triple integral \emph{is} this limit:"
            r" $\sum\sum\sum$ becomes $\iiint$,",
            r"$\Delta V$ becomes $dV$, and the sample points fill all of $B$.",
            edge=DOWN, buff=1.9, size=36,
        )
        self.play(FadeIn(gloss))
        self.wait(3.4)
        self.clear_fixed(gloss, lim)

        closing = self.caption(
            r"The mass of $B$ is the triple integral of its density over"
            r" $B$.",
            edge=DOWN, buff=1.9, size=40,
        )
        self.play(FadeIn(closing))
        self.wait(3.2)
        self.clear_fixed(closing, final)

        # 7: the general form
        head = self.caption(r"In general", size=46)
        gen = self.formula(
            r"\iiint_E f(x,y,z)\,dV \;=\; \iiint_E f(x,y,z)\,dx\,dy\,dz",
            edge=DOWN, buff=0.55, size=48,
        )
        note = self.caption(
            r"The mass was one application.  For any $f(x,y,z)$ and any"
            r" solid $E$,",
            r"the triple integral is the same limit of the same kind of sum,",
            r"with $f$ in place of $\rho$.",
            edge=DOWN, buff=1.95, size=34,
        )
        self.play(FadeIn(head), Write(gen), run_time=1.6)
        self.play(FadeIn(note))
        self.wait(3.6)
        self.play(FadeOut(note), FadeOut(gen), FadeOut(head),
                  FadeOut(self.b_lab), FadeOut(self.smooth),
                  FadeOut(self.axes), run_time=0.9)
        self.wait(0.4)


def main(argv):
    still = None
    if "--still" in argv:
        still = argv[argv.index("--still") + 1]

    tmp = Path(tempfile.mkdtemp(prefix="block-mass-manim-"))
    config.media_dir = str(tmp)
    config.pixel_width, config.pixel_height = 1920, 1080
    config.frame_rate = 30
    config.background_color = "#000000"
    config.output_file = "block_mass_1080p"
    config.disable_caching = True

    if still:
        config.save_last_frame = True
        config.write_to_movie = False
        BlockMass.only = still
        BlockMass().render()
        png = next(tmp.rglob("*.png"))
        out = Path.cwd() / f"block_mass_{still}.png"
        shutil.move(str(png), str(out))
        print(f"wrote {out}")
        return

    BlockMass().render()
    produced = next(tmp.rglob("block_mass_1080p.mp4"))
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(produced), str(OUT_FILE))
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"wrote {OUT_FILE}")


if __name__ == "__main__":
    main(sys.argv[1:])
