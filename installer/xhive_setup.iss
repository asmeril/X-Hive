; XHive Setup Script
; Inno Setup 6
; Kurulum:
;   1. XHive.exe -> {pf}\XHive
;   2. Python worker -> {userappdata}\XHive\worker
;   3. Kalici veriler -> {userappdata}\XHive\data, cookies, browser_data, locks
;   4. Kurulum sonrasi: Python 3.11 yoksa indir+kur, venv olustur, pip install

#define PythonVersion "3.11.9"
#define PythonInstallerURL "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"

#define MyAppName "XHive"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "asmeril"
#define MyAppURL "https://github.com/asmeril/X-Hive"
#define MyAppExeName "x-hive-desktop.exe"

; Derleme oncesi su dosyalar var olmali:
;   ..\apps\desktop\src-tauri\target\release\XHive.exe
;   ..\apps\worker\  (tum worker klasoru)

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
; Kullanici profili altina kur (admin gerekmez)
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Cikti
OutputDir=output
OutputBaseFilename=XHive_Setup_v{#MyAppVersion}
; Ikonlar
SetupIconFile=..\apps\desktop\src-tauri\icons\icon.ico
; Sikistirma
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; Lisans gerekmez, kurulum basit
DisableDirPage=no
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Minimum Windows 10
MinVersion=10.0

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaustu kisayolu olustur"; GroupDescription: "Ek gorevler:"

[Dirs]
; Kalici veri klasorleri - uygulama ilk acilisinda bunlari kullanir
Name: "{userappdata}\{#MyAppName}"
Name: "{userappdata}\{#MyAppName}\data"
Name: "{userappdata}\{#MyAppName}\locks"
Name: "{userappdata}\{#MyAppName}\browser_data"
Name: "{userappdata}\{#MyAppName}\worker"
Name: "{userappdata}\{#MyAppName}\worker\cookies"

[Files]
; Ana uygulama exe
Source: "..\apps\desktop\src-tauri\target\release\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Worker dosyalari -> AppData\XHive\worker
; Temel Python modulleri
Source: "..\apps\worker\app\*"; DestDir: "{userappdata}\{#MyAppName}\worker\app"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\apps\worker\intel\*"; DestDir: "{userappdata}\{#MyAppName}\worker\intel"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\apps\worker\approval\*"; DestDir: "{userappdata}\{#MyAppName}\worker\approval"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\apps\worker\posting\*"; DestDir: "{userappdata}\{#MyAppName}\worker\posting"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\apps\worker\scheduling\*"; DestDir: "{userappdata}\{#MyAppName}\worker\scheduling"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\apps\worker\tools\*"; DestDir: "{userappdata}\{#MyAppName}\worker\tools"; Flags: ignoreversion recursesubdirs createallsubdirs

; Kok Python dosyalari (sadece uretimde kullanilan)
Source: "..\apps\worker\ai_content_generator.py"; DestDir: "{userappdata}\{#MyAppName}\worker"; Flags: ignoreversion
Source: "..\apps\worker\chrome_pool.py"; DestDir: "{userappdata}\{#MyAppName}\worker"; Flags: ignoreversion
Source: "..\apps\worker\config.py"; DestDir: "{userappdata}\{#MyAppName}\worker"; Flags: ignoreversion
Source: "..\apps\worker\content_generator.py"; DestDir: "{userappdata}\{#MyAppName}\worker"; Flags: ignoreversion
Source: "..\apps\worker\health_check.py"; DestDir: "{userappdata}\{#MyAppName}\worker"; Flags: ignoreversion
Source: "..\apps\worker\human_behavior.py"; DestDir: "{userappdata}\{#MyAppName}\worker"; Flags: ignoreversion
Source: "..\apps\worker\lock_manager.py"; DestDir: "{userappdata}\{#MyAppName}\worker"; Flags: ignoreversion
Source: "..\apps\worker\metrics_collector.py"; DestDir: "{userappdata}\{#MyAppName}\worker"; Flags: ignoreversion
Source: "..\apps\worker\orchestrator.py"; DestDir: "{userappdata}\{#MyAppName}\worker"; Flags: ignoreversion
Source: "..\apps\worker\post_scheduler.py"; DestDir: "{userappdata}\{#MyAppName}\worker"; Flags: ignoreversion
Source: "..\apps\worker\rate_limiter.py"; DestDir: "{userappdata}\{#MyAppName}\worker"; Flags: ignoreversion
Source: "..\apps\worker\safety_logger.py"; DestDir: "{userappdata}\{#MyAppName}\worker"; Flags: ignoreversion
Source: "..\apps\worker\structured_logger.py"; DestDir: "{userappdata}\{#MyAppName}\worker"; Flags: ignoreversion
Source: "..\apps\worker\task_queue.py"; DestDir: "{userappdata}\{#MyAppName}\worker"; Flags: ignoreversion
Source: "..\apps\worker\telegram_bot.py"; DestDir: "{userappdata}\{#MyAppName}\worker"; Flags: ignoreversion
Source: "..\apps\worker\x_daemon.py"; DestDir: "{userappdata}\{#MyAppName}\worker"; Flags: ignoreversion
Source: "..\apps\worker\approval_manager.py"; DestDir: "{userappdata}\{#MyAppName}\worker"; Flags: ignoreversion
Source: "..\apps\worker\api_server.py"; DestDir: "{userappdata}\{#MyAppName}\worker"; Flags: ignoreversion
Source: "..\apps\worker\run.py"; DestDir: "{userappdata}\{#MyAppName}\worker"; Flags: ignoreversion
Source: "..\apps\worker\requirements.txt"; DestDir: "{userappdata}\{#MyAppName}\worker"; Flags: ignoreversion

; .env.example -> .env olarak kopyala (varsa uzerine yazma)
Source: "..\apps\worker\.env.example"; DestDir: "{userappdata}\{#MyAppName}\worker"; DestName: ".env"; Flags: onlyifdoesntexist

; Cookie sablonlari (bos, kullanicinin doldurmasi icin)
Source: "..\apps\worker\cookies\.gitkeep"; DestDir: "{userappdata}\{#MyAppName}\worker\cookies"; Flags: ignoreversion

; NOT: .venv dahil edilmiyor - kurulum sonrasi otomatik olusturulur

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{#MyAppName} Kaldır"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Kurulum sonrasi uygulamayi ac
Filename: "{app}\{#MyAppExeName}"; \
  Description: "{#MyAppName} uygulamasini baslat"; \
  Flags: nowait postinstall skipifsilent

[Code]
var
  PythonDownloadPage: TDownloadWizardPage;

function GetPythonPath(): String;
begin
  Result := '';
  // Kullanici profili altindaki Python kurulumlarini kontrol et
  if FileExists(ExpandConstant('{localappdata}\Programs\Python\Python311\python.exe')) then
    Result := ExpandConstant('{localappdata}\Programs\Python\Python311\python.exe')
  else if FileExists(ExpandConstant('{localappdata}\Programs\Python\Python312\python.exe')) then
    Result := ExpandConstant('{localappdata}\Programs\Python\Python312\python.exe')
  else if FileExists(ExpandConstant('{localappdata}\Programs\Python\Python310\python.exe')) then
    Result := ExpandConstant('{localappdata}\Programs\Python\Python310\python.exe')
  // Sistem geneli Python kurulumlarini kontrol et
  else if FileExists('C:\Python311\python.exe') then
    Result := 'C:\Python311\python.exe'
  else if FileExists('C:\Python312\python.exe') then
    Result := 'C:\Python312\python.exe'
  else if FileExists('C:\Python310\python.exe') then
    Result := 'C:\Python310\python.exe';
end;

function NeedsPython(): Boolean;
begin
  Result := (GetPythonPath() = '');
end;

function VenvExists(): Boolean;
begin
  Result := FileExists(ExpandConstant('{userappdata}\{#MyAppName}\worker\.venv\Scripts\python.exe'));
end;

procedure InitializeWizard();
begin
  PythonDownloadPage := CreateDownloadPage(
    'Python 3.11 İndiriliyor',
    'Python 3.11.9 kurmak için indiriliyor, lütfen bekleyin...',
    nil
  );
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  ResultCode: Integer;
  PythonInstaller: String;
begin
  Result := True;

  // Python yoksa indirme sayfasinda indir ve kur
  if (CurPageID = wpReady) and NeedsPython() then
  begin
    PythonDownloadPage.Clear;
    PythonDownloadPage.Add(
      '{#PythonInstallerURL}',
      'python-3.11.9-amd64.exe',
      ''
    );
    PythonDownloadPage.Show;
    try
      try
        PythonDownloadPage.Download;
        PythonInstaller := ExpandConstant('{tmp}\python-3.11.9-amd64.exe');

        // Python sessiz kurulum:
        // InstallAllUsers=0 -> sadece mevcut kullanici (admin gerekmez)
        // PrependPath=1    -> PATH'e ekle
        // Include_pip=1    -> pip dahil
        PythonDownloadPage.SetText('Python 3.11.9 kuruluyor...', '');
        if not Exec(PythonInstaller,
          '/quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=0',
          '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
        begin
          MsgBox('Python kurulumu baslatılamadı. Lutfen python.org adresinden Python 3.11 kurarak tekrar deneyin.', mbError, MB_OK);
          Result := False;
        end else if ResultCode <> 0 then
        begin
          MsgBox('Python kurulumu hata ile tamamlandı (kod: ' + IntToStr(ResultCode) + '). Lutfen manuel olarak Python 3.11 kurun.', mbError, MB_OK);
          Result := False;
        end;
      except
        MsgBox('Python indirilemedi. Internet baglantınızı kontrol edin veya python.org adresinden Python 3.11 kurun.', mbError, MB_OK);
        Result := False;
      end;
    finally
      PythonDownloadPage.Hide;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  PythonPath: String;
  VenvPath: String;
  WorkerPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    WorkerPath := ExpandConstant('{userappdata}\{#MyAppName}\worker');
    VenvPath := WorkerPath + '\.venv';
    PythonPath := GetPythonPath();

    if PythonPath = '' then
    begin
      MsgBox('Python bulunamadı. Uygulamayı çalıştırmak için python.org adresinden Python 3.11 kurun.', mbError, MB_OK);
      Exit;
    end;

    // .venv yoksa olustur
    if not DirExists(VenvPath + '\Scripts') then
    begin
      WizardForm.StatusLabel.Caption := 'Python sanal ortamı oluşturuluyor...';

      Exec(PythonPath, '-m venv "' + VenvPath + '"', WorkerPath,
           SW_HIDE, ewWaitUntilTerminated, ResultCode);

      if ResultCode = 0 then
      begin
        WizardForm.StatusLabel.Caption := 'Python bağımlılıkları kuruluyor (bu birkaç dakika sürebilir)...';
        Exec(VenvPath + '\Scripts\python.exe',
             '-m pip install --upgrade pip --quiet',
             WorkerPath, SW_HIDE, ewWaitUntilTerminated, ResultCode);
        Exec(VenvPath + '\Scripts\python.exe',
             '-m pip install -r "' + WorkerPath + '\requirements.txt" --quiet',
             WorkerPath, SW_HIDE, ewWaitUntilTerminated, ResultCode);
      end else
        MsgBox('Python sanal ortamı oluşturulamadı. Uygulamayı ilk açışınızda otomatik tekrar denenecek.', mbInformation, MB_OK);
    end else
    begin
      // venv var, sadece pip install yap (guncelleme senaryosu)
      WizardForm.StatusLabel.Caption := 'Python bağımlılıkları güncelleniyor...';
      Exec(VenvPath + '\Scripts\python.exe',
           '-m pip install -r "' + WorkerPath + '\requirements.txt" --quiet',
           WorkerPath, SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;

// Kaldirma sirasinda veri klasorlerini silme (kullanici verilerini koru)
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Sadece worker kod dosyalarini sil, veri klasorlerini birak
    // {userappdata}\XHive\data, cookies, browser_data korunur
  end;
end;
