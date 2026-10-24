# Audio: TTS, music, SFX, mix

## 1. Narration

```bash
python scripts/tts.py vo/lines.json -o vo/ --voice zh-CN-XiaoxiaoNeural --gap 0.35
```

`lines.json`:

```json
[{"id":"s1","text":"脑子里，有一百个想法。"},
 {"id":"s2","text":"它们散落在便签、聊天和文档里。","rate":"-2%"}]
```

Writes `vo/<id>.mp3` and `vo/vo.json` with `{id,text,file,duration,start}`. Pass `--starts starts.json`
to pin absolute starts; otherwise it schedules sequentially with `--gap`. Requires `pip install edge-tts`.
Chinese edge-tts does not emit word boundaries; scenes are scheduled per line. For word-level timing,
run faster-whisper on the generated audio (optional).

## 2. Music + SFX

```bash
python scripts/audio.py --vo vo/vo.json --duration 32 --out audio/mix.wav --bpm 92
python scripts/audio.py --vo vo/vo.json --events audio/events.json --out audio/mix.wav
```

`events.json`:

```json
[{"t":0.5,"kind":"whoosh","gain":1.0,"pan":0.5},
 {"t":3.8,"kind":"thud"},
 {"t":9.2,"kind":"chime"}]
```

Kinds: `whoosh, click, tick, pop, thud, chime, stamp`. All are numpy-synthesised; no samples.
`audio.py` writes `mix.wav`, `bgm.wav`, `sfx.wav`, `vo.wav`, ducks the BGM under narration and
peak-normalises to 0.95.

## 3. Mux + master

```bash
ffmpeg -v error -y -i out/video.mp4 -i audio/mix.wav -c:v copy -c:a aac -b:a 192k \
  -shortest -movflags +faststart out/mux.mp4
ffmpeg -v error -y -i out/mux.mp4 -c:v copy -af "loudnorm=I=-14:TP=-1.5:LRA=11" \
  -c:a aac -b:a 192k -movflags +faststart out/final.mp4
```

Target: −14 LUFS integrated, −1.5 dBTP, music ≈ −10 dB under voice, 0.2–0.3 s duck fades.

## 4. Verify

- `verify.py` checks peak ≤ −1.0 dBFS, 0 clipped, ≥15 % quiet windows.
- Measure a voice window and a gap with `ffmpeg -ss ... -t ... -af astats`. A healthy mix:
  voice ≈ −18 dB RMS, gaps ≈ −40 dB.
- If a published file must be matched to a reference WAV, use cross-correlation; `≥0.9` means the
  same version.
