#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0

import os
import random
import numpy as np
import pygame
import sys
import time
from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, K_ESCAPE, K_RETURN
from pygame.locals import K_a, K_e, K_z, K_s, K_q, K_d, K_r, K_p
from pygame.locals import K_w, K_x, K_c, K_v, K_t, K_g
from pygame.locals import K_LEFT, K_RIGHT, K_DOWN, K_UP
try:
    sys.path.append("%s/../python-lib" % os.path.dirname(__file__))
    from pygame_utils import Screen, Window, ComplexPlane
    from common import PHI, usage_cli_complex, run_main, gradient, rgb250
except ImportError:
    raise

from opencl_complex import calc_fractal_opencl


class BurningJuliaSet(Window, ComplexPlane):
    def __init__(self, args):
        Window.__init__(self, args.winsize)
        self.c = args.c
        self.args = args
        self.max_iter = args.max_iter
        self.color = args.color
        self.set_view(center=args.center, radius=args.radius)

    def render(self, frame, draw_info=False):
        start_time = time.monotonic()
        x = np.linspace(self.plane_min[0], self.plane_max[0],
                        self.window_size[0])
        y = np.linspace(self.plane_min[1], self.plane_max[1],
                        self.window_size[1]) * 1j
        q = np.ravel(y+x[:, np.newaxis]).astype(np.complex128)
        nparray = calc_fractal_opencl(q, "juliaship", self.max_iter, self.args,
                                      seed=self.c)
        self.blit(nparray)
        if draw_info:
            self.draw_axis()
            self.draw_function_msg()
            self.draw_cpoint()
        print("%04d: %.2f sec: ./burning_julia.py --max_iter '%s' --c '%s' "
              "--center '%s' "
              "--radius %s" % (
                    frame, time.monotonic() - start_time,
                    int(self.max_iter),
                    self.c,
                    self.center, self.radius))

    def draw_function_msg(self):
        if self.c.real >= 0:
            r_sign = "+"
        else:
            r_sign = ""
        if self.c.imag >= 0:
            i_sign = "+"
        else:
            i_sign = ""
        self.c_str = "z*z%s%.5f%s%.5fj" % (
            r_sign, self.c.real, i_sign, self.c.imag)
        self.draw_msg(self.c_str)

    def draw_cpoint(self):
        self.draw_complex(self.c, (255, 0, 0))


seeds = (
    (-1.15 - 0.4j),
    (-1.15 - 0.4j),
    (-1 - 1j),
    (-0.75 - 0.9j),
    (0 - 1j),
    (0.675 - 1.15j),
    (0.87 - 1.52j),
    (0.975 - 1.175j),
    (0.29 - 0.29j),
    (0.425 + 0.25j),
    (0 + 0.297j),
    (-0.8 + 0.1j),
)


def main():
    args = usage_cli_complex(center=0, radius=3, c=random.choice(seeds))
    if len(sys.argv) <= 3:
        print("JuliaSet explorer\n"
              "=================\n"
              "\n"
              "Click the window to center\n"
              "Use keyboard arrow to move window, 'a'/'e' to zoom in/out, "
              "'r' to reset view\n"
              "Use 'qzsd' to change c value or RETURN key to "
              "browse known seeds\n",
              "Use 'w'/'x' to decrease/increase real c change step\n"
              "Use 'c'/'v' to decrease/increase imag c change step\n")

    screen = Screen(args.winsize)
    clock = pygame.time.Clock()
    scene = BurningJuliaSet(args)
    screen.add(scene)
    frame = 0
    redraw = True
    cr_step = 1
    ci_step = 1
    while True:
        if redraw:
            frame += 1
            scene.render(frame)
            screen.update()
            pygame.display.update()
            redraw = False
            if args.record:
                screen.capture(args.record, frame)

        for e in pygame.event.get():
            if e.type not in (KEYDOWN, MOUSEBUTTONDOWN):
                continue
            if e.type == MOUSEBUTTONDOWN:
                plane_coord = scene.convert_to_plane(e.pos)
                if e.button in (1, 3):
                    if e.button == 1:
                        step = 3/4.0
                    else:
                        step = 4/3.0
                    scene.set_view(center=plane_coord,
                                   radius=scene.radius * step)
                    redraw = True
                else:
                    print("Clicked", e.pos)
            else:
                if e.key == K_ESCAPE:
                    exit(0)
                if e.key == K_p:
                    screen.capture("./", time.time())
                if e.key in (K_w, K_x):
                    d_step = cr_step * 0.5
                    if e.key == K_w:
                        d_step *= -1
                    cr_step += d_step
                    print("New cr_step:", cr_step)
                if e.key in (K_c, K_v):
                    d_step = ci_step * 0.5
                    if e.key == K_c:
                        d_step *= -1
                    ci_step += d_step
                    print("New ci_step:", ci_step)
                redraw = True
                if e.key == K_RETURN:
                    scene.c = random.choice(seeds)
                elif e.key in (K_a, K_e):
                    if e.key == K_e:
                        step = 3/4.0
                    elif e.key == K_a:
                        step = 4/3.0
                    scene.set_view(radius=scene.radius * step)
                elif e.key in (K_z, K_s, K_q, K_d):
                    fact = 20
                    if e.key == K_z:
                        step = complex(0,  fact/scene.scale[1] * ci_step)
                    elif e.key == K_s:
                        step = complex(0, -fact/scene.scale[1] * ci_step)
                    elif e.key == K_q:
                        step = -fact / scene.scale[0] * cr_step
                    elif e.key == K_d:
                        step = fact / scene.scale[0] * cr_step
                    scene.c += step
                elif e.key in (K_LEFT, K_RIGHT, K_DOWN, K_UP):
                    if e.key == K_LEFT:
                        step = -10/scene.scale[0]
                    elif e.key == K_RIGHT:
                        step = +10/scene.scale[0]
                    elif e.key == K_DOWN:
                        step = complex(0, -10/scene.scale[1])
                    elif e.key == K_UP:
                        step = complex(0,  10/scene.scale[1])
                    scene.set_view(center=scene.center + step)
                elif e.key in (K_t, K_g):
                    fact = scene.max_iter / 10
                    if e.key == K_g:
                        fact = fact * -1
                    scene.max_iter += fact
                elif e.key == K_r:
                    scene.set_view(center=args.center, radius=args.radius)
                else:
                    redraw = False
                    continue
        clock.tick(25)

if __name__ == "__main__":
    run_main(main)
