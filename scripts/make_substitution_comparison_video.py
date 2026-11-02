#!/usr/bin/env python3
"""Side-by-side Manim explanation of substitution in one and two variables.

Run: python scripts/make_substitution_comparison_video.py
Produces assets/videos/substitution_comparison_1080p.mp4 (1080p, 30fps, silent).
The typography and palette follow make_stokes_proof_idea_video.py.
The local graphs use x=u^2 near u=1, and (x,y)=(u^2,v) near (1,v_0).
Finite ratios are 2+Delta u; zooming makes their common limit 2 visible.
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


def axes_at(origin, xrange, yrange, unit=1):
    """Equal physical units on both axes, also shared by the two area plots."""
    axes = Axes(x_range=[*xrange, 1], y_range=[*yrange, 1],
                x_length=unit * (xrange[1] - xrange[0]),
                y_length=unit * (yrange[1] - yrange[0]), tips=False,
                axis_config={"include_ticks": False, "stroke_color": GREY,
                             "stroke_width": 1.4})
    axes.shift(np.array(origin) - axes.c2p(0, 0))
    return axes


def graph_curve(axes, function, start, stop, color=BLUE):
    return VMobject(color=color, stroke_width=3).set_points_smoothly(
        [axes.c2p(t, function(t)) for t in np.linspace(start, stop, 70)])


def cell(axes, width, height, color, lower=(0, 0)):
    x, y = lower
    return Polygon(axes.c2p(x, y), axes.c2p(x+width, y),
                   axes.c2p(x+width, y+height), axes.c2p(x, y+height),
                   color=color, fill_opacity=.28, stroke_width=3)


def interval_global(epsilon):
    axes = axes_at([-4.95, -1.85, 0], (0, 1.8), (0, 3.2))
    curve = graph_curve(axes, lambda u: u*u, 0, 1.75)
    start, corner, end = axes.c2p(1, 1), axes.c2p(1+epsilon, 1), axes.c2p(1+epsilon, (1+epsilon)**2)
    horizontal = Line(start, corner, color=BLUE, stroke_width=6)
    vertical = Line(corner, end, color=ORANGE, stroke_width=6)
    focus = SurroundingRectangle(VGroup(horizontal, vertical), buff=.13, color=PURPLE, stroke_width=2)
    labels = VGroup(math("u", 25).next_to(axes.x_axis, RIGHT, buff=.1),
                    math("x", 25).next_to(axes.y_axis, UP, buff=.1),
                    math(r"\Delta u", 22, BLUE).next_to(horizontal, DOWN, buff=.1),
                    math(r"\Delta x", 22, ORANGE).next_to(vertical, RIGHT, buff=.1),
                    math("(1,1)", 23).next_to(Dot(start), LEFT, buff=.12))
    return VGroup(axes, curve, horizontal, vertical, Dot(start, radius=.045),
                  Dot(end, radius=.045, color=ORANGE), focus, labels)


def interval_zoom(epsilon):
    # Coordinates are offsets from (1,1), magnified by 1/epsilon:
    # (x-1)/epsilon = 2q + epsilon*q^2, q=(u-1)/epsilon.
    axes = axes_at([-4.65, -1.85, 0], (-.2, 1.45), (-.2, 3.2), unit=.95)
    curve = always_redraw(lambda: graph_curve(
        axes, lambda q: 2*q + epsilon.get_value()*q*q, -.12, 1.24))
    tangent = DashedLine(axes.c2p(-.12, -.24), axes.c2p(1.24, 2.48),
                         color=PURPLE, stroke_width=2, dash_length=.07)
    horizontal = Line(axes.c2p(0, 0), axes.c2p(1, 0), color=BLUE, stroke_width=6)
    vertical = always_redraw(lambda: Line(
        axes.c2p(1, 0), axes.c2p(1, 2+epsilon.get_value()), color=ORANGE, stroke_width=6))
    endpoint = always_redraw(lambda: Dot(axes.c2p(1, 2+epsilon.get_value()), radius=.045, color=ORANGE))
    dx = always_redraw(lambda: math(r"\Delta x", 25, ORANGE).next_to(vertical, RIGHT, buff=.13))
    labels = VGroup(math(r"\Delta u", 25, BLUE).next_to(horizontal, DOWN, buff=.15),
                    math("(1,1)", 21).next_to(Dot(axes.c2p(0, 0)), LEFT, buff=.14),
                    words("tangent slope 2", 23, PURPLE).move_to([-2.55, .85, 0]),
                    math("u", 24).next_to(axes.x_axis, RIGHT, buff=.1),
                    math("x", 24).next_to(axes.y_axis, UP, buff=.1))
    return VGroup(axes, tangent, curve, horizontal, vertical, endpoint, dx, labels)


def area_global(epsilon):
    plots = VGroup()
    for origin, transformed in (([.5, -1.35, 0], False), ([3.8, -1.35, 0], True)):
        axes = axes_at(origin, (0, 2.55), (0, 1.6))
        grid = VGroup()
        for t in np.linspace(0, 1.5, 7):
            x = t*t if transformed else t
            grid.add(Line(axes.c2p(x, 0), axes.c2p(x, 1.5), stroke_width=1, color=GREY))
            grid.add(Line(axes.c2p(0, t), axes.c2p(2.25 if transformed else 1.5, t),
                          stroke_width=1, color=GREY))
        width = 2*epsilon + epsilon*epsilon if transformed else epsilon
        patch = cell(axes, width, epsilon, ORANGE if transformed else BLUE, lower=(1, .5))
        focus = SurroundingRectangle(patch, buff=.09, color=PURPLE, stroke_width=2)
        labels = VGroup(math("x" if transformed else "u", 24).next_to(axes.x_axis, RIGHT, buff=.08),
                        math("y" if transformed else "v", 24).next_to(axes.y_axis, UP, buff=.08),
                        words("old coordinates" if transformed else "new coordinates", 22).move_to(
                            [origin[0]+1.2, .75, 0]))
        plots.add(VGroup(axes, grid, patch, focus, labels))
    plots.add(Arrow([3.05, -.65, 0], [3.65, -.65, 0], color=PURPLE, buff=.06))
    return plots


def area_zoom(epsilon):
    uv = axes_at([.5, -1.35, 0], (-.15, 2.55), (-.15, 1.65))
    xy = axes_at([3.8, -1.35, 0], (-.15, 2.55), (-.15, 1.65))
    source = cell(uv, 1, 1, BLUE)
    image = always_redraw(lambda: cell(xy, 2+epsilon.get_value(), 1, ORANGE))
    source_grid = VGroup()
    for t in (.25, .5, .75):
        source_grid.add(Line(uv.c2p(t, 0), uv.c2p(t, 1), color=BLUE, stroke_width=1),
                        Line(uv.c2p(0, t), uv.c2p(1, t), color=BLUE, stroke_width=1))

    def image_grid():
        lines = VGroup()
        e = epsilon.get_value()
        for t in (.25, .5, .75):
            lines.add(Line(xy.c2p(2*t+e*t*t, 0), xy.c2p(2*t+e*t*t, 1), color=ORANGE, stroke_width=1),
                      Line(xy.c2p(0, t), xy.c2p(2+e, t), color=ORANGE, stroke_width=1))
        return lines

    grid = always_redraw(image_grid)
    labels = VGroup(
        math(r"\Delta u", 24, BLUE).move_to(uv.c2p(.5, -.33)),
        math(r"\Delta v", 23, BLUE).rotate(PI/2).move_to(uv.c2p(-.24, .5)),
        math(r"\Delta x", 24, ORANGE).move_to(xy.c2p(1.1, -.33)),
        math(r"\Delta y=\Delta v", 20, ORANGE).rotate(PI/2).move_to(xy.c2p(-.25, .5)),
        math(r"\Delta u\,\Delta v", 23, BLUE).move_to(uv.c2p(.5, 1.25)),
        math(r"\Delta x\,\Delta y", 23, ORANGE).move_to(xy.c2p(1.1, 1.25)),
        math(r"(1,v_0)", 18).move_to(uv.c2p(-.12, -.48)),
        math(r"(1,v_0)", 18).move_to(xy.c2p(-.12, -.48)),
        words("new coordinates", 22).move_to([1.7, .75, 0]),
        words("old coordinates", 22).move_to([5, .75, 0]),
        math("u", 23).next_to(uv.x_axis, RIGHT, buff=.07),
        math("v", 23).next_to(uv.y_axis, UP, buff=.07),
        math("x", 23).next_to(xy.x_axis, RIGHT, buff=.07),
        math("y", 23).next_to(xy.y_axis, UP, buff=.07))
    arrow = Arrow([3.05, -.8, 0], [3.6, -.8, 0], color=PURPLE, buff=.05)
    origins = VGroup(Dot(uv.c2p(0, 0), radius=.035), Dot(xy.c2p(0, 0), radius=.035))
    return VGroup(uv, xy, source, image, source_grid, grid, labels, arrow, origins)


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

        # Start with actual coordinate graphs, select corresponding pieces,
        # then magnify the pieces instead of presenting detached shapes.
        self.play(FadeOut(maps))
        examples = pair(r"x=u^2,\quad u\approx1", r"x=u^2,\quad y=v,\quad u\approx1", 1.85, 30)
        note = caption("2. Select a small interval and a small rectangle near u = 1.")
        coarse_interval = interval_global(.4)
        coarse_area = area_global(.4)
        self.play(Write(examples), FadeIn(note))
        self.play(FadeIn(coarse_interval), FadeIn(coarse_area), run_time=3)
        self.wait(4)
        epsilon = ValueTracker(.4)
        zoom_interval = interval_zoom(epsilon)
        zoom_area = area_zoom(epsilon)
        zoom_note = caption("Zoom into the highlighted pieces; use the same scale on corresponding axes.")
        self.play(ReplacementTransform(coarse_interval, zoom_interval),
                  ReplacementTransform(coarse_area, zoom_area),
                  ReplacementTransform(note, zoom_note), run_time=3)
        ratio1 = math(r"\frac{\Delta x}{\Delta u}=", 30).move_to([-4.05, -2.7, 0])
        ratio2 = math(r"\frac{\Delta x\,\Delta y}{\Delta u\,\Delta v}=", 30).move_to([2.95, -2.7, 0])
        number1 = DecimalNumber(2.4, num_decimal_places=3, font_size=32).next_to(ratio1, RIGHT, buff=.15)
        number2 = DecimalNumber(2.4, num_decimal_places=3, font_size=32).next_to(ratio2, RIGHT, buff=.15)
        number1.add_updater(lambda m: m.set_value(2+epsilon.get_value()).next_to(ratio1, RIGHT, buff=.15))
        number2.add_updater(lambda m: m.set_value(2+epsilon.get_value()).next_to(ratio2, RIGHT, buff=.15))
        ratios = VGroup(ratio1, ratio2, number1, number2)
        self.play(FadeIn(ratios))
        self.wait(3)
        limit_note = caption("Shrink the pieces and magnify further: both ratios approach 2.")
        self.play(ReplacementTransform(zoom_note, limit_note))
        self.play(epsilon.animate.set_value(.1), run_time=3, rate_func=smooth)
        self.wait(2)
        self.play(epsilon.animate.set_value(.02), run_time=3, rate_func=smooth)
        self.wait(2)
        # Freeze, then retain the enlarged local pictures during the formulas.
        zoom_interval.clear_updaters(recursive=True)
        zoom_area.clear_updaters(recursive=True)
        ratios.clear_updaters(recursive=True)
        local1 = math(r"\Delta x\approx2\Delta u", 29, ORANGE).move_to([-3.55, -2.7, 0])
        local2 = math(r"\Delta x\,\Delta y\approx2\Delta u\,\Delta v", 29, ORANGE).move_to([3.55, -2.7, 0])
        final_note = caption("In the limit: dx = 2 du, and dx dy = 2 du dv at u = 1.")
        self.play(FadeOut(ratios), FadeIn(local1, local2), ReplacementTransform(limit_note, final_note))
        self.wait(5)
        insets = VGroup(zoom_interval, zoom_area)
        self.play(zoom_interval.animate.scale(.5).move_to([-3.55, -1.6, 0]),
                  zoom_area.animate.scale(.65).move_to([3.55, -1.6, 0]),
                  FadeOut(examples, local1, local2, final_note), FadeIn(maps), run_time=2)

        factors = pair(r"dx=h'(u)\,du", r"dA=\left|\frac{\partial(x,y)}{\partial(u,v)}\right|\,du\,dv", .75, 34, ORANGE)
        labels = VGroup(words(r"$h'(1)=2$ in the graph below", 25).move_to([-3.55, -.05, 0]),
                        words(r"$J(u,v)=\frac{\partial(x,y)}{\partial(u,v)}$; $J(1,v)=2$ below", 25).move_to([3.55, -.05, 0]))
        note = caption("The enlarged local pictures stay: a length scale becomes an area scale.")
        self.play(Write(factors), FadeIn(labels, note), run_time=3)
        self.wait(6)
        self.play(FadeOut(labels, factors, note))

        # Function values and measure must both be transformed.
        values = pair(r"f(x)\longrightarrow f(h(u))", r"F(x,y)\longrightarrow F(T(u,v))", .75, 31, BLUE)
        pieces = pair(r"f(h(u))\,h'(u)\,\Delta u", r"F(T(u,v))\,|J(u,v)|\,\Delta u\,\Delta v", -.05, 30)
        note = caption("3. Same function value at the same point; multiply by the new piece size.")
        self.play(Write(values), FadeIn(note), run_time=2)
        self.wait(3)
        self.play(Write(pieces), run_time=2)
        self.wait(5)
        self.play(FadeOut(values, pieces, note, maps))

        # Keep the correspondence readable instead of one long double integral.
        one = math(r"\int_{h(a)}^{h(b)} f(x)\,dx", 36).move_to([-3.55, 1.65, 0])
        two = math(r"\iint_R F(x,y)\,dA", 36).move_to([3.55, 1.65, 0])
        eqs = pair("=", "=", .9, 34)
        newone = math(r"\int_a^b f(h(u))\,h'(u)\,du", 32).move_to([-3.55, .15, 0])
        newtwo = math(r"\iint_S F(T(u,v))\,\left|\frac{\partial(x,y)}{\partial(u,v)}\right|\,du\,dv", 29).move_to([3.55, .15, 0])
        steps = words("New domain. Same function at mapped points. Local scale factor.", 25).move_to([0, -2.95, 0])
        note = caption("4. Add up all the small contributions: the integral is unchanged.")
        self.play(Write(one), Write(two), FadeIn(note), run_time=2)
        self.play(Write(eqs), Write(newone), Write(newtwo), run_time=3)
        self.play(FadeIn(steps))
        self.wait(8)
        self.play(FadeOut(one, two, eqs, newone, newtwo, steps, note, insets, left, right, divider))

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
