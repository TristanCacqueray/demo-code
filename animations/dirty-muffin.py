#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0

import os
import sys
import pygame
import numpy as np

from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, K_ESCAPE, K_RETURN
from pygame.locals import K_LEFT, K_RIGHT, K_DOWN, K_UP, K_SPACE
try:
    sys.path.append("%s/../python-lib" % os.path.dirname(__file__))
    sys.path.append("%s/../complex-fractal" % os.path.dirname(__file__))
    from pygame_utils import Screen, Window, ComplexPlane, Waterfall, SpectroGraph
    from common import PHI, usage_cli_complex, run_main, gradient, rgb250
    from common import Animation
    from midi import Midi
    from scipy_utils import Audio, SpectroGram, AudioBand, AudioMod
    from pygame_utils import ColorMod, Graph
except ImportError:
    raise

from julia_set import JuliaSet


class Demo(Animation):
    def __init__(self, scene, midi, mod):
        self.scenes = [
            [6625, None],
            [6006, self.end],
            [5250, self.intim1],
            [4015, self.bass1],
            [2242, self.tr1],
            [0,    self.intro],
        ]
        super().__init__()
        self.scene = scene
        self.midi = midi
        self.mod = mod

        self.piano = 0
        self.space_piano = 0
        self.kick = 0
        self.hat = 0
        self.snare = 0
        self.bass_mod = 0

        self.zoom_mod = None

    def end(self, frame):
        if self.scene_init:
            self.zoom_mod = self.logspace(0.1, 7)
            self.pow_mod = self.logspace(1, 100)
        self.scene.c -= (0.00001-0.0001j) * self.pow_mod[self.scene_pos]

    def intim1(self, frame):
        if self.scene_init:
            self.base_c = self.scene.c
#            self.zoom_mod = self.logspace(0.1, 0.2)
        if self.piano:
            self.snare = 0
            self.base_c += complex(0, 0.00008)
            self.piano = 0
#            self.kick = self.kick / 2
#            self.kick = 0
#        self.base_c += complex(0, 0.00001) * self.piano
        self.scene.c = self.base_c + \
            1e-4 * self.kick + \
            complex(0, 8e-5) * self.snare

    def bass1(self, frame):
        if self.scene_init:
            self.zoom_mod = None
            self.piano = 0
            self.base_c = self.scene.c
            self.fadeout = self.logspace(0.00951363581679, 0.1, 20)
        if self.piano:
            self.base_c += 1e-7
            self.piano = 0
            self.snare = 0
        self.scene.c = self.base_c + \
            complex(0, 1e-6) * self.kick + \
            complex(-3e-6, 0) * self.snare
        if frame > 5230:
            self.scene.set_view(radius=self.fadeout[frame - 5230])

    def tr1(self, frame):
        if self.scene_init:
            self.zoom_mod = self.logspace(self.base_radius, 0.00951363581679)
            self.pow_mod = self.logspace(1, 500)
            self.base_c = self.scene.c
            self.bass = 0
        if frame < 3000:
            bass = np.max(self.mod.get(frame)) * 3
            if bass > self.bass:
                self.bass += (bass - self.bass) / 5
            else:
                self.bass -= (self.bass - bass) / 10
            self.scene.c = self.base_c + \
                self.pow_mod[self.scene_pos] * 0.1e-12 * self.bass
#            if self.bass > 0:
#                self.bass -= self.bass / 50
        else:
            if self.piano:
                self.base_c += self.pow_mod[self.scene_pos] * 1e-9
                self.piano = 0
                self.snare = self.snare / 10
            self.scene.c = self.base_c + \
                self.pow_mod[self.scene_pos] * complex(0, 1e-9) * self.kick + \
                self.pow_mod[self.scene_pos] * complex(-1e-9, 0) * self.snare

    def intro(self, frame):
        if self.scene_init:
            self.scene.max_iter = 5000
            self.base_c = -0.7488757803975103+0.06927834896471036j
            self.base_radius = 4.02263406465e-05
            self.scene.set_view(radius=self.base_radius)
        if frame == 0:
            self.scene.c = self.base_c
            self.piano = 0
        else:
            if self.piano:
                self.base_c += 3e-12
                self.piano = 0
                self.snare = 0
            snare_effect = -1e-11
            if frame < 1250:
                kick_effect = 8e-12
            else:
                kick_effect = 4e-11
            self.scene.c = self.base_c + \
                complex(0, kick_effect) * self.kick +  \
                complex(snare_effect, 0) * self.snare

    def update(self, frame):
        try:
            midi_events = self.midi.get(frame + 250)
        except Exception:
            midi_events = []
        for event in midi_events:
            if event["track"] == "Intim8" or event["track"] == "tow of us":
                for ev in event["ev"]:
                    if ev["type"] == "chords":
                        self.piano = np.max(list(ev["pitch"].values())) / 127
                    else:
                        print(ev)
            elif event["track"].startswith("les "):
                print("HEREEE", event)
                for ev in event["ev"]:
                    if ev["type"] == "chords":
                        self.space_piano = np.max(
                            list(ev["pitch"].values())) / 127
                    else:
                        print(ev)
            elif event["track"] == "kick":
                for ev in event["ev"]:
                    if ev["type"] == "chords":
                        for pitch in ev["pitch"]:
                            if pitch == 48:
                                self.kick = ev["pitch"][48] / 127
                            else:
                                print("Drum %d : %d" % (
                                    pitch, ev["pitch"][pitch]))
                    else:
                        print(ev)
            elif event["track"] == "snares":
                for ev in event["ev"]:
                    if ev["type"] == "chords":
                        for pitch in ev["pitch"]:
                            if pitch == 112:
                                self.snare = ev["pitch"][112] / 127
                            else:
                                print("Snare %d: %d" % (
                                    pitch, ev["pitch"][pitch]))

            elif event["track"] == "DirtyBass":
                for ev in event["ev"]:
                    if ev["type"] == "mod" and ev["mod"] == 1:
                        if ev["val"] < self.bass_mod * 127:
                            self.bass_mod -= self.bass_mod / 10
                        else:
                            self.bass_mod = ev["val"] / 127
            else:
                print(event)
        super().update(frame)
        if self.zoom_mod is not None:
            self.scene.set_view(radius=self.zoom_mod[self.scene_pos])

        if self.piano > 0:
            self.piano -= self.piano / 25
        if self.space_piano > 0:
            self.space_piano -= self.space_piano / 50
        if self.kick > 0:
            self.kick -= self.kick / 10
        if self.snare > 0:
            self.snare -= self.snare / 10
        if self.hat > 0:
            self.hat -= self.hat / 10
        self.piano


def main():
    import sys
#    sys.argv.append("--gradient")
#    sys.argv.append("/usr/share/gimp/2.0/gradients/Four_bars.ggr")
    args = usage_cli_complex(sys.argv[1:], worker=1)
    args.color = "gradient_freq"
    args.midi_skip = 250

    if not args.wav:
        print("--wav is required")
        exit(1)

    if not args.audio_mod:
        args.audio_mod = "../render_data/muffin/dirty_muffin-vti_satubass.wav"

    mod = Audio(args.audio_mod, args.fps, play=False)

    audio = Audio(args.wav, args.fps, play=not args.record)
    midi = Midi(args.midi, args.fps)

    clock = pygame.time.Clock()

    screen = Screen(args.winsize)

    scene = JuliaSet(args)

    demo = Demo(scene, midi, mod)

    screen.add(scene)

    frame = args.skip
    paused = False

    # Warm opencl
    scene.render(0)
    for skip in range(args.skip):
        demo.update(skip)

    while True:
        if not paused:
            try:
                audio.get(frame)
            except IndexError:
                break

            demo.update(frame)

            scene.render(frame)
            screen.update()
            if args.record:
                screen.capture(args.record, frame)
            pygame.display.update()
            frame += 1

        for e in pygame.event.get():
            if e.type not in (KEYDOWN, MOUSEBUTTONDOWN):
                continue
            if e.type == MOUSEBUTTONDOWN:
                print("Clicked", e.pos)
            else:
                if e.key == K_RIGHT:
                    frame += args.fps
                elif e.key == K_LEFT:
                    frame = max(0, frame - args.fps)
                elif e.key == K_UP:
                    frame += args.fps * 60
                elif e.key == K_DOWN:
                    frame = max(0, frame - args.fps * 60)
                elif e.key == K_SPACE:
                    paused = not paused
                elif e.key == K_ESCAPE:
                    exit(0)

        if not args.record:
            clock.tick(args.fps)
    if args.video and args.record:
        import subprocess
        subprocess.Popen([
            "ffmpeg", "-y", "-framerate", str(args.fps),
            "-start_number", str(args.skip),
            "-i", "%s/%%04d.png" % args.record,
            "-i", args.wav,
            "-c:a", "libvorbis", "-c:v", "libvpx", "-threads", "4",
            "-b:v", "5M",
            "%s/%04d-%s.webm" % (args.record, args.skip, args.anim)
        ]).wait()


if __name__ == "__main__":
    run_main(main)
