#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0

import os, sys
sys.path.append("%s/../python-lib" % os.path.dirname(__file__))
from pygame_utils import *


def compute_markus_lyapunov(param):
    window_size, offset, scale, sampling, seed, x0, max_iter, max_init, step_size, chunk = param

    results = np.zeros(step_size, dtype='i4')
    pos = 0

    while pos < step_size:
        step_pos = pos + chunk * step_size
        screen_coord = (step_pos / window_size[1], step_pos % window_size[1])
        c = np.complex128(complex(
            screen_coord[0] / scale[0] + offset[0],
            ((window_size[1] - screen_coord[1]) / scale[1] + offset[1])
        ))
        markus_func = lambda x: c.real if seed[idx % len(seed)] == "A" else c.imag

        # Init
        x = np.float128(x0)
        try:
            for idx in xrange(0, max_init):
                r = markus_func(idx)
                with np.errstate(over='raise'):
                    x = r * x * ( 1 - x )
        except FloatingPointError:
            pass

        # Exponent
        total = np.float64(0)
        try:
            for idx in range(0, max_iter):
                r = markus_func(idx)
                with np.errstate(over='raise'):
                    x = r * x * ( 1 - x )
                v = abs(r - 2 * r * x)
                if v == 0:
                    break
                total = total + math.log(v) / math.log(1.23)
        except FloatingPointError:
            pass

        if total == 0 or total == float('Inf'):
            exponent = 0
        else:
            exponent = total / float(max_iter)
        results[pos] = exponent
        pos += sampling
    return results


def color_factory(size, base_hue = 0.65):
    def color_scale(x):
        if x < 0:
            v = abs(x) / size
            hue = base_hue - .4 * v
            sat = 0.6 + 0.4 * v
        else:
            hue = base_hue
            sat = 0.6
        return hsv(hue, sat, 0.7)
    return color_scale

class MarkusLyapunov(Window, ComplexPlane):
    def __init__(self, args):
        Window.__init__(self, args.winsize)
        self.args = args
        self.seed = args.seed
        self.x0 = 0.5
        self.max_iter = 100
        self.max_init = 50
        self.set_view(args.center, args.radius)
        self.color_vector = np.vectorize(color_factory(22.))

    def render(self, frame):
        start_time = time.time()

        nparray = self.compute_chunks(compute_markus_lyapunov, [self.seed, self.x0, self.max_iter, self.max_init])
        #np.save("/tmp/markus", nparray)
        #nparray = np.load("/tmp/markus.npy")

        #print "min:", min(nparray), "max:", max(nparray), "mean:", nparray.mean()
        #self.color_vector = np.vectorize(color_factory(float(abs(min(nparray)))))
        self.blit(self.color_vector(nparray))
        print "%04d: %.2f sec: ./markus_lyapunov.py --seed '%s' --center '%s' --radius '%s'" % (frame, time.time() - start_time, self.seed, self.center, self.radius)


def main():
    if len(sys.argv) <= 3:
        print "Markus-Lyapunov explorer"
        print "========================"
        print ""
        print "Click the window to center"
        print "Use keyboard arrow to move window, 'a'/'e' to zoom in/out, 'r' to reset view"

    args = usage_cli_complex(center=2+2j, radius = 2., seed="AB")
    screen = Screen(args.winsize)
    clock = pygame.time.Clock()
    scene = MarkusLyapunov(args)
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
                    scene.set_view(center = plane_coord, radius = scene.radius * step)
                    redraw = True
                else:
                    print "Clicked", e.pos
            else:
                if e.key == K_ESCAPE:
                    exit(0)
                redraw = True
                if e.key in (K_a, K_e):
                    if   e.key == K_a: step = 1/4.0
                    elif e.key == K_e: step = 4/1.0
                    scene.set_view(radius = scene.radius * step)
                elif e.key in (K_LEFT,K_RIGHT,K_DOWN,K_UP):
                    if   e.key == K_LEFT:  step = -10/scene.scale[0]
                    elif e.key == K_RIGHT: step = +10/scene.scale[0]
                    elif e.key == K_DOWN:  step = complex(0, -10/scene.scale[1])
                    elif e.key == K_UP:    step = complex(0,  10/scene.scale[1])
                    scene.set_view(center = scene.center + step)
                elif e.key == K_r:
                    scene.set_view(center = 2+2j, radius = 2.)
                else:
                    redraw = False
                    continue
        clock.tick(25)

if __name__ == "__main__":
    run_main(main)
