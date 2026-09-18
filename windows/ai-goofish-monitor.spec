# PyInstaller onedir build. Keep the resource directories beside the executable
# so SQLite, login states, prompts, logs, and images remain user-editable.
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

ROOT = Path(SPEC).resolve().parent.parent

datas = [
    (str(ROOT / "dist"), "dist"),
    (str(ROOT / "static"), "static"),
    (str(ROOT / "prompts"), "prompts"),
    (str(ROOT / "config.json.example"), "."),
    (str(ROOT / ".env.example"), "."),
]

# OpenAI imports jiter as a compiled submodule at runtime. Keep the package
# and its native extension together in frozen Windows builds.
datas += collect_data_files("jiter")
binaries = collect_dynamic_libs("jiter")
hiddenimports = (
    collect_submodules("src")
    + collect_submodules("openai")
    + collect_submodules("jiter")
    + ["jiter.jiter"]
)

a = Analysis(
    [str(ROOT / "desktop_launcher.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name="YuTanRadar",
    icon=str(ROOT / "web-ui" / "public" / "app-icon.ico"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="YuTanRadar",
)
