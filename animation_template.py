#!/bin/env python
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

import yaml

from utils.animation import Animation, run_main
from utils.audio import SpectroGram, AudioMod
from utils.midi import MidiMod


p = """
gradient: sunrise
"""


class Demo(Animation):
    def __init__(self):
        self.scenes = [
            [8000, None],
            [0,    self.intro],
        ]
        super().__init__(yaml.load(p))

    def intro(self, frame):
        ...

    def setAudio(self, audio):
        self.audio = audio
        self.spectre = SpectroGram(audio.audio_frame_size)
        self.audio_events = {
            "low": AudioMod((1, 4), "avg"),
        }
        return

    def setMidi(self, midi, midi_skip):
        self.midi = midi
        self.midi_skip = midi_skip
        self.midi_events = {
            "name": MidiMod("name", mod="one-off"),
        }


if __name__ == "__main__":
    run_main(Demo())
