; SpotiParty Windows installer (Inno Setup 6).
; Build the app first (desktop/dist/SpotiParty.exe, see desktop/README.md), then:
;   ISCC.exe desktop\installer.iss                      -> desktop\dist\SpotiParty-Setup-1.0.0.exe
;   ISCC.exe /DAppVersion=1.2.0 desktop\installer.iss   -> another version
; Installs for the current user only: no administrator rights and no install-mode question.

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{6B0E4C9A-3F2D-4E7B-9A51-5C2B7D8E1F40}
AppName=SpotiParty
AppVersion={#AppVersion}
AppVerName=SpotiParty {#AppVersion}
AppPublisher=Mike den Hertog
AppPublisherURL=https://github.com/CodeAura/SpotiParty
AppSupportURL=https://github.com/CodeAura/SpotiParty
VersionInfoVersion={#AppVersion}
DefaultDirName={autopf}\SpotiParty
DefaultGroupName=SpotiParty
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=SpotiParty-Setup-{#AppVersion}
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\SpotiParty.exe
UninstallDisplayName=SpotiParty
WizardStyle=modern
; Dutch or English from the Windows language; the language question only for other languages.
ShowLanguageDialog=auto
WizardSmallImageFile=wizard-small.bmp
WizardImageFile=wizard-large.bmp
Compression=lzma2/max
SolidCompression=yes
CloseApplications=force
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
LicenseFile=..\LICENSE

[Languages]
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
dutch.RemoveData=Ook je SpotiParty-instellingen en Spotify-login op deze PC verwijderen?
english.RemoveData=Also remove your SpotiParty settings and Spotify login from this PC?

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\SpotiParty.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SpotiParty"; Filename: "{app}\SpotiParty.exe"
Name: "{group}\{cm:UninstallProgram,SpotiParty}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\SpotiParty"; Filename: "{app}\SpotiParty.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SpotiParty.exe"; Description: "{cm:LaunchProgram,SpotiParty}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Stop a running SpotiParty and its app window before the files are removed.
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM SpotiParty.exe"; Flags: runhidden; RunOnceId: "StopSpotiParty"

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and DirExists(ExpandConstant('{localappdata}\SpotiParty')) then
    // A silent uninstall keeps the data; otherwise the user chooses (No is the default).
    if (not UninstallSilent) and
       (MsgBox(CustomMessage('RemoveData'), mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES) then
      DelTree(ExpandConstant('{localappdata}\SpotiParty'), True, True, True);
end;
