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
import logging
import os
import sys
import pygame
import numpy

import utils.audio
import utils.game
import utils.widgets
from utils.audio import AudioMod

from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, K_ESCAPE
from pygame.locals import K_LEFT, K_RIGHT, K_DOWN, K_UP, K_SPACE

import hy
import utils.modulations as M


def usage(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Explore audio filters")
    parser.add_argument("--list-sound-devices", action='store_true')
    parser.add_argument("--sound-device")
    parser.add_argument("--size", type=float,
                        default=float(os.environ.get("SIZE", 7)),
                        help="render size x for (160x90) * x")
    parser.add_argument("--fps", type=int, default=25,
                        help="frames per second")
    parser.add_argument("--debug", action="store_true",
                        help="show debug information")
    parser.add_argument("--wav")
    parser.add_argument("--skip", default=0, type=int)
    args = parser.parse_args(argv)
    if args.list_sound_devices:
        import sounddevice
        print(sounddevice.query_devices())
        exit(0)

    if args.sound_device or os.environ.get("DEMO_SD"):
        import sounddevice
        if args.sound_device:
            sounddevice.default.device = int(args.sound_device)
        else:
            sounddevice.default.device = int(os.environ["DEMO_SD"])

    args.winsize = list(map(lambda x: int(x * args.size), [160,  90]))
    logging.basicConfig(
        format='%(asctime)s %(levelname)-5.5s %(name)s - %(message)s',
        level=logging.DEBUG if args.debug else logging.INFO)
    return args


def main():
    args = usage()

    audio = utils.audio.Audio(args.wav, args.fps, play=False)
    player = utils.audio.AudioPlayer(
        audio.freq, audio.blocksize, audio.channels)
    print("Frame numbers = %d" % audio.audio_frame_number)
    clock = pygame.time.Clock()

    screen = utils.game.Screen(args.winsize)

    filters = utils.audio.Filters(dict(
#        hpass=utils.audio.FilterButter(500, 'hp', audio.freq)
        lpass=utils.audio.FilterIIR(0.01, 0.1, ftype='ellip'),
        mpass=utils.audio.FilterIIR((0.1, 0.2),  (0.05, 0.25), ftype='ellip'),
        hpass=utils.audio.FilterIIR(0.3, 0.2, ftype='ellip')))

    lmod = M.AudioFilterModulator("lpass") #, 15)
    mmod = M.AudioFilterModulator("mpass")
    hmod = M.AudioFilterModulator("hpass") #, 10)

    x, y = args.winsize
    wav_graph = utils.widgets.WavGraph((2*x//3, y//2), audio.blocksize)

    hgh_color = utils.widgets.ModColor((x//3, y//6))
    hgh_graph = utils.widgets.WavGraph((2*x//3, y//6), audio.blocksize)
    mid_color = utils.widgets.ModColor((x//3, y//6), base_hue=0.4)
    low_color = utils.widgets.ModColor((x//3, y//6), base_hue=0.1)

    screen.add(wav_graph, (1*x//3, y//2))
    screen.add(hgh_color)
    screen.add(hgh_graph, (1*x//3, 0))
    screen.add(mid_color, (0, y//6))
    screen.add(low_color, (0, 2*y//6))

    frame = args.skip
    paused = False
    while True:
        if not paused:
            audio_buf = audio.get(frame)
            wav_graph.render_mono(audio_buf)
            filters.update(audio_buf)
            #audio_fbuf = filters.play_data("mpass")

            low_color.render(lmod(filters))
            mid_color.render(mmod(filters))
            hgh_color.render(hmod(filters))
            #hgh_graph.render_monobuf(filters.data["hpass"])
            #print(type(audio_fbuf), len(audio_fbuf), audio_fbuf[:10])

            player.play(audio_buf)
            #player.play(filters.play_data("hpass"))
            #if frame > 5:
            #    break

            screen.update()
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

        clock.tick(args.fps)
        if frame % args.fps == 0:
            print("%d\r" % (frame // args.fps), end='')

if __name__ == "__main__":
    main()
