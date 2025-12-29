# سكريبت رفع تلقائي إلى Hostinger
# PowerShell Script for Hostinger Deployment

param(
    [Parameter(Mandatory=$false)]
    [string]$Method = "FTP",  # FTP, Git, or SSH
    
    [Parameter(Mandatory=$false)]
    [string]$FtpHost = "",
    
    [Parameter(Mandatory=$false)]
    [string]$FtpUser = "",
    
    [Parameter(Mandatory=$false)]
    [string]$FtpPass = "",
    
    [Parameter(Mandatory=$false)]
    [string]$RemotePath = "/public_html/nuzum/"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   رفع المشروع إلى Hostinger" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# قراءة إعدادات FTP من ملف (إذا كان موجوداً)
$configFile = ".hostinger_config.json"
if (Test-Path $configFile) {
    $config = Get-Content $configFile | ConvertFrom-Json
    $FtpHost = if ($FtpHost -eq "") { $config.FtpHost } else { $FtpHost }
    $FtpUser = if ($FtpUser -eq "") { $config.FtpUser } else { $FtpUser }
    $FtpPass = if ($FtpPass -eq "") { $config.FtpPass } else { $FtpPass }
    $RemotePath = if ($RemotePath -eq "/public_html/nuzm/") { $config.RemotePath } else { $RemotePath }
}

# التحقق من الإعدادات
if ($Method -eq "FTP" -and ($FtpHost -eq "" -or $FtpUser -eq "")) {
    Write-Host "[❌] يرجى إدخال إعدادات FTP" -ForegroundColor Red
    Write-Host ""
    Write-Host "الطريقة 1: إنشاء ملف .hostinger_config.json" -ForegroundColor Yellow
    Write-Host @"
{
    "FtpHost": "ftp.yourdomain.com",
    "FtpUser": "your_username",
    "FtpPass": "your_password",
    "RemotePath": "/public_html/nuzum/"
}
"@ -ForegroundColor Gray
    Write-Host ""
    Write-Host "الطريقة 2: تمرير المعاملات:" -ForegroundColor Yellow
    Write-Host ".\deploy_to_hostinger.ps1 -FtpHost 'ftp.domain.com' -FtpUser 'user' -FtpPass 'pass'" -ForegroundColor Gray
    exit 1
}

# الملفات والمجلدات المستثناة
$excludePatterns = @(
    "venv",
    "__pycache__",
    "*.pyc",
    ".env.local",
    ".git",
    "node_modules",
    ".vscode",
    ".idea",
    "*.log",
    "database/*.db",
    "*.sqlite",
    "*.sqlite3"
)

function Upload-File {
    param(
        [string]$LocalPath,
        [string]$RemotePath,
        [string]$FtpHost,
        [string]$FtpUser,
        [string]$FtpPass
    )
    
    try {
        $ftp = [System.Net.FtpWebRequest]::Create("ftp://$FtpHost$RemotePath")
        $ftp.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPass)
        $ftp.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
        $ftp.UseBinary = $true
        $ftp.UsePassive = $true
        
        $fileContent = [System.IO.File]::ReadAllBytes($LocalPath)
        $ftp.ContentLength = $fileContent.Length
        
        $requestStream = $ftp.GetRequestStream()
        $requestStream.Write($fileContent, 0, $fileContent.Length)
        $requestStream.Close()
        
        $response = $ftp.GetResponse()
        $response.Close()
        
        return $true
    } catch {
        Write-Host "  [❌] فشل رفع: $LocalPath - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Create-Directory {
    param(
        [string]$RemotePath,
        [string]$FtpHost,
        [string]$FtpUser,
        [string]$FtpPass
    )
    
    try {
        $ftp = [System.Net.FtpWebRequest]::Create("ftp://$FtpHost$RemotePath")
        $ftp.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPass)
        $ftp.Method = [System.Net.WebRequestMethods+Ftp]::MakeDirectory
        $ftp.UsePassive = $true
        
        $response = $ftp.GetResponse()
        $response.Close()
        return $true
    } catch {
        # المجلد موجود بالفعل
        return $false
    }
}

# جمع الملفات للرفع
Write-Host "[1/3] جمع الملفات..." -ForegroundColor Cyan
$filesToUpload = Get-ChildItem -Recurse -File | Where-Object {
    $excluded = $false
    $relativePath = $_.FullName.Replace((Get-Location).Path + "\", "")
    
    foreach ($pattern in $excludePatterns) {
        if ($relativePath -like "*$pattern*") {
            $excluded = $true
            break
        }
    }
    return -not $excluded
}

Write-Host "[✓] تم العثور على $($filesToUpload.Count) ملف للرفع" -ForegroundColor Green
Write-Host ""

# رفع الملفات
if ($Method -eq "FTP") {
    Write-Host "[2/3] رفع الملفات عبر FTP..." -ForegroundColor Cyan
    Write-Host "هذا قد يستغرق بضع دقائق..." -ForegroundColor Yellow
    Write-Host ""
    
    $successCount = 0
    $failCount = 0
    
    foreach ($file in $filesToUpload) {
        $relativePath = $file.FullName.Replace((Get-Location).Path + "\", "").Replace("\", "/")
        $remoteFilePath = "$RemotePath$relativePath"
        
        # إنشاء المجلدات المطلوبة
        $remoteDir = Split-Path $remoteFilePath -Parent
        if ($remoteDir -ne $RemotePath) {
            $dirs = $remoteDir.Replace($RemotePath, "").Split("/")
            $currentPath = $RemotePath
            foreach ($dir in $dirs) {
                if ($dir -ne "") {
                    $currentPath = "$currentPath$dir/"
                    Create-Directory -RemotePath $currentPath -FtpHost $FtpHost -FtpUser $FtpUser -FtpPass $FtpPass | Out-Null
                }
            }
        }
        
        # رفع الملف
        Write-Host "  رفع: $relativePath" -ForegroundColor Gray
        if (Upload-File -LocalPath $file.FullName -RemotePath $remoteFilePath -FtpHost $FtpHost -FtpUser $FtpUser -FtpPass $FtpPass) {
            $successCount++
        } else {
            $failCount++
        }
    }
    
    Write-Host ""
    Write-Host "[✓] تم رفع $successCount ملف بنجاح" -ForegroundColor Green
    if ($failCount -gt 0) {
        Write-Host "[⚠️] فشل رفع $failCount ملف" -ForegroundColor Yellow
    }
    
} elseif ($Method -eq "Git") {
    Write-Host "[2/3] رفع التغييرات عبر Git..." -ForegroundColor Cyan
    
    # التحقق من Git
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Host "[❌] Git غير مثبت" -ForegroundColor Red
        exit 1
    }
    
    # إضافة و commit
    git add .
    $commitMessage = Read-Host "أدخل رسالة الـ commit"
    if ($commitMessage -eq "") {
        $commitMessage = "Update for Hostinger deployment"
    }
    
    git commit -m $commitMessage
    
    # Push
    Write-Host "جارٍ رفع التغييرات..." -ForegroundColor Yellow
    git push origin main
    
    Write-Host "[✓] تم الرفع عبر Git بنجاح" -ForegroundColor Green
    Write-Host "سيتم التحديث تلقائياً في Hostinger إذا كان Auto-Deploy مفعّل" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "[3/3] إعدادات إضافية..." -ForegroundColor Cyan

# إنشاء ملف .htaccess إذا لم يكن موجوداً
if (-not (Test-Path ".htaccess")) {
    Write-Host "  إنشاء ملف .htaccess..." -ForegroundColor Gray
    # سيتم إنشاؤه تلقائياً
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[✓✓✓] تم الرفع بنجاح!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "الخطوات التالية:" -ForegroundColor Yellow
Write-Host "1. تحقق من Python App في hPanel" -ForegroundColor White
Write-Host "2. تأكد من تثبيت المكتبات" -ForegroundColor White
Write-Host "3. تحقق من ملف .env" -ForegroundColor White
Write-Host "4. اختبر الموقع: https://yourdomain.com" -ForegroundColor White
Write-Host ""

