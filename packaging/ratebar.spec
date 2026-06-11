# PyInstaller spec for ratebar — macOS menu bar app (.app bundle).
# Run from the packaging/ dir:  uv run pyinstaller ratebar.spec
# (or use packaging/build_dmg.sh). Paths below are relative to this dir.
from PyInstaller.utils.hooks import collect_all

# rumps sits on pyobjc; pull everything it needs so the bundle is self-contained.
rumps_datas, rumps_binaries, rumps_hidden = collect_all("rumps")

a = Analysis(
    ["launcher.py"],
    pathex=["../src"],          # so `import ratebar` resolves from source
    binaries=rumps_binaries,
    datas=rumps_datas,
    hiddenimports=rumps_hidden + ["ratebar", "requests"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ratebar",
    console=False,              # GUI / windowed
)

coll = COLLECT(exe, a.binaries, a.datas, name="ratebar")

app = BUNDLE(
    coll,
    name="ratebar.app",
    icon=None,
    bundle_identifier="com.biplav00.ratebar",
    info_plist={
        "LSUIElement": True,    # menu-bar only: no Dock icon, no window
        "CFBundleName": "ratebar",
        "CFBundleDisplayName": "ratebar",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "0.1.0",
    },
)
