[Setup]
AppId=labPontoGusto.FotosAprimoradas
AppName=Fotos Aprimoradas
AppVersion=1.2.0
SetupIconFile=fotos.ico
AppPublisher=Lab Gusto
DefaultDirName={autopf}\labPontoGusto\Fotos Aprimoradas
DefaultGroupName=lab.gusto
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
OutputDir=release
OutputBaseFilename=labGusto-Fotos-Aprimoradas-Setup
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\FotosAprimoradas.exe
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "dist\FotosAprimoradas\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; Flags: unchecked

[Icons]
Name: "{autoprograms}\lab.gusto\Fotos Aprimoradas"; Filename: "{app}\FotosAprimoradas.exe"
Name: "{commondesktop}\Fotos Aprimoradas"; Filename: "{app}\FotosAprimoradas.exe"; Tasks: desktopicon

[Run]
Description: "Abrir Fotos Aprimoradas"; Filename: "{app}\FotosAprimoradas.exe"; Flags: postinstall nowait skipifsilent
