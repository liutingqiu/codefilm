# vendor/ — optional pinned browser libraries

Nothing is bundled here by default. codefilm runs with zero third-party JavaScript; this folder
is where the agent puts a library when a film genuinely needs one.

## Rules

- **Pin the exact version.** Use the version in
  [`../references/js-libraries.md`](../references/js-libraries.md); never `@latest` in a render.
- **Use an official source.** Official npm tarball or the pinned CDN URL from the library page.
  Do not use a random mirror. Do not run postinstall scripts from an unfamiliar package.
- **Keep it local for the final render.** Load `vendor/<name>@<version>/...` with a relative
  `<script src>` or an import map. A runtime CDN is fine for a quick preview, not for the render.
- **Record provenance.** Add a row below with version, source URL, SHA-256, and license. Keep the
  upstream license file in the library folder.
- **Do not edit vendored code.** Patch the composition or adapter layer instead.

## Registry

| Library | Version | Source URL | SHA-256 | License | Used by |
|---|---|---|---|---|---|
| GSAP (`gsap.min.js`) | 3.15.0 | `https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js` | `92bb9a96476f983d212a2bc4f54c889039c1696dd4461d40a736860938570fbb` | GSAP Standard (**not MIT**) | `examples/gsap-demo` |

The library folders are **gitignored by default** in this repository: third-party code keeps its
own license and should not be relicensed by this MIT project. Commit a vendored folder only when
the license clearly permits it. The registry row above is still required so the build is
reproducible.

## Loading examples

```html
<!-- UMD: one script, global -->
<script src="vendor/gsap@3.15.0/gsap.min.js"></script>
<script src="../../library/adapters.js"></script>
```

```html
<!-- ESM: import map, then a module script -->
<script type="importmap">
{"imports": {"three": "./vendor/three@0.186.1/three.module.js"}}
</script>
<script type="module">
  import * as THREE from 'three';
  // build the scene; window.__seek = (t) => { update(t); renderer.render(scene, camera); };
</script>
```

After adding a library, run:

```bash
python scripts/check.py comp.html --runtime
python scripts/render.py comp.html -o out/draft.mp4
```
