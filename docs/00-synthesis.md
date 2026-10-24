# 代码生视频 / 视频复刻：仓库调研与统一系统设计

> 调研时间：2026-10-23
> 工作区：`D:\mine\video-skills-lab`
> 目标：把现有 skill / 插件 / 框架的精华抽出来，合成一个可移植、可验证、主要在本地跑的“代码生视频”系统。
> 结论先行：**能合成，而且现有材料已经足够。但必须先承认“任意视频”不成立，用路由把视频分成“可代码化 / 混合 / 生成式 / 实拍剪辑”四类。**

---

## 0. 一句话结论

现成的 30+ 个项目里，真正稀缺的不是“让模型写 HTML”，而是四件事：

1. **确定性时间契约**（`seek(t)` / `render(t)` 是纯函数）；
2. **逐帧验证闭环**（并排 diff、循环缝、确定性、节奏/承接/曲线/出框 oracle）；
3. **证据化分析**（每个判断带时间码、置信度、measured/observed/inferred/default）；
4. **可复用的动效与场景库**（不是每次从零写 GSAP）。

把这三层拼起来，就是一个比任何单个仓库都完整的系统。剩下的都是风格库和 provider 适配。

---

## 1. 已克隆仓库与定位

共 34 个仓库（`repos/`），约 4.3 GB。按角色分：

### A. 引擎 / 框架

| 仓库 | 许可证 | 关键贡献 | 取舍 |
|---|---|---|---|
| `heygen-com/hyperframes` | Apache-2.0 | HTML→视频的完整工业级框架：渲染契约、lint/check、Studio、registry（210 blocks + 238 components）、motion doctrine、seam gate、Remotion 迁移+逐帧校验 | **主引擎候选**；体量大（1.5G），可只取契约与参考文档 |
| `lovisdotio/motion2code` | MIT | 最小确定性契约 `window.anim`；`study_video.py` / `palette.py` / `frame_diff.py` / `check_anim.py` / `render_anim.py`；SVG+GSAP 架构；循环缝 | **最小内核首选**；代码干净、可读、无重依赖 |
| `feitangyuan/onetake` | **PolyForm-NC** | `__seek(t)` 纯函数；39 个动效库；**真实快门运动模糊**（多帧线性光积分）；并行 worker；`verify_promo.py` 的节奏/承接/曲线/出框 oracle；look 系统 | 思路极强，但**非商业许可**：只可借鉴架构，商用需 clean-room 重写 |
| `lemomo-ai/lemo-opuscar` | MIT | 59 种“纯代码电影风格”库；`window.render(t)` + `window.READY` + `window.TEXTS(t)`；`readcheck` 阅读时长检查；Kokoro/edge-tts + ASR 校验；mux 响度/颗粒 | **风格库与音频工具的首选来源**（MIT 可复用） |
| `calesthio/OpenMontage` | **AGPL-3.0** | 13 条生产管线（animated-explainer/cinematic/documentary/hybrid/screen-demo/talking-head/avatar/localization-dub 等）；139 个 SKILL；**参考视频分析 → 5 维镜头语言 → 能力审计 → 2–3 个差异化方案 → sample-first → 分阶段审批**；Backlot 可视化审批板；7 维 provider 评分；自检（ffprobe/抽帧/响度/字幕/交付承诺） | **治理与流程的首选参考**；生成式优先、体量大、AGPL：只借流程与 schema，不复制代码 |
| `remotion-dev/skills` | 见仓库 | Remotion 官方 12 个 skill（create/render/markup/captions/maps/3D 等） | React 路线备选 |
| `diffusionstudio/lottie` | MIT | 用 agent 生成 Lottie 动画 | 轻量动效备选 |

### B. 复刻 / 逆向

| 仓库 | 许可证 | 关键贡献 | 取舍 |
|---|---|---|---|
| `garycaogan/pixel-diary` | MIT | 分集 JSON → 时间轴 → HyperFrames 项目；12 种场景渲染器；**合成打字音/8-bit BGM**；像素立绘/表情差分；QA | 场景类型与音频合成的极佳范本 |
| `ljq-broll-video-generator` | MIT | 证据/置信度模型；layout → motion → QA 的“唯一责任阶段”归因；两轮修正门；JSON Schema | **质量门与 schema 设计的范本** |
| `motalim-ai/motion-starter-kit` | MIT | `analyze.py`：切点/镜头长度/运动条/调色板/onset；`STYLE.md` 数字模板；一次提问；静帧对照 | 参考分析层范本 |
| `huangserva/skill_video-style-analysis` | 未标 | 6 层 16 维语义分析；ASR 优先 + 三级降级；角色参考图；TTS 音画对齐 | 分析 rubric 很好；代码未标许可，只取方法 |
| `CY-CHENYUE/video-replication-sop-cy` | 未标 | 7 步 SOP；Gemini 看视频；角色卡锁定；每 10 秒分镜；一致性质检 | 分镜包生产流程参考 |
| `huojiaheng123-cpu/video-replication-breakdown` | 未标 | HTML 拆解页；钩子/叙事/分镜/风格/声音/素材六层；复刻脚本 | 报告结构参考 |
| `whaojie797-design/video-reverse-engineering` | MIT | `extract_shots.sh`：下载/抽帧/字幕/音频/元数据；镜头术语表；S-A-C-S-C 提示词 | 素材抓取脚本可直接用 |
| `kurbaitaev/ghost-editor` | MIT | 口播剪辑；参考剪辑逆向；**风格是 SYSTEM 不是模板**；approval sheet；taste 记忆；QA 报告 | 审批门与“品味记忆”设计范本 |
| `lvsccode/ecom-video-seedance-prompt` | 未标 | 基于 `deepseek-v4-flash-vision` 的镜头拆解；S-A-C-S-C；Seedance 提示词包 | **DeepSeek 视觉能力的实证**；只取方法 |

### C. 生成式 / 混合

| 仓库 | 许可证 | 关键贡献 | 取舍 |
|---|---|---|---|
| `hypit-ai/hypit` | Apache-2.0 | 完整“导演/制片”体系：Brief/Treatment/Timeline/Canvas、生成与作者组件混合、Studio | 概念体系庞大；可借“reference as evidence” |
| `riffkit/dsh-plugin` | MIT | 云端“公式级改编/镜头级换人”两种模式；报价门 | 商业 SaaS，不作核心 |
| `Alisa0808/vox-director` | MIT | Vox 纸拼贴解说；beat map/主题预设/节奏（3–6 秒一镜）；两处人工审批 | 生成式路线的节奏与提示词范本 |
| `bobobo2026/explainer-video` | MIT | 中文科普：选题/事实核查→口语稿→TTS 字级对齐→卡点→混音→质检 rubric→平台文案 | **中文脚本与音频时间轴范本** |
| `digitalsamba/claude-code-video-toolkit` | MIT | Remotion + TTS/音乐/QC/合成 UI 演示/发布 | 工具链齐全，偏重 |
| `JuneYaooo/cheap-claude-video` | Apache-2.0 | “视频配方”蒸馏：把一条成片拆成可复现配方 | 思路可借 |
| `439436269-ctrl/dsh-video-pipeline` | MIT | 19 个原子 skill；manifest 合成；`media-verify`（astats/NCC/亮度）；发布流水线 | **合成与验收脚本可直接用** |
| `STARDUSTLC666/dsh-remotion` | MIT | Remotion 官方 skill 的 DSH 移植；本地视频工作台 | React 路线插件化参考 |

### D. 风格 / 镜头库

| 仓库 | 许可证 | 关键贡献 |
|---|---|---|
| `kingselyjoe/video-shotcraft-dsh` | Apache-2.0 | 152 张镜头配方卡 + 已验收模板 + 2.5D 页面相机 + 音乐卡点 + 独立终检 |
| `promo-video-skill` (BrewReel) | Apache-2.0 | `storyboard.json` 语义层；19 种镜头；行业合规校验；便宜模型只写 JSON；TTS 时长驱动 |
| `pixel2motion` | MIT | 位图 logo → 最小 SVG → 12 原则动画；平滑度门；Final Frame Contract；动效 QA |
| `chengfeng-videocut-skills` | Apache-2.0 | 中文视频剪辑 skill 集 |
| `chenyuxiaojin/cyxj-hyperframes` | MIT | HyperFrames 教程视频工程与复用工具 |
| `onetake` / `lemo-opuscar` | 见上 | 39 动效 + 59 风格 |

### E. 索引 / 备份

| 仓库 | 许可证 | 说明 |
|---|---|---|
| `zhuyansen/awesome-claude-video-skills` | CC0 | 336 个视频 skill 的分类索引与安全分级 |
| `hermes-skills-backup` | 未标 | 455 个 skill 备份；含 `hyperframes-video-opening-replication`、`video-timing-reverse-engineer` 等 |
| `Aurirlk/Aurirlk-DSH-skills` | MIT | DSH skill 合集（多数与视频无关） |

---

## 2. 三条技术路线（必须分清）

### 路线 A：HTML/Canvas + 纯函数时间 → 逐帧截图 → FFmpeg

代表：HyperFrames、motion2code、onetake、lemo-opuscar、pixel-diary。

- 画面由代码描述，`seek(t)` / `render(t)` 是纯函数；
- 无头浏览器按帧 seek，截图，FFmpeg 编码；
- **确定性**：同一输入同一输出；
- 适合：2D 动效、UI、字幕卡、图表、地图、像素动画、屏幕录制重建、logo 动画。
- 不适合：实拍人物、真实光影、复杂 3D、有机纹理。

### 路线 B：React/Remotion

代表：Remotion 官方 skills、dsh-remotion、motion-starter-kit、ljq-broll、video-shotcraft、promo-video-skill。

- 同样是代码出片，组件化更强，Studio 可交互；
- 适合中大型工程、团队协作、模板化生产；
- 代价：Node/React 依赖重，便宜模型容易写坏；需要 `npm install` 和渲染器许可。

### 路线 C：生成式模型 + 提示词/分镜

代表：vox-director、ecom-seedance-prompt、skill_video-style-analysis、riffkit、hypit、dsh-video-pipeline 的 t2v 部分。

- 依赖 Seedance/即梦/可灵/Veo/Sora 等；
- 适合实拍感、人物、复杂场景；
- 产物通常是分镜表 + 提示词 + 参考图，不是代码；
- 成本按秒计，质量不稳定，需要重roll。

**统一系统不能只做 A 或只做 C，必须做“路由 + 混合”。**

---

## 3. 十四个可复用机制（真正的精华）

### M1. 确定性时间契约
- `window.__seek(t) -> Promise`（onetake）
- `window.anim = {duration, seek, play, pause}`（motion2code）
- `window.render(t)`（lemo）
- `window.__timelines[id] = gsap.timeline({paused:true})`（HyperFrames）
- **规则**：无 `Date.now()`、无未播种随机、无 wall-clock rAF、无不可 seek 的 CSS 动画；一切可见状态是 t 的函数。

### M2. 逐帧验证
- `frame_diff.py`：源片 | 代码并排图 + 平均绝对差 + 最差 5 个时刻（motion2code）
- `check_anim.py --runtime`：契约、循环缝、确定性、控制台错误、网络白名单（motion2code）
- `snapshot --against` + SSIM（HyperFrames）
- `verify_promo.py`：节奏 CV、静止比、burst、音频、承接分、曲线 px/frame、出框（onetake）

### M3. 运动指纹
- 能量图（每 1/12 秒一字符）
- 切点、镜头长度分布、静止比、最长静默
- 光流：峰值 px/frame、t80（0.23 = expo snap，0.67 = 对称 S 曲线）、smear（<0.78 = 有快门模糊）
- 调色板：主色/背景/强调色/占比
- 音频：人声占比、onset/分钟

### M4. 证据与置信度
每个判断标注 `measured | observed | inferred | default`，并带时间码/帧号/依据；无法唯一恢复的信息保留 Top-3 候选与已知差异（ljq）。

### M5. 风格圣经（数字化的“感觉”）
把形容词变成数字：纸/墨/强调色、字体/字重/字号/字距、阴影偏移/模糊/透明度、颗粒/暗角、缓动曲线、时长/间隔帧数（HyperFrames `SPEC.md`、motion-starter-kit `STYLE.md`）。

### M6. 镜头卡与场景库
- S-A-C-S-C：主体/动作/场景/光影/镜头/色彩/约束（ecom）
- 19–152 种镜头语义（BrewReel、video-shotcraft）
- 12 种场景渲染器（pixel-diary：title/flow/status/cards/lines/image/ledger/ask/follow/end/chat/clip）

### M7. 动效词汇与转场
- `cut-the-curve`：五个速度匹配 seam + waterfall entry + nudge curve
- `motion-doctrine`：vector law、the current、carrier、causal motion、seam gate
- onetake 39 moves：entrances/carries/contact/sims/camera/fluid
- 规则：一次只讲一个动效；落定后必须呼吸；静止是节奏的一部分。

### M8. 音频时间轴
- 字级时间戳驱动画面（explainer-video、pixel-diary）
- 音效锚在“第 i 句的某个词”（`cues.json`）
- 合成 SFX/BGM（pixel-diary 的 `audio.py`：打字音、pop、thud、sweep、8-bit bed）
- 响度：-14 ~ -16 LUFS；音乐 ducking；astats 分窗核验；NCC 版本比对

### M9. 审批门与成本门
- 分镜/关键帧确认后才批量生成（vox-director、pixel-diary）
- 报价后再调付费 API（dsh-video-pipeline、riffkit）
- 草稿 1080p30，验收后才 4K60（onetake）
- “没看到交付行不许写报告”（BrewReel）

### M10. Manifest 合成
镜头列表 + 配音时间轴 + SRT → 一条成片；路径相对 manifest；归一化、concat、adelay/amix、烧字幕、faststart；字幕失败自动降级（dsh-video-pipeline `video-compose.py`）。

### M11. 可移植 skill 形态
`SKILL.md` + `references/` + `scripts/` + `templates/`；Claude Code / Codex / DSH 共用；`AGENTS.md` 做跨 agent 入口；脚本用 stdlib + ffmpeg + 浏览器驱动，不绑定框架。

### M12. 品味记忆
用户每次纠正（“太多推镜”“这个音效土”）写成一条 taste 规则，带指标和上限；下次构建前读取，构建时警告（ghost-editor）。

### M13. 五维镜头语言（OpenMontage）
每个镜头按固定五维描述，避免“凭感觉写 prompt”：

1. **Subject**：类型、数量、年龄、角色、服装、识别特征；跨镜头的出现/消失/切换。
2. **Subject Motion**：按时间顺序的动作；平行/顺序/反应式交互；位移/手势/表情。
3. **Scene**：叠加层（字幕/图形/水印）单独列出 + POV + 场景 + 时间 + 动态元素。
4. **Spatial Framing**：景别（ECU/CU/MS/WS/EWS）、主体位置、景深层次、相对高度、这些如何变化。
5. **Camera**：播放速度、镜头畸变、机位高度、角度、对焦/景深、稳像、运动（推/拉/摇/移/升降/环绕）。

并强制给每个镜头标 `motion_type`：`motion_clip`（生成视频）/ `animated_still`（静图+Ken Burns）/ `static_image`（静图）。这直接决定生产路线，不能靠猜。

### M14. Pipeline 治理（OpenMontage）
- **Rule Zero**：所有生产必须走 pipeline，不允许即兴调 API。
- 每条 pipeline 是一个 YAML manifest：stages + 每阶段输入/输出 artifact + 可用工具 + checkpoint + success criteria。
- 每个阶段先读 `stage-director` skill，再动工具；Layer 3 provider skill 必须在写 prompt 前读完。
- **能力审计**：先列出“参考需要什么 vs 当前有什么”，明确 BLOCKED/READY/GAP，再报价。
- **2–3 个差异化方案**：禁止 carbon copy；每个方案写清“保留什么/改变什么/成本/真实观感”。
- **Sample-first**：先做 10–15 秒样品（hook + 一个中段），审批后才全量生产。
- **Backlot**：本地审批板，阶段亮起、脚本页、场景卡、每个 provider 决策与花费都上墙。

---

## 4. 提议的统一系统：`codefilm`

> 中文名暂定“代码片场”。一个可移植 skill，两种模式，四类路由，六层流水线。

### 4.1 定位

- **输入**：一条参考视频（URL/文件），或一个主题/脚本/风格。
- **输出**：可编辑的代码工程 + 渲染成片 + 对照页 + QA 报告。
- **核心承诺**：不是“任意视频都能像素级复刻”，而是：
  - 能用代码描述的部分，**重建为可编辑代码**；
  - 不能用代码描述的部分，**明确路由**到生成式/实拍/剪辑；
  - 每个结论都有帧级证据，每个成片都过质量门。

### 4.2 四类路由（`ROUTE.md`）

```
参考视频
├─ 主要是平面 2D 动效 / UI / 排版 / 图表 / 地图 / 像素 / 录屏
│   → CODE：HTML/SVG/Canvas + GSAP，本地渲染
├─ 有实拍人物/真实场景，但用户拥有素材
│   → EDIT：素材剪辑 + 代码叠加层（字幕/图表/标注/动效）
├─ 有实拍人物/真实场景，用户没有素材
│   → GEN：分镜 + 提示词 + 参考图，交给 Seedance/即梦/可灵/Veo
└─ 数字人/口播/换脸/换语言
    → AVATAR：TTS/克隆 + 唇形同步 + 合成
```

混合是常态：CODE 做界面/字幕/图表，GEN 做 B-roll，EDIT 做真人段。

### 4.3 六层流水线

| 层 | 输入 | 输出 | 关键脚本 |
|---|---|---|---|
| 1 Ingest | URL/文件 | `source.json`、`frames/`、`cuts/`、`audio.wav`、`subs.srt` | `ingest.py` |
| 2 Analyze | `source.json` | `analysis.json`、`STYLE.md`、`ROUTE.md` | `analyze.py` |
| 3 Direct | 分析 + 用户意图 | `SPEC.md`、`beats.json`、`script.json`、`ledger.json` | agent + `plan.py` |
| 4 Build | 规格 | `index.html`、`assets/`、`style.json` | agent + `templates/` + `library/` |
| 5 Verify | 代码 + 源片 | `diff/`、`qa.json`、`VERDICT` | `frame_diff.py`、`check.py`、`verify.py` |
| 6 Render | 代码 + 音频 | `out.mp4`、`compare.html`、`report.md` | `render.py`、`compose.py` |

### 4.4 目录结构

```
codefilm/
├─ SKILL.md                    # 入口：定位、路由、六步工作流、硬规则
├─ AGENTS.md                   # 跨 agent 入口（Claude Code / Codex / DSH）
├─ references/
│  ├─ ingest.md
│  ├─ analyze.md               # 6 层 16 维 + 镜头卡 + 运动指纹
│  ├─ route.md                 # 四类路由决策树
│  ├─ direct.md                # 三个概念 / 节拍表 / SPEC 数字 / vector ledger
│  ├─ build.md                 # HTML/SVG/GSAP 契约、场景类型、相机、排版
│  ├─ verify.md                # 帧差、循环缝、确定性、节奏/承接/曲线/出框
│  ├─ media.md                 # 调色板/字体/图标/TTS/SFX/BGM/B-roll
│  ├─ render.md                # 快门模糊、并行、编码、混音
│  ├─ deliver.md               # compare.html、报告、打包
│  ├─ motion-doctrine.md       # seam law / carrier / causal motion
│  ├─ motion-library.md        # 39 moves + 缓动表
│  ├─ shot-glossary.md         # 景别/运镜/构图/光线/转场
│  └─ quality-rubric.md        # 0–3 分逐项 rubric
├─ scripts/
│  ├─ ingest.py                # yt-dlp/ffmpeg/ffprobe/frames/cuts/ASR
│  ├─ analyze.py               # 能量图/光流/调色板/镜头统计/contact sheet
│  ├─ plan.py                  # JSON → 时间轴（字级/线索/场景）
│  ├─ render.py                # 确定性截帧 + 快门模糊 + 并行 + ffmpeg
│  ├─ frame_diff.py            # 源片 vs 代码，并排图 + 分数
│  ├─ check.py                 # 契约/确定性/循环缝/网络/控制台
│  ├─ verify.py                # 节奏/承接/曲线/出框/音频 oracle
│  ├─ audio.py                 # 合成 SFX/BGM + 混音
│  ├─ tts.py                   # edge-tts/Kokoro + 字级时间
│  ├─ compose.py               # manifest → 成片（ffmpeg）
│  └─ package.py               # 安装到 ~/.claude/skills、~/.agents/skills、DSH
├─ templates/
│  ├─ comp.html                # 最小契约 + helpers
│  ├─ scene-*.html             # title/cards/chart/chat/pixel/compare
│  ├─ compare.html             # 源片 vs 代码同步对照
│  └─ film.json                # 项目 manifest
├─ library/
│  ├─ motion.js                # 动效库（自研/借鉴后重写）
│  ├─ ui_kit.js                # 重建 UI 的舞台/坐标/高亮
│  ├─ looks.json               # 风格 token
│  └─ sfx/                     # 合成音色定义
└─ styles/                     # 可选：8–59 种风格配方（按需安装）
```

### 4.5 数据契约

`film.json`：

```json
{
  "id": "my-film",
  "mode": "replicate | create",
  "route": "code | edit | gen | avatar | hybrid",
  "source": {"file": "source.mp4", "duration": 12.5, "width": 1920, "height": 1080, "fps": 30},
  "canvas": {"width": 1920, "height": 1080, "fps": 30, "duration": 12.5},
  "style": "styles/paper-ink/style.json",
  "beats": "beats.json",
  "spec": "SPEC.md",
  "ledger": "ledger.json",
  "assets": ["assets/..."],
  "qa": {"frame_diff_max": 40, "rhythm_cv_min": 0.25, "carry_min": 0.5}
}
```

`beats.json`（场景/时间/文字/动作/声音）：

```json
[
  {"id": "hook", "start": 0.0, "end": 2.4, "scene": "title",
   "text": "Web motion is usually decoration.",
   "motion": "wordrise", "sfx": [{"t": 0.2, "kind": "pop"}]}
]
```

`ledger.json`（接缝向量账本）：

```json
[
  {"cut": 4.2, "exit": {"axis": "x", "dir": -1}, "entry": {"axis": "x", "dir": -1},
   "carrier": "#card", "technique": "cut-the-curve"}
]
```

### 4.6 质量门（硬门）

1. **契约门**：`check.py` 0 error；`seek(t)` 两次同图；无网络/控制台错误。
2. **循环门**：`frame(duration) == frame(0)`；最后一帧与第 0 帧差 < 阈值。
3. **复刻门**：`frame_diff` 在 hold 段 < 10，快动段 < 30，最差时刻 < 40；逐张并排图必须人看。
4. **节奏门**：镜头长度 CV ≥ 0.25；静止比 ≥ 25%；至少 1 秒静默；有 burst（若参考有）。
5. **承接门**：每个场景边界有 carrier；carry score ≥ 0.5（FAIL）/ 0.7（WARN）。
6. **曲线门**：>80 px/frame 的快动必须有快门模糊；否则 FAIL。
7. **出框门**：`__meta.inFrame` 声明的元素不得出框。
8. **音频门**：峰值 ≤ -3 dBFS；0 clipped；音乐 ducking；人声 -14~-16 LUFS。
9. **文字门**：每个文本在屏时长 ≥ 中文字数/4.5 + 1.5 秒；不压主体、不裁切。
10. **交付门**：`manifest.json` 记录源/成片 sha256、时长、各项检查结论；没有 `交付：` 行不算完成。

### 4.7 工作流（8 步）

0. **路由**：判断 CODE/EDIT/GEN/AVATAR/HYBRID；明确告诉用户能复刻到什么程度。
1. **拆解**：下载/抽帧/切点/ASR/OCR/联系图/运动指纹/调色板。
2. **分析**：6 层语义 + 镜头卡 + 风格圣经；标注证据与置信度。
3. **导演**：三个不同概念 → 用户选（或自选）；写 SPEC/beat sheet/vector ledger。
4. **建景**：从场景库复制；只写语义，不写坐标；用 style tokens。
5. **验证**：check → frame_diff → verify_promo；只看通过后的帧。
6. **审批**：给用户看 contact sheet + compare.html；确认后才渲染。
7. **渲染**：1080p30 草稿 → 验收 → 4K60/最终；合成音频。
8. **交付**：mp4 + 代码 + compare.html + QA 报告 + 已知差异。

---

## 5. 每个仓库的“精华 → 落点”映射

| 来源 | 借什么 | 落在哪 |
|---|---|---|
| HyperFrames | 渲染契约、lint 规则、motion doctrine、cut-the-curve、story/spec、registry 思路 | `build.md`、`motion-doctrine.md`、`check.py` |
| motion2code | 最小契约、study_video、palette、frame_diff、check_anim、compare.html | `scripts/*`、`templates/comp.html` |
| onetake | `__seek`、39 moves、快门渲染、verify_promo、look tokens | `render.py`、`motion.js`、`verify.py`、`looks.json` |
| lemo-opuscar | 59 风格、`render(t)`+`TEXTS(t)`+`readcheck`、TTS/ASR、mux | `styles/`、`tts.py`、`verify.py`、`compose.py` |
| pixel-diary | 分集 JSON→时间轴、场景渲染器、合成 SFX/BGM、像素文字 | `plan.py`、`templates/scene-*`、`audio.py` |
| ljq-broll | 证据/置信度 schema、layout→motion→QA 归因、两轮门 | `analysis.json`、`verify.py` |
| motion-starter-kit | analyze.py 运动条/镜头统计、STYLE.md 数字模板 | `analyze.py`、`direct.md` |
| explainer-video | 中文脚本结构、TTS 字级时间、cues、audio_bed、rubric | `direct.md`、`audio.py`、`quality-rubric.md` |
| ghost-editor | 风格是 SYSTEM、approval sheet、taste 记忆、QA 报告 | `direct.md`、`deliver.md`、`taste.json` |
| dsh-video-pipeline | manifest 合成、astats/NCC/亮度核验 | `compose.py`、`verify.py` |
| video-reverse-engineering | extract_shots.sh、镜头术语表、S-A-C-S-C | `ingest.py`、`shot-glossary.md` |
| skill_video-style-analysis | 6 层 16 维、ASR 降级 | `analyze.md` |
| ecom-seedance-prompt | DeepSeek 视觉拆解、S-A-C-S-C、提示词包 | `route.md`（GEN 分支） |
| vox-director | beat map、主题预设、3–6 秒一镜、审批门 | `direct.md`（GEN 分支） |
| video-shotcraft | 152 镜头卡、页面相机、音乐卡点、独立终检 | `styles/`、`verify.py` |
| promo-video-skill | 语义层 JSON、便宜模型只写 JSON、合规校验 | `beats.json`、`SKILL.md` |
| remotion-skills | React 路线 | 可选后端 |
| hypit | Brief/Treatment/Timeline 概念、reference as evidence | `direct.md` |
| OpenMontage | 5 维镜头语言、motion_type 路由、pipeline manifest/stage director/artifact/checkpoint、能力审计、2–3 方案、sample-first、Backlot 审批板 | `analyze.md`、`route.md`、`direct.md`、`SKILL.md` |

---

## 6. 必须放弃 / 降级的东西

1. **“复刻任意视频”**：路由之外的内容不承诺。
2. **文件大小当内容代理**（hermes 的一些笔记）：粗糙，改用帧差 + 边缘密度 + 光流。
3. **CSS 无限动画做“呼吸/漂浮”**：不可 seek，破坏确定性；用 GSAP 时间轴或 `draw(t)`。
4. **把整场切换塞进 `class="clip"`**：HyperFrames 明确禁止；用子合成/透明度切换。
5. **只产出提示词、没有验证的“复刻”**：只能算 GEN 分支，不能算成片。
6. **云端/付费 API 作为核心依赖**：核心必须本地可跑；provider 只做可选适配。
7. **过度模板化**：风格是 SYSTEM（不变量 + 槽位），不是一套固定镜头。

---

## 7. 许可证与法律

| 类型 | 仓库 | 处理 |
|---|---|---|
| Apache-2.0 | HyperFrames、dsh-video-pipeline、hypit、video-shotcraft、promo-video-skill 等 | 可复用，保留 NOTICE/LICENSE |
| MIT | motion2code、pixel-diary、ljq、lemo、ghost-editor、vox-director、explainer-video 等 | 可复用，保留版权声明 |
| **PolyForm-NC** | **onetake** | **不可直接用于商业**；只借架构思想，代码 clean-room 重写 |
| **AGPL-3.0** | **OpenMontage**（待读） | 不与闭源/可分发系统混合；只作参考或独立进程调用 |
| 未标 | skill_video-style-analysis、ecom-seedance-prompt、video-replication-* | 只取方法，不复制代码 |

---

## 8. 分阶段实现计划

### P0（1–2 天）：最小可用内核
- `ingest.py`：本地文件 + yt-dlp；ffprobe 缺失时用 `ffmpeg -i` 解析兜底。
- `analyze.py`：切点、镜头长度、能量图、调色板、contact sheet、运动条。
- `templates/comp.html`：`__seek(t)` + `__ready` + `__meta` + `__motion`。
- `render.py`：Playwright/CDP 截帧 + FFmpeg；先无快门模糊。
- `frame_diff.py` + `check.py`：并排图、循环缝、确定性。
- 验证：用 3 条参考（动态字、UI 演示、像素对话）各做 5–10 秒。

### P1（3–5 天）：动效与场景
- `motion.js`：30–40 个 moves（进入/承接/接触/相机/流体）。
- 场景库：title/cards/lines/flow/status/ledger/chat/image/clip/chart。
- `looks.json`：8 套风格 token（纸墨、深色科技、瑞士、riso、像素、手绘、蓝图、Vox）。
- `render.py`：快门运动模糊 + 并行 worker + resume。
- `verify.py`：节奏/承接/曲线/出框/阅读时长。

### P2（1 周）：音频与生成式
- `tts.py`：edge-tts + Kokoro；字级时间；多音字校正。
- `audio.py`：合成 SFX/BGM；ducking；-14 LUFS。
- `compose.py`：manifest 合成；字幕烧录；降级重试。
- GEN 分支：分镜 + 提示词 + 参考图；不直接调付费 API，只产出可粘贴包（或可选 provider）。
- EDIT 分支：素材剪辑 + 代码叠加。

### P3（1 周）：风格库与打包
- `styles/`：从 lemo 59 风格中挑 8–12 个重写为 tokens + 场景组合。
- `taste.json`：用户纠正记忆。
- `package.py`：安装到 `~/.claude/skills/codefilm`、`~/.agents/skills/codefilm`、DSH plugin。
- 文档：SKILL.md、AGENTS.md、quickstart、3 个完整案例。

---

## 9. 本机已验证的事实

1. **确定性 seek 可行**：用 raw-browser 打开 motion2code gallery 的 `think-big`，`seek(3.0)` 截图 → `seek(7.0)` → `seek(3.0)` 再截图，FFmpeg PSNR = **inf**（逐像素一致）。
2. **raw-browser 可以替代 Playwright 做交互式验证**：打开页面、设置 1920×1080 viewport、按 `?t=` 定位、截图。批量渲染仍需独立浏览器驱动（Playwright/CDP），因为 raw 只存在于本会话。
3. **本机 ffprobe 不在 PATH**（只有 ffmpeg）。所有脚本必须有 `ffmpeg -i` 解析兜底，或在安装时提示补 ffprobe。
4. **Node 26 / Python 3.13 / FFmpeg 6.0 可用**；Chrome 与 Edge 已安装。
5. **motion2code 的 gallery 可直接跑**（CDN GSAP 正常加载），说明“单 HTML + SVG + GSAP”在本机可行。

---

## 10. 待补

- `story-to-handdrawn-video` 克隆为空仓库，需确认是否已迁移。
- `hermes-skills-backup` 455 个 skill 只扫了视频相关目录，未逐篇读。
- 各仓库的 `references/` 深度文档（HyperFrames 的 7 个 reference、lemo 的 TECHNIQUE/DIRECTOR、onetake 的 motion-library、OpenMontage 的 13 条 pipeline 全文）只读了目录与关键篇，未逐行读。
- OpenMontage 的 139 个 SKILL 只读了 `video-reference-analyst`、`AGENT_GUIDE` 与 hybrid pipeline；其余管线按需再读。

---

## 11. 建议的下一步

1. **先做 P0**：把 `ingest/analyze/comp/render/frame_diff/check` 六个文件跑通，拿 3 条参考做端到端验证。
2. **同时写 SKILL.md**：只写路由、硬规则、六步工作流；不写大而全的 API 文档。
3. **风格库后置**：先用 1 套默认 look 把闭环跑顺，再扩到 8 套。
4. **不要一开始做 59 风格 / 152 镜头卡**：那是内容，不是引擎；引擎稳了再灌。
5. **许可证隔离**：onetake 只读不抄；OpenMontage 独立进程/参考；其余 MIT/Apache 保留声明。

---

## 12. P0 已落地（2026-10-23）

`D:\mine\video-skills-lab\codefilm\` 已建成并验证：

| 文件 | 作用 | 实测 |
|---|---|---|
| `scripts/ingest.py` | 本地/URL 下载、抽帧、切点、联系图、音频、可选 ASR | 在 `think-big` 参考上跑通：854×480、24fps、10.13s、4 个切点 |
| `scripts/analyze.py` | 能量图、静止比、切点、burst、最长静默、调色板 | 输出 `analysis.json` + `energy.txt` |
| `scripts/check.py` | 契约、确定性、循环缝、控制台/网络 | 两个 demo 均 PASS；determinism = 0.0 |
| `scripts/render.py` | Playwright 逐帧截图 + FFmpeg | 240 帧 / 8s / 1920×1080，约 37s |
| `scripts/frame_diff.py` | 源片 vs 成片并排图 + 分数 | 自比 0.00；`think-big` 复刻 1.5–51 |
| `scripts/verify.py` | 节奏/静止/burst/音频 oracle | demo 与带音频成片均 PASS；音频 -20.8 dBFS、0 clipped |
| `scripts/compose.py` | manifest 合成、配音延迟、SRT 烧录、自适应字幕样式 | 带正弦音轨 + SRT 跑通 |
| `scripts/install.py` | 安装到 Claude/Codex skills 目录 | 测试安装 213KB |
| `templates/comp.html` | 8 秒、1920×1080 demo | 已渲染并逐帧检查 |
| `examples/think-big/` | 2.6 秒真实复刻样例 | 0–1.75s 分数 1.5–18；2.0/2.25s 51（多色竖条转场未复刻） |

**跨契约验证**：`render.py` 直接渲染 motion2code 的 `window.anim` 页面（`think-big` 3 秒）成功，
说明引擎不绑定自家模板。

**本机事实**：`ffprobe` 不在 PATH，`probe()` 已回退到 `ffmpeg -i`；Playwright 用系统 Chrome；
渲染 240 帧约 37 秒。

**未做（P1/P2）**：快门运动模糊、光流、TTS/SFX 合成、风格库、GEN/AVATAR provider、
自动镜头卡标注、HyperFrames/Remotion 可选后端。

完整设计、路由、质量门和“精华 → 落点”映射见本文件第 3–8 节。

---

## 13. P1 + P2 已落地（2026-10-24）

| 能力 | 落点 | 实测 |
|---|---|---|
| 动效库（36 个纯函数） | `library/motion.js` | `tests/test_motion.js` 12 组通过 |
| 场景库（7 个 builder） | `library/scenes.js` | `examples/scene-demo` 9.4s 渲染通过；场景门修复了标签泄漏 |
| 8 套 look | `library/looks.js` | `examples/looks-demo` 8 卡画廊 |
| 8 套风格配方 | `styles/index.json` | look + 场景组合 + 避坑 |
| 快门运动模糊 | `render.py --shutter` | 180° / 4 worker / 960 帧 / 204s / 5,037 captures |
| 并行 + resume | `render.py --workers --resume` | 缺失帧续渲通过 |
| carry/framing/curves/reading | `scripts/probe.py` + `verify.py --comp` | promo: carry 1.0、framing PASS、curves PASS |
| 光流 | `analyze.py --flow` | think-big: peak 75.3 px/frame, fast 33% |
| TTS | `scripts/tts.py` | 中文 edge-tts 两行测试通过 |
| 音频合成/混音 | `scripts/audio.py` | BGM+SFX+VO，ducking，峰值归一 |
| EDIT 路线 | `scripts/edit_plan.py` + `compose.py` trim | 4s 两段剪辑测试通过 |
| GEN 路线 | `scripts/gen_prompts.py` | 分镜 JSON → Seedance/generic prompt pack |
| taste | `scripts/taste.py` | add/list 通过 |
| 安装 | `install.py --target claude/agents/dsh` | 含 library/styles/tests |
| CI | `.github/workflows/ci.yml` | compile + node tests + static checks |

仍未做：真实 GEN/EDIT provider API 调用、DSH 市场打包、平台级 QA、更多完整风格样例。
