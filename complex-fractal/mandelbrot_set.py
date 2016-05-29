#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0

import os, sys
sys.path.append("%s/../python-lib" % os.path.dirname(__file__))
from pygame_utils import *


def compute_mandelbrot(param):
    window_size, offset, scale, sampling, max_iter, step_size, chunk = param

    escape_limit = 1e150

    results = np.zeros(step_size, dtype='i4')
    pos = 0

    while pos < step_size:
        step_pos = pos + chunk * step_size
        screen_coord = (step_pos / window_size[1], step_pos % window_size[1])
        u = 0
        c = np.complex128(complex(
            screen_coord[0] / scale[0] + offset[0],
            ((window_size[1] - screen_coord[1]) / scale[1] + offset[1])
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

class MandelbrotSet(Window, ComplexPlane):
    def __init__(self, args, max_iter=69):
        Window.__init__(self, args.winsize)
        self.max_iter = float(max_iter)
        self.args = args
        self.color_vector = np.vectorize(grayscale_color_factory(self.max_iter))
        self.color_vector = np.vectorize(grayscale_color_factory(self.max_iter))
        self.set_view(center = args.center, radius = args.radius)

    def render(self, frame):
        start_time = time.time()
        nparray = self.compute_chunks(compute_mandelbrot, [self.max_iter])
        self.blit(self.color_vector(nparray))
        self.draw_axis()
        print "%04d: %.2f sec: ./mandelbrot_set.py --center '%s' --radius '%s'" % (frame, time.time() - start_time, self.center, self.radius)


def main():
    if len(sys.argv) <= 3:
        print "MandelbrotSet explorer"
        print "======================"
        print ""
        print "Left/right click to zoom in/out, Middle click to draw JuliaSet"
        print "Use keyboard arrow to move view and r to reset"

    args = usage_cli_complex(center=-0.8, radius = 1.3)
    screen = Screen(args.winsize)
    clock = pygame.time.Clock()
    scene = MandelbrotSet(args)
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
                scene_coord = scene.convert_to_plane(e.pos)
                if e.button in (1, 3):
                    if e.button == 1:
                        step = 0.5
                    else:
                        step = 1.5
                    scene.set_view(center = scene_coord, radius = scene.radius * step)
                    redraw = True
                else:
                    args.pids.add(subprocess.Popen(["./julia_set.py", "--c", str(scene_coord)]))
            else:
                if e.key == K_ESCAPE:
                    return
                redraw = True
                if e.key in (K_LEFT,K_RIGHT,K_DOWN,K_UP):
                    if   e.key == K_LEFT:  step = -10/scene.scale[0]
                    elif e.key == K_RIGHT: step = +10/scene.scale[0]
                    elif e.key == K_DOWN:  step = complex(0, -10/scene.scale[1])
                    elif e.key == K_UP:    step = complex(0,  10/scene.scale[1])
                    scene.set_view(center = scene.center + step)
                elif e.key == K_r:
                    scene.set_view(center = 0j, radius = 1.5)
                else:
                    redraw = False
                    print
                    continue
        clock.tick(25)

if __name__ == "__main__":
    run_main(main)
