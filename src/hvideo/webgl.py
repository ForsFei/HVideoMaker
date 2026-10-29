"""Local-only Three.js rendering, sampled at explicit timeline times."""
import base64
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
import mimetypes
import os
from pathlib import Path
import secrets
from threading import Thread
from urllib.parse import unquote, urlsplit
from PIL import Image
from .visuals import find_font


def three_directory():
    path = Path(os.environ.get("HVIDEO_THREE_DIR", Path(__file__).resolve().parents[2]/"node_modules"/"three")).resolve()
    if not (path/"build"/"three.module.js").is_file():
        raise RuntimeError("Three.js is missing. Run setup-webgl.ps1 in the library directory.")
    return path


def browser_options():
    if custom := os.environ.get("HVIDEO_CHROME_PATH"):
        if not Path(custom).is_file():
            raise FileNotFoundError(f"Browser not found: {custom}")
        return {"executable_path": custom}
    for path in ("C:/Program Files/Google/Chrome/Application/chrome.exe", "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"):
        if Path(path).is_file():
            return {"executable_path": path}
    return {}  # Playwright-managed Chromium; install with setup-webgl.ps1 -InstallChromium.


def safe_asset(root, name):
    path = (root/name).resolve()
    return path if path.is_relative_to(root) and path.is_file() else None


class WebGLRenderer:
    def __init__(self, config):
        self.config = config
        self.server = self.browser = self.playwright = None
        self.thread = None
        self.errors = []
        self.info = {}

    def __enter__(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("Playwright is missing. Run setup-webgl.ps1.") from exc
        three = three_directory()
        web = Path(__file__).resolve().parent/"web"
        font = Path(find_font(self.config.get("style",{}).get("font")))
        config = self.config
        token = secrets.token_urlsafe(20)
        prefix = f"/{token}/"

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                url = unquote(urlsplit(self.path).path)
                if not url.startswith(prefix):
                    self.send_error(404)
                    return
                name = url[len(prefix):]
                if name == "config.json":
                    content = json.dumps(config,ensure_ascii=False).encode("utf-8")
                    mime = "application/json"
                else:
                    path = font if name == "font" else safe_asset(three,name[6:]) if name.startswith("three/") else safe_asset(web,name or "index.html")
                    if path is None:
                        self.send_error(404)
                        return
                    content = path.read_bytes()
                    mime = "text/javascript" if path.suffix==".js" else mimetypes.guess_type(str(path))[0] or "application/octet-stream"
                self.send_response(200)
                self.send_header("Content-Type",mime)
                self.send_header("Content-Length",str(len(content)))
                self.end_headers()
                self.wfile.write(content)

        try:
            self.server = ThreadingHTTPServer(("127.0.0.1",0),Handler)
            self.thread = Thread(target=self.server.serve_forever,daemon=True)
            self.thread.start()
            self.playwright = sync_playwright().start()
            flags = ["--enable-webgl", "--ignore-gpu-blocklist", "--hide-scrollbars"]
            if os.environ.get("HVIDEO_SOFTWARE_GL")=="1":
                flags += ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
            self.browser = self.playwright.chromium.launch(headless=True,args=flags,**browser_options())
            self.page = self.browser.new_page(viewport={"width":config["video"]["width"],"height":config["video"]["height"]},device_scale_factor=1)
            origin = f"http://127.0.0.1:{self.server.server_port}"
            self.page.route("**/*",lambda route: route.continue_() if route.request.url.startswith(origin+prefix) else route.abort())
            self.page.on("pageerror",lambda error:self.errors.append(str(error)))
            self.page.on("console",lambda msg:self.errors.append(msg.text) if msg.type=="error" else None)
            self.page.goto(origin+prefix+"index.html",wait_until="load")
            self.page.wait_for_function("window.hvideoReady === true || Boolean(window.hvideoError)",timeout=90000)
            if error := self.page.evaluate("window.hvideoError || null"):
                raise RuntimeError(error)
            self.info = self.page.evaluate("window.hvideoInfo")
            self.raise_errors()
            return self
        except BaseException as exc:
            self.__exit__(None,None,None)
            if isinstance(exc,Exception):
                raise RuntimeError(f"WebGL initialization failed: {exc}") from exc
            raise

    def raise_errors(self):
        if self.errors:
            raise RuntimeError("Browser rendering failed: "+"\n".join(self.errors[-5:]))

    def frame(self, time):
        self.raise_errors()
        data = self.page.evaluate("time => window.hvideoFrame(time)",time)
        self.raise_errors()
        return Image.open(BytesIO(base64.b64decode(data))).convert("RGB")

    def __exit__(self, *args):
        try:
            if self.browser: self.browser.close()
        finally:
            try:
                if self.playwright: self.playwright.stop()
            finally:
                if self.server:
                    self.server.shutdown()
                    self.server.server_close()
                if self.thread: self.thread.join(timeout=3)


@contextmanager
def renderer_for(config):
    if config.get("renderer",{}).get("backend","pillow")=="threejs":
        with WebGLRenderer(config) as renderer:
            yield renderer
    else:
        from .visuals import Renderer
        yield Renderer(config)
