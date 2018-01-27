#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0

# supersampling:
# ls [0-9]*.png | xargs -L 1 -P 8 -I png convert png -resize 375x375 gpng
# encoding:
# ffmpeg -y -framerate 25 -i g%04d.png -i minimeda.wav -c:a libvorbis \
#    -c:v libx264 -threads 8 -b:v 512M minimeda.mp4

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

from burning_julia import BurningJuliaSet


class Demo(Animation):
    def __init__(self, scene):
        self.scenes = [
            [2600, None],
            [2150, self.end],
            [1550, self.long],
            [1500, self.tr],
            [750,  self.kick],
            [0,    self.intro],
        ]
        super().__init__()
        self.scene = scene
        self.mid = ColorMod((1, 1), (20, 120), "high", base_hue=0.4, decay=30)
        self.low = ColorMod((1, 1), (4, 8), "mean", base_hue=0.1, decay=100)
        self.kick = 0

    def end(self, frame):
        if self.scene_init:
            self.r_mod = self.logspace(self.base_radius, 0.5)
            self.p_mod = self.logspace(1, 100000000)
        if self.mid_mod:
            self.base_c += 3e-11 * self.mid_mod * self.p_mod[self.scene_pos]
        else:
            self.base_c += 1e-11 * self.p_mod[self.scene_pos]
        self.scene.c = self.base_c
        self.scene.set_view(radius=self.r_mod[self.scene_pos])

    def long(self, frame):
        if self.scene_init:
            self.base_c = self.scene.c
        if self.mid_mod:
            self.base_c += 1e-11 * self.mid_mod
        if self.kick > 0.1:
            self.base_c -= 2e-10j * self.kick
        self.scene.c = self.base_c
        if self.scene_pos < 50:
            self.base_radius = self.r_mod[self.scene_pos + 30]
            self.scene.set_view(radius=self.base_radius)


    def tr(self, frame):
        if self.scene_init:
            self.c_mod = self.geomspace(
                self.scene.c, -1.7107331882152361-0.011338878533109253j)
            self.r_mod = self.logspace(self.base_radius, 1.27278655952e-05, 80)
#            self.i_mod = self.logspace(self.base_iter, 10000)
        self.scene.c = self.c_mod[self.scene_pos]
        if self.scene_pos >= 30:
            self.base_radius = self.r_mod[self.scene_pos - 30]
            self.scene.set_view(radius=self.base_radius)
#        self.scene.max_iter = self.i_mod[self.scene_pos]


    def kick(self, frame):
        if self.scene_init:
            # -1.7107802103169505-0.004076294028543666j
            # 0.0022576303745
            ...
        if self.mid_mod:
            self.base_c -= 0.00007j * self.mid_mod
        self.scene.c = self.base_c + 0.0005 * self.kick

    def intro(self, frame):
        if self.scene_init:
            self.scene.max_iter = 1000
            self.base_c = -1.7107802103169505+0.002469444644572093j
            self.base_radius = 0.0225508404546
            self.scene.set_view(radius=self.base_radius)
            self.base_iter = 1000
        if self.mid_mod:
            self.base_c -= 0.000014j * self.mid_mod
        self.scene.c = self.base_c

    def update(self, frame, spectrogram):
        self.mid_mod = self.mid.get(spectrogram)
        self.low_mod = self.low.get(spectrogram)
        kick = max(0, self.low_mod - 0.6)
        if kick > self.kick:
            self.kick = kick
        else:
            self.kick -= self.kick / 30
        super().update(frame)


def main():
    import sys
    sys.argv.append("--gradient")
    sys.argv.append("../render_data/gradcentral/AG/AG_zebra.ggr")
    args = usage_cli_complex(sys.argv[1:], worker=1)

    if not args.wav:
        print("--wav is required")
        exit(1)

    audio = Audio(args.wav, args.fps, play=not args.record)

    spectre = SpectroGram(audio.audio_frame_size)
    clock = pygame.time.Clock()

    screen = Screen(args.winsize)

    scene = BurningJuliaSet(args)

    demo = Demo(scene)

    screen.add(scene)

    frame = args.skip
    paused = False

    # Warm opencl
    scene.render(0)
    audio.play = False
    for skip in range(args.skip):
        audio_buf = audio.get(skip)
        spectre.transform(audio_buf)
        demo.update(skip, spectre)
    audio.play = not args.record

    while True:
        if not paused:
            try:
                audio_buf = audio.get(frame)
                spectre.transform(audio_buf)
            except IndexError:
                audio_buf = 0

            try:
                demo.update(frame, spectre)
            except ValueError:
                break

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
