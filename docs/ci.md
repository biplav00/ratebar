# CI & Releases

ratebar builds itself on GitHub Actions: [`.github/workflows/build.yml`](../.github/workflows/build.yml).

## What runs, and when

| Trigger | What happens |
|---|---|
| Push to `main` | Test → build `.app`/`.dmg` → upload the `.dmg` as a build **artifact** |
| Pull request → `main` | Same test + build (verifies the PR builds) — no release |
| Push a tag `v*` (e.g. `v0.3.0`) | Same, **plus** attach the `.dmg` to the GitHub **Release** for that tag |

The job runs on a **`macos-14`** (Apple Silicon) runner, so the produced bundle
is arm64 — matching local `packaging/build_dmg.sh` output.

## Steps

1. `actions/checkout`
2. Install [uv](https://docs.astral.sh/uv/) (`astral-sh/setup-uv`, cache enabled)
3. `uv sync --frozen` — installs from `uv.lock`, including the dev group
   (`pytest`, `pyinstaller`)
4. `uv run pytest -q`
5. `bash packaging/build_dmg.sh` — PyInstaller → `.app`, then `hdiutil` → `.dmg`
6. `actions/upload-artifact` — the `.dmg`
7. On tags only: `softprops/action-gh-release` attaches the `.dmg`

## Getting the build

- **From a push to main:** open the run under the repo's **Actions** tab →
  the **`ratebar-dmg`** artifact (a zip containing `ratebar.dmg`).
- **From a release:** the `.dmg` is attached directly to the release.

## Cutting a release

Tag and push — the workflow builds and attaches the `.dmg` automatically:

```bash
git tag v0.3.0
git push origin v0.3.0
```

The release notes default to auto-generated. To control them, create the release
first (`gh release create v0.3.0 --notes "…"`) — the workflow will add the
`.dmg` to it.

## Notes

- The build is **unsigned / not notarized** (no Apple Developer cert in CI).
  Downloaders open it once via right-click → Open. Adding signing/notarization
  later means storing certs as repo secrets and a `codesign`/`notarytool` step.
- `permissions: contents: write` is scoped so the tag job can upload release
  assets; nothing else needs write access.
- `concurrency` cancels an in-flight build when a newer commit lands on the same
  ref.
