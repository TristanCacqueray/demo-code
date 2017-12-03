#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0

import os
import random
import numpy as np
import pygame
import sys
import time
from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, K_ESCAPE, K_RETURN
from pygame.locals import K_a, K_e, K_z, K_s, K_q, K_d, K_r
from pygame.locals import K_LEFT, K_RIGHT, K_DOWN, K_UP
try:
    sys.path.append("%s/../python-lib" % os.path.dirname(__file__))
    from pygame_utils import Screen, Window, ComplexPlane
    from common import PHI, usage_cli_complex, run_main
except ImportError:
    raise


def compute_julia_set(param):
    window_size, offset, scale, sampling, max_iter, c, step_size, chunk = param

    escape_limit = 1e150

    results = np.zeros(step_size, dtype='i4')
    pos = 0

    while pos < step_size:
        step_pos = pos + chunk * step_size
        screen_coord = (step_pos / window_size[1], step_pos % window_size[1])
        u = np.complex128(complex(
            screen_coord[0] / scale[0] + offset[0],
            screen_coord[1] / scale[1] + offset[1],
        ))
        idx = 0
        while idx < max_iter:
            u = u * u + c
            if abs(u.real) > escape_limit or abs(u.imag) > escape_limit:
                break
            idx += 1
        results[pos] = idx
        pos += sampling
    return results


class JuliaSet(Window, ComplexPlane):
    def __init__(self, args, max_iter=32):
        Window.__init__(self, args.winsize)
        self.c = args.c
        self.args = args
        self.max_iter = float(max_iter)
        self.color_vector = np.vectorize(args.color(self.max_iter))
        self.set_view(center=args.center, radius=args.radius)

    def render(self, frame):
        start_time = time.monotonic()
        nparray = self.compute_chunks(compute_julia_set,
                                      [self.max_iter, self.c])
        self.blit(self.color_vector(nparray))
        self.draw_axis()
        self.draw_function_msg()
        self.draw_cpoint()
        print(self.c)
        print("%04d: %.2f sec: ./julia_set.py --c '%s' --center '%s' "
              "--radius %s" % (frame, time.monotonic() - start_time, self.c,
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
    complex(PHI, PHI),
    (-0.15000+0.95000j),
    (-0.64000+0.70000j),
    (-0.64000+0.50000j),
    (+0.47000-0.24000j),
    (-0.77000-0.15000j),
    (-1.38000-0.09000j),
    (-1.17000+0.18000j),
    (-0.08000+0.70000j),
    (-0.11000+1.00000j),
    (0.28200+0.48000j),
)


def main():
    if len(sys.argv) <= 3:
        print("JuliaSet explorer\n"
              "=================\n"
              "\n"
              "Click the window to center\n"
              "Use keyboard arrow to move window, 'a'/'e' to zoom in/out, "
              "'r' to reset view\n"
              "Use 'qzsd' to change c value or RETURN key to "
              "browse known seeds")

    args = usage_cli_complex(center=0, radius=3, c=random.choice(seeds))
    screen = Screen(args.winsize)
    clock = pygame.time.Clock()
    scene = JuliaSet(args)
    screen.add(scene)
    frame = 0
    redraw = True
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
                        step = complex(0,  fact/scene.scale[1])
                    elif e.key == K_s:
                        step = complex(0, -fact/scene.scale[1])
                    elif e.key == K_q:
                        step = -fact / scene.scale[0]
                    elif e.key == K_d:
                        step = fact / scene.scale[0]
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
                elif e.key == K_r:
                    scene.set_view(center=args.center, radius=args.radius)
                else:
                    redraw = False
                    continue
        clock.tick(25)

if __name__ == "__main__":
    run_main(main)
