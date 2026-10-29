# 项目配置 v1

配置使用 UTF-8 JSON。可从 `src/hvideo/templates/` 的示例开始，不必每次读取生成器源码。

| 字段 | 含义 |
|---|---|
| `schema_version` | 当前为 `1` |
| `seed` | 非负整数；相同配置可复现相同画面、声音 |
| `video.width / height` | 偶数像素尺寸；默认 960×540 |
| `video.fps / duration` | 帧率与秒数；两者相乘必须为整数帧数 |
| `video.crf` | H.264 质量，整数 0–51，默认 19，越低文件越大 |
| `brand / label` | HUD 左右上角标记 |
| `style.accent` | RGB 数组，取值 0–255 |
| `style.font` | 可选，字体文件绝对路径或相对 project.json 的路径 |
| `style.show_hud` | 是否显示状态标记和进度条 |
| `scenes` | 按开始时间排列的非重叠镜头；允许中间留空 |
| `audio.bed` | 氛围音频率数组，空数组关闭背景音 |
| `audio.bed_gain / gain` | 背景音与整体线性增益，默认 0.025 / 1.8 |
| `audio.cues` | 合成音效事件列表 |
| `subtitles` | 可选字幕列表；导出独立 SRT 和 MP4 字幕轨，不烧入画面 |
| `renderer.backend` | `pillow`（默认）或 `threejs`，每个项目选择一个 |
| `renderer.bloom / bloom_strength` | 三维后处理辉光开关、强度，默认 true / 0.65 |
| `renderer.exposure` | 三维色调映射曝光，默认 1.1 |

## 镜头

```json
{
  "id": "intro", "type": "particle-ring", "start": 0, "duration": 12,
  "title": "从代码，到声光", "subtitle": "可修改的副标题", "particles": 360,
  "intro_labels": ["正在生成粒子场", "让秩序，从噪声中浮现"],
  "fade_in": 0.4, "fade_out": 1.2
}
```

`type` 支持 `particle-ring`、`title-card`。标题卡忽略粒子与 intro_labels。`subtitle` 是镜头的固定副标题，和下方的时码字幕不同。镜头动画按自身时长缩放，粒子镜头的标题约从镜头 42% 处开始出现。长标题会缩小以适应宽度；复杂段落需单独设计排版。

## 音效与字幕

```json
{
  "audio": {
    "bed": [], "gain": 1.8,
    "cues": [
      {"scene": "intro", "at": 4.8, "type": "note", "frequency": 523.251, "duration": 1.2, "gain": 0.1, "pan": -0.3},
      {"at": 3.6, "type": "sweep", "duration": 1.2, "gain": 0.12}
    ]
  },
  "subtitles": [{"start": 0.5, "end": 2.5, "text": "这里是一句字幕"}]
}
```

没有 `scene` 时，`at` 是全片绝对秒数；有 `scene` 时，`at` 是该镜头起点的偏移秒数。`duration` 是音效持续时长，默认 0.7 秒；超出全片末尾的尾音会截断。`pan` 范围 -1（左）到 1（右）。音符使用正弦基音与泛音合成，扫频为平滑噪声包络；不使用采样、人声或外部模型。字幕必须按时间排列且不重叠。播放器是否默认显示字幕由播放器决定；联系表仅预览画面，查看字幕请播放 MP4 或读取 SRT。

输出 WAV 为 48 kHz / 16-bit / 立体声；MP4 为 H.264 / yuv420p + AAC，适合常见播放器。若接入 TTS，需另外实现旁白输入、混音与对齐；当前配置尚不接受旁白文件。

## 三维镜头

使用 `cosmic-city` 模板创建完整三维项目。`renderer.backend` 为 `threejs` 时，镜头支持以下类型：

| 类型 | 场景参数 | 实现内容 |
|---|---|---|
| `star-flight` | `star_count`，默认 1800 | 立体星场、光环通道、星光轨迹 |
| `orbital-planet` | `star_count`，默认 2200 | 噪声函数地表、云层、昼夜、大气辉光、卫星与月球 |
| `neon-city` | `building_count` 默认 180、`star_count` 默认 800 | 实例化建筑、程序化窗纹、交通线与车流、立交、远处地标 |

三维镜头同样使用 `id/start/duration/title/subtitle/fade_in/fade_out`，可额外设置 `eyebrow` 为左下角章节标签。

```json
{
  "id":"planet", "type":"orbital-planet", "start":5, "duration":6,
  "title":"一个世界，正在苏醒", "subtitle":"程序化地表与轨道卫星",
  "camera":{
    "from":[9,3.7,15], "to":[-3,1.3,10.8],
    "look_at":[0,0,0], "look_at_end":[0,0,0], "fov":48
  }
}
```

`camera.from/to` 为世界坐标起点与终点，使用平滑插值运镜；`look_at/look_at_end` 控制视线目标，后者默认等于前者；`fov` 为垂直视角（度）。Y 为上方，默认朝向负 Z。字段缺省时使用该场景的默认运镜。星球半径 3.8，位于原点；城市主要街道沿负 Z 延伸，中央地标在 Z=-78。当前只实现起止点运镜，尚无通用关键帧编辑器或模型导入。

辉光为 UnrealBloomPass + OutputPass，场景按绝对秒数更新，不依赖实时帧率。相同配置跨 GPU 可能存在少量像素差异。三维 `style.accent` 当前预留，场景使用各自预设颜色；修改场景配色需调整 `web/engine.js`。
