"""Shared time and interpolation primitives for image and audio code."""
import numpy as np


def smooth(start, end, time):
    if end <= start:
        return np.asarray(time) >= end
    x = np.clip((np.asarray(time) - start) / (end - start), 0, 1)
    return x * x * (3 - 2 * x)


def envelope(time, duration, fade_in=0.3, fade_out=0.5):
    return smooth(0, fade_in, time) * (1 - smooth(duration - fade_out, duration, time))


def cue_time(cue, scenes):
    """Resolve a global time, or an offset relative to a named scene."""
    return float(cue.get("at", 0)) + next(
        (s["start"] for s in scenes if s["id"] == cue.get("scene")), 0
    )
