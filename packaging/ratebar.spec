# PyInstaller spec for ratebar — macOS menu bar app (.app bundle).
# Run from the packaging/ dir:  uv run pyinstaller ratebar.spec
# (or use packaging/build_dmg.sh). Paths below are relative to this dir.
from PyInstaller.utils.hooks import collect_all

# Pull the pyobjc AppKit/objc bits so the bundle is self-contained.
ak_d, ak_b, ak_h = collect_all("AppKit")
oc_d, oc_b, oc_h = collect_all("objc")
pkg_datas = ak_d + oc_d
pkg_binaries = ak_b + oc_b
pkg_hidden = ak_h + oc_h + [
    "ratebar", "ratebar.ui.popover", "ratebar.ui.bar_view",
    "ratebar.gauge", "requests",
]

a = Analysis(
    ["launcher.py"],
    pathex=["../src"],          # so `import ratebar` resolves from source
    binaries=pkg_binaries,
    datas=pkg_datas,
    hiddenimports=pkg_hidden,
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
    icon="ratebar.icns",
    bundle_identifier="com.biplav00.ratebar",
    info_plist={
        "LSUIElement": True,    # menu-bar only: no Dock icon, no window
        "CFBundleName": "ratebar",
        "CFBundleDisplayName": "ratebar",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "0.1.0",
    },
)
