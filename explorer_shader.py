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
    parser.add_argument("--skip", type=int, default=0)
    parser.add_argument("--max-frame", type=int, default=65535)
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--paused", action="store_true")
    parser.add_argument("--params", help="manual parameters")
    parser.add_argument("fragment", help="fragment file",
                        nargs='?')
    args = parser.parse_args(argv)
    if args.fragment is None:
        args.fragment = "fragments/new.glsl"
    if args.params is not None:
        if os.path.exists(args.params):
            args.params = json.loads(open(args.params))
        else:
            args.params = json.loads(args.params)
    if args.record and not os.path.exists(args.record):
        os.makedirs(args.record)
    args.winsize = list(map(lambda x: int(x * args.size), [160,  90]))
    return args


def main():
    args = usage()
    scene = FragmentShader(args)
    backend = app.__backend__
    clock = app.__init__(backend=backend, framerate=args.fps)
    scene.alive = True
    topause = args.paused
    frame = args.skip
    while scene.alive:
        start_time = time.monotonic()
        if scene.update(frame):
            scene.render(frame)
        if args.record:
            scene.capture(os.path.join(args.record, "%04d.png" % frame))
            backend.process(0)
        else:
            backend.process(clock.tick())
        if scene.paused:
            continue
        frame += 1
        if topause:
            topause = False
            scene.paused = True
        print("%04d: %.2f sec %s" % (
            frame, time.monotonic() - start_time,
            json.dumps(scene.controller.get(), sort_keys=True)))
        if frame > args.max_frame:
            break

    if args.record:
        import subprocess
        cmd = [
            "ffmpeg", "-y", "-framerate", str(args.fps),
            "-i", "%s/%%04d.png" % args.record,
            "-c:v", "copy",
            "%s/render.mp4" % (args.record)]
        print("Running: %s" % " ".join(cmd))
        subprocess.Popen(cmd).wait()


if __name__ == "__main__":
    main()
