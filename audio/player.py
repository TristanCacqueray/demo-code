#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0

import os
import sys
import pygame

from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, K_ESCAPE, K_RETURN
from pygame.locals import K_LEFT, K_RIGHT, K_DOWN, K_UP, K_SPACE
try:
    sys.path.append("%s/../python-lib" % os.path.dirname(__file__))
    from pygame_utils import Screen, Window, ComplexPlane, Waterfall, SpectroGraph
    from common import PHI, usage_cli_complex, run_main, gradient, rgb250
    from scipy_utils import Audio, SpectroGram
    from pygame_utils import ColorMod
    from midi import Midi
except ImportError:
    raise


def main():
    args = usage_cli_complex(worker=1)

    if not args.wav:
        print("--wav is required")
        exit(1)

    if args.midi:
        midi = Midi(args.midi)
    else:
        midi = None

    audio = Audio(args.wav, args.fps, play=True)
    print("Frame numbers = %d" % audio.audio_frame_number)
    clock = pygame.time.Clock()

    screen = Screen(args.winsize)

    spectre = SpectroGram(audio.audio_frame_size)
    x, y = args.winsize
    waterfall = Waterfall((2 * x//3, y//2), audio.audio_frame_size, 2)
    graph = SpectroGraph((x, y//2), audio.audio_frame_size)

    max_freq = audio.audio_frame_size // 2
    high_color = ColorMod((x//3, y//6), (308, max_freq), "avg")
    mid_color = ColorMod((x//3, y//6), (30, 70), "mean", base_hue=0.4)
    low_color = ColorMod((x//3, y//6), (4, 8), "mean", base_hue=0.1)

    screen.add(waterfall, (x//3, 0))
    screen.add(graph, (0, y//2))
    screen.add(high_color)
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
            high_color.render(spectre)
            mid_color.render(spectre)
            low_color.render(spectre)

            screen.update()
            pygame.display.update()
            if midi:
                midi_events = midi.get(args.midi_skip + frame)
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
    run_main(main)
