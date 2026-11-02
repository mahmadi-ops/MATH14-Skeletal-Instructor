#!/usr/bin/env python3
"""Compare local intervals with local parallelograms, using Manim.

Run: python scripts/make_substitution_comparison_video.py
Output: assets/videos/substitution_rectangles_parallelograms_1080p.mp4 (1080p, 30fps, silent).
Style follows make_stokes_proof_idea_video.py. The 2D construction follows
fig-jacobian-area-manim: a grid rectangle, its genuinely curved image,
and the tangent parallelogram spanned by T_u Delta u and T_v Delta v.

The illustrative map is T(u,v)=(2u+v+0.3v^2, v+0.3u^2), on [-.75,.75]^2.
It is independent of the later hyperbola exercise. At the selected corner
(0,0), T_u=(2,0), T_v=(1,1), and J=2. Both grid families have curved images.
The orange area is measured from the sampled image boundary, not from the
violet parallelogram. Its ratio tends to 2 as the selected cell shrinks.
"""
import shutil
import tempfile
from pathlib import Path

import numpy as np
from manim import *

OUT = Path(__file__).resolve().parents[1] / 'assets/videos/substitution_rectangles_parallelograms_1080p.mp4'
BLUE, RED = '#2e9aff', '#fc6255'
ORANGE, PURPLE, GREY = '#ff862f', '#c77dff', '#7f7f7f'
TPL = TexTemplate(preamble=r'\usepackage{amsmath}\usepackage{amssymb}')


def words(s, size=30, color=WHITE):
    return Tex(s, tex_template=TPL, font_size=size, color=color)


def math(s, size=36, color=WHITE):
    return MathTex(s, tex_template=TPL, font_size=size, color=color)


def axes_at(origin, xrange, yrange, unit=1):
    axes = Axes(x_range=[*xrange, 1], y_range=[*yrange, 1],
                x_length=unit*(xrange[1]-xrange[0]),
                y_length=unit*(yrange[1]-yrange[0]), tips=False,
                axis_config={'include_ticks': False, 'stroke_color': GREY,
                             'stroke_width': 1.3})
    axes.shift(np.array(origin)-axes.c2p(0, 0))
    return axes


def curve(axes, points, color, width=2):
    return VMobject(color=color, stroke_width=width).set_points_smoothly(
        [axes.c2p(float(p[0]), float(p[1])) for p in points])


def ratio(label, value, center, color=ORANGE):
    lhs = math(label+'=', 32)
    number = DecimalNumber(value(), num_decimal_places=4, font_size=32, color=color)
    group = VGroup(lhs, number).arrange(RIGHT, buff=.15).move_to(center)

    def update(m):
        target = value()
        if abs(m.get_value()-target) > .000005:
            m.set_value(target)
        m.next_to(lhs, RIGHT, buff=.15)
    number.add_updater(update)
    return group


def interval_view(epsilon, zoomed=False):
    axes = axes_at([-4.7, -1.65, 0], (-.15, 1.45) if zoomed else (0, 1.8),
                   (-.2, 3.2) if zoomed else (0, 3.2), unit=.95)

    def geometry():
        e = epsilon.get_value()
        t = np.linspace(-.12, 1.24, 70) if zoomed else np.linspace(0, 1.75, 70)
        f = (lambda q: 2*q+e*q*q) if zoomed else (lambda u: u*u)
        graph = curve(axes, np.column_stack((t, f(t))), BLUE, 3)
        a = (0, 0) if zoomed else (1, 1)
        b = (1, 0) if zoomed else (1+e, 1)
        c = (1, 2+e) if zoomed else (1+e, (1+e)**2)
        horizontal = Line(axes.c2p(*a), axes.c2p(*b), color=BLUE, stroke_width=6)
        vertical = Line(axes.c2p(*b), axes.c2p(*c), color=ORANGE, stroke_width=6)
        labels = VGroup(math(r'\Delta u', 25, BLUE).next_to(horizontal, DOWN, buff=.12),
                        math(r'\Delta x', 25, ORANGE).next_to(vertical, RIGHT, buff=.13),
                        math('(1,1)', 21).next_to(Dot(axes.c2p(*a)), LEFT, buff=.14))
        result = VGroup(graph, horizontal, vertical, labels,
                        Dot(axes.c2p(*c), radius=.04, color=ORANGE))
        if zoomed:
            tangent = DashedLine(axes.c2p(-.12, -.24), axes.c2p(1.24, 2.48),
                                 color=PURPLE, stroke_width=3, dash_length=.07)
            result.add_to_back(tangent)
        else:
            result.add(SurroundingRectangle(VGroup(horizontal, vertical),
                                           buff=.13, color=PURPLE, stroke_width=2))
        return result
    axes_labels = VGroup(math('u', 24).next_to(axes.x_axis, RIGHT, buff=.1),
                         math('x', 24).next_to(axes.y_axis, UP, buff=.1))
    return VGroup(axes, always_redraw(geometry), axes_labels)


def interval_bars(epsilon):
    origin, unit = np.array([.8, 1, 0]), 1.15
    source = Line(origin, origin+unit*RIGHT, color=BLUE, stroke_width=7)
    actual = always_redraw(lambda: Line(origin+DOWN,
        origin+DOWN+(2+epsilon.get_value())*unit*RIGHT, color=ORANGE, stroke_width=7))
    model = Line(origin+2*DOWN, origin+2*DOWN+2*unit*RIGHT, color=PURPLE, stroke_width=7)
    labels = VGroup(
        math(r'\Delta u', 27, BLUE).next_to(source, UP, buff=.13),
        math(r'\Delta x', 27, ORANGE).move_to([2.2, .35, 0]),
        math(r"h'(1)\,\Delta u", 27, PURPLE).next_to(model, UP, buff=.13),
        words('input interval', 25).move_to([4.9, 1, 0]),
        words('true image', 25, ORANGE).move_to([4.9, 0, 0]),
        words('tangent prediction', 25, PURPLE).move_to([4.9, -1, 0]))
    return VGroup(source, actual, model, labels)


def transform(u, v):
    return np.array([2*u+v+.3*v*v, v+.3*u*u])


def rectangle_ring(h, samples=100):
    t = np.linspace(0, 1, samples, endpoint=False)
    return np.concatenate((np.column_stack((h*t, 0*t)),
        np.column_stack((0*t+h, h*t)), np.column_stack((h*(1-t), 0*t+h)),
        np.column_stack((0*t, h*(1-t)))))


def image_area_ratio(h):
    ring = rectangle_ring(h, 160)
    points = transform(ring[:, 0], ring[:, 1]).T
    points -= points[0]
    area = abs(np.sum(points[:, 0]*np.roll(points[:, 1], -1)
                      -points[:, 1]*np.roll(points[:, 0], -1)))/2
    return float(area/(h*h))


def area_view(h_tracker, zoomed=False, show_model=False):
    # Both plots use the same units. Zoom magnifies BOTH by 1/h.
    if zoomed:
        uv = axes_at([-4.65, -.85, 0], (-.2, 1.4), (-.2, 1.45), 1.1)
        xy = axes_at([1.45, -.85, 0], (-.6, 3.9), (-.35, 1.65), 1.1)
    else:
        uv = axes_at([-4.4, -.1, 0], (-1, 1), (-1, 1.2), 1.25)
        xy = axes_at([2, -.1, 0], (-2.35, 2.7), (-1, 1.3), 1.25)

    def geometry():
        h = h_tracker.get_value()
        side = 1 if zoomed else h
        if zoomed:
            positions, lo, hi = [0, 1], -.18, 1.18
            def mapped(u, v):
                return transform(h*u, h*v)/h
        else:
            # Keep the selected [0,h] x [0,h] rectangle a grid cell even
            # between the discrete refinement levels during an animation.
            interior = np.arange(np.ceil(-.75/h), np.floor(.75/h)+1)*h
            positions, lo, hi = np.unique(np.r_[interior, -.75, .75]), -.75, .75
            mapped = transform
        uv_grid, xy_grid = VGroup(), VGroup()
        t = np.linspace(lo, hi, 55)
        for p in positions:
            for points, color in ((np.column_stack((t, 0*t+p)), BLUE),
                                  (np.column_stack((0*t+p, t)), RED)):
                uv_grid.add(curve(uv, points, color, 1).set_stroke(opacity=.4))
                xy_grid.add(curve(xy, mapped(points[:, 0], points[:, 1]).T, color, 1.3).set_stroke(opacity=.45))
        source = Polygon(uv.c2p(0, 0), uv.c2p(side, 0), uv.c2p(side, side), uv.c2p(0, side),
                         color=ORANGE, fill_opacity=.24, stroke_width=2.5)
        ring = rectangle_ring(h, 36)
        image = transform(ring[:, 0], ring[:, 1]).T/(h if zoomed else 1)
        patch = Polygon(*[xy.c2p(*p) for p in image], color=ORANGE,
                        fill_opacity=.25, stroke_width=3)
        source_edges = VGroup(
            Arrow(uv.c2p(0, 0), uv.c2p(side, 0), buff=0, color=BLUE, stroke_width=4),
            Arrow(uv.c2p(0, 0), uv.c2p(0, side), buff=0, color=RED, stroke_width=4))
        result = VGroup(uv_grid, xy_grid, source, patch, source_edges)
        if show_model:
            vertices = [xy.c2p(0, 0), xy.c2p(2*side, 0),
                        xy.c2p(3*side, side), xy.c2p(side, side)]
            fill = Polygon(*vertices, color=PURPLE, stroke_width=0, fill_opacity=.12)
            outline = DashedVMobject(Polygon(*vertices, color=PURPLE, fill_opacity=0,
                                             stroke_width=4), num_dashes=32)
            vectors = VGroup(
                Arrow(vertices[0], vertices[1], buff=0, color=BLUE, stroke_width=5),
                Arrow(vertices[0], vertices[3], buff=0, color=RED, stroke_width=5))
            result.add(fill, outline, vectors)
        du = math(r'\Delta u', 25, BLUE).next_to(source_edges[0], DOWN, buff=.12)
        dv = math(r'\Delta v', 25, RED).next_to(source_edges[1], LEFT, buff=.12)
        result.add(du, dv, Dot(uv.c2p(0, 0), radius=.045), Dot(xy.c2p(0, 0), radius=.045))
        if show_model:
            result.add(math(r'T_u\,\Delta u', 25, BLUE).move_to(xy.c2p(side, -.25*side)),
                       math(r'T_v\,\Delta v', 25, RED).rotate(PI/4).move_to(xy.c2p(.2*side, .75*side)))
        return result

    labels = VGroup(
        math('u', 24).next_to(uv.x_axis, RIGHT, buff=.1),
        math('v', 24).next_to(uv.y_axis, UP, buff=.1),
        math('x', 24).next_to(xy.x_axis, RIGHT, buff=.1),
        math('y', 24).next_to(xy.y_axis, UP, buff=.1),
        math('p=(u_0,v_0)', 23).move_to(uv.c2p(-.18, -.48 if zoomed else -.38)),
        math('T(p)', 23).move_to(xy.c2p(-.05, -.48 if zoomed else -.38)))
    arrow = Arrow([-2.75, .1, 0], [-1.35, .1, 0], buff=.05, color=WHITE)
    labels.add(math('T', 30).next_to(arrow, UP, buff=.08))
    return VGroup(uv, xy, always_redraw(geometry), labels, arrow)


class SubstitutionComparison(Scene):
    def construct(self):
        self.camera.background_color = BLACK
        def pause(seconds): self.wait(seconds, frozen_frame=True)
        def caption(s): return words(s, 27).to_edge(DOWN, buff=.3)
        def heading(s): return words(s, 37).to_edge(UP, buff=.25)

        title = heading('Change of variables: compare the small pieces')
        intro = words('A small piece is predicted by a local linear map.', 34).move_to([0, .4, 0])
        self.play(Write(title), FadeIn(intro), run_time=2)
        pause(3)
        self.play(FadeOut(intro), Transform(title, heading('One variable: interval versus tangent prediction')))
        e = ValueTracker(.4)
        formula = math(r'x=h(u)=u^2,\quad u_0=1', 32).move_to([-3.55, 2.45, 0])
        enlarged = words('Intervals at right: magnified equally', 26).move_to([3.1, 2.45, 0])
        graph = interval_view(e)
        bars = interval_bars(e)
        note = caption('The blue interval has a true image (orange) and a tangent prediction (violet).')
        self.play(Write(formula), FadeIn(enlarged, graph, bars, note), run_time=3)
        pause(4)
        zoom_graph = interval_view(e, True)
        self.play(ReplacementTransform(graph, zoom_graph), run_time=3)
        readout = ratio(r'\frac{\text{length of true image}}{\Delta u}', lambda:2+e.get_value(), [0, -2.4, 0])
        reference = math(r"\text{tangent prediction}/\Delta u=|h'(1)|=2", 29, PURPLE).move_to([0, -3.05, 0])
        self.play(FadeIn(readout), Write(reference))
        new_note = caption('Refine and zoom: the true image interval approaches the tangent prediction.')
        self.play(ReplacementTransform(note, new_note))
        self.play(e.animate.set_value(.1), run_time=3)
        pause(2)
        self.play(e.animate.set_value(.02), run_time=3)
        pause(4)
        length_snapshot = VGroup(zoom_graph, bars).copy().clear_updaters(recursive=True)
        self.play(FadeOut(zoom_graph, bars, formula, enlarged, readout, reference, new_note))

        self.play(Transform(title, heading('Two variables: rectangle, curved image, local parallelogram')))
        map_label = math(r'T(u,v)=(x(u,v),y(u,v))', 32).move_to([0, 2.6, 0])
        headers = VGroup(words(r'$uv$-plane: rectangles', 29).move_to([-4.1, 1.9, 0]),
                         words(r'$xy$-plane: curved grid', 29).move_to([3.3, 1.9, 0]))
        h = ValueTracker(.75)
        coarse = area_view(h)
        note = caption('A rectangle cut out by u = constant and v = constant maps to a curved cell.')
        self.play(Write(map_label), FadeIn(headers, coarse, note), run_time=3)
        pause(5)
        model = area_view(h, show_model=True)
        definitions = VGroup(
            math(r'T_u(p)=\left\langle\frac{\partial x}{\partial u},\frac{\partial y}{\partial u}\right\rangle_p=\langle2,0\rangle', 26, BLUE).move_to([-3.5, 2.65, 0]),
            math(r'T_v(p)=\left\langle\frac{\partial x}{\partial v},\frac{\partial y}{\partial v}\right\rangle_p=\langle1,1\rangle', 26, RED).move_to([3.5, 2.65, 0]))
        for definition in definitions:
            if definition.width > 6.4:
                definition.scale_to_fit_width(6.4)
        new_note = caption('The violet parallelogram is spanned by the two tangent edge vectors.')
        self.play(ReplacementTransform(coarse, model), FadeOut(map_label), Write(definitions),
                  ReplacementTransform(note, new_note), run_time=3)
        area_readout = ratio(r'\frac{\text{area of curved image}}{\Delta u\,\Delta v}',
                             lambda:image_area_ratio(h.get_value()), [0, -2.15, 0])
        area_reference = math(r'\text{area of violet parallelogram}=|J(p)|\,\Delta u\,\Delta v=2\Delta u\,\Delta v',
                              27, PURPLE).move_to([0, -2.95, 0])
        if area_reference.width > 12.7:
            area_reference.scale_to_fit_width(12.7)
        self.play(FadeIn(area_readout), Write(area_reference))
        pause(5)
        self.play(h.animate.set_value(.375), run_time=3)
        pause(2)
        zoom = area_view(h, True, True)
        zoom_note = caption('Zoom to the chosen cell, then refine: the curved patch hugs the parallelogram.')
        self.play(ReplacementTransform(model, zoom), ReplacementTransform(new_note, zoom_note), run_time=3)
        self.play(h.animate.set_value(.1875), run_time=3)
        pause(2)
        self.play(h.animate.set_value(.09375), run_time=3)
        pause(2)
        self.play(h.animate.set_value(.0234375), run_time=3)
        pause(3)
        local_value = math(r'J(p)=\left.\frac{\partial(x,y)}{\partial(u,v)}\right|_p=\begin{vmatrix}2&1\\0&1\end{vmatrix}=2',
                           29, PURPLE).move_to([0, 2.65, 0])
        final_note = caption('The image area divided by the rectangle area approaches the absolute Jacobian.')
        self.play(ReplacementTransform(definitions, local_value), ReplacementTransform(zoom_note, final_note))
        pause(5)
        area_snapshot = zoom.copy().clear_updaters(recursive=True)
        self.play(FadeOut(zoom, headers, local_value, area_readout, area_reference, final_note))

        # Keep both enlarged local constructions visible while comparing factors.
        self.play(Transform(title, heading('The same local linear idea, one dimension higher')))
        length_snapshot.scale_to_fit_width(5.7).move_to([-3.55, -1.35, 0])
        area_snapshot.scale_to_fit_width(5.9).move_to([3.55, -1.35, 0])
        labels = VGroup(words('Local intervals', 32, BLUE).move_to([-3.55, 2.65, 0]),
                        words('Local rectangles and parallelograms', 28, BLUE).move_to([3.55, 2.65, 0]))
        factors = VGroup(
            math(r'\Delta x\approx h^{\prime}(u)\,\Delta u', 32).move_to([-3.55, 1.65, 0]),
            math(r'A_{\text{image}}\approx\left|\frac{\partial(x,y)}{\partial(u,v)}\right|\Delta u\,\Delta v',
                 29).move_to([3.55, 1.65, 0]))
        if factors[1].width > 6.2:
            factors[1].scale_to_fit_width(6.2)
        factor_names = VGroup(words('length scale: derivative', 27, PURPLE).move_to([-3.55, .55, 0]),
                             words('area scale: absolute Jacobian', 27, PURPLE).move_to([3.55, .55, 0]))
        note = caption('Replace each small image by its local linear prediction, then add the contributions.')
        self.play(FadeIn(labels, length_snapshot, area_snapshot, note), Write(factors), FadeIn(factor_names), run_time=3)
        pause(6)
        self.play(FadeOut(factors, factor_names, note))
        one = math(r'\int_{h(a)}^{h(b)} f(x)\,dx', 34).move_to([-3.55, 1.8, 0])
        two = math(r'\iint_R F(x,y)\,dA', 34).move_to([3.55, 1.8, 0])
        eqs = VGroup(math('=', 32).move_to([-3.55, 1.05, 0]), math('=', 32).move_to([3.55, 1.05, 0]))
        newone = math(r'\int_a^b f(h(u))\,h^{\prime}(u)\,du', 31).move_to([-3.55, .3, 0])
        newtwo = math(r'\iint_S F(T(u,v))\left|\frac{\partial(x,y)}{\partial(u,v)}\right|du\,dv', 28).move_to([3.55, .3, 0])
        note = caption('Same function at the mapped points; the local scale factor changes the small piece.')
        self.play(Write(one), Write(two), Write(eqs), Write(newone), Write(newtwo), FadeIn(note), run_time=4)
        pause(8)
        self.play(*[FadeOut(m) for m in (labels, length_snapshot, area_snapshot, one, two, eqs, newone, newtwo, note)])
        closing = words(r'The derivative scales length.\\The Jacobian determinant scales area.', 42).move_to([0, .65, 0])
        orientation = words(r'Single integrals: signed derivative with oriented limits.\\Double integrals: absolute Jacobian, since area is nonnegative.', 26).move_to([0, -1.35, 0])
        self.play(Write(closing), FadeIn(orientation), run_time=2)
        pause(5)


if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='substitution-manim-') as temp:
        with tempconfig({'media_dir': temp, 'pixel_width': 1920, 'pixel_height': 1080,
                         'frame_rate': 30, 'background_color': BLACK,
                         'disable_caching': True, 'output_file': 'substitution_comparison'}):
            scene = SubstitutionComparison()
            scene.render()
            OUT.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(scene.renderer.file_writer.movie_file_path, OUT)
    print(OUT)
