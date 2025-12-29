# سكريبت إعداد ورفع المشروع إلى Hostinger
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   إعداد ورفع المشروع إلى Hostinger" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# التحقق من طريقة الرفع
Write-Host "اختر طريقة الرفع:" -ForegroundColor Yellow
Write-Host "1. Git (إذا كان المشروع متصل بـ Git Repository)" -ForegroundColor White
Write-Host "2. FTP (رفع مباشر عبر FTP)" -ForegroundColor White
Write-Host "3. إنشاء ملف إعدادات فقط" -ForegroundColor White
Write-Host ""

$choice = Read-Host "اختر (1/2/3)"

if ($choice -eq "1") {
    # طريقة Git
    Write-Host ""
    Write-Host "[Git] التحقق من Git Repository..." -ForegroundColor Cyan
    
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Host "[❌] Git غير مثبت" -ForegroundColor Red
        exit 1
    }
    
    $remote = git remote get-url origin 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[✓] Git Repository موجود: $remote" -ForegroundColor Green
        Write-Host ""
        Write-Host "جارٍ رفع التغييرات..." -ForegroundColor Yellow
        
        git add .
        $commitMsg = Read-Host "أدخل رسالة الـ commit (أو اضغط Enter للاستخدام الافتراضي)"
        if ($commitMsg -eq "") {
            $commitMsg = "Deploy to Hostinger - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
        }
        
        git commit -m $commitMsg
        git push origin main
        
        Write-Host ""
        Write-Host "[✓✓✓] تم الرفع عبر Git بنجاح!" -ForegroundColor Green
        Write-Host "إذا كان Auto-Deploy مفعّل في Hostinger، سيتم التحديث تلقائياً" -ForegroundColor Cyan
        
    } else {
        Write-Host "[❌] المشروع غير متصل بـ Git Repository" -ForegroundColor Red
        Write-Host ""
        Write-Host "يرجى:" -ForegroundColor Yellow
        Write-Host "1. أنشئ Git Repository على GitHub/GitLab" -ForegroundColor White
        Write-Host "2. شغّل: git remote add origin <repository-url>" -ForegroundColor White
        Write-Host "3. شغّل هذا السكريبت مرة أخرى" -ForegroundColor White
    }
    
} elseif ($choice -eq "2") {
    # طريقة FTP
    Write-Host ""
    Write-Host "[FTP] إعدادات FTP" -ForegroundColor Cyan
    Write-Host ""
    
    # طلب بيانات FTP
    $ftpHost = Read-Host "أدخل FTP Host (مثلاً: ftp.yourdomain.com)"
    $ftpUser = Read-Host "أدخل FTP Username"
    $ftpPass = Read-Host "أدخل FTP Password" -AsSecureString
    $ftpPassPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($ftpPass))
    $remotePath = Read-Host "أدخل Remote Path (مثلاً: /public_html/nuzum/)"
    
    if ($remotePath -eq "") {
        $remotePath = "/public_html/nuzum/"
    }
    
    # حفظ الإعدادات
    $config = @{
        FtpHost = $ftpHost
        FtpUser = $ftpUser
        FtpPass = $ftpPassPlain
        RemotePath = $remotePath
    } | ConvertTo-Json
    
    $config | Out-File -FilePath ".hostinger_config.json" -Encoding utf8
    Write-Host ""
    Write-Host "[✓] تم حفظ الإعدادات في .hostinger_config.json" -ForegroundColor Green
    Write-Host ""
    
    # رفع الملفات
    Write-Host "جارٍ رفع الملفات..." -ForegroundColor Yellow
    & .\deploy_to_hostinger.ps1 -Method FTP
    
} elseif ($choice -eq "3") {
    # إنشاء ملف إعدادات فقط
    Write-Host ""
    Write-Host "[إعدادات] إنشاء ملف إعدادات..." -ForegroundColor Cyan
    Write-Host ""
    
    $ftpHost = Read-Host "أدخل FTP Host (مثلاً: ftp.yourdomain.com)"
    $ftpUser = Read-Host "أدخل FTP Username"
    $ftpPass = Read-Host "أدخل FTP Password" -AsSecureString
    $ftpPassPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($ftpPass))
    $remotePath = Read-Host "أدخل Remote Path (مثلاً: /public_html/nuzum/)"
    
    if ($remotePath -eq "") {
        $remotePath = "/public_html/nuzum/"
    }
    
    $config = @{
        FtpHost = $ftpHost
        FtpUser = $ftpUser
        FtpPass = $ftpPassPlain
        RemotePath = $remotePath
        Database = @{
            Host = "localhost"
            Name = "nuzum_db"
            User = "nuzum_user"
            Password = ""
            Port = 3306
        }
        PythonApp = @{
            Name = "nuzum"
            Version = "3.11"
            Port = 5000
        }
    } | ConvertTo-Json -Depth 3
    
    $config | Out-File -FilePath ".hostinger_config.json" -Encoding utf8
    Write-Host ""
    Write-Host "[✓✓✓] تم إنشاء ملف .hostinger_config.json بنجاح!" -ForegroundColor Green
    Write-Host ""
    Write-Host "الآن يمكنك شغّل:" -ForegroundColor Yellow
    Write-Host "  .\deploy_to_hostinger.ps1" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

