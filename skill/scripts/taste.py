#!/usr/bin/env python3
"""Persist taste corrections as small, checkable rules.

  python scripts/taste.py add "too many zooms" --metric punch_ins --max 2
  python scripts/taste.py add "that riser is cheesy" --ban-sfx riser-1
  python scripts/taste.py add "captions a bit larger" --set captions.size=50
  python scripts/taste.py list
  python scripts/taste.py check --json

Taste is a prior: a film's own spec/beats always win. Only the user's own words are
`from: user`; a rule the agent learned is `from: skill`.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

DEFAULT = "taste.json"


def load(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save(path: str, rows: list[dict]):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")


def _value(v: str):
    """Keep numbers/bools typed so rules stay checkable."""
    try:
        return json.loads(v)
    except (json.JSONDecodeError, TypeError):
        return v


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", default=DEFAULT)
    sub = ap.add_subparsers(dest="cmd", required=True)

    add = sub.add_parser("add", help="record one correction")
    add.add_argument("text")
    add.add_argument("--from", dest="source", choices=["user", "skill"], default="user")
    add.add_argument("--metric", default=None)
    add.add_argument("--max", type=float, default=None)
    add.add_argument("--set", dest="set_value", default=None, help="key=value")
    add.add_argument("--ban-sfx", default=None)

    sub.add_parser("list", help="print all rules")
    chk = sub.add_parser("check", help="print rules as JSON")
    chk.add_argument("--json", action="store_true")

    a = ap.parse_args()
    rows = load(a.file)
    if a.cmd == "add":
        rule = {"id": f"T{len(rows)+1:03d}", "text": a.text, "from": a.source,
                "created": _dt.date.today().isoformat()}
        if a.metric:
            rule["metric"] = a.metric
            if a.max is not None:
                rule["max"] = a.max
        if a.set_value:
            if "=" not in a.set_value:
                sys.exit("--set needs key=value")
            k, v = a.set_value.split("=", 1)
            rule["set"] = {k: _value(v)}
        if a.ban_sfx:
            rule["ban_sfx"] = a.ban_sfx
        rows.append(rule)
        save(a.file, rows)
        print(f"added {rule['id']} ({rule['from']}): {a.text}")
    elif a.cmd == "list":
        for r in rows:
            extra = " ".join(f"{k}={r[k]}" for k in ("metric", "max", "set", "ban_sfx") if k in r)
            print(f"{r['id']} [{r.get('from','user')}] {r['text']}" + (f"  ({extra})" if extra else ""))
        print(f"{len(rows)} rule(s) in {a.file}")
    elif a.cmd == "check":
        print(json.dumps(rows, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
