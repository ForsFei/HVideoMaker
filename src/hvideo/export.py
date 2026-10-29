import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import numpy as np
from PIL import Image, ImageDraw
from .audio import synthesize, write_wav
from .webgl import renderer_for
from .subtitles import write_srt


def ffmpeg():
    configured = os.environ.get("FFMPEG_BINARY")
    if configured:
        return configured
    if executable := shutil.which("ffmpeg"):
        return executable
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def verify(video):
    video = Path(video).resolve()
    result = subprocess.run([ffmpeg(),"-hide_banner","-nostats","-progress","pipe:1","-i",str(video),"-map","0:v:0","-map","0:a:0","-f","null","-"],capture_output=True,text=True)
    if result.returncode:
        raise RuntimeError(f"Video/audio decoding failed:\n{result.stderr[-4000:]}")
    decoded_frames = [int(line.split("=",1)[1]) for line in result.stdout.splitlines() if line.startswith("frame=")]
    return {"file":str(video),"bytes":video.stat().st_size,"decode_ok":True,"decoded_frames":decoded_frames[-1] if decoded_frames else 0,"has_subtitles":"Subtitle:" in result.stderr,"streams": [line.strip() for line in result.stderr.splitlines() if "Stream #0:" in line][:2]}


def preview(config, output, times=None):
    with renderer_for(config) as renderer:
        return _preview(config, output, times, renderer)


def _preview(config, output, times, renderer):
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    duration = config["video"]["duration"]
    times = times if times is not None else [duration*x for x in (.12,.35,.6,.85)]
    if not times or any(not math.isfinite(t) or t<0 or t>=duration for t in times):
        raise ValueError("Preview times must be within [0, video duration)")
    thumbs=[]
    for i,t in enumerate(times):
        im=renderer.frame(t)
        im.save(output/f"frame-{i:02d}-{t:06.2f}.png")
        im.thumbnail((480,270))
        tile=Image.new("RGB",(480,300),(5,10,22))
        tile.paste(im,((480-im.width)//2,0))
        ImageDraw.Draw(tile).text((10,280),f"{t:.2f}s",fill="white")
        thumbs.append(tile)
    sheet=Image.new("RGB",(960,300*math.ceil(len(thumbs)/2)),(5,10,22))
    for i,tile in enumerate(thumbs): sheet.paste(tile,((i%2)*480,(i//2)*300))
    sheet.save(output/"contact-sheet.jpg",quality=92)
    return output/"contact-sheet.jpg"


def render(config, output):
    with renderer_for(config) as renderer:
        return _render(config, output, renderer)


def _render(config, output, renderer):
    output = Path(output).resolve()
    output.mkdir(parents=True,exist_ok=True)
    # Fail before replacing outputs if the font or encoder is unavailable.
    executable = ffmpeg()
    samples = synthesize(config)
    stats = {"duration":len(samples)/48000,"peak":float(np.max(np.abs(samples))),"rms":float(np.sqrt(np.mean(samples**2)))}
    v=config["video"]
    with tempfile.TemporaryDirectory(prefix=".render-",dir=output) as temp:
        temp=Path(temp)
        write_wav(temp/"audio.wav",samples)
        cmd=[executable,"-y","-hide_banner","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f'{v["width"]}x{v["height"]}',"-r",str(v["fps"]),"-i","-","-i",str(temp/"audio.wav")]
        if config.get("subtitles"):
            write_srt(temp/"subtitles.srt",config["subtitles"])
            cmd += ["-i",str(temp/"subtitles.srt"),"-map","0:v:0","-map","1:a:0","-map","2:s:0","-c:s","mov_text","-metadata:s:s:0","language=zho"]
        # A subtitle track may end earlier than the video; avoid -shortest.
        cmd += ["-c:v","libx264","-preset","fast","-crf",str(v.get("crf",19)),"-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart",str(temp/"video.mp4")]
        with (temp/"encoder.log").open("w+") as log:
            process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
            try:
                total=round(v["duration"]*v["fps"])
                for i in range(total):
                    im=renderer.frame(i/v["fps"])
                    process.stdin.write(im.tobytes())
                    if i==int(total*.62): im.save(temp/"poster.png")
                    if i%max(1,round(v["fps"]*2))==0: print(f"Rendered {i}/{total}",flush=True)
                process.stdin.close()
                if process.wait():
                    log.seek(0)
                    raise RuntimeError(log.read()[-4000:])
            except BaseException:
                if process.poll() is None: process.kill()
                process.wait()
                if process.stdin and not process.stdin.closed: process.stdin.close()
                raise
        checked=verify(temp/"video.mp4")
        if checked["decoded_frames"] != total:
            raise RuntimeError(f"Expected {total} frames, decoded {checked['decoded_frames']}")
        for name in ("video.mp4","audio.wav","poster.png"):
            (temp/name).replace(output/name)
        if config.get("subtitles"):
            (temp/"subtitles.srt").replace(output/"subtitles.srt")
        else:
            (output/"subtitles.srt").unlink(missing_ok=True)
    checked["file"]=str(output/"video.mp4")
    checked["renderer"]=getattr(renderer,"info",{"backend":"pillow"})
    checked.update({"frames":total,"width":v["width"],"height":v["height"],"fps":v["fps"],"audio":stats})
    (output/"project-resolved.json").write_text(json.dumps(config,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (output/"report.json").write_text(json.dumps(checked,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return checked
