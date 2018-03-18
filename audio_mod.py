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

import utils.midi
import utils.audio
import utils.game
import utils.widgets

from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, K_ESCAPE
from pygame.locals import K_LEFT, K_RIGHT, K_DOWN, K_UP, K_SPACE


def usage(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Explore audio and adjust mod")
    parser.add_argument("--size", type=float,
                        default=float(os.environ.get("SIZE", 7)),
                        help="render size x for (160x90) * x")
    parser.add_argument("--fps", type=int, default=25,
                        help="frames per second")
    parser.add_argument("--debug", action="store_true",
                        help="show debug information")
    parser.add_argument("--midi")
    parser.add_argument("--midi-skip", type=int, default=0)
    parser.add_argument("--wav")
    parser.add_argument("--skip", default=0, type=int)
    args = parser.parse_args(argv)
    args.winsize = list(map(lambda x: int(x * args.size), [160,  90]))
    logging.basicConfig(
        format='%(asctime)s %(levelname)-5.5s %(name)s - %(message)s',
        level=logging.DEBUG if args.debug else logging.INFO)
    return args


def main():
    args = usage()

    if not args.wav:
        print("--wav is required")
        exit(1)

    if args.midi:
        midi = utils.midi.Midi(args.midi)
    else:
        midi = None

    audio = utils.audio.Audio(args.wav, args.fps, play=True)
    print("Frame numbers = %d" % audio.audio_frame_number)
    clock = pygame.time.Clock()

    screen = utils.game.Screen(args.winsize)

    spectre = utils.audio.SpectroGram(audio.audio_frame_size)
    x, y = args.winsize
    waterfall = utils.widgets.Waterfall((2 * x//3, y//2), 2)
    graph = utils.widgets.SpectroGraph((x, y//2), audio.audio_frame_size)

    max_freq = audio.audio_frame_size // 2
    if not args.midi:
        hgh_mod = utils.audio.AudioMod((373, max_freq), "max")
        mid_mod = utils.audio.AudioMod((25, 70), "avg")
        low_mod = utils.audio.AudioMod((0, 24), "max")
    else:
        hgh_mod = utils.midi.MidiMod("snare")
        mid_mod = utils.midi.MidiMod("kick")
        low_mod = utils.midi.MidiMod("andy 67", decay=1)
    hgh_color = utils.widgets.ModColor((x//3, y//6))
    mid_color = utils.widgets.ModColor((x//3, y//6), base_hue=0.4)
    low_color = utils.widgets.ModColor((x//3, y//6), base_hue=0.1)

    screen.add(waterfall, (x//3, 0))
    screen.add(graph, (0, y//2))
    screen.add(hgh_color)
    screen.add(mid_color, (0, y//6))
    screen.add(low_color, (0, 2*y//6))

    frame = args.skip
    paused = False
    while True:
        if not paused:
            audio_buf = audio.get(frame)

            spectre.transform(audio_buf)
            graph.render(spectre)
            waterfall.render(spectre)
            if not args.midi:
                hgh_color.render(hgh_mod.update(spectre))
                mid_color.render(mid_mod.update(spectre))
                low_color.render(low_mod.update(spectre))

            screen.update()
            pygame.display.update()
            if midi:
                midi_events = midi.get(args.midi_skip + frame)
                hgh_color.render(hgh_mod.update(midi_events))
                mid_color.render(mid_mod.update(midi_events))
                low_color.render(low_mod.update(midi_events))
                if midi_events:
                    print(frame, midi_events)
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
