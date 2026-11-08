#define AppName "Verificador de vetor - Cromotransfer"
#define AppVersion "1.1.3"
#define AppExe "Verificador_de_vetor_Cromotransfer.exe"

[Setup]
AppId={{B8B1E67C-7A43-4D67-9A54-1F9D4B23C2E1}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Cromotransfer
DefaultDirName={autopf}\Verificador Cromotransfer
DefaultGroupName={#AppName}
OutputDir=dist
OutputBaseFilename=Verificador_Cromotransfer_Instalador
SetupIconFile=assets\logo_icone.ico
UninstallDisplayIcon={app}\{#AppExe}
ArchitecturesInstallIn64BitMode=x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Files]
Source: "dist\Verificador_de_vetor_Cromotransfer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos adicionais:"

[Run]
Filename: "{app}\{#AppExe}"; Description: "Abrir {#AppName}"; Flags: postinstall nowait skipifsilent
