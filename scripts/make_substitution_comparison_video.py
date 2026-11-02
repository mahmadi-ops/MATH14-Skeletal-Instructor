#!/usr/bin/env python3
"""Simple linear changes of variables, rendered with Manim.

Run: python scripts/make_substitution_comparison_video.py
Output: assets/videos/substitution_stretch_parallelograms_1080p.mp4
(1080p, 30fps, silent). Black/Computer Modern styling matches the book.

1D: x=2u stretches a subdivided interval and each of its pieces by 2.
2D: T(u,v)=(2u+v,v) carries [0,4]x[0,3] to one large parallelogram,
     subdivided into a 4x3 grid of smaller parallelograms. Every cell's
     area is exactly doubled. Both pictures use equal coordinate units.
The enlarged selected pieces remain in the final integral comparison.
"""
import shutil
import tempfile
from pathlib import Path

import numpy as np
from manim import *

OUT = Path(__file__).resolve().parents[1] / 'assets/videos/substitution_stretch_parallelograms_1080p.mp4'
BLUE, RED = '#2e9aff', '#fc6255'
ORANGE, PURPLE, GREY = '#ff862f', '#c77dff', '#7f7f7f'
TPL = TexTemplate(preamble=r'\usepackage{amsmath}\usepackage{amssymb}')


def words(s, size=30, color=WHITE):
    return Tex(s, tex_template=TPL, font_size=size, color=color)


def math(s, size=36, color=WHITE):
    return MathTex(s, tex_template=TPL, font_size=size, color=color)


def transform(u, v):
    return np.array([2*u+v, v])


def interval_parts(origin, unit, stretch, color):
    start = np.array(origin)
    line = Line(start, start+4*unit*stretch*RIGHT, color=color, stroke_width=8)
    ticks, numbers = VGroup(), VGroup()
    for k in range(5):
        p = start+k*unit*stretch*RIGHT
        ticks.add(Line(p+.11*DOWN, p+.11*UP, color=WHITE, stroke_width=2))
        numbers.add(math(str(k*stretch), 24).next_to(Dot(p), DOWN, buff=.2))
    return VGroup(line, ticks, numbers)


def stretch_closeup():
    a, b = np.array([-2.8, .65, 0]), np.array([-2.8, -.95, 0])
    small = Line(a, a+1.7*RIGHT, color=BLUE, stroke_width=11)
    large = Line(b, b+3.4*RIGHT, color=PURPLE, stroke_width=11)
    ends = VGroup()
    for p in (small.get_start(), small.get_end(), large.get_start(), large.get_end()):
        ends.add(Line(p+.1*DOWN, p+.1*UP, color=WHITE, stroke_width=2))
    labels = VGroup(math(r'\Delta u', 32, BLUE).next_to(small, UP, buff=.15),
                    math(r'\Delta x=2\Delta u', 32, PURPLE).next_to(large, UP, buff=.15),
                    math('u', 28).next_to(small, LEFT, buff=.25),
                    math('x', 28).next_to(large, LEFT, buff=.25))
    arrow = Arrow([1.6, .5, 0], [1.6, -.8, 0], color=WHITE, buff=.08)
    label = math(r'\times2', 30).next_to(arrow, RIGHT, buff=.15)
    return VGroup(small, large, ends, labels, arrow, label)


def axes_at(origin, xmax, ymax, unit):
    axes = Axes(x_range=[0, xmax, 1], y_range=[0, ymax, 1],
                x_length=xmax*unit, y_length=ymax*unit, tips=False,
                axis_config={'include_ticks': False, 'stroke_color': GREY, 'stroke_width':1.2})
    axes.shift(np.array(origin)-axes.c2p(0, 0))
    return axes


def rectangle(axes, u, v, width, height, color, mapped=False, fill=.2):
    points = ((u,v),(u+width,v),(u+width,v+height),(u,v+height))
    coords = [transform(*p) if mapped else p for p in points]
    return Polygon(*[axes.c2p(*p) for p in coords], color=color,
                   fill_opacity=fill, stroke_width=3)


def grid(axes, mapped=False):
    lines = VGroup()
    def p(u,v):return axes.c2p(*(transform(u,v) if mapped else (u,v)))
    for u in (1,2,3):
        lines.add(Line(p(u,0),p(u,3),color=ORANGE if mapped else BLUE,stroke_width=1.8))
    for v in (1,2):
        lines.add(Line(p(0,v),p(4,v),color=ORANGE if mapped else BLUE,stroke_width=1.8))
    return lines


def area_closeup():
    uv = axes_at([-4.8,-.85,0],1.4,1.4,1.4)
    xy = axes_at([.7,-.85,0],3.4,1.4,1.4)
    source = rectangle(uv,0,0,1,1,BLUE,fill=.25)
    target = rectangle(xy,0,0,1,1,PURPLE,mapped=True,fill=.28)
    edges = VGroup(Arrow(uv.c2p(0,0),uv.c2p(1,0),buff=0,color=BLUE,stroke_width=5),
                   Arrow(uv.c2p(0,0),uv.c2p(0,1),buff=0,color=RED,stroke_width=5),
                   Arrow(xy.c2p(0,0),xy.c2p(2,0),buff=0,color=BLUE,stroke_width=5),
                   Arrow(xy.c2p(0,0),xy.c2p(1,1),buff=0,color=RED,stroke_width=5))
    labels = VGroup(math(r'\Delta u',27,BLUE).next_to(edges[0],DOWN,buff=.15),
                    math(r'\Delta v',27,RED).next_to(edges[1],LEFT,buff=.15),
                    math(r'T_u\Delta u',27,BLUE).next_to(edges[2],DOWN,buff=.15),
                    math(r'T_v\Delta v',27,RED).rotate(PI/4).move_to(xy.c2p(.2,.75)),
                    math('u',25).next_to(uv.x_axis,RIGHT,buff=.1),
                    math('v',25).next_to(uv.y_axis,UP,buff=.1),
                    math('x',25).next_to(xy.x_axis,RIGHT,buff=.1),
                    math('y',25).next_to(xy.y_axis,UP,buff=.1))
    arrow = Arrow([-2.5,0,0],[-1.2,0,0],buff=.05,color=WHITE)
    labels.add(math('T',30).next_to(arrow,UP,buff=.1))
    return VGroup(uv,xy,source,target,edges,labels,arrow)


class SubstitutionComparison(Scene):
    def construct(self):
        self.camera.background_color=BLACK
        def pause(n):self.wait(n,frozen_frame=True)
        def title(s):return words(s,38).to_edge(UP,buff=.25)
        def caption(s):return words(s,28).to_edge(DOWN,buff=.3)
        def swap(old,new):self.play(FadeOut(old),FadeIn(new))

        heading=title('Change of variables: stretch lengths, scale areas')
        self.play(Write(heading),run_time=2)
        pause(2)
        new_heading=title('One variable: a simple stretch')
        swap(heading,new_heading);heading=new_heading
        formula=math(r'x=h(u)=2u',38).move_to([0,2.45,0])
        source=interval_parts([-4.2,.65,0],.75,1,BLUE)
        image=interval_parts([-4.2,-1.1,0],.75,2,ORANGE)
        names=VGroup(math('u',30).next_to(source[0],LEFT,buff=.25),
                     math('x',30).next_to(image[0],LEFT,buff=.25))
        arrow=Arrow([2,.5,0],[2,-.95,0],buff=.08,color=WHITE)
        times=math(r'\times2',32).next_to(arrow,RIGHT,buff=.15)
        note=caption('Stretch the interval by 2. Every small interval stretches by the same factor.')
        self.play(Write(formula),FadeIn(source,names[0],note),run_time=2)
        self.play(TransformFromCopy(source,image),FadeIn(names[1]),Create(arrow),Write(times),run_time=3)
        pause(4)
        chosen=Line([-3.45,.65,0],[-2.7,.65,0],color=BLUE,stroke_width=14)
        stretched=Line([-2.7,-1.1,0],[-1.2,-1.1,0],color=PURPLE,stroke_width=14)
        self.play(FadeIn(chosen),TransformFromCopy(chosen,stretched),run_time=2)
        pause(2)
        close_length=stretch_closeup()
        self.play(FadeOut(source,image,names,arrow,times,chosen,stretched),FadeIn(close_length),run_time=2)
        factor=math(r'\Delta x=2\Delta u,\qquad \frac{dx}{du}=2',34).move_to([0,-2.45,0])
        self.play(Write(factor))
        pause(4)
        length_snapshot=close_length.copy()
        self.play(FadeOut(close_length,formula,factor,note))

        new_heading=title('Two variables: a large parallelogram made of smaller ones')
        swap(heading,new_heading);heading=new_heading
        mapping=math(r'T(u,v)=(2u+v,v)',35).move_to([0,2.65,0])
        headers=VGroup(words(r'$uv$-plane: a rectangle',28).move_to([-4.8,1.95,0]),
                       words(r'$xy$-plane: a parallelogram',28).move_to([2.4,1.95,0]))
        uv=axes_at([-6.2,-1,0],4.4,3.4,.7)
        xy=axes_at([-1.75,-1,0],11.5,3.4,.7)
        axis_labels=VGroup(math('u',24).next_to(uv.x_axis,RIGHT,buff=.08),
                           math('v',24).next_to(uv.y_axis,UP,buff=.08),
                           math('x',24).next_to(xy.x_axis,RIGHT,buff=.08),
                           math('y',24).next_to(xy.y_axis,UP,buff=.08))
        rect=rectangle(uv,0,0,4,3,BLUE,fill=.1)
        para=rectangle(xy,0,0,4,3,ORANGE,mapped=True,fill=.1)
        map_arrow=Arrow([-3.15,.05,0],[-2,.05,0],buff=.05,color=WHITE)
        map_name=math('T',29).next_to(map_arrow,UP,buff=.08)
        note=caption('The whole rectangle maps to one large parallelogram.')
        self.play(Write(mapping),FadeIn(headers,uv,xy,axis_labels,rect,note),run_time=2)
        self.play(TransformFromCopy(rect,para),Create(map_arrow),Write(map_name),run_time=3)
        pause(3)
        small_rectangles=grid(uv)
        small_parallelograms=grid(xy,True)
        new_note=caption('Divide the rectangle into small rectangles; each maps to a small parallelogram.')
        swap(note,new_note);note=new_note
        self.play(Create(small_rectangles),run_time=2)
        self.play(TransformFromCopy(small_rectangles,small_parallelograms),run_time=3)
        pause(5)
        chosen_rect=rectangle(uv,1,1,1,1,BLUE,fill=.4)
        chosen_para=rectangle(xy,1,1,1,1,PURPLE,mapped=True,fill=.4)
        self.play(FadeIn(chosen_rect),TransformFromCopy(chosen_rect,chosen_para),run_time=2)
        area_factor=math(r'\frac{\text{area of each parallelogram}}{\text{area of its rectangle}}=2',32).move_to([0,-2.45,0])
        self.play(Write(area_factor))
        pause(4)
        close_area=area_closeup()
        all_plots=VGroup(uv,xy,axis_labels,rect,para,map_arrow,map_name,small_rectangles,small_parallelograms,chosen_rect,chosen_para)
        self.play(FadeOut(all_plots,area_factor),FadeIn(close_area),run_time=2)
        new_note=caption('Enlarge one corresponding pair: its area is exactly doubled.')
        swap(note,new_note);note=new_note
        area_factor=math(r'\Delta A=2\Delta u\,\Delta v',34,PURPLE).move_to([0,-2.1,0])
        jac=math(r'J=\frac{\partial(x,y)}{\partial(u,v)}=\begin{vmatrix}2&1\\0&1\end{vmatrix}=2',29).move_to([0,-2.95,0])
        self.play(Write(area_factor),Write(jac),run_time=3)
        pause(5)
        area_snapshot=close_area.copy()
        self.play(FadeOut(close_area,mapping,headers,area_factor,jac,note))

        new_heading=title('Same idea: a length factor becomes an area factor')
        swap(heading,new_heading);heading=new_heading
        length_snapshot.scale_to_fit_width(5.4).move_to([-3.55,-1.1,0])
        area_snapshot.scale_to_fit_width(5.9).move_to([3.55,-1.1,0])
        labels=VGroup(words('Single integral',32,BLUE).move_to([-3.55,2.6,0]),
                      words('Double integral',32,BLUE).move_to([3.55,2.6,0]))
        factors=VGroup(math(r'dx=2\,du',36).move_to([-3.55,1.5,0]),
                       math(r'dA=\left|\frac{\partial(x,y)}{\partial(u,v)}\right|du\,dv=2\,du\,dv',30).move_to([3.55,1.5,0]))
        if factors[1].width>6.3:factors[1].scale_to_fit_width(6.3)
        self.play(FadeIn(labels,length_snapshot,area_snapshot),Write(factors),run_time=3)
        note=caption('The same factor applies to every small piece in these linear examples.')
        self.play(FadeIn(note));pause(5)
        self.play(FadeOut(factors,note))
        one=math(r'\int_{h(a)}^{h(b)}f(x)\,dx=\int_a^bf(2u)\,2\,du',28).move_to([-3.55,1.25,0])
        two=math(r'\iint_R F(x,y)\,dA=\iint_S F(2u+v,v)\,2\,du\,dv',25).move_to([3.55,1.25,0])
        if one.width>6.3:one.scale_to_fit_width(6.3)
        if two.width>6.3:two.scale_to_fit_width(6.3)
        note=caption('Change the coordinates in the function, and multiply by the size factor.')
        self.play(Write(one),Write(two),FadeIn(note),run_time=3)
        pause(7)


if __name__=='__main__':
    with tempfile.TemporaryDirectory(prefix='substitution-manim-') as temp:
        with tempconfig({'media_dir':temp,'pixel_width':1920,'pixel_height':1080,'frame_rate':30,
                         'background_color':BLACK,'disable_caching':True,'output_file':'substitution_comparison'}):
            scene=SubstitutionComparison();scene.render()
            OUT.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(scene.renderer.file_writer.movie_file_path,OUT)
    print(OUT)
