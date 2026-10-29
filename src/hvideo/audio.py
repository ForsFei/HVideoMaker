"""Offline wave synthesis and sample-accurate cue placement."""
import math
import wave
import numpy as np
from .timeline import envelope, cue_time

SR = 48000


def note(frequency, duration, gain=.1):
    t = np.arange(round(duration * SR)) / SR
    return (np.sin(2*np.pi*frequency*t) + .28*np.sin(2*np.pi*frequency*2.005*t)) * np.exp(-t*6) * np.minimum(t/.004, 1) * gain


def place(bus, mono, at, pan=0):
    start = round(at * SR)
    n = min(len(mono), len(bus) - start)
    if n > 0:
        bus[start:start+n, 0] += mono[:n] * math.sqrt((1-pan)/2)
        bus[start:start+n, 1] += mono[:n] * math.sqrt((1+pan)/2)


def synthesize(config):
    duration = config["video"]["duration"]
    a = config["audio"]
    t = np.arange(round(SR * duration)) / SR
    bus = np.zeros((len(t), 2))
    for j, frequency in enumerate(a["bed"]):
        tone = (np.sin(2*np.pi*frequency*t + .4*np.sin(2*np.pi*.12*t)) + .24*np.sin(4*np.pi*frequency*t)) * a["bed_gain"]
        bus[:, 0] += tone * (.8+.2*math.cos(j))
        bus[:, 1] += tone * (.8+.2*math.sin(j))
    rng = np.random.default_rng(config["seed"] + 1)
    for cue in a["cues"]:
        if cue["type"] == "note":
            mono = note(cue["frequency"], cue["duration"], cue["gain"])
        else:
            n = round(cue["duration"] * SR)
            noise = rng.normal(0, 1, n)
            mono = np.convolve(noise, np.ones(16)/16, mode="full")[:n]
            mono *= np.sin(np.linspace(0, np.pi, n))**2 * cue["gain"]
        place(bus, mono, cue_time(cue, config["scenes"]), cue["pan"])
    fade = envelope(t, duration, min(1.2, duration/4), min(1.5, duration/4))
    bus *= fade[:, None] * a["gain"]
    peak = float(np.max(np.abs(bus)))
    if peak > .92:
        bus *= .92 / peak
    return bus


def write_wav(path, samples):
    with wave.open(str(path), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes((samples * 32767).astype("<i2").tobytes())


def inspect_wav(path):
    with wave.open(str(path), "rb") as f:
        if f.getsampwidth() != 2:
            raise ValueError("Expected 16-bit PCM WAV")
        samples = np.frombuffer(f.readframes(f.getnframes()), dtype="<i2").astype(float)/32768
        return {"duration": f.getnframes()/f.getframerate(), "sample_rate": f.getframerate(), "channels": f.getnchannels(), "peak": float(np.max(np.abs(samples))), "rms": float(np.sqrt(np.mean(samples**2)))}
