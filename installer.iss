; Inno Setup script for OMR QA Form Scanner
; Download Inno Setup from: https://jrsoftware.org/isdl.php
; Compile with:  iscc installer.iss

#define AppName      "OMR QA Form Scanner"
#define AppVersion   "1.0.0"
#define AppPublisher "Your Organization"
#define AppURL       "https://your-org.example.com"
#define AppExeName   "OMR_Scanner.exe"
#define DistDir      "dist\OMR_Scanner"

[Setup]
; Unique GUID — regenerate with Tools > Generate GUID in Inno Setup IDE
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
; Require admin rights so the app can write to Program Files
PrivilegesRequired=admin
OutputDir=installer_output
OutputBaseFilename=OMR_Scanner_Setup_v{#AppVersion}
; Compression
Compression=lzma2/ultra64
SolidCompression=yes
; Wizard style
WizardStyle=modern
; Minimum Windows version: Windows 10
MinVersion=10.0
; Target 64-bit architecture
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Uncomment once you have an icon:
; SetupIconFile=assets\icon.ico
; UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "{cm:CreateDesktopIcon}";    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Copy the entire PyInstaller output folder
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}";          Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";    Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove the SQLite database on uninstall (optional — comment out to keep user data)
; Type: files; Name: "{app}\data\omr.db"

[Code]
// Check if running on 64-bit Windows
function InitializeSetup(): Boolean;
begin
  if not IsWin64 then
  begin
    MsgBox('This application requires a 64-bit version of Windows.', mbError, MB_OK);
    Result := False;
  end
  else
    Result := True;
end;
