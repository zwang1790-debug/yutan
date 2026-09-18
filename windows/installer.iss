; Inno Setup script for the Windows onedir release.
; Build the application first with build_windows.ps1.

#define AppName "鱼探 Radar"
#ifndef AppVersion
#define AppVersion "2.1.1"
#endif
#define AppPublisher "鱼探 Radar"
#define AppExeName "YuTanRadar.exe"
#define ReleaseDir "..\release\YuTanRadar"

[Setup]
AppId={{B8D5A96B-6E8E-4A78-9A80-4F9CC8B0A721}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\YuTanRadar
; Reuse the existing install directory during upgrades so customer data stays in place.
UsePreviousAppDir=yes
DefaultGroupName={#AppName}
UsePreviousGroup=no
OutputDir=..\release
OutputBaseFilename=YuTanRadar-Setup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\web-ui\public\app-icon.ico
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#AppExeName}
CloseApplications=yes
RestartApplications=no

[Files]
; List generated files explicitly so upgrades can never touch user data or .env.
Source: "{#ReleaseDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ReleaseDir}\.playwright-browsers\*"; DestDir: "{app}\.playwright-browsers"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ReleaseDir}\dist\*"; DestDir: "{app}\dist"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ReleaseDir}\static\*"; DestDir: "{app}\static"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ReleaseDir}\prompts\*"; DestDir: "{app}\prompts"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#ReleaseDir}\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ReleaseDir}\.env.example"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ReleaseDir}\config.json.example"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ReleaseDir}\FIRST_RUN.txt"; DestDir: "{app}"; Flags: ignoreversion

[InstallDelete]
; Remove shortcuts created by the legacy installation. User data is not touched.
Type: files; Name: "{autodesktop}\闲鱼智能监控.lnk"
Type: files; Name: "{userprograms}\闲鱼智能监控\闲鱼智能监控.lnk"
Type: dirifempty; Name: "{userprograms}\闲鱼智能监控"
Type: files; Name: "{autodesktop}\AiGoofishMonitor.lnk"
Type: files; Name: "{userprograms}\AiGoofishMonitor\AiGoofishMonitor.lnk"
Type: dirifempty; Name: "{userprograms}\AiGoofishMonitor"
; If an upgrade reuses the legacy install directory, remove only the old entrypoint.
Type: files; Name: "{app}\AiGoofishMonitor.exe"
Type: files; Name: "{app}\AiGoofishMonitor.exe.previous"
; Also cover a legacy install path when the new installer is launched as a fresh install.
Type: files; Name: "{localappdata}\Programs\AiGoofishMonitor\AiGoofishMonitor.exe"
Type: files; Name: "{localappdata}\Programs\AiGoofishMonitor\AiGoofishMonitor.exe.previous"

[Dirs]
; Keep user data when the application is uninstalled or upgraded.
Name: "{app}\data"; Flags: uninsneveruninstall
Name: "{app}\state"; Flags: uninsneveruninstall
Name: "{app}\logs"; Flags: uninsneveruninstall
Name: "{app}\images"; Flags: uninsneveruninstall
Name: "{app}\jsonl"; Flags: uninsneveruninstall
Name: "{app}\price_history"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; IconIndex: 0
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; IconIndex: 0

[Run]
Filename: "{app}\{#AppExeName}"; Description: "启动 {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Deliberately do not delete data, login states, logs, or user configuration.
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}\.playwright-browsers"
