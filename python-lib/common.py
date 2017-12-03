#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0

import argparse
import cmath
import math
import colorsys
import sys
import signal
import multiprocessing
import numpy as np


# Raw color
def rgb(r, g, b):
    return int(b * 0xff) | int((g * 0xff)) << 8 | int(r * 0xff) << 16


def rgb250(r, g, b):
    return int(b) | int(g) << 8 | int(r) << 16


def hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(b * 0xff) | int((g * 0xff)) << 8 | int(r * 0xff) << 16


def grayscale(r):
    return int(r * 0xff) | int((r * 0xff)) << 8 | int(r * 0xff) << 16


def dark_color_factory(scale, dummy):
    def dark_color(x):
        if x == scale:
            return 0
        return hsv(0.6 + 0.4 * x / (2 * scale), 0.7, 0.5)
    return dark_color


def bright_color_factory(scale, base_hue=0.4):
    def bright_color(x):
        if x == scale:
            return 0
        return hsv(base_hue + x / scale, 0.7, 0.7)
    return bright_color


def grayscale_color_factory(scale):
    def grayscale_color(x):
        if x == scale:
            return 0
        return grayscale(x / scale)
    return grayscale_color


def log_sin_lightblue(scale):
    def color_func(x):
        if x == 0 or x == scale:
            return 0
        rlog = abs(math.sin(math.log(math.pow(x + 50, 7))))
        glog = abs(math.sin(math.log(math.pow(x + 50, 7))))
        blog = abs(math.sin(math.log(math.pow(x + 150, 7))))
        return rgb250(10 + 150 * rlog, 40 + 150 * glog, 100 + 150 * blog)
    return color_func

ColorMap = {
    'grayscale': grayscale_color_factory,
    'log+sin+lightblue': log_sin_lightblue,
}

# Basic maths
MAX_SHORT = float((2 ** (2 * 8)) // 2)
PHI = (1+math.sqrt(5))/2.0


def rotate_point(point, angle):
    return complex(point[0] * math.cos(angle) - point[1] * math.sin(angle),
                   point[0] * math.sin(angle) + point[1] * math.cos(angle))


# CLI usage
def usage_cli_complex(argv=sys.argv[1:], center=0j, radius=3., c=0, seed='',
                      worker=multiprocessing.cpu_count()):
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", metavar="DIR", help="record frame in png")
    parser.add_argument("--size", type=float, default=2.5,
                        help="render size (2.5)")
    parser.add_argument("--center", type=complex, default=center,
                        help="plane center(%s)" % center)
    parser.add_argument("--radius", type=float, default=radius,
                        help="plane radius (%s)" % radius)
    parser.add_argument("--worker", type=int, default=worker,
                        help="number of cpu (%s)" % worker)
    parser.add_argument("--seed", type=str, default=seed,
                        help="str seed")
    parser.add_argument("--colormap", default="grayscale",
                        choices=list(ColorMap.keys()))
    parser.add_argument("--max_iter", default=42, type=float)
    parser.add_argument("--c", type=complex, default=c,
                        help="complex seed (%s)" % c)
    parser.add_argument("--opencl", action="store_const", const=True)
    parser.add_argument("--sampling", type=int, default=1)
    args = parser.parse_args(argv)
    args.winsize = list(map(lambda x: int(x * args.size), [100,  100]))
    args.length = args.winsize[0] * args.winsize[1]
    args.pids = set()
    args.center = np.complex128(args.center)
    args.radius = np.float64(args.radius)
    if not args.opencl and args.worker >= 2:
        if args.length / args.worker != args.length // args.worker:
            raise RuntimeError("Worker isn't a multiple of %d" % args.length)
        args.pool = multiprocessing.Pool(args.worker, lambda: signal.signal(
            signal.SIGINT, signal.SIG_IGN))
    else:
        args.pool = None
    args.color = ColorMap[args.colormap]
    return args


def run_main(main):
    try:
        main()
    except KeyboardInterrupt:
        pass
    if args.pool:
        args.pool.terminate()
        args.pool.join()
        del args.pool
    for pid in args.pids:
        pid.terminate()


class ComplexPlane:
    def set_view(self, center=None, radius=None):
        if center is not None:
            self.center = center
        if radius is not None:
            if radius == 0:
                raise RuntimeError("Radius can't be null")
            self.radius = radius
        self.plane_min = (self.center.real - self.radius,
                          self.center.imag - self.radius)
        self.plane_max = (self.center.real + self.radius,
                          self.center.imag + self.radius)
        # Coordinate conversion vector
        self.offset = (self.plane_min[0], self.plane_min[1])
        self.scale = (
            self.window_size[0] / float(self.plane_max[0] - self.plane_min[0]),
            self.window_size[1] / float(self.plane_max[1] - self.plane_min[1])
        )

    def compute_chunks(self, method, params):
        params = [self.window_size, self.offset, self.scale,
                  self.args.sampling] + params + [self.length]
        if self.args.worker >= 2:
            # Divide image length by number of worker
            params[-1] //= self.args.worker
            # Append chunk position
            params = list(map(lambda x: params + [x], range(self.args.worker)))
            # Compute
            res = self.args.pool.map(method, params)
            # Return flatten array
            return np.array(res).flatten()
        # Mono process just compute first chunk
        return method(params + [0])

    def convert_to_plane(self, screen_coord):
        return complex(
            screen_coord[0] / self.scale[0] + self.offset[0],
            screen_coord[1] / self.scale[1] + self.offset[1]
        )

    def convert_to_screen(self, plane_coord):
        return [
            int((plane_coord.real - self.offset[0]) * self.scale[0]),
            int((plane_coord.imag - self.offset[1]) * self.scale[1])
        ]

    def draw_complex(self, complex_coord, color=[242]*3):
        self.draw_point(self.convert_to_screen(complex_coord), color)

    def draw_axis(self, axis_color=(28, 28, 28)):
        center_coord = self.convert_to_screen(0j)
        self.draw_line(
            (center_coord[0], 0),
            (center_coord[0], self.window_size[1]),
            color=axis_color)
        self.draw_line(
            (0, center_coord[1]),
            (self.window_size[0], center_coord[1]),
            color=axis_color)


# Modulation
class Path:
    def __init__(self, points, size):
        self.points = points
        self.size = size
        self.len_pairs = float(len(points) - 1)
        self.xpath = np.array(map(lambda x: x.__getattribute__("real"),
                                  self.points))
        self.ypath = np.array(map(lambda x: x.__getattribute__("imag"),
                                  self.points))

    def points_pairs(self):
        for idx in range(len(self.points) - 1):
            yield (self.points[idx], self.points[idx + 1])

    def logs(self):
        path = []
        for a, b in self.points_pairs():
            for point in np.logspace(np.log10(a), np.log10(b),
                                     self.size // self.len_pairs):
                path.append(point)
        return path

    def gen_logs(self):
        logs = self.logs()
        for c in logs:
            yield c

    def lines(self):
        path = []
        for a, b in self.points_pairs():
            for point in np.linspace(a, b, self.size / self.len_pairs):
                path.append(point)
        return path

    def gen_lines(self):
        path = self.lines()
        for c in path:
            yield c

    def sin(self, factor=0.23, cycles=1, sign=1, maxy=1.0):
        path = []
        for a, b in self.points_pairs():
            idx = 0
            angle = cmath.phase(b - a)
            distance = cmath.polar(b - a)[0]
            sinx = np.linspace(0, distance, self.size / self.len_pairs)
            siny = map(lambda x: sign * maxy * math.sin(
                cycles * x * math.pi / float(distance)), sinx)
            for idx in range(self.size // self.len_pairs):
                p = (sinx[idx], siny[idx] * factor)
                path.append(a + rotate_point(p, angle))
        return path

    def gen_sin(self, factor=0.23, cycles=1, sign=1, maxy=1.0):
        path = self.sin(factor, cycles, sign, maxy)
        for c in path:
            yield c

    def splines(self):
        try:
            import scipy.interpolate
        except ImportError:
            return []
        path = []
        t = np.arange(self.xpath.shape[0], dtype=float)
        t /= t[-1]
        nt = np.linspace(0, 1, self.size)
        x1 = scipy.interpolate.spline(t, self.xpath, nt)
        y1 = scipy.interpolate.spline(t, self.ypath, nt)
        for pos in range(len(nt)):
            path.append(complex(x1[pos], y1[pos]))
        return path

    def gen_splines(self):
        path = self.splines()
        for c in path:
            yield c
