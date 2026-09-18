from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]


def test_windows_delivery_chain_uses_yutan_radar_brand():
    files = (
        ROOT / "windows" / "ai-goofish-monitor.spec",
        ROOT / "windows" / "build_windows.ps1",
        ROOT / "windows" / "build_installer.ps1",
        ROOT / "windows" / "run_windows.ps1",
        ROOT / "windows" / "README.md",
        ROOT / "windows" / "FIRST_RUN.txt",
        ROOT / "start.sh",
        ROOT / "src" / "api" / "routes" / "backup.py",
    )
    content = "\n".join(path.read_text(encoding="utf-8") for path in files)

    assert "AiGoofishMonitor" not in content
    assert "闲鱼监控系统" not in content
    assert "YuTanRadar" in content
    assert "鱼探 Radar" in content

    installer = (ROOT / "windows" / "installer.iss").read_text(encoding="utf-8")
    assert '#define AppVersion "2.1.1"' in installer
    assert "AiGoofishMonitor" not in content


def test_installer_preserves_upgrade_identity_and_uses_branded_entrypoint():
    content = (ROOT / "windows" / "installer.iss").read_text(encoding="utf-8")

    assert "AppId={{B8D5A96B-6E8E-4A78-9A80-4F9CC8B0A721}" in content
    assert '#define AppName "鱼探 Radar"' in content
    assert '#define AppVersion "2.1.1"' in content
    assert '#define AppExeName "YuTanRadar.exe"' in content
    assert r'#define ReleaseDir "..\release\YuTanRadar"' in content
    assert r"DefaultDirName={localappdata}\Programs\YuTanRadar" in content
    assert "OutputBaseFilename=YuTanRadar-Setup-{#AppVersion}" in content
    assert r"SetupIconFile=..\web-ui\public\app-icon.ico" in content
    assert r'Type: files; Name: "{autodesktop}\闲鱼智能监控.lnk"' in content
    assert r'Type: files; Name: "{userprograms}\闲鱼智能监控\闲鱼智能监控.lnk"' in content
    assert r'Type: files; Name: "{app}\AiGoofishMonitor.exe"' in content
    assert r'Type: files; Name: "{localappdata}\Programs\AiGoofishMonitor\AiGoofishMonitor.exe"' in content
    assert r'IconFilename: "{app}\{#AppExeName}"; IconIndex: 0' in content
    assert "UsePreviousGroup=no" in content


def test_windows_icon_contains_standard_sizes():
    icon_path = ROOT / "web-ui" / "public" / "app-icon.ico"
    assert icon_path.is_file()

    with Image.open(icon_path) as icon:
        expected_sizes = {
            (16, 16),
            (24, 24),
            (32, 32),
            (48, 48),
            (64, 64),
            (128, 128),
            (256, 256),
        }
        assert expected_sizes.issubset(icon.info.get("sizes", set()))
