#!/usr/bin/env python3
"""Synthesize a BGM bed + SFX and mix narration (numpy, no samples).

  python scripts/audio.py --vo vo/vo.json --duration 32 --out audio/mix.wav
  python scripts/audio.py --vo vo/vo.json --events events.json --bpm 92

events.json:
  [{"t": 0.5, "kind": "whoosh", "gain": 1.0, "pan": 0.5}, ...]
  kinds: whoosh, click, tick, pop, thud, chime, stamp

Writes <out>, plus bgm.wav / sfx.wav / vo.wav next to it. Peak-normalised to 0.95;
mux with `ffmpeg ... -af loudnorm=I=-14:TP=-1.5:LRA=11`.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cf_common import CFError, die, ensure_dir  # noqa: E402

SR = 44100
RNG = np.random.default_rng(7)


def midi(n: int) -> float:
    return 440.0 * 2 ** ((n - 69) / 12)


def add(buf: np.ndarray, t: float, sig: np.ndarray, gain: float = 1.0, pan: float = .5):
    i = int(t * SR)
    if i >= buf.shape[1] or i < 0:
        return
    j = min(buf.shape[1], i + len(sig))
    seg = sig[: j - i] * gain
    buf[0, i:j] += seg * (1 - pan)
    buf[1, i:j] += seg * pan


def pad(freq, dur, amp):
    n = int(SR * dur); t = np.arange(n) / SR
    env = np.minimum(t / .6, 1) * np.exp(-t * .35)
    return (np.sin(2*np.pi*freq*t) + .32*np.sin(2*np.pi*2*freq*t+.3)
            + .12*np.sin(2*np.pi*3*freq*t+.7)) * env * amp


def pluck(freq, dur, amp):
    n = int(SR * dur); t = np.arange(n) / SR
    env = (1 - np.exp(-t * 220)) * np.exp(-t * 7.5)
    return (np.sin(2*np.pi*freq*t) + .45*np.sin(2*np.pi*2*freq*t)
            + .18*np.sin(2*np.pi*3*freq*t)) * env * amp


def bass(freq, dur, amp):
    n = int(SR * dur); t = np.arange(n) / SR
    return np.sin(2*np.pi*freq*t) * (1 - np.exp(-t*80)) * np.exp(-t*3.2) * amp


def kick(amp=.16):
    n = int(SR*.28); t = np.arange(n)/SR; f = np.linspace(115,45,n)
    return np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t*9) * amp


def hat(amp=.03):
    n = int(SR*.035); nz = RNG.uniform(-1,1,n)
    nz = np.convolve(nz, np.ones(18)/18, mode="same")
    return nz * np.exp(-np.arange(n)/SR*90) * amp


def whoosh(dur=.55, amp=.20):
    n = int(SR*dur); nz = RNG.uniform(-1,1,n)
    nz = np.convolve(nz, np.ones(80)/80, mode="same")
    t = np.arange(n)/SR
    return nz * np.sin(np.pi*np.clip(t/dur,0,1))**1.6 * amp


def click(amp=.12):
    n = int(SR*.03); nz = RNG.uniform(-1,1,n)
    return nz * np.exp(-np.arange(n)/SR*140) * amp


def tick(amp=.08):
    n = int(SR*.022); t = np.arange(n)/SR
    return np.sin(2*np.pi*1700*t) * np.exp(-t*180) * amp


def pop_sfx(amp=.14):
    n = int(SR*.08); t = np.arange(n)/SR; f = np.linspace(520,980,n)
    return np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t*38) * amp


def thud(amp=.28):
    n = int(SR*.38); t = np.arange(n)/SR
    low = np.sin(2*np.pi*72*t) * np.exp(-t*11)
    nz = RNG.uniform(-1,1,n)
    nz = np.convolve(nz, np.ones(30)/30, mode="same") * np.exp(-t*18)
    return (low + .35*nz) * amp


def chime(amp=.10):
    n = int(SR*1.6); t = np.arange(n)/SR; sig = np.zeros(n)
    for f, g in [(880,1),(1320,.55),(1760,.28),(2640,.12)]:
        sig += g*np.sin(2*np.pi*f*t)*np.exp(-t*2.6)
    return sig * amp


SFX = {"whoosh": whoosh, "click": click, "tick": tick, "pop": pop_sfx,
       "thud": thud, "chime": chime, "stamp": lambda amp=.3: thud(amp)}


def build_bgm(duration: float, bpm: float) -> np.ndarray:
    total = duration + 1
    n = int(SR*total); buf = np.zeros((2, n))
    beat = 60.0/bpm; bar = beat*4
    chords = [[48,52,55,59], [45,48,52,55], [41,45,48,52], [43,47,50,53]]
    pattern = [0,2,1,3,2,0,3,1]
    bars = int(total/bar)+2
    for b in range(bars):
        t0 = b*bar; chord = chords[b % 4]
        for note in chord:
            add(buf, t0, pad(midi(note), bar*.98, .09), .11, .5)
        for k in range(8):
            add(buf, t0+k*beat/2, pluck(midi(chord[pattern[k] % len(chord)]+12), beat*.46, .07),
                .10, .32 if k % 2 == 0 else .68)
        for bi in (0,2):
            add(buf, t0+bi*beat, bass(midi(chord[0]-12), beat*.9, .09), .13, .5)
            add(buf, t0+bi*beat, kick(), .16, .5)
        for k in range(4):
            add(buf, t0+k*beat+beat/2, hat(), .045, .6)
    return buf


def build_sfx(events: list[dict], duration: float) -> np.ndarray:
    n = int(SR*(duration+1)); buf = np.zeros((2, n))
    for ev in events:
        kind = ev.get("kind", "whoosh")
        fn = SFX.get(kind)
        if not fn:
            continue
        dur = float(ev.get("dur", .55 if kind == "whoosh" else .3))
        sig = fn(dur, ev.get("amp", .2)) if kind == "whoosh" else fn()
        add(buf, float(ev.get("t", 0)), sig, float(ev.get("gain", 1)), float(ev.get("pan", .5)))
    return buf


def load_vo(vo_path: Path, duration: float) -> np.ndarray:
    n = int(SR*(duration+1)); buf = np.zeros((2, n))
    rows = json.loads(vo_path.read_text(encoding="utf-8"))
    for row in rows:
        p = Path(row["file"])
        if not p.exists():
            die(f"VO file missing: {p}")
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "f32le",
                            "-ac", "1", "-ar", str(SR), "-"], capture_output=True)
        sig = np.frombuffer(r.stdout or b"", dtype=np.float32)
        add(buf, float(row.get("start", 0)), sig.astype(np.float32), 1.0, .5)
    return buf


def duck_env(vo: np.ndarray, depth: float = .32, fade: float = .3) -> np.ndarray:
    n = vo.shape[1]
    env = np.ones(n, np.float32)
    active = np.abs(vo).mean(axis=0) > 1e-4
    f = int(fade*SR)
    # smooth the activity into a ducking envelope
    a = active.astype(np.float32)
    k = max(1, int(.15*SR))
    a = np.convolve(a, np.ones(k)/k, mode="same")
    env = 1 - (1-depth)*np.clip(a*8, 0, 1)
    return env


def write_wav(path: Path, stereo: np.ndarray):
    peak = float(np.max(np.abs(stereo))) if stereo.size else 0.0
    if peak > 0:
        stereo = stereo / peak * .95
    pcm = (np.clip(stereo.T, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vo", default=None, help="vo.json from tts.py")
    ap.add_argument("--duration", type=float, default=0)
    ap.add_argument("--out", default="audio/mix.wav")
    ap.add_argument("--bpm", type=float, default=92)
    ap.add_argument("--events", default=None, help="SFX events JSON")
    ap.add_argument("--music-gain", type=float, default=.9)
    ap.add_argument("--sfx-gain", type=float, default=.85)
    ap.add_argument("--vo-gain", type=float, default=1.0)
    ap.add_argument("--no-bgm", action="store_true")
    ap.add_argument("--no-sfx", action="store_true")
    a = ap.parse_args()
    vo_path = Path(a.vo) if a.vo else None
    rows = json.loads(vo_path.read_text(encoding="utf-8")) if vo_path else []
    duration = a.duration or (max((float(r.get("start", 0)) + float(r.get("duration", 0)) for r in rows), default=0) + 1.0)
    if duration <= 0:
        die("give --duration or a vo.json with timings")
    out = Path(a.out); ensure_dir(out.parent)
    vo = load_vo(vo_path, duration) if vo_path else np.zeros((2, int(SR*(duration+1))))
    bgm = build_bgm(duration, a.bpm) if not a.no_bgm else np.zeros((2, int(SR*(duration+1))))
    events = json.loads(Path(a.events).read_text(encoding="utf-8")) if a.events else []
    sfx = build_sfx(events, duration) if not a.no_sfx else np.zeros((2, int(SR*(duration+1))))
    bgm *= duck_env(vo)[None, :]
    mix = vo*float(a.vo_gain) + bgm*float(a.music_gain) + sfx*float(a.sfx_gain)
    write_wav(out, mix)
    write_wav(out.with_name("vo.wav"), vo)
    write_wav(out.with_name("bgm.wav"), bgm)
    write_wav(out.with_name("sfx.wav"), sfx)
    print(f"mix {duration:.2f}s -> {out}  peak {np.max(np.abs(mix)):.3f}  "
          f"vo {len(rows)} lines  sfx {len(events)} events")


if __name__ == "__main__":
    try:
        main()
    except CFError as e:
        die(str(e))
