"""Build the 32s Shiguang promo soundtrack: BGM + SFX + VO, mixed and written to audio/mix.wav.

Pure numpy. All levels are relative; the final mix is normalised to -1.5 dBFS peak and then
loudnorm'd to -14 LUFS by ffmpeg at mux time.
"""
from __future__ import annotations

import json
import math
import subprocess
import wave
from pathlib import Path

import numpy as np

SR = 44100
DUR = 32.0
rng = np.random.default_rng(7)

# VO schedule (seconds)
STARTS = {"s1": 0.6, "s2": 3.9, "s3": 8.1, "s4": 11.7,
          "s5": 17.0, "s6": 21.8, "s7": 24.8, "s8": 27.9}


def midi(n: int) -> float:
    return 440.0 * 2 ** ((n - 69) / 12)


def add(buf: np.ndarray, t: float, sig: np.ndarray, gain: float = 1.0, pan: float = 0.5):
    i = int(t * SR)
    if i >= buf.shape[1] or i < 0:
        return
    j = min(buf.shape[1], i + len(sig))
    seg = sig[: j - i] * gain
    buf[0, i:j] += seg * (1.0 - pan)
    buf[1, i:j] += seg * pan


def pad(freq: float, dur: float, amp: float) -> np.ndarray:
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.minimum(t / 0.6, 1.0) * np.exp(-t * 0.35)
    sig = (np.sin(2 * np.pi * freq * t)
           + 0.32 * np.sin(2 * np.pi * 2 * freq * t + 0.3)
           + 0.12 * np.sin(2 * np.pi * 3 * freq * t + 0.7))
    return sig * env * amp


def pluck(freq: float, dur: float, amp: float) -> np.ndarray:
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = (1 - np.exp(-t * 220)) * np.exp(-t * 7.5)
    sig = (np.sin(2 * np.pi * freq * t)
           + 0.45 * np.sin(2 * np.pi * 2 * freq * t)
           + 0.18 * np.sin(2 * np.pi * 3 * freq * t))
    return sig * env * amp


def bass(freq: float, dur: float, amp: float) -> np.ndarray:
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = (1 - np.exp(-t * 80)) * np.exp(-t * 3.2)
    return np.sin(2 * np.pi * freq * t) * env * amp


def kick(amp: float = 0.16) -> np.ndarray:
    n = int(SR * 0.28)
    t = np.arange(n) / SR
    f = np.linspace(115, 45, n)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) * amp


def hat(amp: float = 0.03) -> np.ndarray:
    n = int(SR * 0.035)
    nz = rng.uniform(-1, 1, n)
    k = 18
    nz = np.convolve(nz, np.ones(k) / k, mode="same")
    return nz * np.exp(-np.arange(n) / SR * 90) * amp


def whoosh(dur: float = 0.55, amp: float = 0.20) -> np.ndarray:
    n = int(SR * dur)
    nz = rng.uniform(-1, 1, n)
    k = 80
    nz = np.convolve(nz, np.ones(k) / k, mode="same")
    t = np.arange(n) / SR
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.6
    return nz * env * amp


def click(amp: float = 0.12) -> np.ndarray:
    n = int(SR * 0.03)
    nz = rng.uniform(-1, 1, n)
    return nz * np.exp(-np.arange(n) / SR * 140) * amp


def tick(amp: float = 0.08) -> np.ndarray:
    n = int(SR * 0.022)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * 1700 * t) * np.exp(-t * 180) * amp


def pop(amp: float = 0.14) -> np.ndarray:
    n = int(SR * 0.08)
    t = np.arange(n) / SR
    f = np.linspace(520, 980, n)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38) * amp


def thud(amp: float = 0.28) -> np.ndarray:
    n = int(SR * 0.38)
    t = np.arange(n) / SR
    low = np.sin(2 * np.pi * 72 * t) * np.exp(-t * 11)
    nz = rng.uniform(-1, 1, n)
    nz = np.convolve(nz, np.ones(30) / 30, mode="same") * np.exp(-t * 18)
    return (low + 0.35 * nz) * amp


def chime(amp: float = 0.10) -> np.ndarray:
    n = int(SR * 1.6)
    t = np.arange(n) / SR
    sig = np.zeros(n)
    for f, g in [(880, 1.0), (1320, 0.55), (1760, 0.28), (2640, 0.12)]:
        sig += g * np.sin(2 * np.pi * f * t) * np.exp(-t * 2.6)
    return sig * amp


def build_bgm() -> np.ndarray:
    total = DUR + 1.0
    n = int(SR * total)
    buf = np.zeros((2, n))
    bpm = 92.0
    beat = 60.0 / bpm
    bar = beat * 4
    chords = [
        [48, 52, 55, 59],  # Cmaj7
        [45, 48, 52, 55],  # Am7
        [41, 45, 48, 52],  # Fmaj7
        [43, 47, 50, 53],  # G7
    ]
    pattern = [0, 2, 1, 3, 2, 0, 3, 1]
    bars = int(total / bar) + 2
    for b in range(bars):
        t0 = b * bar
        chord = chords[b % 4]
        for note in chord:
            add(buf, t0, pad(midi(note), bar * 0.98, 0.09), 0.11, 0.5)
        for k in range(8):
            note = chord[pattern[k] % len(chord)] + 12
            add(buf, t0 + k * beat / 2, pluck(midi(note), beat * 0.46, 0.07),
                0.10, 0.32 if k % 2 == 0 else 0.68)
        for bi in (0, 2):
            add(buf, t0 + bi * beat, bass(midi(chord[0] - 12), beat * 0.9, 0.09), 0.13, 0.5)
        for bi in (0, 2):
            add(buf, t0 + bi * beat, kick(), 0.16, 0.5)
        for k in range(4):
            add(buf, t0 + k * beat + beat / 2, hat(), 0.045, 0.6)
    return buf


def build_sfx() -> np.ndarray:
    n = int(SR * (DUR + 1))
    buf = np.zeros((2, n))
    # scene whooshes
    for t in [0.25, 3.55, 7.75, 11.35, 16.65, 24.55, 27.55]:
        add(buf, t, whoosh(), 0.18, 0.5)
    # s2 ticks / clicks
    for i, t in enumerate([3.95, 4.45, 4.95, 5.45, 5.95, 6.45, 6.95]):
        add(buf, t, tick(), 0.08, 0.35 + 0.05 * (i % 2))
    for t in [5.8, 6.7]:
        add(buf, t, click(), 0.13, 0.5)
    # s3 reveal
    add(buf, 8.65, pop(0.16), 1.0, 0.5)
    add(buf, 9.0, thud(0.22), 1.0, 0.5)
    add(buf, 9.2, chime(0.12), 1.0, 0.5)
    # s4 typing
    for i in range(14):
        add(buf, 12.0 + i * 0.11, tick(0.05), 1.0, 0.42)
    add(buf, 14.55, click(0.16), 1.0, 0.5)
    add(buf, 14.78, pop(0.15), 1.0, 0.5)
    # s5 nodes + links
    for t in [17.25, 17.85, 18.45]:
        add(buf, t, pop(0.12), 1.0, 0.5)
    add(buf, 17.55, whoosh(0.6, 0.10), 1.0, 0.5)
    # s6 checks + stamp
    for t in [22.2, 22.8, 23.4]:
        add(buf, t, tick(0.10), 1.0, 0.5)
    add(buf, 23.8, thud(0.30), 1.0, 0.5)
    add(buf, 23.95, chime(0.10), 1.0, 0.5)
    # s7 / s8
    add(buf, 25.0, whoosh(0.45, 0.08), 1.0, 0.5)
    add(buf, 27.95, chime(0.12), 1.0, 0.5)
    add(buf, 28.4, bass(midi(36), 1.8, 0.12), 1.0, 0.5)
    return buf


def load_vo() -> tuple[np.ndarray, dict]:
    meta = json.loads(Path("vo.json").read_text(encoding="utf-8"))
    n = int(SR * (DUR + 1))
    vo = np.zeros((2, n))
    used = {}
    for row in meta:
        sid = row["id"]
        start = STARTS[sid]
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", row["file"], "-f", "f32le",
                            "-ac", "1", "-ar", str(SR), "-"], capture_output=True)
        sig = np.frombuffer(r.stdout, dtype=np.float32).astype(np.float32)
        add(vo, start, sig, 1.0, 0.5)
        used[sid] = {"start": start, "duration": round(len(sig) / SR, 3), "text": row["text"]}
    return vo, used


def duck_env(used: dict) -> np.ndarray:
    n = int(SR * (DUR + 1))
    env = np.ones(n, np.float32)
    fade = int(0.30 * SR)
    for v in used.values():
        a = max(0, int((v["start"] - 0.25) * SR))
        b = min(n, int((v["start"] + v["duration"] + 0.25) * SR))
        env[a:b] = 0.32
        if a > fade:
            env[a - fade:a] = np.linspace(1.0, 0.32, fade)
        if b + fade < n:
            env[b:b + fade] = np.linspace(0.32, 1.0, fade)
    return env


def write_wav(path: str, stereo: np.ndarray):
    peak = float(np.max(np.abs(stereo))) if stereo.size else 0.0
    if peak > 0:
        stereo = stereo / peak * 0.95
    pcm = (np.clip(stereo.T, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    Path("audio").mkdir(exist_ok=True)
    vo, used = load_vo()
    bgm = build_bgm()
    sfx = build_sfx()
    bgm *= duck_env(used)[None, :]
    mix = vo * 1.0 + bgm * 0.9 + sfx * 0.85
    write_wav("audio/vo.wav", vo)
    write_wav("audio/bgm.wav", bgm)
    write_wav("audio/sfx.wav", sfx)
    write_wav("audio/mix.wav", mix)
    Path("timing.json").write_text(json.dumps({"duration": DUR, "vo": used}, ensure_ascii=False, indent=1),
                                   encoding="utf-8")
    print(f"mix: {mix.shape[1]/SR:.2f}s  peak {np.max(np.abs(mix)):.3f}")
    for sid, v in used.items():
        print(f"  {sid} {v['start']:.2f}s + {v['duration']:.2f}s  {v['text']}")


if __name__ == "__main__":
    main()
