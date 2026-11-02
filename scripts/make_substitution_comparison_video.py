#!/usr/bin/env python3
"""Side-by-side Manim explanation of substitution in one and two variables.

Run: python scripts/make_substitution_comparison_video.py
Produces assets/videos/substitution_comparison_1080p.mp4 (1080p, 30fps, silent).
The typography and palette follow make_stokes_proof_idea_video.py.
"""
import shutil
import tempfile
from pathlib import Path

import numpy as np
from manim import *

OUT = Path(__file__).resolve().parents[1] / "assets/videos/substitution_comparison_1080p.mp4"
BLUE = "#2e9aff"
ORANGE = "#ff862f"
PURPLE = "#c77dff"
GREY = "#7f7f7f"
TPL = TexTemplate(preamble=r"\usepackage{amsmath}\usepackage{amssymb}")


def words(s, size=30, color=WHITE):
    return Tex(s, tex_template=TPL, font_size=size, color=color)


def math(s, size=36, color=WHITE):
    return MathTex(s, tex_template=TPL, font_size=size, color=color)


class SubstitutionComparison(Scene):
    def construct(self):
        self.camera.background_color = BLACK
        title = words("Change of variables: the same idea in two dimensions", 38).to_edge(UP, buff=.3)
        left = words("Single integral", 32, BLUE).move_to([-3.55, 2.65, 0])
        right = words("Double integral", 32, BLUE).move_to([3.55, 2.65, 0])
        divider = Line([0, 2.3, 0], [0, -2.65, 0], color=GREY, stroke_width=1)
        self.play(Write(title), FadeIn(left, right), Create(divider), run_time=2)
        self.wait(2)

        def pair(a, b, y, size=36, color=WHITE):
            return VGroup(math(a, size, color).move_to([-3.55, y, 0]),
                          math(b, size, color).move_to([3.55, y, 0]))

        def caption(s):
            return words(s, 29).to_edge(DOWN, buff=.35)

        # Read both maps in the same direction: new coordinates to old ones.
        maps = pair(r"u\longmapsto x=h(u)", r"(u,v)\longmapsto (x,y)=T(u,v)", 1.65, 32, PURPLE)
        domains = pair(r"[a,b]\longmapsto [h(a),h(b)]", r"S\longmapsto R", .65, 32)
        sub = words(r"where $T(u,v)=(f(u,v),g(u,v))$", 24).move_to([3.55, -.05, 0])
        note = caption("1. Describe the same points using new coordinates.")
        self.play(Write(maps), FadeIn(note), run_time=2)
        self.play(Write(domains), FadeIn(sub), run_time=2)
        self.wait(5)
        self.play(FadeOut(domains, sub, note))

        # The local measure factors, illustrated with affine maps so the
        # displayed ratios are exact, before stating the local general case.
        examples = pair(r"x=2u", r"T(u,v)=(2u+v,v)", .75, 32)
        note = caption("2. A small piece changes size when the coordinates change.")
        self.play(Write(examples), FadeIn(note))
        uline = Line([-5.5, -.5, 0], [-4.5, -.5, 0], color=BLUE, stroke_width=8)
        xline = Line([-5.5, -1.5, 0], [-3.5, -1.5, 0], color=ORANGE, stroke_width=8)
        ulab = math(r"\Delta u", 28, BLUE).next_to(uline, UP, buff=.16)
        xlab = math(r"\Delta x=2\Delta u", 28, ORANGE).next_to(xline, DOWN, buff=.16)
        arr = Arrow([-2.2, -.4, 0], [-2.2, -1.6, 0], color=PURPLE, buff=.1)
        ratio1 = math(r"\frac{\Delta x}{\Delta u}=2", 32).move_to([-3.55, -2.5, 0])
        origin = np.array([1.2, -1.5, 0])
        square = Polygon(origin, origin+RIGHT, origin+RIGHT+UP, origin+UP,
                         color=BLUE, fill_opacity=.3, stroke_width=3)
        target = np.array([3.4, -1.5, 0])
        para = Polygon(target, target+2*RIGHT, target+3*RIGHT+UP, target+RIGHT+UP,
                       color=ORANGE, fill_opacity=.3, stroke_width=3)
        slab = math(r"\Delta u\,\Delta v", 27, BLUE).next_to(square, UP, buff=.18)
        plab = math(r"\Delta A=2\Delta u\,\Delta v", 27, ORANGE).next_to(para, DOWN, buff=.18)
        ratio2 = math(r"\frac{\Delta A}{\Delta u\,\Delta v}=2", 32).move_to([3.55, -2.5, 0])
        self.play(Create(uline), Write(ulab), Create(square), Write(slab), run_time=2)
        self.play(TransformFromCopy(uline, xline), TransformFromCopy(square, para),
                  Create(arr), Write(xlab), Write(plab), run_time=3)
        self.play(Write(ratio1), Write(ratio2))
        self.wait(5)
        geometry = VGroup(uline, xline, ulab, xlab, arr, square, para, slab, plab, ratio1, ratio2, examples)
        self.play(FadeOut(geometry, note))

        factors = pair(r"dx=h'(u)\,du", r"dA=\left|\frac{\partial(x,y)}{\partial(u,v)}\right|\,du\,dv", .75, 34, ORANGE)
        labels = VGroup(words("local length scale", 28).move_to([-3.55, -.05, 0]),
                        words("local area scale", 28).move_to([3.55, -.05, 0]))
        jac = VGroup(
            math(r"J(u,v)=\frac{\partial(x,y)}{\partial(u,v)}", 31),
            math(r"=\begin{vmatrix}\frac{\partial x}{\partial u}&\frac{\partial x}{\partial v}\\[.4em]\frac{\partial y}{\partial u}&\frac{\partial y}{\partial v}\end{vmatrix}", 29),
        ).arrange(DOWN, buff=.18).move_to([3.55, -1.45, 0])
        assumption = words(r"For the length picture, take $h'(u)>0$.", 24).move_to([-3.55, -1.15, 0])
        note = caption("For nonlinear maps, these are local scales: zoom in on a tiny piece.")
        self.play(Write(factors), FadeIn(labels, assumption, note), Write(jac), run_time=3)
        self.wait(6)
        self.play(FadeOut(labels, assumption, jac, note))

        # Function values and measure must both be transformed.
        values = pair(r"f(x)\longrightarrow f(h(u))", r"F(x,y)\longrightarrow F(T(u,v))", -.35, 31, BLUE)
        pieces = pair(r"f(h(u))\,h'(u)\,\Delta u", r"F(T(u,v))\,|J(u,v)|\,\Delta u\,\Delta v", -1.45, 30)
        note = caption("3. Same function value at the same point; multiply by the new piece size.")
        self.play(Write(values), FadeIn(note), run_time=2)
        self.wait(3)
        self.play(Write(pieces), run_time=2)
        self.wait(5)
        self.play(FadeOut(values, pieces, factors, note, maps))

        # Keep the correspondence readable instead of one long double integral.
        one = math(r"\int_{h(a)}^{h(b)} f(x)\,dx", 38).move_to([-3.55, 1.45, 0])
        two = math(r"\iint_R F(x,y)\,dA", 38).move_to([3.55, 1.45, 0])
        eqs = pair("=", "=", .55, 36)
        newone = math(r"\int_a^b f(h(u))\,h'(u)\,du", 34).move_to([-3.55, -.35, 0])
        newtwo = math(r"\iint_S F(T(u,v))\,\left|\frac{\partial(x,y)}{\partial(u,v)}\right|\,du\,dv", 30).move_to([3.55, -.35, 0])
        steps = words("New domain. Same function at mapped points. Local scale factor.", 29).move_to([0, -2.1, 0])
        note = caption("4. Add up all the small contributions: the integral is unchanged.")
        self.play(Write(one), Write(two), FadeIn(note), run_time=2)
        self.play(Write(eqs), Write(newone), Write(newtwo), run_time=3)
        self.play(FadeIn(steps))
        self.wait(8)
        self.play(FadeOut(one, two, eqs, newone, newtwo, steps, note, left, right, divider))

        # Connect to the familiar forward u-substitution in the cited text.
        familiar = words("The familiar substitution writes the map the other way", 34).move_to([0, 2, 0])
        forward = math(r"u=g(x),\qquad du=g'(x)\,dx", 40).move_to([0, .95, 0])
        identity = math(r"\int_a^b f(g(x))\,g'(x)\,dx=\int_{g(a)}^{g(b)}f(u)\,du", 35).move_to([0, -.1, 0])
        inverse = words(r"Where $h=g^{-1}$: $x=h(u)$ and $dx=h'(u)\,du$.", 31).move_to([0, -1.15, 0])
        orient = words(r"Single integrals use signed derivatives and oriented limits.\\"
                       r"Double integrals use $|J(u,v)|$ because area is nonnegative.", 28).move_to([0, -2.3, 0])
        self.play(FadeIn(familiar), Write(forward), run_time=2)
        self.play(Write(identity), run_time=2)
        self.play(FadeIn(inverse), run_time=1)
        self.wait(5)
        self.play(FadeIn(orient))
        self.wait(7)
        self.play(FadeOut(familiar, forward, identity, inverse, orient))
        takeaway = words(r"The derivative scales length.\\The Jacobian determinant scales area.", 44).move_to([0, .5, 0])
        closing = words("Change coordinates, change the small piece, keep the integral.", 30).move_to([0, -1.3, 0])
        self.play(Write(takeaway), FadeIn(closing), run_time=3)
        self.wait(6)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="substitution-manim-") as temp:
        with tempconfig({"media_dir": temp, "pixel_width": 1920,
                         "pixel_height": 1080, "frame_rate": 30,
                         "background_color": BLACK, "disable_caching": True,
                         "output_file": "substitution_comparison"}):
            scene = SubstitutionComparison()
            scene.render()
            OUT.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(scene.renderer.file_writer.movie_file_path, OUT)
    print(OUT)
