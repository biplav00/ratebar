# CI & Releases

ratebar builds itself on GitHub Actions: [`.github/workflows/build.yml`](../.github/workflows/build.yml).

## What runs, and when

| Trigger | What happens |
|---|---|
| Push to `main` | Test → build `.app`/`.dmg` → upload the `.dmg` as a build **artifact** |
| Pull request → `main` | Same test + build (verifies the PR builds) — no release |
| Push a tag `v*` (e.g. `v0.3.0`) | Same, **plus** attach the `.dmg` to the GitHub **Release** for that tag |

## Jobs

- **`build`** (runs on every trigger, `macos-14` Apple-Silicon runner, so the
  bundle is arm64): checkout → install uv → `uv sync --frozen` →
  `uv run pytest -q` → `bash packaging/build_dmg.sh` (PyInstaller → `.app`,
  `hdiutil` → `.dmg`) → upload the `.dmg` artifact.
- **`release`** (tags `v*` only): downloads the artifact and attaches the `.dmg`
  to the GitHub Release.

## Security posture

- Default `permissions: contents: read`. Only the tag-gated `release` job is
  granted `contents: write` — PR/branch builds never hold write.
- All third-party actions are pinned to **commit SHAs** (with a `# vX.Y.Z`
  comment), not mutable tags, to resist supply-chain tag-moving.
- `run:` steps use no untrusted `github.event.*` input, so there's no script
  injection surface.

## Getting the build

- **From a push to main:** open the run under the repo's **Actions** tab →
  the **`Ratebar-dmg`** artifact (a zip containing `Ratebar.dmg`).
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
