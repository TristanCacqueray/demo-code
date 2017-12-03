#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0

import os
import sys
import pygame
import numpy as np
from mandelbrot_set import MandelbrotSet
try:
    sys.path.append("%s/../python-lib" % os.path.dirname(__file__))
    from pygame_utils import Screen
    from common import usage_cli_complex, run_main
except ImportError:
    raise


def zoom_out(radius, center, steps):
    # Only move center last 5%
    center_move_start = steps - 5 * steps // 100
    center_step = np.logspace(
        np.log10(center[0] + 10+10j), np.log10(center[1].real + 10+10j),
        steps - center_move_start)
    radius_step = np.logspace(np.log10(radius[0]), np.log10(radius[1]), steps)

    def update_view(scene, frame):
        if frame >= center_move_start:
            scene.set_view(
                center=center_step[frame - center_move_start] - (10+10j))
        scene.set_view(radius=radius_step[frame])
    return update_view


def main():
    args = usage_cli_complex()
    if not args.steps:
        print("Set --steps for the number of frame")
        exit(1)

    screen = Screen(args.winsize)
    scene = MandelbrotSet(args)
    screen.add(scene)

    animation = zoom_out(
        [args.radius, 1.3], [args.center, complex(-0.8, 0)], args.steps)

    for frame in range(args.skip, args.steps):
        animation(scene, frame)
        scene.render(frame, draw_axis=False)
        screen.update()
        pygame.display.update()
        if args.record:
            screen.capture(args.record, frame)


if __name__ == "__main__":
    run_main(main)
