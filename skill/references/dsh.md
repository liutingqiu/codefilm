# DSH (DeepSeek Harness) install

`codefilm` is a normal `SKILL.md` folder, so DSH can read it from its skill directory:

```bash
python scripts/install.py --target dsh     # ~/.dsh/skills/codefilm
```

Restart DSH. The skill's scripts use Python + ffmpeg; rendering and `probe.py` need Playwright
(`pip install playwright`). If your DSH version reads `~/.agents/skills` instead, use
`--target agents`.

## As a plugin

If you package it as a DSH plugin, the plugin must ship the skill folder and declare it. A minimal
layout (check your DSH version's plugin schema; this is an example, not a tested marketplace package):

```
codefilm-dsh/
  package.json
  cordis.patch.yml
  skills/codefilm/        <- copy of this skill
```

`package.json`:

```json
{
  "name": "codefilm-dsh",
  "version": "0.1.0",
  "private": true,
  "description": "codefilm — make videos by writing code",
  "dsh": {"skills": "skills"},
  "files": ["skills", "README.md"]
}
```

Build it from this skill:

```bash
mkdir -p dist/codefilm-dsh/skills
cp -r . dist/codefilm-dsh/skills/codefilm
```

Do not publish to npm until the skill passes the project's own `check.py`/`verify.py` on your
machine and the licenses in `references/credits.md` have been reviewed.
