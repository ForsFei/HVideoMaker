# HNova Video

本地代码音视频工具库。提供 Pillow 二维渲染与 Three.js/WebGL 2 三维渲染，支持粒子光环、标题卡、星空穿行、旋转星球、未来城市，以及合成声音、统一时间轴、字幕与 MP4 导出。不调用音视频生成 API。

## 开始使用

需要 Python 3.11+。在 PowerShell 中：

```powershell
git clone https://github.com/ForsFei/HVideoMaker.git
cd HVideoMaker
.\setup.ps1
.\hvideo.ps1 doctor
.\hvideo.ps1 new projects\my-intro --template particle-ring --title "你好，HNova"
.\hvideo.ps1 preview projects\my-intro\project.json
.\hvideo.ps1 render projects\my-intro\project.json
```

无需激活虚拟环境。`setup.ps1 -Python <python.exe>` 可指定解释器；`-ReuseSystemPackages` 可在该解释器已具备 NumPy/Pillow 时复用已有包。FFmpeg 优先取 `FFMPEG_BINARY` 环境变量，其次 PATH，再使用 `imageio-ffmpeg` 自带的编码器，无需单独安装。中文字体优先使用本机微软雅黑，也可以在 `style.font` 配置字体文件。

## 三维动画

本机已安装 Playwright 与 Three.js，可直接生成三维项目：

```powershell
.\hvideo.ps1 new projects\my-world --template cosmic-city
.\hvideo.ps1 preview projects\my-world\project.json --times "1.5,7.5,12.5,15.5"
.\hvideo.ps1 render projects\my-world\project.json
.\hvideo.ps1 doctor --webgl
```

新机器上先运行 `setup-webgl.ps1`，需要 Node.js/npm 和可用的 Chrome/Edge。没有浏览器时运行 `setup-webgl.ps1 -InstallChromium` 安装 Playwright Chromium。第一次安装需要联网；后续渲染的模块、字体、地表和建筑纹理均从本地加载，不依赖 CDN。Three.js 版本固定在 package-lock.json。

示例 `projects/cosmic-city/` 为 18 秒三维短片：星空穿行 → 带大气效果与卫星的程序化星球 → 180 栋建筑的城市与车流。它是风格化三维动画，不包含真实地理数据、物理准确的大气散射或光线追踪反射。报告会记录实际 GPU、WebGL 版本和 Three.js 版本。

配置 `renderer.backend: "threejs"` 选择三维引擎；未配置则继续使用 Pillow。每个项目目前使用单一后端。三维摄像机的位置、目标、视角，以及星星和建筑数量均可配置，见 [配置说明](docs/project-config.md)。

## 项目与输出

- `src/hvideo/`：配置、时间轴、画面、声音、字幕、导出、命令行。
- `src/hvideo/templates/`：新项目模板，包含可运行的默认配置。
- `projects/code-light/`：从第一次 demo 整理而来的 12 秒粒子短片。
- `projects/title-study/`：6 秒双镜头标题短片，演示相对镜头时间与可关闭字幕。
- `projects/cosmic-city/`：18 秒三维星球与城市样片。
- `skills/hnova-video/`：供 Codex 调用本库的轻量 skill 源文件。
- `tests/`：时间轴、声音确定性、编码前配置校验等检查。

默认输出在各项目的 `output/` 中：`video.mp4`、`audio.wav`、`poster.png`、`project-resolved.json`、`report.json`。配置字幕时另有 `subtitles.srt`，并在 MP4 中封装可关闭的字幕轨。预览在 `output/preview/`。渲染先写临时文件，编码和完整解码成功后替换成片；修改配置后应重新生成预览。

```powershell
# 只预览几个时刻，不编码全片
.\hvideo.ps1 preview projects\code-light\project.json --times "1,4.8,7.5,11" --width 960
# 渲染到自选目录
.\hvideo.ps1 render projects\code-light\project.json --output outputs\demo
# 检查已有 MP4 的视频、音频流能否完整解码
.\hvideo.ps1 check outputs\demo\video.mp4
# 运行核心行为检查
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
# 安装或更新用户 skill
.\install-skill.ps1
```

`render` 会输出进度，并自动完整解码验证音视频；音轨峰值会限制在 0.92 以下，结果写入报告。该检查不代替对画面与音乐的审美判断。

## 如何复用

先创建项目，修改文案、颜色、镜头、音效落点；确实需要新视觉效果时再扩展画面引擎。配置说明见 [docs/project-config.md](docs/project-config.md)。每部视频独立保存配置和专用文件，不复制整套生成器。源码与配置可提交到 Git，虚拟环境和渲染输出已忽略。

Pillow 画面以 960×540 为设计坐标，按输出尺寸直接绘制，不先渲染小图再放大；非 16:9 输出保持画面比例居中。WebGL 根据实际输出宽高比设置透视摄像机。两个后端的竖屏专用文字排版尚未实现。支持配置时长、分辨率、帧率；改时长时需要一起调整音效。当前音轨离线生成并存入内存，先以短片为主要用途。

Pillow 新镜头在 `visuals.py` 添加；三维镜头在 `web/engine.js` 添加并在 `config.py` 注册类型；新音色放 `audio.py`。`webgl.py` 管理浏览器和仅绑定 127.0.0.1 的临时资源服务，导出结束或出错时自动关闭。仅接收本次随机路径下的本地资源请求，不访问外网。相同 seed 和相同浏览器/GPU 环境中 `frame(time)` 可按任意顺序复现；不同 GPU 的像素结果可能有少量差异。

三维后端优先 `HVIDEO_CHROME_PATH` 指定的浏览器，然后本机 Chrome/Edge，最后 Playwright Chromium；`HVIDEO_THREE_DIR` 可指定 Three.js 包目录。硬件 WebGL 不可用时可设置 `$env:HVIDEO_SOFTWARE_GL="1"` 使用 SwiftShader，软件渲染会明显变慢。默认不强制切换到软件渲染。

需要验证三维任意时间取帧、运镜变化和浏览器资源回收时：

```powershell
$env:HVIDEO_TEST_WEBGL="1"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Skill 安装后可在新的聊天中使用 `$hnova-video`，或描述“使用 HNova Video 生成代码视频”。技能是否出现在当前聊天的列表由应用刷新机制决定；在刷新前也可以直接指定本代码库路径使用。
