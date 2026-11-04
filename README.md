# Motion Showreel · 本地使用

制作新视频时，在 Codex 中说「使用 F:/HNova/11MotionShowreel/motion-showreel/SKILL.md，做一支……」。可以直接给主题、时长、横竖屏、是否需要口播，以及配乐和音效用代码生成还是使用已有文件。每部作品放在 F:/HNova/11MotionShowreel/projects/ 的独立子目录。

## Windows 环境

需要 Node.js 18+、FFmpeg 和 FFprobe，以及 Playwright 可用的 Chromium、Chrome 或 Edge。工具依赖位于 Skill 的 scripts/node_modules 中。已配置的机器可直接运行下面的环境检查。重新配置时执行：

```powershell
$s = 'F:/HNova/11MotionShowreel/motion-showreel/scripts'
npm.cmd ci --prefix $s
npm.cmd install --prefix $s --no-save --package-lock=false @ffmpeg-installer/win32-x64@4.1.0 @ffprobe-installer/win32-x64@5.1.0
```

这两个二进制包适用于 Windows x64。已有 FFmpeg 和 FFprobe 在 PATH 时可以跳过第二条。若没有 Chrome 或 Edge，可进入 scripts 目录执行 npx.cmd playwright install chromium。

```powershell
$s = 'F:/HNova/11MotionShowreel/motion-showreel/scripts'
$env:Path = "$s/node_modules/@ffmpeg-installer/win32-x64;$s/node_modules/@ffprobe-installer/win32-x64;$env:Path"
node "$s/check-env.mjs"
```

## 制作与导出

1. 让 Codex 按 Skill 创建项目、制作分镜和风格帧。图像用 index.html 和 motion.js，声音与画面共用 timeline.js。
2. 在浏览器剪辑工作区播放、拖动、检查声音。满意后点击「导出视频」，成片位于项目的 out/。
3. 要改片子时继续编辑该项目的源码，重新预览并导出。

已迁移的旧作品在 projects/ 下按片名分目录保存，每个目录只包含成片 MP4。

[上游 Skill 与源码](https://github.com/ConardLi/garden-skills/tree/2b9a89340b70f632d31c0f1c69fce94a7912423e/skills/motion-showreel)
