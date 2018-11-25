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
import json
import time
import os
import numpy as np
from PIL import Image

from glumpy import app, gl, gloo
from glumpy.app.window import key
from glumpy.app.window.event import EventDispatcher

from . controller import Controller
from . audio import Audio, NoAudio
from . midi import Midi, NoMidi


class Window(EventDispatcher):
    alive = True
    draw = True

    def __init__(self, winsize, screen):
        self.winsize = winsize
        self.window = screen
        self.init_program()
        self.fbuffer = np.zeros(
            (self.window.height, self.window.width * 3), dtype=np.uint8)

    def capture(self, filename):
        gl.glReadPixels(
            0, 0, self.window.width, self.window.height,
            gl.GL_RGB, gl.GL_UNSIGNED_BYTE, self.fbuffer)
        image = Image.frombytes("RGB", self.winsize, np.ascontiguousarray(np.flip(self.fbuffer, 0)))
        image.save(filename, 'png')

    def on_draw(self, dt):
        pass

    def on_resize(self, width, height):
        pass

    def on_key_press(self, k, modifiers):
        if k == key.ESCAPE:
            self.alive = False
        elif k == key.SPACE:
            self.paused = not self.paused
        self.draw = True


def fragment_loader(filename: str, export: bool):
    final = []
    uniforms = {"mods": {}}
    shadertoy = False

    def loader(lines: list):
        for line in lines:
            if line.startswith("#include"):
                loader(open(os.path.join(os.path.dirname(filename),
                                         line.split()[1][1:-1])
                            ).read().split('\n'))
            else:
                export_line = ""
                if line.startswith('uniform'):
                    param = line.split()[2][:-1]
                    param_type = line.split()[1]
                    if param_type == "float":
                        val = 0.
                    elif param_type == "vec2":
                        val = [0., 0.]
                    elif param_type == "vec3":
                        val = [0., 0., 0.]
                    elif param_type == "vec4":
                        val = [0., 0., 0., 0.]
                    else:
                        raise RuntimeError("Unknown uniform %s" % line)
                    if '//' in line:
                        if 'slider' in line:
                            slider_str = line[line.index('slider'):].split(
                                '[')[1].split(']')[0]
                            smi, sma, sre = list(map(
                                float, slider_str.split(',')))
                            uniforms["mods"][param] = {
                                "type": param_type,
                                "sliders": True,
                                "min": smi,
                                "max": sma,
                                "resolution": sre,
                            }
                        val_str = line.split()[-1]
                        if param_type == "float":
                            val = float(val_str)
                        elif param_type == "vec3":
                            val = list(map(float, val_str.split(',')))
                        uniforms[param] = val
                        if shadertoy:
                            if param_type.startswith("vec"):
                                val_str = "%s%s" % (param_type, tuple(val))
                            else:
                                val_str = str(val)
                            export_line = "const %s %s = %s;" % (
                                param_type, param, val_str
                            )
                if export and export_line:
                    final.append(export_line)
                else:
                    final.append(line)
    fragment = open(filename).read()
    if "void mainImage(" in fragment:
        shadertoy = True
        if not export:
            final.append("""uniform vec2 iResolution;
uniform vec4 iMouse;
uniform float iTime;
void mainImage(out vec4 fragColor, in vec2 fragCoord);
void main(void) {mainImage(gl_FragColor, gl_FragCoord.xy);}""")
    loader(fragment.split('\n'))
    return "\n".join(final), uniforms


class FragmentShader(Window):
    """A class to simplify raymarcher/DE experiment"""
    vertex = """
attribute vec2 position;

void main(void) {
  gl_Position = vec4(position, 0., 1.);
}
"""
    buttons = {
        app.window.mouse.NONE: 0,
        app.window.mouse.LEFT: 1,
        app.window.mouse.MIDDLE: 2,
        app.window.mouse.RIGHT: 3
    }

    def __init__(self, args):
        self.fps = args.fps
        self.record = args.record
        self.iMouse = None
        self.old_program = None
        self.load_program(args.fragment, args.export)
        self.program_params = set(self.params.keys()) - set(('mods', ))
        self.controller = Controller(self.params, default={})
        self.screen = app.Window(width=args.winsize[0], height=args.winsize[1])
        super().__init__(args.winsize, self.screen)
        self.controller.set(self.screen, self)
        self.screen.attach(self)
        self.paused = False

    def load_program(self, fragment_path, export=False):
        self.fragment_path = fragment_path
        self.fragment_mtime = os.stat(fragment_path).st_mtime
        self.fragment, self.params = fragment_loader(fragment_path, export)
        if export:
            print(self.fragment)
            exit(0)

    def init_program(self):
        # Ensure size is set
        #print("program param: ", self.program_params)
        #print("---[")
        #print(self.fragment)
        #print("]---")
        self.program = gloo.Program(self.vertex, self.fragment, count=4)
        self.program['position'] = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
        # TODO: make those setting parameter
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        self.on_resize(*self.winsize)
        if self.iMouse:
            self.program["iMouse"] = self.iMouse

    def update(self, frame):
        self.draw = False
        mtime = os.stat(self.fragment_path).st_mtime
        if mtime > self.fragment_mtime:
            self.old_program = self.program
            self.load_program(self.fragment_path)
            self.init_program()
        if self.controller.root:
            self.controller.root.update()
        if self.paused:
            return self.draw
        self.draw = True
        return self.draw

    def render(self, dt):
        self.window.clear()
        for p in self.program_params:
            self.program[p] = self.params[p]
        dt = dt / self.fps

        self.program["iTime"] = dt
        try:
            self.program.draw(gl.GL_TRIANGLE_STRIP)
            if self.old_program:
                self.old_program.delete()
                del self.old_program
                self.old_program = None
                print("Loaded new program!")
        except RuntimeError:
            if not self.old_program:
                raise
            self.old_program.draw(gl.GL_TRIANGLE_STRIP)
            self.program.delete()
            del self.program
            self.program = self.old_program
            self.old_program = None
            self.paused = True
    def on_resize(self, width, height):
        self.program["iResolution"] = width, height
        self.winsize = (width, height)
        self.draw = True

    def on_mouse_drag(self, x, y, dx, dy, button):
        self.iMouse = x, self.winsize[1] - y, self.buttons[button], 0
        self.program["iMouse"] = self.iMouse
        if "pitch" in self.params:
            self.params["pitch"] -= dy / 50
        if "yaw" in self.params:
            self.params["yaw"] += dx / 50
        self.draw = True

    def on_mouse_release(self, x, y, button):
        self.program["iMouse"] = x, self.winsize[1] - y, 0, 0

    def on_mouse_scroll(self, x, y, dx, dy):
        if "fov" in self.params:
            self.params["fov"] += self.params["fov"] / 10 * dy
        self.draw = True

    def on_key_press(self, k, modifiers):
        super().on_key_press(k, modifiers)
        if "cam" in self.params:
            s = 0.1
            if k == 87:  # z
                self.params['cam'][2] += s
            if k == 83:  # s
                self.params['cam'][2] -= s
            if k == 65:  # a
                self.params['cam'][0] -= s
            if k == 68:  # d
                self.params['cam'][0] += s
            if k == 69:  # a
                self.params["cam"][1] += s
            if k == 81:  # b
                self.params["cam"][1] -= s
        self.draw = True


def usage():
    parser = argparse.ArgumentParser()
    parser.add_argument("--paused", action='store_true')
    parser.add_argument("--record", metavar="DIR", help="record frame in png")
    parser.add_argument("--wav", metavar="FILE")
    parser.add_argument("--midi", metavar="FILE")
    parser.add_argument("--midi_skip", type=int, default=0)
    parser.add_argument("--fps", type=int, default=25)
    parser.add_argument("--skip", default=0, type=int, metavar="FRAMES_NUMBER")
    parser.add_argument("--size", type=float, default=8,
                        help="render size")
    args = parser.parse_args()
    args.winsize = list(map(lambda x: int(x * args.size), [160,  90]))
    args.map_size = list(map(lambda x: x//5, args.winsize))
    return args


def run_main(demo, Scene):
    args = usage()
    screen = app.Window(width=args.winsize[0], height=args.winsize[1])
    scene = Scene(args.winsize, screen)
    screen.attach(scene)

    backend = app.__backend__
    clock = app.__init__(backend=backend, framerate=args.fps)

    if args.wav:
        audio = Audio(args.wav, args.fps, play=not args.record)
    else:
        audio = NoAudio()
    demo.setAudio(audio)

    if args.midi:
        midi = Midi(args.midi)
    else:
        midi = NoMidi()
    demo.setMidi(midi, args.midi_skip)
    demo.set(screen, scene)

    import pygame
    pygame.init()
    scene.render(0)
    audio.play = False
    demo.silent = True
    for skip in range(args.skip):
        demo.update(skip)
    demo.silent = False
    audio.play = not args.record
    demo.update_sliders()

    scene.alive = True

    if args.paused:
        demo.paused = True
        args.paused = False

    frame = args.skip
    while scene.alive:
        start_time = time.monotonic()
        demo.update(frame)

        if not demo.paused:
            frame += 1
        if scene.render(frame):
            print("%04d: %.2f sec '%s'" % (
                frame, time.monotonic() - start_time,
                json.dumps(demo.get(), sort_keys=True)))

        if args.record:
            scene.capture(os.path.join(args.record, "%04d.png" % frame))

        backend.process(clock.tick())

    if args.record:
        import subprocess
        cmd = [
            "ffmpeg", "-y", "-framerate", str(args.fps),
            "-i", "%s/%%04d.png" % args.record,
            "-i", args.wav,
            "-c:a", "libvorbis", "-c:v", "copy",
            "%s/render.mp4" % (args.record)]
        print("Running: %s" % " ".join(cmd))
        subprocess.Popen(cmd).wait()
