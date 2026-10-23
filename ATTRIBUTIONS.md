# Attributions

`codefilm` is a clean-room implementation. **No source code from the projects below is included in
this repository.** The table records what informed the design, the contract, or the demo. Where a
project is MIT or Apache-2.0, its ideas and parameter choices were adapted with attribution; where a
project is AGPL-3.0 or PolyForm-Noncommercial, only architecture and process were studied — no code
was copied.

## Directly informed the engine

| Project | License | What informed `codefilm` |
|---|---|---|
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | Apache-2.0 | render contract (`data-start`/`data-duration`, paused timeline, deterministic render), lint/check, motion doctrine, cut-the-curve, story/spec discipline |
| [lovisdotio/motion2code](https://github.com/lovisdotio/motion2code) | MIT | minimal `window.anim` contract, study/palette/frame_diff/check/render approach, SVG+GSAP architecture |
| [feitangyuan/onetake](https://github.com/feitangyuan/onetake) | **PolyForm-Noncommercial-1.0.0** | `__seek(t)` architecture, 39-move motion library idea, shutter motion blur, verify oracle. **No code copied.** |
| [lemomo-ai/lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) | MIT | `render(t)` + `TEXTS(t)` + `readcheck`, style-library concept, TTS/ASR/mux workflow |
| [garycaogan/pixel-diary](https://github.com/garycaogan/pixel-diary) | MIT | episode JSON → timeline, scene renderers, synthesized SFX/BGM, pixel text |
| [liaojianquan9-source/ljq-broll-video-generator](https://github.com/liaojianquan9-source/ljq-broll-video-generator) | MIT | evidence/confidence schema, layout→motion→QA attribution, two-round fix gate |
| [motalim-ai/motion-starter-kit](https://github.com/motalim-ai/motion-starter-kit) | MIT | reference analysis metrics (cut rate, shot length, motion strips, palette, onsets), numeric style bible |
| [kurbaitaev/ghost-editor](https://github.com/kurbaitaev/ghost-editor) | MIT | style-as-system, approval sheet, taste memory, render QA report |
| [bobobo2026/explainer-video](https://github.com/bobobo2026/explainer-video) | MIT | Chinese script structure, TTS word timeline, cue anchoring, audio bed, quality rubric |
| [439436269-ctrl/dsh-video-pipeline](https://github.com/439436269-ctrl/dsh-video-pipeline) | MIT | manifest compose, `astats`/NCC/brightness verification, orchestration + atomic skills |
| [whaojie797-design/video-reverse-engineering](https://github.com/whaojie797-design/video-reverse-engineering) | MIT | `extract_shots.sh` workflow, shot glossary, S-A-C-S-C prompt structure |
| [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) | **AGPL-3.0** | reference-video entry point, five-aspect shot language, `motion_type` routing, capability audit, 2–3 differentiated concepts, sample-first, pipeline/checkpoint governance. **No code copied.** |

## Surveyed for style, prompting or orchestration

| Project | License | Contribution |
|---|---|---|
| [hypit-ai/hypit](https://github.com/hypit-ai/hypit) | Apache-2.0 | Brief/Treatment/Timeline/Canvas concepts; reference as evidence |
| [huangserva/skill_video-style-analysis](https://github.com/huangserva/skill_video-style-analysis) | No license file | 6-layer 16-dimension analysis rubric; ASR-first fallback (ideas only) |
| [CY-CHENYUE/video-replication-sop-cy](https://github.com/CY-CHENYUE/video-replication-sop-cy) | No license file | 7-step replication SOP; character-card locking (ideas only) |
| [huojiaheng123-cpu/video-replication-breakdown-skill](https://github.com/huojiaheng123-cpu/video-replication-breakdown-skill) | No license file | HTML breakdown page; hook/narrative/storyboard/style/audio layers (ideas only) |
| [lvsccode/ecom-video-seedance-prompt](https://gitee.com/lvsccode/ecom-video-seedance-prompt) | No license file | DeepSeek vision shot cards; S-A-C-S-C prompt package (ideas only) |
| [Alisa0808/vox-director](https://github.com/Alisa0808/vox-director) | MIT | beat map, theme presets, 3–6 s shot cadence, two approval gates |
| [digitalsamba/claude-code-video-toolkit](https://github.com/digitalsamba/claude-code-video-toolkit) | MIT | TTS/music/QC tooling, synthetic UI demos, project lifecycle |
| [JuneYaooo/cheap-claude-video](https://github.com/JuneYaooo/cheap-claude-video) | Apache-2.0 | “video recipe” distillation idea |
| [STARDUSTLC666/dsh-remotion](https://github.com/STARDUSTLC666/dsh-remotion) | MIT | Remotion skill porting and local video workbench |
| [llafztq/dsh-video-tool](https://github.com/llafztq/dsh-video-tool) | MIT | ffmpeg-based trim/concat/subtitle/frame-grab toolset |
| [kingselyjoe/video-shotcraft-dsh](https://github.com/kingselyjoe/video-shotcraft-dsh) | Apache-2.0 | 152 shot recipe cards, 2.5D page camera, beat-synced cuts, final review |
| [Finderchangchang/promo-video-skill](https://github.com/Finderchangchang/promo-video-skill) | Apache-2.0 | semantic `storyboard.json`, cheap-model-only-writes-JSON, compliance checks |
| [nolangz/pixel2motion](https://github.com/nolangz/pixel2motion) | MIT | raster logo → minimal SVG → 12-principles animation; smoothness gate; final-frame contract |
| [Agentchengfeng/chengfeng-videocut-skills](https://github.com/Agentchengfeng/chengfeng-videocut-skills) | Apache-2.0 | Chinese video-editing skill collection |
| [chenyuxiaojin/cyxj-hyperframes](https://github.com/chenyuxiaojin/cyxj-hyperframes) | MIT | HyperFrames tutorial-video projects and reusable toolkit |
| [riffkit/dsh-plugin](https://github.com/riffkit/dsh-plugin) | MIT | adapt-vs-swap riff modes, quote-before-spend |
| [remotion-dev/skills](https://github.com/remotion-dev/skills) | See repository | Remotion official agent skills (alternative backend) |
| [diffusionstudio/lottie](https://github.com/diffusionstudio/lottie) | MIT | agent-generated Lottie animations |
| [gnipbao/story-to-handdrawn-video](https://github.com/gnipbao/story-to-handdrawn-video) | No license file | surveyed; repository clone was empty at the time |
| [zhuyansen/awesome-claude-video-skills](https://github.com/zhuyansen/awesome-claude-video-skills) | CC0-1.0 | 336-project index used to find the projects above |
| [xuanxuan1983/hermes-skills-backup](https://github.com/xuanxuan1983/hermes-skills-backup) | No license file | 455-skill backup; used to find HyperFrames timing/replication notes (ideas only) |
| [Aurirlk/Aurirlk-DSH-skills](https://github.com/Aurirlk/Aurirlk-DSH-skills) | MIT | DSH skill packaging reference |

## Assets in this repository

- **Picture:** original code in `promo/comp.html`; no stock footage, images or video models.
- **Music / SFX:** synthesized from scratch with numpy in `promo/audio_build.py`; no third-party
  samples.
- **Voice:** generated with [edge-tts](https://github.com/rany2/edge-tts) using the Microsoft
  `zh-CN-XiaoxiaoNeural` voice. No voice model weights are included. The generated narration is
  included as a demo asset and is **not** relicensed under MIT; check Microsoft's terms before
  redistributing the audio on its own, or regenerate it with a voice you have rights to.
- **Fonts:** the promo uses the system font “Microsoft YaHei” via CSS. No font files are included or
  redistributed.
- **Fictional brand:** 拾光 / Shiguang and `shiguang.app` are fictional and created for this demo.
- **Icons:** all drawn with CSS/SVG in the composition.

## If you reuse this repository

MIT for the code and the original demo (`LICENSE`). If you reuse ideas from an AGPL or
PolyForm-Noncommercial project listed above, that project’s license governs your distribution; do not
copy their code into a permissively licensed product without checking.
