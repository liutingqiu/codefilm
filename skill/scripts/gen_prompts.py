#!/usr/bin/env python3
"""Turn a shot list into a copy-paste prompt pack for a video model (GEN route).

  python scripts/gen_prompts.py shots.json -o prompts.md --format seedance

shots.json:
  [{"id":"A","time":"0-3s","subject":"a woman at a desk",
    "action":"she opens a laptop slowly","scene":"warm studio, morning",
    "light":"soft window light, side","camera":"slow dolly in, 35mm",
    "style":"photographic, warm paper tones","product":"@product ref 1",
    "text":"optional on-screen line"}]

No API calls: this is the prompt package the agent or user pastes into Seedance / Kling / Veo.
The script never invents a reference asset; @names in the input are kept verbatim.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cf_common import CFError, die, write_json  # noqa: E402

NEGATIVE = "blur, distortion, extra fingers, deformed hands, text artifacts, watermark, logo, flicker, jump cut"


def build(shots: list[dict], fmt: str) -> str:
    lines = ["# Shot prompts", ""]
    for s in shots:
        sid = s.get("id", "?")
        tm = s.get("time", "")
        parts = [s.get(k, "").strip() for k in ("subject", "action", "scene", "light", "camera", "style")]
        prompt = "，".join(p for p in parts if p)
        if s.get("product"):
            prompt += f"，产品参考：{s['product']}"
        if s.get("text"):
            prompt += f"，画面文字：{s['text']}"
        if fmt == "seedance":
            prompt += "，画面稳定，人物五官自然，结构正常，无抖动，无闪烁。"
        lines += [f"## Shot {sid} {('· ' + tm) if tm else ''}", "", "```", prompt.strip("，"), "```", ""]
    lines += ["## Negative", "", "```", NEGATIVE, "```", "",
              "## Reference assets", "",
              "- @product ref 1: clean product photo, solid background, even light",
              "- @character ref 1: front-facing portrait, neutral expression (optional)",
              "", "## Notes", "",
              "- One camera move per shot; keep the light direction fixed within a shot.",
              "- Do not put a real brand logo or a real person's face into a generated shot unless you have the rights.",
              "- Check each generated clip against the shot's time and purpose before assembling."]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("shots")
    ap.add_argument("-o", "--out", default="prompts.md")
    ap.add_argument("--format", choices=["seedance", "generic"], default="generic")
    a = ap.parse_args()
    shots = json.loads(Path(a.shots).read_text(encoding="utf-8"))
    if not isinstance(shots, list) or not shots:
        die("shots JSON must be a non-empty array")
    md = build(shots, a.format)
    Path(a.out).write_text(md, encoding="utf-8")
    write_json(Path(a.out).with_suffix(".json"), {"format": a.format, "shots": shots,
                                                  "negative": NEGATIVE})
    print(f"wrote {a.out} ({len(shots)} shots)")


if __name__ == "__main__":
    try:
        main()
    except CFError as e:
        die(str(e))
