# PyInstaller spec for the seller-only license issuer.
# The private key is deliberately not included in this build.
from pathlib import Path

ROOT = Path(SPEC).resolve().parent.parent

a = Analysis(
    [str(ROOT / "tools" / "license_issuer_gui.pyw")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=["tools.license_issuer_core"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="YuTanRadar-LicenseIssuer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "web-ui" / "public" / "app-icon.ico"),
)
