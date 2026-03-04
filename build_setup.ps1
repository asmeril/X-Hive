Write-Host "Inno Setup (xhive_setup.iss) bileseni derleniyor... Lutfen bekleyin." -ForegroundColor Yellow

$ISCC_Path = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-Not (Test-Path $ISCC_Path)) {
    Write-Host "[HATA] Inno Setup 6 kurucu bulunamadi! 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' dizinini kontrol edin." -ForegroundColor Red
    Exit
}

$Iss_File = "C:\XHive\X-Hive\installer\xhive_setup.iss"
$Output_Dir = "C:\XHive\X-Hive\installer\output"
$Version_File = "C:\XHive\X-Hive\installer\version.txt"

if (-Not (Test-Path $Version_File)) {
    Write-Host "[HATA] version.txt bulunamadi: $Version_File" -ForegroundColor Red
    Exit
}

$AppVersion = (Get-Content $Version_File -Raw).Trim()
if ($AppVersion -notmatch '^\d+\.\d+\.\d+$') {
    Write-Host "[HATA] Gecersiz versiyon formati: $AppVersion" -ForegroundColor Red
    Exit
}

# Calistir
& $ISCC_Path "/DMyAppVersion=$AppVersion" $Iss_File

Write-Host "`n[BASARILI] Yeni Kurulum Dosyasi Olusturuldu!" -ForegroundColor Green
Write-Host "Lutfen su dosyayi laptopunuza kopyalayip kurun:" -ForegroundColor Cyan
Write-Host "$Output_Dir\XHive_Setup_v${AppVersion}_*.exe" -ForegroundColor White
