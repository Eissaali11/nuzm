# رفع مباشر إلى Hostinger - سكريبت تفاعلي
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   رفع المشروع مباشرة إلى Hostinger" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# التحقق من Git أولاً
$useGit = $false
if (Get-Command git -ErrorAction SilentlyContinue) {
    $remote = git remote get-url origin 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[✓] Git Repository موجود: $remote" -ForegroundColor Green
        Write-Host ""
        $choice = Read-Host "هل تريد استخدام Git للرفع؟ (y/n)"
        if ($choice -eq "y" -or $choice -eq "Y" -or $choice -eq "نعم") {
            $useGit = $true
        }
    }
}

if ($useGit) {
    # استخدام Git
    Write-Host ""
    Write-Host "جارٍ رفع التغييرات عبر Git..." -ForegroundColor Yellow
    
    git add .
    $commitMsg = "Deploy to Hostinger - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    git commit -m $commitMsg
    git push origin main
    
    Write-Host ""
    Write-Host "[✓✓✓] تم الرفع عبر Git بنجاح!" -ForegroundColor Green
    Write-Host "إذا كان Auto-Deploy مفعّل في Hostinger، سيتم التحديث تلقائياً" -ForegroundColor Cyan
    
} else {
    # استخدام FTP
    Write-Host "إعدادات FTP:" -ForegroundColor Yellow
    Write-Host ""
    
    $FtpHost = Read-Host "أدخل FTP Host (مثلاً: ftp.yourdomain.com)"
    $FtpUser = Read-Host "أدخل FTP Username"
    $FtpPass = Read-Host "أدخل FTP Password" -AsSecureString
    $FtpPassPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($FtpPass))
    $RemotePath = Read-Host "أدخل Remote Path (اضغط Enter للاستخدام الافتراضي: /public_html/nuzum/)"
    
    if ($RemotePath -eq "") {
        $RemotePath = "/public_html/nuzum/"
    }
    
    Write-Host ""
    Write-Host "جارٍ رفع الملفات..." -ForegroundColor Yellow
    Write-Host ""
    
    # استدعاء سكريبت الرفع
    & .\quick_deploy.ps1 -FtpHost $FtpHost -FtpUser $FtpUser -FtpPass $FtpPassPlain -RemotePath $RemotePath
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

