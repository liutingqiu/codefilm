#!/usr/bin/env python3
"""Install codefilm into an agent's skills directory.

  python scripts/install.py --target claude     # ~/.claude/skills/codefilm
  python scripts/install.py --target agents     # ~/.agents/skills/codefilm
  python scripts/install.py --target dsh        # ~/.dsh/skills/codefilm
  python scripts/install.py --dest /path/codefilm

Copies SKILL.md, AGENTS.md, README.md, scripts/, templates/, references/, library/, examples/,
tests/ — not work products (out/, work/, diff/, __pycache__). Existing destination is replaced
after a .bak backup.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INCLUDE = ["SKILL.md", "AGENTS.md", "README.md", "scripts", "templates", "references",
           "library", "styles", "examples", "tests"]
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.render.json", "*.build",
                                "out", "work", "diff", "_frames", "_seq", ".git")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", choices=["claude", "agents", "dsh"], default="claude")
    ap.add_argument("--dest", help="explicit destination directory (overrides --target)")
    a = ap.parse_args()
    if a.dest:
        dest = Path(a.dest).expanduser().resolve()
    elif a.target == "claude":
        dest = Path.home() / ".claude" / "skills" / "codefilm"
    elif a.target == "agents":
        dest = Path.home() / ".agents" / "skills" / "codefilm"
    else:
        dest = Path.home() / ".dsh" / "skills" / "codefilm"
    if dest.exists():
        backup = dest.with_name(dest.name + ".bak")
        if backup.exists():
            shutil.rmtree(backup)
        dest.rename(backup)
        print(f"backup: {backup}")
    dest.mkdir(parents=True, exist_ok=True)
    for name in INCLUDE:
        src = ROOT / name
        if not src.exists():
            continue
        dst = dest / name
        if src.is_dir():
            shutil.copytree(src, dst, ignore=IGNORE)
        else:
            shutil.copy2(src, dst)
    print(f"installed codefilm -> {dest}")
    print("Restart the agent to pick up the skill. Rendering needs: pip install playwright")


if __name__ == "__main__":
    main()
