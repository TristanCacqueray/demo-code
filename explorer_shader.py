#!/usr/bin/env python
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
import sys
import os
import json
import time

from utils.gamegl import FragmentShader, app


def usage(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=float,
                        default=float(os.environ.get("SIZE", 7)),
                        help="render size x for (160x90) * x")
    parser.add_argument("--record", metavar="DIR",
                        help="record rendering destination")
    parser.add_argument("--fps", type=int, default=25,
                        help="frames per second")
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--paused", action="store_true")
    parser.add_argument("fragment", help="fragment file",
                        nargs='?')
    args = parser.parse_args(argv)
    if args.fragment is None:
        args.fragment = "fragments/new.glsl"
    args.winsize = list(map(lambda x: int(x * args.size), [160,  90]))
    return args


def main():
    args = usage()
    scene = FragmentShader(args)
    backend = app.__backend__
    clock = app.__init__(backend=backend, framerate=args.fps)
    scene.alive = True
    topause = args.paused
    frame = 0
    while scene.alive:
        start_time = time.monotonic()
        if scene.update(frame):
            scene.render(frame)
        backend.process(clock.tick())
        frame += 1
        if scene.paused:
            continue
        if topause:
            topause = False
            scene.paused = True
        print("%04d: %.2f sec %s" % (
            frame, time.monotonic() - start_time,
            json.dumps(scene.controller.get(), sort_keys=True)))


if __name__ == "__main__":
    main()
