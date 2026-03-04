Write-Host "Inno Setup baslatiliyor..." -ForegroundColor Cyan

$InnoSetup = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
$Script = "C:\XHive\X-Hive\installer\xhive_setup.iss"
$VersionFile = "C:\XHive\X-Hive\installer\version.txt"

if (-Not (Test-Path $InnoSetup)) {
    Write-Host "HATA: Inno Setup 6 bulunamadi!" -ForegroundColor Red
    Exit
}

if (-Not (Test-Path $VersionFile)) {
    Write-Host "HATA: version.txt bulunamadi!" -ForegroundColor Red
    Exit
}

$AppVersion = (Get-Content $VersionFile -Raw).Trim()
if ($AppVersion -notmatch '^\d+\.\d+\.\d+$') {
    Write-Host "HATA: Gecersiz versiyon formati: $AppVersion" -ForegroundColor Red
    Exit
}

$process = Start-Process -FilePath $InnoSetup -ArgumentList "/DMyAppVersion=$AppVersion", "`"$Script`"" -Wait -NoNewWindow -PassThru
if ($process.ExitCode -eq 0) {
    Write-Host "Derleme Basarili! Yeni Setup Output klasorunde." -ForegroundColor Green
} else {
    Write-Host "Derleme Sirasinda Hata Olustu. Exit Code: $($process.ExitCode)" -ForegroundColor Red
}
