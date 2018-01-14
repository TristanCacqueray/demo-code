#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0

import os
import sys
import time
import numpy as np
import pygame
import subprocess
from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, K_ESCAPE
from pygame.locals import K_a, K_e, K_r, K_p
from pygame.locals import K_LEFT, K_RIGHT, K_DOWN, K_UP
try:
    sys.path.append("%s/../python-lib" % os.path.dirname(__file__))
    from pygame_utils import Screen, Window, ComplexPlane
    from common import usage_cli_complex, run_main, gradient
except ImportError:
    raise

try:
    import pyopencl as cl
    prg, ctx = None, None
except ImportError:
    print("OpenCL is disabled")


def calc_fractal_opencl(q, maxiter, norm, color, gradient_func=None):
    global prg, ctx

    if not prg:
        ctx = cl.create_some_context()
        prg_src = []
        num_color = 4096
        if color == "gradient":
            colors_array = []
            for idx in range(num_color):
                colors_array.append(str(gradient_func.color(idx/num_color)))
            prg_src.append("__constant uint gradient[] = {%s};" %
                           ",".join(colors_array))
        prg_src.append("""
        #pragma OPENCL EXTENSION cl_khr_byte_addressable_store : enable
        #pragma OPENCL EXTENSION cl_khr_fp64 : enable
        __kernel void mandelbrot(__global double2 *q,
                                 __global uint *output, uint const max_iter)
        {
            int gid = get_global_id(0);
            double nreal, real = 0;
            double imag = 0;
            double modulus = 0;
            double escape = 2.0f;
            double mu = 0;
            output[gid] = 0;
            for(int idx = 0; idx < max_iter; idx++) {
                nreal = real*real - imag*imag + q[gid].x;
                imag = 2* real*imag + q[gid].y;
                real = nreal;
                modulus = sqrt(imag*imag + real*real);
                if (modulus > escape){
        """)
        if norm == "escape":
            prg_src.append(
                "mu = idx - log(log(modulus)) / log(2.0f) + "
                "log(log(escape)) / log(2.0f);"
            )
            prg_src.append("mu = mu / (double)max_iter;")

        else:
            prg_src.append("mu = idx / (double)max_iter;")
        if color == "gradient":
            prg_src.append("output[gid] = gradient[(int)(mu * %d)];" %
                           (num_color - 1))
        elif color == "dumb":
            prg_src.append("output[gid] = mu * 0xffff;")

        prg_src.append("break; }}}")
        print("\n".join(prg_src))
        prg = cl.Program(ctx, "\n".join(prg_src)).build()
    output = np.empty(q.shape, dtype=np.uint32)

    queue = cl.CommandQueue(ctx)

    mf = cl.mem_flags
    q_opencl = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=q)
    output_opencl = cl.Buffer(ctx, mf.WRITE_ONLY, output.nbytes)

    prg.mandelbrot(queue, output.shape, None, q_opencl,
                   output_opencl, np.uint32(maxiter))
    cl.enqueue_copy(queue, output, output_opencl).wait()
#    unique, counts = np.unique(output, return_counts=True)
#    print(dict(zip(unique, counts)))
    return output


def calc_fractal_python(c, maxiter):
    output = np.zeros(c.shape)
    z = np.zeros(c.shape, np.complex128)
    for it in range(int(maxiter)):
        notdone = np.less(z.real*z.real + z.imag*z.imag, 4.0)
        output[notdone] = it
        z[notdone] = z[notdone]**2 + c[notdone]
    output[output == maxiter-1] = 0
    return output


class MandelbrotSet(Window, ComplexPlane):
    def __init__(self, args):
        Window.__init__(self, args.winsize)
        self.max_iter = args.max_iter
        self.args = args
        self.color = args.color
        self.set_view(center=args.center, radius=args.radius)

    def render(self, frame, draw_axis=True):
        start_time = time.time()
        x = np.linspace(self.plane_min[0], self.plane_max[0],
                        self.window_size[0])
        y = np.linspace(self.plane_min[1], self.plane_max[1],
                        self.window_size[1]) * 1j
        q = np.ravel(y+x[:, np.newaxis]).astype(np.complex128)
        if self.args.opencl:
            nparray = calc_fractal_opencl(
                q, self.max_iter, self.args.norm, self.color,
                self.args.gradient)
        else:
            nparray = calc_fractal_python(q, self.max_iter)
        self.blit(nparray)
        if draw_axis:
            self.draw_axis()
        print("%04d: %.2f sec: ./mandelbrot_set.py --center '%s' "
              "--radius '%s'" % (frame, time.time() - start_time, self.center,
                                 self.radius))


def main():
    if len(sys.argv) <= 3:
        print("MandelbrotSet explorer\n"
              "======================\,"
              "\n"
              "Left/right click to zoom in/out, Middle click "
              "to draw JuliaSet\n"
              "Press 'p' to capture an image\n"
              "Use keyboard arrow to move window, 'a'/'e' to zoom in/out, "
              "'r' to reset view\n")

    args = usage_cli_complex(center=-0.8, radius=1.3)
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
                        step = 3/4.0
                    else:
                        step = 4/3.0
                    scene.set_view(center=scene_coord,
                                   radius=scene.radius * step)
                    redraw = True
                else:
                    argv = ["./julia_set.py", "--c", str(scene_coord),
                            "--colormap", args.colormap,
                            "--max_iter", str(args.max_iter)]
                    if args.opencl:
                        argv.append("--opencl")
                    if args.sub_radius:
                        argv.extend(["--radius", str(args.sub_radius)])
                    args.pids.add(subprocess.Popen(argv))
            else:
                if e.key == K_ESCAPE:
                    return
                if e.key == K_p:
                    screen.capture("./", time.time())
                redraw = True
                if e.key in (K_LEFT, K_RIGHT, K_DOWN, K_UP):
                    if   e.key == K_LEFT:  step = -10/scene.scale[0]
                    elif e.key == K_RIGHT: step = +10/scene.scale[0]
                    elif e.key == K_DOWN:  step = complex(0,  10/scene.scale[1])
                    elif e.key == K_UP:    step = complex(0, -10/scene.scale[1])
                    scene.set_view(center=scene.center + step)
                elif e.key in (K_a, K_e):
                    if e.key == K_e:
                        step = 3/4.0
                    elif e.key == K_a:
                        step = 4/3.0
                    scene.set_view(radius=scene.radius * step)
                elif e.key == K_r:
                    scene.set_view(center=0j, radius=1.5)
                else:
                    redraw = False
                    print
                    continue
        clock.tick(25)

if __name__ == "__main__":
    run_main(main)
