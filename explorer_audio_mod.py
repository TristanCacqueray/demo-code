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
from utils.audio import AudioMod
from utils.midi import MidiMod

from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, K_ESCAPE
from pygame.locals import K_LEFT, K_RIGHT, K_DOWN, K_UP, K_SPACE

import hy
import utils.modulations as M


def usage(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Explore audio and adjust mod")
    parser.add_argument("--list-sound-devices", action='store_true')
    parser.add_argument("--sound-device")
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

    if args.midi:
        midi = utils.midi.Midi(args.midi)
    else:
        midi = None

    audio = utils.audio.Audio(args.wav, args.fps, play=True)
    print("Frame numbers = %d" % audio.audio_frame_number)
    clock = pygame.time.Clock()

    screen = utils.game.Screen(args.winsize)

    spectre = utils.audio.SpectroGram(audio.blocksize)
    x, y = args.winsize
    waterfall = utils.widgets.Waterfall((2 * x//3, y//2), 2)
    graph = utils.widgets.SpectroGraph((x, y//2), audio.blocksize)

    max_freq = audio.blocksize // 2
    if True:
        audio_events = {
            "hgh": M.AudioModulator((575, max_freq)),
            "mid": M.AudioModulator((36, 100)),
            "low": M.AudioModulator((0, 22)),
        }
        midi_events = {
            "hgh": M.PitchModulator("SpacePiano1"),
            "mid": M.PitchModulator("Redrum 1 copy"),
            "low": M.PitchModulator("DirtyBass"),
        }

    if not args.midi:
        hgh_mod = audio_events["hgh"]
        mid_mod = audio_events["mid"]
        low_mod = audio_events["low"]
    else:
        hgh_mod = midi_events["hgh"]
        mid_mod = midi_events["mid"]
        low_mod = midi_events["low"]
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
    # TODO: add a toggle to enable midi mod event debug
    debug_mod_ev = set()
    while True:
        if not paused:
            audio_buf = audio.get(frame)

            spectre.transform(audio_buf)
            graph.render(spectre)
            waterfall.render(spectre)
            if not args.midi:
                hgh_color.render(hgh_mod(spectre))
                mid_color.render(mid_mod(spectre))
                low_color.render(low_mod(spectre))

            screen.update()
            pygame.display.update()
            if midi:
                midi_events = midi.get(args.midi_skip + frame)
                #print(v)
                hgh_color.render(hgh_mod(midi_events))
                mid_color.render(mid_mod(midi_events))
                low_color.render(low_mod(midi_events))
                if midi_events:
                    # Look for mod event
                    mod_ev = False
                    for event in midi_events:
                        mod_evs = [ev for ev in event["ev"]
                                   if ev["type"] == "mod"]
                        if mod_evs:
                            for ev in mod_evs:
                                ev_id = "%s-%s" % (event["track"], ev["mod"])
                                if ev_id in debug_mod_ev:
                                    # TODO: remove the event instead
                                    mod_ev = True
                                    debug_mod_ev.add(ev_id)
                                    break
                    # Skip mod event, (todo: remove empty track)
                    if not mod_ev:
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
