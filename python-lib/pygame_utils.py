#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0

import os
import numpy as np

from common import *
import pygame
import pygame.draw
import pygame.image
from pygame.locals import *

# for headless rendering
if "XAUTHORITY" not in os.environ:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
if "AUDIO" not in os.environ:
    os.environ["SDL_AUDIODRIVER"] = "dummy"


# Pygame abstraction
class Screen:
    def __init__(self, screen_size):
        pygame.init()
        self.font = pygame.font.SysFont(u'dejavusansmono', 18)
        self.screen = pygame.display.set_mode(screen_size)
        self.windows = []

    def draw_msg(self, msg, coord=(5, 5), color=(180, 180, 255)):
        text = self.font.render(msg, True, color)
        self.screen.blit(text, coord)

    def capture(self, dname, frame):
        if not os.path.isdir(dname):
            os.mkdir(dname)
        fname = "%s/%04d.png" % (dname, frame)
        try:
            pygame.image.save(self.screen, fname)
            print("Saved to %s" % fname)
        except Exception as e:
            print(fname, e)
            raise

    def add(self, window, coord=(0, 0)):
        self.windows.append((window, coord))

    def update(self):
        for window, coord in self.windows:
            if window.pixels is not None:
                pygame.surfarray.blit_array(window.surface, window.pixels)
            self.screen.blit(window.surface, coord)


class ScreenPart:
    def __init__(self, window_size):
        try:
            self.surface = pygame.Surface(window_size)
            self.window_size = map(int, window_size)
            self.length = self.window_size[0] * self.window_size[1]
            self.pixels = np.zeros(self.length, dtype='i4').reshape(
                *self.window_size)
        except:
            print("Invalid window_size", window_size)
            raise

    def blit(self, nparray):
        pygame.surfarray.blit_array(self.surface, nparray.reshape(
            *self.window_size))

# Ready to use 'widget'
class WavGraph(ScreenPart):
    def __init__(self, window_size, frame_size):
        ScreenPart.__init__(self, window_size)
        self.frame_size = frame_size
        self.wav_step = self.frame_size / self.window_size[1]
        self.x_range = self.window_size[0] / 2

    def render(self, buf):
        # Wav graph
        pixels = np.zeros(self.length, dtype='i4').reshape(*self.window_size)
        for y in range(0, self.window_size[1]):
            mbuf = np.mean(buf[y * self.wav_step:(y + 1) * self.wav_step],
                           axis=1)
            left = mbuf[0]
            right = mbuf[1]
            mono = np.mean(mbuf)
            # pixels[int(self.x_range + ((self.x_range) / 2.) * mono / (MAX_SHORT/2.))][y] = 0xf1
            # pixels[1 + int(self.x_range-1) * abs(right) / MAX_SHORT][y] = 0x00f100
            # pixels[self.window_size[0] - 1 - int(self.x_range) * abs(left) / MAX_SHORT][y] = 0xf10000
            for point, offset, color in ((left, -10, 0xf10000),
                                         (right, +10, 0x00f100),
                                         (mono, 0, 0xf1)):
                pixels[int(self.x_range + offset + (
                    (self.x_range - abs(offset)) / 2.) * point /
                           (MAX_SHORT/2.))][y] = color
        self.pixels = pixels


class Waterfall(ScreenPart):
    def __init__(self, window_size, frame_size, width=1):
        ScreenPart.__init__(self, window_size)
        self.frame_size = frame_size
        self.width = width

    def render(self, spectrogram):
        self.pixels = np.roll(self.pixels, -1, axis=0)
        for y in range(self.window_size[1] - 1, 0, -1):
            inv_y = self.window_size[1] - y
            if self.width == 1:
                point = spectrogram.freq[inv_y]
            else:
                if (inv_y + 1) * self.width >= len(spectrogram.freq):
                    break
                point = np.mean(spectrogram.freq[int(inv_y * self.width):
                                                 int((inv_y + 1) * self.width)])
            self.pixels[-1][y] = hsv(0.5 + 0.3 * point, 0.3 + 0.6 * point, 0.2 + 0.8 * point)


# Legacy abstraction
class Window:
    def __init__(self, window_size):
        self.surface = pygame.Surface(window_size)
        self.font = pygame.font.SysFont(u'dejavusansmono', 18)
        self.window_size = window_size
        self.length = window_size[0] * window_size[1]
        self.pixels = None

    def fill(self, color=[0]*3):
        self.surface.fill(color)

    def draw_msg(self, msg, coord=(5, 5), color=(180, 180, 255)):
        text = self.font.render(msg, True, color)
        self.surface.blit(text, coord)

    def draw_line(self, start_coord, end_coord, color=(28, 28, 28)):
        pygame.draw.line(self.surface, color, start_coord, end_coord)

    def draw_point(self, coord, color=[242]*3):
        self.surface.set_at(coord, color)

    def blit(self, nparray):
        pygame.surfarray.blit_array(self.surface,
                                    nparray.reshape(*self.window_size))


class Plane(ComplexPlane, Window):
    pass


def main(argv):
    WINSIZE = (600, 600)
    screen = Screen(WINSIZE)
    plane = Plane(WINSIZE)
    plane.set_view(0, 3)
    screen.add(plane)

    src_path = np.array((0j, -1j, 0j, 1j, 0j, -1-1j))
    final_path = np.array((-1-1j, -1+1j, 1+1j, 0, 0.5-1j, 1-0.5j))
    current_path = np.copy(src_path)
    clock = pygame.time.Clock()
    frame = 0
    while True:
        plane.fill()
        plane.draw_axis()

        path = Path(current_path, 600)
        current_path += (final_path - current_path) / 24.0
        if (frame+1) % 100 == 0:
            t = final_path
            final_path = src_path
            src_path = t
            current_path = src_path

        for point in path.gen_lines():
            plane.draw_complex(point)

        for point in path.gen_logs():
            plane.draw_complex(point, color=(0,96, 96))

        for point in path.gen_sin(0.2 * math.cos(frame / 7.0),
                                  7 * (abs(math.sin(frame / 60.0)))):
            plane.draw_complex(point, color=(42, 120, 23))

        for point in path.gen_splines():
            plane.draw_complex(point, color=(120, 10, 50))

        screen.update()
        pygame.display.update()

        for e in pygame.event.get():
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                exit(0)

        frame += 1
        clock.tick(12)

if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        raise
        pass
