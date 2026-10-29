import copy
import json
import math
from pathlib import Path
from .timeline import cue_time


def number(value, name, low=0, high=float("inf")):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{name} must be a finite number in [{low}, {high}]")
    return value


def validate(data):
    c = copy.deepcopy(data)
    if c.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    v = c["video"]
    for key in ("width", "height"):
        n = number(v[key], key, 64, 7680)
        if int(n) != n or n % 2:
            raise ValueError(f"{key} must be an even integer for H.264")
        v[key] = int(n)
    number(v["fps"], "fps", 1, 120)
    duration = number(v["duration"], "duration", .1, 3600)
    if abs(duration * v["fps"] - round(duration * v["fps"])) > 1e-6:
        raise ValueError("duration * fps must be a whole number of frames")
    number(v.get("crf", 19), "crf", 0, 51)
    if int(v.get("crf", 19)) != v.get("crf", 19):
        raise ValueError("crf must be an integer")
    color = c.get("style", {}).get("accent", [65, 210, 225])
    if not isinstance(color, list) or len(color) != 3:
        raise ValueError("style.accent must be an RGB list")
    for channel in color:
        number(channel, "accent channel", 0, 255)
    seed = c.setdefault("seed", 526)
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    scenes = c["scenes"]
    if not scenes:
        raise ValueError("At least one scene is required")
    ids = set()
    backend = c.get("renderer",{}).get("backend","pillow")
    if backend not in ("pillow","threejs"):
        raise ValueError("renderer.backend must be pillow or threejs")
    number(c.get("renderer",{}).get("exposure",1.1),"exposure",.1,5)
    number(c.get("renderer",{}).get("bloom_strength",.7),"bloom strength",0,3)
    last_end = 0
    for s in scenes:
        if not isinstance(s["id"], str) or not s["id"] or s["id"] in ids:
            raise ValueError("Scene IDs must be nonempty and unique")
        ids.add(s["id"])
        allowed = ("star-flight","orbital-planet","neon-city") if backend=="threejs" else ("particle-ring","title-card")
        if s["type"] not in allowed:
            raise ValueError(f"Unknown scene type: {s['type']}")
        for key,default,maximum in (("star_count",1600,12000),("building_count",180,500)):
            count = number(s.get(key,default),key,0,maximum)
            if int(count)!=count: raise ValueError(f"{key} must be an integer")
        camera = s.get("camera",{})
        for key in ("from","to","look_at","look_at_end"):
            if key in camera:
                if not isinstance(camera[key],list) or len(camera[key])!=3:
                    raise ValueError(f"camera.{key} must contain three coordinates")
                for value in camera[key]: number(value,f"camera.{key}",-10000,10000)
        number(camera.get("fov",50),"camera fov",10,110)
        number(s["start"], "scene start", 0, duration)
        number(s["duration"], "scene duration", .01, duration)
        end = s["start"] + s["duration"]
        if s["start"] < last_end - 1e-8 or end > duration + 1e-8:
            raise ValueError("Scenes must be ordered, non-overlapping, and within video duration")
        last_end = end
        count = s.get("particles", 360)
        number(count, "particles", 0, 10000)
        if int(count) != count:
            raise ValueError("particles must be an integer")
        for key in ("fade_in", "fade_out"):
            number(s.get(key, .4), key, 0, s["duration"])
        labels = s.get("intro_labels", ["Generating particles"])
        if not isinstance(labels, list) or not labels or not all(isinstance(x, str) for x in labels):
            raise ValueError("intro_labels must be a nonempty list of strings")
    last_end = 0
    for subtitle in c.get("subtitles", []):
        number(subtitle["start"], "subtitle start", last_end, duration)
        number(subtitle["end"], "subtitle end", subtitle["start"], duration)
        if subtitle["end"] <= subtitle["start"] or not isinstance(subtitle["text"], str) or not subtitle["text"].strip():
            raise ValueError("Subtitles need nonempty text and a positive duration")
        last_end = subtitle["end"]
    audio = c.setdefault("audio", {})
    number(audio.setdefault("gain", 1.8), "audio gain", 0, 8)
    number(audio.setdefault("bed_gain", .025), "bed gain", 0, 1)
    audio.setdefault("bed", [130.8128, 195.9977, 261.6256, 329.6276])
    for freq in audio["bed"]:
        number(freq, "bed frequency", 20, 20000)
    for cue in audio.setdefault("cues", []):
        if cue["type"] not in ("note", "sweep"):
            raise ValueError(f"Unknown audio cue: {cue['type']}")
        if "scene" in cue and cue["scene"] not in ids:
            raise ValueError(f"Unknown cue scene: {cue['scene']}")
        number(cue.get("at", 0), "cue offset", 0, duration)
        number(cue_time(cue, scenes), "cue time", 0, duration - 1/48000)
        number(cue.setdefault("duration", .7), "cue duration", 1/48000, duration)
        number(cue.setdefault("gain", .1), "cue gain", 0, 2)
        number(cue.setdefault("pan", 0), "cue pan", -1, 1)
        if cue["type"] == "note":
            number(cue.setdefault("frequency", 523.251), "cue frequency", 20, 20000)
    return c


def load(path):
    path = Path(path).resolve()
    c = validate(json.loads(path.read_text(encoding="utf-8-sig")))
    if font := c.get("style", {}).get("font"):
        font = Path(font)
        c["style"]["font"] = str(font if font.is_absolute() else path.parent / font)
    return c
