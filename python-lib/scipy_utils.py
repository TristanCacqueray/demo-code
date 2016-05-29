#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0

from common import *
try:
    import scipy.io.wavfile
    use_scipy=True
except ImportError:
    use_scipy=False

# scipyio abstraction
def load_wav(wav_file, fps = 25, init_mixer = True):
    if not use_scipy:
        return [], 0, 0
    freq, wav = scipy.io.wavfile.read(wav_file)
    if freq % fps != 0:
        raise RuntimeError("Can't load wav %d Hz at %d fps" % (freq, fps))
    audio_frame_size = freq / fps
    audio_frames_path = np.linspace(0, len(wav), int(len(wav) / freq * fps), endpoint=False)
    if init_mixer:
        pygame.mixer.init(frequency = freq, channels = len(wav[0]), buffer = audio_frame_size)
    return wav, audio_frame_size, audio_frames_path


# Fft abstraction (frame based short fft)
class SpectroGram:
    def __init__(self, frame_size):
        self.frame_size = frame_size
        overlap_fac = 0.5
        self.hop_size = np.int32(np.floor(self.frame_size * (1 - overlap_fac)))
        self.fft_window = np.hanning(self.frame_size)
        self.inner_pad = np.zeros(self.frame_size)
        self.amps = {}

    def transform(self, buf):
        self.buf = buf
        mono = np.mean(buf, axis=1)
        windowed = self.fft_window * mono
        padded = np.append(windowed, self.inner_pad)
        spectrum = np.fft.fft(padded) / self.frame_size
        autopower = np.abs(spectrum * np.conj(spectrum))
        if (mono == 0).all():
            self.freq = autopower[:self.frame_size/2]
        else:
            dbres = 20*np.log10(autopower[:self.frame_size/2])
            clipres = np.clip(dbres, -40, 200) * 1 / 196.
            self.freq = clipres + 0.204081632654

# IIR filter abstraction
class Filter:
    def __init__(self, bpass, bstop, ftype='butter'):
        import scipy.signal.filter_design as fd
        import scipy.signal.signaltools as st
        self.b, self.a = fd.iirdesign(bpass, bstop, 1, 100, ftype=ftype, output='ba')
        self.ic = st.lfiltic(self.b, self.a, (0.0,))
    def filter(self, data):
        import scipy.signal.signaltools as st
        res = st.lfilter(self.b, self.a, data, zi=self.ic)
        self.ic = res[-1]
        return res[0]

class AudioMod:
    def __init__(self, filename, frames, filter_type, delay = 10.0):
        self.frames = frames
        self.mod = np.zeros(frames)
        self.cache_filename = "%s.mod" % filename
        if not os.path.isfile(self.cache_filename):
            if filter_type == 1:
                self.fp = Filter(0.01, 0.1, ftype='ellip')
            elif filter_type == 2:
                self.fp = Filter((0.1, 0.2),  (0.05, 0.25), ftype='ellip')
            if not os.path.isfile(filename):
                print "Could not load %s" % filename
                return
            wave_values = self.load_wave(filename)
            open(self.cache_filename, "w").write("\n".join(map(str, wave_values))+"\n")
        else:
            wave_values = map(float, open(self.cache_filename).readlines())
        imp = 0.0
        for i in xrange(0, self.frames):
            if wave_values[i] >= imp:
                imp = wave_values[i]
            else:
                delta = (imp - wave_values[i]) / delay
                imp -= delta
            self.mod[i] = imp

    def load_wave(self, filename):
        import wave
        wav = wave.open(filename, "r")
        if wav.getsampwidth() != 2 or wav.getnchannels() != 1:
            print "Only support mono 16bit encoding..."
            exit(1)

        # Read all frames
        buf = wav.readframes(wav.getnframes())

        # Convert to float array [-1; 1]
        w = np.fromstring(buf, np.int16) / float((2 ** (2 * 8)) / 2)

        step = wav.getnframes() / self.frames + 1
        wave_values = []
        for i in xrange(0, wav.getnframes(), step):
            wf = w[i:i+step]
            if self.fp:
                wf = self.fp.filter(wf)

            v = np.max(np.abs(wf))
            wave_values.append(float(v))
        return wave_values

    def plot(self):
        p = subprocess.Popen(['gnuplot'], stdin=subprocess.PIPE)
        open("/tmp/plot", "w").write("\n".join(map(lambda x: str(self.get(x)), range(0, self.frames))))
        #for i in xrange(0, self.frames):

        p.stdin.write("plot '/tmp/plot' with lines\n")
        p.wait()

    def get(self, frame):
        return self.mod[frame]



