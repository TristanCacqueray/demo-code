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

import pygame
import numpy as np

from . import hsv
from . game import Window


MAX_SHORT = float((2 ** (2 * 8)) / 2)


class WavGraph(Window):
    def __init__(self, window_size, frame_size):
        Window.__init__(self, window_size)
        self.frame_size = frame_size
        self.wav_step = self.frame_size // self.window_size[0]
        self.y_range = self.window_size[1] // 2
        print(self.window_size[0])

    def render(self, buf):
        pixels = np.zeros(self.length, dtype='i4').reshape(*self.window_size)
        for x in range(0, self.window_size[0]):
            mbuf = np.mean(
                buf[x * self.wav_step:(x + 1) * self.wav_step], axis=1)
            if not len(mbuf):
                break
            left = mbuf[0]
            right = mbuf[1]
            mono = np.mean(mbuf)
            for point, offset, color in (
                    (left, -10, 0xf10000),
                    (right, +10, 0x00f100),
                    (mono, 0, 0xf1)):
                amp = int(self.y_range +
                          offset +
                          ((self.y_range - abs(offset)) / 2.) * point /
                          (MAX_SHORT/2.))
                pixels[x][amp] = color
        self.pixels = pixels

    def render_mono(self, buf):
        pixels = np.zeros(self.length, dtype='i4').reshape(*self.window_size)
        for x in range(0, self.window_size[0]):
            mbuf = np.mean(
                buf[x * self.wav_step:(x + 1) * self.wav_step], axis=1)
            if not len(mbuf):
                break
            mono = np.mean(mbuf)
            amp = min(
                int(self.y_range + self.y_range * mono / (MAX_SHORT / 2.0)),
                self.y_range * 2)
            pixels[x][amp] = 0xf1
        self.pixels = pixels

    def render_monobuf(self, buf):
        pixels = np.zeros(self.length, dtype='i4').reshape(*self.window_size)
        for x in range(0, self.window_size[0]):
            mono = np.mean(
                buf[x * self.wav_step:(x + 1) * self.wav_step]) / MAX_SHORT
            amp = int(self.y_range + self.y_range * mono)
            pixels[x][amp] = 0xf1
        self.pixels = pixels



class Waterfall(Window):
    def __init__(self, window_size, zoom=1):
        Window.__init__(self, window_size)
        self.zoom = zoom
        self.pixels = np.zeros(self.length, dtype='i4').reshape(*window_size)

    def render(self, spectrogram):
        self.pixels = np.roll(self.pixels, -1, axis=0)
        for y in range(0, self.window_size[1], self.zoom):
            inv_y = self.window_size[1] - y - 1
            point = spectrogram.freq[y // self.zoom]
            for suby in range(self.zoom):
                self.pixels[-1][inv_y - suby] = hsv(
                    0.5 + 0.4 * point,
                    0.3 + 0.6 * point,
                    0.2 + 0.7 * point)


class SpectroGraph(Window):
    def __init__(self, window_size, frame_size, zoom=1, decay=10):
        super().__init__(window_size)
        self.height = window_size[1]
        self.values = np.zeros(frame_size // 2)
        self.zoom = zoom
        self.decay = decay
        self.graph_length = min(window_size[0] - self.zoom, frame_size // 2)

    def render(self, spectrogram):
        self.fill(0x00000)
        for x in range(0, self.graph_length, self.zoom):
            freq_pos = x // self.zoom
            val = spectrogram.band[freq_pos]
            if self.values[freq_pos] > val:
                decay = (self.values[freq_pos] - val) / self.decay
                val = self.values[freq_pos] - decay
            self.values[freq_pos] = val
            for subx in range(self.zoom):
                self.draw_line(
                    (x + subx, self.height),
                    (x + subx, self.height - val * self.height),
                    0xfafafa)


class ModColor(Window):
    def __init__(self, window_size, base_hue=0.6):
        super().__init__(window_size)
        self.base_hue = base_hue
        self.values = np.zeros(self.window_size[0]) + self.window_size[1]

    def render(self, val):
        self.values = np.roll(self.values, -1)
        self.values[-1] = self.window_size[1] - self.window_size[1] * val
        self.surface.fill(hsv(self.base_hue + 0.3 * val, 0.8, 0.5 + 2 * val))
        for x in range(0, self.window_size[0] - 1):
            pygame.draw.line(self.surface, 0xfafafa,
                             (x, self.values[x]),
                             (x + 1, self.values[x+1]))
