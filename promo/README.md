# 拾光 · 32 秒品牌片

> 拾光 / Shiguang 是为本开源项目虚构的产品，不代表任何真实公司。

一支 32 秒、1920×1080、30 fps 的中文品牌片。画面全部是 HTML/CSS/SVG + `render(t)`；
配音由 edge-tts 生成；音乐和音效由 numpy 合成；没有素材库、没有视频模型、没有剪辑软件。

**成片：** [`out/shiguang-promo.mp4`](out/shiguang-promo.mp4)
**联系表：** [`out/contact.png`](out/contact.png)

## 规格

| | |
|---|---|
| 时长 | 32.00 s |
| 帧数 | 960（30 fps） |
| 画面 | 1920×1080，单文件 `comp.html` |
| 配音 | `zh-CN-XiaoxiaoNeural`，8 句，25.8 s |
| 音乐 | 92 BPM，Cmaj7 / Am7 / Fmaj7 / G7，numpy 合成 |
| 音效 | whoosh / tick / click / pop / thud / chime，全部合成 |
| 母版 | −14 LUFS，−1.2 dBFS true peak，AAC 192 kbps |
| 渲染 | 960 帧约 83 s（单进程 headless Chrome） |

## 时间线

| 时间 | 场景 | 旁白 | 画面 |
|---|---|---|---|
| 0.0–3.6 | 钩子 | 脑子里，有一百个想法。 | 30 张便签漂浮；大字逐字升起 |
| 3.6–7.8 | 张力 | 它们散落在便签、聊天和文档里。 | 三列便签 / 聊天 / 文档；计数器 0→128；光标搜寻 |
| 7.8–11.4 | 揭示 | 拾光，把它们收成一束光。 | 便签向中心收拢 → 竖线 → 标记 → 品牌名 |
| 11.4–16.7 | 记下 | 先记下来。一句话，一张图，都可以。 | 编辑器逐字输入；图片卡片；收进「本周」 |
| 16.7–21.5 | 连起来 | 拾光会连起相关的内容，理出下一步。 | 目标 / 素材 / 下一步三张卡，连线汇聚到「方案」 |
| 21.5–24.5 | 做出来 | 然后，把它做出来。 | 本周计划三条勾选；进度条；「完成」印章 |
| 24.5–27.6 | 对照 | 从散落，到清晰。 | 左侧散落卡 + 右侧已整理计划；大字两行 |
| 27.6–32.0 | 收尾 | 拾光，把想法变成下一步。 | 深色端卡：标记、品牌名、tagline、网址、CTA |

## 文件

```
comp.html          一个文件，纯 render(t)；没有外部图片/视频/字体文件
vo.py              edge-tts 生成 8 句配音和 vo.json
audio_build.py     numpy 合成 BGM + SFX，混入配音，写 audio/mix.wav
vo.json            配音文本、文件、时长
timing.json        配音起点与时长
vo/                8 个 MP3
out/shiguang-promo.mp4   最终成片（有声）
out/contact.png    每 2 秒一帧的联系表
```

`audio/` 是 `audio_build.py` 的生成产物（wav 较大，未提交）。

## 复现

```bash
# 1. 配音（需要网络；edge-tts）
python vo.py

# 2. 音乐 / 音效 / 混音
python audio_build.py

# 3. 契约检查
python ../skill/scripts/check.py comp.html --runtime

# 4. 渲染 960 帧
python ../skill/scripts/render.py comp.html -o out/video.mp4 --fps 30

# 5. 混音 + 响度
ffmpeg -v error -y -i out/video.mp4 -i audio/mix.wav -c:v copy \
  -c:a aac -b:a 192k -shortest -movflags +faststart out/mux.mp4
ffmpeg -v error -y -i out/mux.mp4 -c:v copy \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:a aac -b:a 192k \
  -movflags +faststart out/shiguang-promo.mp4

# 6. 验收
python ../skill/scripts/verify.py out/shiguang-promo.mp4 \
  --shots 0,3.6,7.8,11.4,16.7,21.5,24.5,27.6
```

## 备注

- 字体使用系统 `Microsoft YaHei`，仓库不分发字体文件。
- 配音由 edge-tts 调用 Microsoft 在线语音生成；不含任何声音模型权重。
- 音乐和音效是纯 numpy 合成，不含第三方采样。
- 这不是对任何真实品牌或视频的复刻；它是一支为引擎写的原创 demo。
