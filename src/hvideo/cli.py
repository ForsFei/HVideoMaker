import argparse
import copy
import json
from importlib.resources import files
from pathlib import Path
import subprocess
from . import __version__
from .config import load, validate


def main():
    parser=argparse.ArgumentParser(prog="hvideo",description="HNova 本地代码音视频工具")
    parser.add_argument("--version",action="version",version=__version__)
    sub=parser.add_subparsers(dest="command",required=True)
    new=sub.add_parser("new",help="从模板创建项目，不覆盖已有文件")
    new.add_argument("directory",type=Path)
    new.add_argument("--template",choices=["particle-ring","title-card","cosmic-city"],default="particle-ring")
    new.add_argument("--title")
    for command in ("preview","render"):
        p=sub.add_parser(command)
        p.add_argument("project",type=Path)
        p.add_argument("--output",type=Path)
        if command=="preview":
            p.add_argument("--times",help="逗号分隔的秒数，例如 1,4,8")
            p.add_argument("--width",type=int,default=960,help="预览宽度，按成片宽高比缩放")
    check=sub.add_parser("check",help="完整解码并检查视频和音频流")
    check.add_argument("video",type=Path)
    doctor=sub.add_parser("doctor",help="检查依赖、字体和 FFmpeg")
    doctor.add_argument("--webgl",action="store_true",help="实际启动浏览器并检查 WebGL 2")
    args=parser.parse_args()
    try:
        if args.command=="new":
            data=json.loads(files("hvideo").joinpath(f"templates/{args.template}.json").read_text(encoding="utf-8"))
            if args.title is not None: data["scenes"][0]["title"]=args.title
            validate(data)
            args.directory.mkdir(parents=True,exist_ok=True)
            target=args.directory/"project.json"
            with target.open("x",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
            print(target.resolve())
        elif args.command=="doctor":
            from .export import ffmpeg
            from .visuals import find_font
            print("FFmpeg:",ffmpeg())
            result=subprocess.run([ffmpeg(),"-version"],capture_output=True,text=True,check=True)
            print(result.stdout.splitlines()[0])
            print("CJK font:",find_font())
            print("hvideo:",__version__)
            if args.webgl:
                from .webgl import WebGLRenderer
                data=json.loads(files("hvideo").joinpath("templates/cosmic-city.json").read_text(encoding="utf-8"))
                data["video"].update(width=320,height=180)
                with WebGLRenderer(validate(data)) as renderer:
                    renderer.frame(1)
                    print(json.dumps(renderer.info,ensure_ascii=False,indent=2))
        elif args.command=="check":
            from .export import verify
            print(json.dumps(verify(args.video),ensure_ascii=False,indent=2))
        else:
            from .export import preview,render
            c=load(args.project)
            output=args.output or args.project.resolve().parent/"output"
            if args.command=="preview":
                c=copy.deepcopy(c)
                if args.width<64 or args.width>7680: raise ValueError("Preview width must be between 64 and 7680")
                c["video"]["height"]=max(64,round(c["video"]["height"]*args.width/c["video"]["width"]/2)*2)
                c["video"]["width"]=round(args.width/2)*2
                times=[float(t) for t in args.times.split(",")] if args.times else None
                print(preview(c,output/"preview",times))
            else:
                print(json.dumps(render(c,output),ensure_ascii=False,indent=2))
    except (ValueError,KeyError,OSError,RuntimeError,subprocess.SubprocessError) as exc:
        parser.exit(1,f"Error: {exc}\n")


if __name__=="__main__":
    main()
