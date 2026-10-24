#!/usr/bin/env python3
"""Small end-to-end checks for the CLI scripts that do not need Playwright.

Run from the skill folder:
  python -m unittest discover -s tests -p "test_*.py"
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
DEMO = ROOT / "examples" / "demo" / "out.mp4"
PY = sys.executable


def run(script: str, args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([PY, str(SCRIPTS / script), *args], cwd=cwd,
                          capture_output=True, text=True, errors="replace")


@unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg not on PATH")
class EditPlanTests(unittest.TestCase):
    def test_relative_out_lands_next_to_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "cuts.json").write_text(json.dumps({
                "out": "edit.mp4", "width": 320, "height": 180, "fps": 30,
                "clips": [{"file": str(DEMO), "in": 0, "out": 0.5}],
            }), encoding="utf-8")
            p = run("edit_plan.py", [str(d / "cuts.json"), "-o", str(d / "out" / "manifest.json")])
            self.assertEqual(p.returncode, 0, p.stderr)
            m = json.loads((d / "out" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(Path(m["out"]), (d / "out" / "edit.mp4").resolve())
            self.assertAlmostEqual(m["total"], 0.5, places=3)

    def test_missing_file_has_a_clean_error(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "cuts.json").write_text(json.dumps({"clips": [{"in": 0, "out": 1}]}),
                                         encoding="utf-8")
            p = run("edit_plan.py", [str(d / "cuts.json"), "-o", str(d / "m.json")])
            self.assertNotEqual(p.returncode, 0)
            self.assertIn("missing file", p.stderr)
            self.assertNotIn("Traceback", p.stderr)


class GenPromptsTests(unittest.TestCase):
    def test_nested_output_and_english_separator(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "shots.json").write_text(json.dumps([{
                "id": "A", "subject": "a woman", "action": "opens a laptop",
                "scene": "warm studio", "camera": "slow dolly in",
            }]), encoding="utf-8")
            p = run("gen_prompts.py", [str(d / "shots.json"), "-o", str(d / "a" / "b" / "prompts.md")])
            self.assertEqual(p.returncode, 0, p.stderr)
            text = (d / "a" / "b" / "prompts.md").read_text(encoding="utf-8")
            self.assertIn("a woman, opens a laptop, warm studio", text)
            self.assertTrue(text.endswith("\n"))


class TasteTests(unittest.TestCase):
    def test_nested_file_and_typed_value(self):
        with tempfile.TemporaryDirectory() as td:
            p = run("taste.py", ["--file", str(Path(td) / "deep" / "taste.json"),
                                 "add", "bigger captions", "--set", "captions.size=50"])
            self.assertEqual(p.returncode, 0, p.stderr)
            rows = json.loads((Path(td) / "deep" / "taste.json").read_text(encoding="utf-8"))
            self.assertEqual(rows[0]["set"]["captions.size"], 50)


class CheckTests(unittest.TestCase):
    def test_windows_absolute_path_fails(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "bad.html"
            p.write_text("""<html><body><script>
window.__meta={dur:1}; window.__seek=(t)=>{}; window.__ready=1;
const p = "C:\\\\Users\\\\someone\\\\asset.png";
</script></body></html>""", encoding="utf-8")
            r = run("check.py", [str(p)])
            self.assertEqual(r.returncode, 1)
            self.assertIn("absolute personal path", r.stdout + r.stderr)


class InstallTests(unittest.TestCase):
    def test_install_omits_render_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "codefilm"
            p = run("install.py", ["--dest", str(dest)])
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertTrue((dest / "SKILL.md").exists())
            self.assertEqual(list(dest.rglob("*.render.json")), [])
            self.assertEqual(list(dest.rglob("__pycache__")), [])


@unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg not on PATH")
class ComposeTests(unittest.TestCase):
    def test_missing_total_is_computed(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "manifest.json").write_text(json.dumps({
                "out": "out.mp4", "width": 320, "height": 180, "fps": 30,
                "shots": [{"file": str(DEMO), "trim_start": 0, "trim_end": 0.5}],
            }), encoding="utf-8")
            p = run("compose.py", [str(d / "manifest.json")], cwd=d)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertTrue((d / "out.mp4").exists())
            self.assertFalse((d / "out.build").exists())


if __name__ == "__main__":
    unittest.main()
