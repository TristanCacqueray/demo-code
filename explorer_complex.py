#!/bin/env python
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import argparse
import logging
import os
import sys
import time
import yaml
import json

from utils import game
from utils.fractal import Fractal
from utils.controller import Controller


log = logging.getLogger()


def usage(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=float,
                        default=float(os.environ.get("SIZE", 7)),
                        help="render size x for (160x90) * x")
    parser.add_argument("--super-sampling", type=int,
                        help="super sampling mode")
    parser.add_argument("--record", metavar="DIR",
                        help="record rendering destination")
    parser.add_argument("--fps", type=int, default=25,
                        help="frames per second")
    parser.add_argument("--debug", action="store_true",
                        help="show debug information")
    parser.add_argument("params", help="fractal parameters",
                        nargs='?')
    parser.add_argument("variant", help="variant parameters",
                        nargs='?')
    args = parser.parse_args(argv)
    if args.params is None:
        args.params = "complex_parameters/mandelbrot.yaml"
    if os.path.exists(args.params):
        if args.params.endswith(".json"):
            args.params = json.loads(open(args.params))
        elif args.params.endswith(".yaml"):
            args.params = yaml.load(open(args.params))
        else:
            raise RuntimeError("%s: unknown file type" % args.params)
    if args.variant is not None:
        if args.variant in args.params.get("variants", {}):
            args.variant = args.params["variants"][args.variant]
        else:
            args.variant = json.loads(args.variant)
    elif isinstance(args.params, str):
        args.params = json.loads(args.params)
    if args.super_sampling:
        args.params["super_sampling"] = args.super_sampling
    args.winsize = list(map(lambda x: int(x * args.size), [160,  90]))
    args.map_size = list(map(lambda x: x//5, args.winsize))
    logging.basicConfig(
        format='%(asctime)s %(levelname)-5.5s %(name)s - %(message)s',
        level=logging.DEBUG if args.debug else logging.INFO)
    return args


class FractalMap(Fractal):
    def create_map_scene(self, win_size, params):
        self.map_scene = Fractal(win_size, params, gpu=self.gpu)

    def add_c(self, c):
        if self.params["show_map"]:
            if self.params["xyinverted"]:
                c = complex(c.imag, c.real)
            if not len(self.previous_c) or self.previous_c[-1] != c:
                self.previous_c.append(c)
                self.draw = True
                if not self.included(c):
                    # Re-center
                    self.params["map_center_real"] = c.real
                    self.params["map_center_imag"] = c.imag
                    self.draw = True

    def draw_previous_c(self):
        length = len(self.previous_c)
        pos = 0
        for c in self.previous_c:
            pos += 1
            self.draw_complex(c, color=[100 + int(100 * (pos / length))]*3)


class MapController(Controller):
    def on_pygame_clic(self, ev):
        scene = self.scene
        view_prefix = "map_" if self.scene.mapmode else ""
        if (self.params["show_map"] and self.scene.map_scene and
                ev.pos[0] < self.scene.map_scene.window_size[0] and
                ev.pos[1] < self.scene.map_scene.window_size[1]):
            # Map mode
            scene = self.scene.map_scene
            view_prefix = "map_"
        plane_coord = scene.convert_to_plane(ev.pos)
        if ev.button in (1, 3):
            if ev.button == 1:
                step = 3/4.0
            else:
                step = 4/3.0
            self.params[view_prefix + "radius"] *= step
            self.params[view_prefix + "center_real"] = plane_coord.real
            self.params[view_prefix + "center_imag"] = plane_coord.imag
            if scene == self.scene.map_scene:
                self.params["i_step"] = self.params["map_radius"] / 10.
                self.params["r_step"] = self.params["map_radius"] / 10.
                self.update_sliders()
            scene.draw = True
        else:
            x, y = "real", "imag"
            if self.params["xyinverted"]:
                plane_coord = complex(plane_coord.imag, plane_coord.real)
                x, y = "imag", "real"
            if not self.scene.map_scene:
                self.params["map_center_real"] = self.params["center_" + x]
                self.params["map_center_imag"] = self.params["center_" + y]
                self.params["map_radius"] = self.params["radius"]
                self.params["i_step"] = self.params["map_radius"] / 10.
                self.params["r_step"] = self.params["map_radius"] / 10.
                self.update_sliders()
                self.params["c_real"] = plane_coord.real
                self.params["c_imag"] = plane_coord.imag
                self.params["center_real"] = 0
                self.params["center_imag"] = 0
                self.params["radius"] = self.start_params["radius"]
                self.params["julia"] = True
                self.scene.draw = True
                if self.params["show_map"]:
                    self.scene.map_scene = FractalMap(self.map_size,
                                                   self.params,
                                                   gpu=self.scene.gpu)
                    self.screen.add(self.scene.map_scene)
            elif scene == self.scene.map_scene:
                self.params["c_real"] = plane_coord.real
                self.params["c_imag"] = plane_coord.imag
                self.scene.draw = True
            else:
                print("Clicked", ev.pos, plane_coord)


def main():
    args = usage()
    controller = MapController(args.params, args.variant)
    controller.map_size = args.map_size
    screen = game.Screen(args.winsize)
    scene = FractalMap(args.winsize, args.params)
    screen.add(scene)
    if args.params["show_map"] and args.params["julia"]:
        scene.map_scene = Fractal(args.map_size, args.params, scene.gpu)
        screen.add(scene.map_scene)
    controller.set(screen, scene)

    clock = game.clock()
    frame = 0
    while scene.alive:
        start_time = time.monotonic()
        controller.update(frame)
        if scene.render(frame):
            print("%04d: %.2f sec --params '%s'" % (
                frame, time.monotonic() - start_time,
                json.dumps(controller.get(), sort_keys=True)))
            screen.update()
        clock.tick(args.fps)
        frame += 1


if __name__ == "__main__":
    main()
