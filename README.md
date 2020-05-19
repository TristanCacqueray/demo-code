This repository is a collection of code to create visualisation.

Check [demo-render](https://github.com/TristanCacqueray/demo-render) for the result.

# Setup

To run the code, you need to:

```bash
$ python3 -mvenv ~/demo-code-venv
$ . ~/demo-code-venv/bin/activate
(venv) $ pip3 install hy2glsl pyyaml scipy soundfile sounddevice image pyopengl pyopencl Cython scipy pygame numpy hy
# Glumpy needs to be install separately
(venv) $ pip3 install glumpy
# Ensure glfw-dev package is installed
(venv) $ pkg-config --libs glfw3
[Print -lglfw]
# Ensure tkinter binding is working
(venv) $ python3 -m "tkinter"
[Show a tk window]
```

Check audio input from alsa:

```bash
$ ./explorer_audio_mod.py --help
$ ./explorer_audio_mod.py --list-sound-devices
   0 HDA Intel PCH: ALC285 Analog (hw:0,0), ALSA (2 in, 2 out)
   1 Sennheiser USB headset: Audio (hw:1,0), ALSA (1 in, 2 out)
   ...
$ ./explorer_audio_mode.py --sound-device 1
[show spectrometer from audio mic]
```

Check audio output to alsa:

```bash
$ ./explorer_audio_mod.py --sound-device 1 --wav WAV_FILE_44100.wav
[play wav file and show spectrometer]
```

Check video encoding:

```bash
$ ./explorer_shader.py --max-frame 25 --record /tmp/demo-code-output/
[show window for a second and output files in /tmp]
$ mplayer /tmp/demo-code-output/render.mp4
[show recorded clip]
```

You have a working setup!

# Usage

Run the examples using this environment variable:

```bash
$ export PYTHONPATH=$(pwd)
```

## Simple

Use the `./examples/julia.hy` to try animation and exploration works.
Start the script using `./examples/julia.hy --pause --sound-device NR` using the sound device index of your audio hardware

This will display 3 windows:

* A big one with a dendrite like shape
* A smaller one with a mandelbrot map
* A controller with 2 sliders: `color_power` and `max_iter`

Instructions:

* Press `space` on the bigger window to un-pause the animation.
* The graphic window support `mouse-click` to re-center and `mouse-wheel` to zoom/dezoom.
* The map window support `middle-click` to update the seed of the rendering.
* The controller's sliders can adjust the rendering.

> Try to zoom to a blurry area and increase the `max_iter` to make the rendering sharp.

If you unpause, sending low-frequency in the microphone should make the dentrite move.
Ensure input is working by using the `explorer_audio_mod.py` script first.


## Orbit

The `./examples/orbit.hy` shows another formula.


## 3d

The `./examples/underwater-fractal-creature.py --pause` demonstrates a 3d formula.

Use a `--wav file` for better result. Otherwise, press `space`, use the mouse and try one of the slider!
