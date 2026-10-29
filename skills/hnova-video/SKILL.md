---
name: hnova-video
description: "Create procedural 2D/3D videos and synthesized sound using the local HNova Video library, including Three.js planet/city camera sequences, particle intros and title animations. Use for code-generated video requests and HNova video projects."
---

# HNova Video

代码库位于 `F:\HNova\11HVideoMaker`。先读该目录的 `README.md`；需要配置字段时读 `docs/project-config.md`。在其他聊天中也使用这一份代码库。

已有可执行环境：`F:\HNova\11HVideoMaker\.venv\Scripts\python.exe`。通过 `python -m hvideo` 调用，或运行代码库的 `hvideo.ps1`。环境不存在时运行 `setup.ps1`；使用可用的 Python 3.11+，不要在项目里写死临时依赖缓存或 Codex runtime 路径。

为每部作品在 `projects/<name>/` 建立单独的 `project.json`，用 `new` 从模板创建。优先修改配置和调用已有模块；只有新效果需要时才扩展 `src/hvideo/`。独立项目效果可先写在该项目目录，复用需求明确后再抽取；不要让它依赖别的作品输出。

通常先生成联系表或短样片，检查关键镜头与文字，再按用户要求生成成片。沿用已确定的风格与要求；不为每次渲染增加确认步骤。未知风格可先给出可播放样片。`render` 自动输出视频、WAV、封面、配置快照、验证报告；字幕使用可关闭的字幕轨并导出 SRT。`check` 可独立完整解码现有视频。

本库已有 Pillow 的 `particle-ring/title-card` 和 Three.js/WebGL 2 的 `star-flight/orbital-planet/neon-city`。`cosmic-city` 模板可生成三段三维运镜短片，摄像机、场景数量参数可配置。音效提供合成氛围音、音符、扫频。三维引擎在 `web/engine.js`，Python 浏览器桥接在 `webgl.py`；二者共用原有音频、字幕、导出模块。不要描述为已具备写实人物、人声 TTS、任意模型导入或物理准确的模拟。

三维环境用 `setup-webgl.ps1` 配置，`doctor --webgl` 实际检查浏览器与 GPU。渲染不依赖 CDN；依赖由本地 Three.js/npm 和 Playwright 提供。三维项目配置 `renderer.backend: threejs`，目前不混合后端。先预览几个关键时刻；需要验证确定性时设置 `HVIDEO_TEST_WEBGL=1` 运行测试。默认硬件渲染，软件回退只在硬件不可用时按 README 的说明启用。保留统一时间轴和导出边界；外部 API 只在用户要求或任务确实需要且授权充分时接入。

交付时提供视频预览和绝对路径链接，说明实际完成的内容和验证结果。修改此 skill 时编辑代码库中 `skills/hnova-video/` 的版本，然后运行 `install-skill.ps1` 同步到用户技能目录；不要复制生成引擎到 skill 中。
