# سكريبت تثبيت Python من Microsoft Store
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   تثبيت Python من Microsoft Store" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# محاولة فتح Microsoft Store لتثبيت Python
Write-Host "جارٍ فتح Microsoft Store..." -ForegroundColor Yellow
Write-Host ""

# Python 3.12 من Microsoft Store
$storeUrl = "ms-windows-store://pdp/?ProductId=9NRWMJP3717K"

try {
    Start-Process $storeUrl
    Write-Host "[✓] تم فتح Microsoft Store" -ForegroundColor Green
    Write-Host ""
    Write-Host "الخطوات:" -ForegroundColor Yellow
    Write-Host "1. اضغط 'Install' في Microsoft Store" -ForegroundColor White
    Write-Host "2. انتظر حتى يكتمل التثبيت" -ForegroundColor White
    Write-Host "3. أعد تشغيل PowerShell" -ForegroundColor White
    Write-Host "4. شغّل: .\install_and_run.ps1" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host "[❌] فشل فتح Microsoft Store" -ForegroundColor Red
    Write-Host ""
    Write-Host "يرجى تثبيت Python يدوياً:" -ForegroundColor Yellow
    Write-Host "1. افتح Microsoft Store يدوياً" -ForegroundColor White
    Write-Host "2. ابحث عن 'Python 3.12'" -ForegroundColor White
    Write-Host "3. اضغط 'Install'" -ForegroundColor White
    Write-Host ""
    Write-Host "أو حمّل من: https://www.python.org/downloads/" -ForegroundColor Yellow
}

Write-Host "اضغط أي مفتاح للخروج..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

