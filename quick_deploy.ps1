# سكريبت رفع سريع ومباشر إلى Hostinger
# Quick Deploy Script for Hostinger

param(
    [Parameter(Mandatory=$true)]
    [string]$FtpHost,
    
    [Parameter(Mandatory=$true)]
    [string]$FtpUser,
    
    [Parameter(Mandatory=$true)]
    [string]$FtpPass,
    
    [Parameter(Mandatory=$false)]
    [string]$RemotePath = "/public_html/nuzum/"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   رفع المشروع إلى Hostinger" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# استيراد مكتبة FTP
Add-Type -AssemblyName System.Net.Http

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
    "*.sqlite3",
    "test_*.xlsx",
    "test_*.pdf",
    "*.zip",
    "*.rar"
)

function Upload-File-FTP {
    param(
        [string]$LocalFile,
        [string]$RemoteFile,
        [string]$FtpHost,
        [string]$FtpUser,
        [string]$FtpPass
    )
    
    try {
        $ftpUri = "ftp://$FtpHost$RemoteFile"
        $ftpRequest = [System.Net.FtpWebRequest]::Create($ftpUri)
        $ftpRequest.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPass)
        $ftpRequest.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
        $ftpRequest.UseBinary = $true
        $ftpRequest.UsePassive = $true
        $ftpRequest.KeepAlive = $false
        
        $fileContent = [System.IO.File]::ReadAllBytes($LocalFile)
        $ftpRequest.ContentLength = $fileContent.Length
        
        $requestStream = $ftpRequest.GetRequestStream()
        $requestStream.Write($fileContent, 0, $fileContent.Length)
        $requestStream.Close()
        
        $response = $ftpRequest.GetResponse()
        $response.Close()
        
        return $true
    } catch {
        Write-Host "  [❌] فشل: $LocalFile" -ForegroundColor Red
        return $false
    }
}

function Create-Directory-FTP {
    param(
        [string]$RemoteDir,
        [string]$FtpHost,
        [string]$FtpUser,
        [string]$FtpPass
    )
    
    try {
        $ftpUri = "ftp://$FtpHost$RemoteDir"
        $ftpRequest = [System.Net.FtpWebRequest]::Create($ftpUri)
        $ftpRequest.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPass)
        $ftpRequest.Method = [System.Net.WebRequestMethods+Ftp]::MakeDirectory
        $ftpRequest.UsePassive = $true
        
        $response = $ftpRequest.GetResponse()
        $response.Close()
        return $true
    } catch {
        # المجلد موجود بالفعل أو خطأ آخر
        return $false
    }
}

# جمع الملفات
Write-Host "[1/3] جمع الملفات..." -ForegroundColor Cyan
$filesToUpload = Get-ChildItem -Recurse -File | Where-Object {
    $excluded = $false
    $relativePath = $_.FullName.Replace((Get-Location).Path + "\", "").Replace("\", "/")
    
    foreach ($pattern in $excludePatterns) {
        if ($relativePath -like "*$pattern*") {
            $excluded = $true
            break
        }
    }
    return -not $excluded
}

Write-Host "[✓] تم العثور على $($filesToUpload.Count) ملف" -ForegroundColor Green
Write-Host ""

# رفع الملفات
Write-Host "[2/3] رفع الملفات..." -ForegroundColor Cyan
Write-Host "هذا قد يستغرق بضع دقائق..." -ForegroundColor Yellow
Write-Host ""

$successCount = 0
$failCount = 0
$totalFiles = $filesToUpload.Count
$currentFile = 0

foreach ($file in $filesToUpload) {
    $currentFile++
    $relativePath = $file.FullName.Replace((Get-Location).Path + "\", "").Replace("\", "/")
    $remoteFilePath = "$RemotePath$relativePath"
    
    # إنشاء المجلدات المطلوبة
    $remoteDir = Split-Path $remoteFilePath -Parent
    if ($remoteDir -ne $RemotePath -and $remoteDir -ne "") {
        $dirs = $remoteDir.Replace($RemotePath, "").Split("/")
        $currentPath = $RemotePath
        foreach ($dir in $dirs) {
            if ($dir -ne "") {
                $currentPath = "$currentPath$dir/"
                Create-Directory-FTP -RemoteDir $currentPath -FtpHost $FtpHost -FtpUser $FtpUser -FtpPass $FtpPass | Out-Null
            }
        }
    }
    
    # رفع الملف
    $percent = [math]::Round(($currentFile / $totalFiles) * 100, 1)
    Write-Progress -Activity "رفع الملفات" -Status "رفع: $relativePath" -PercentComplete $percent
    
    if (Upload-File-FTP -LocalFile $file.FullName -RemoteFile $remoteFilePath -FtpHost $FtpHost -FtpUser $FtpUser -FtpPass $FtpPass) {
        $successCount++
    } else {
        $failCount++
    }
}

Write-Progress -Activity "رفع الملفات" -Completed

Write-Host ""
Write-Host "[3/3] النتائج..." -ForegroundColor Cyan
Write-Host "[✓] تم رفع $successCount ملف بنجاح" -ForegroundColor Green
if ($failCount -gt 0) {
    Write-Host "[⚠️] فشل رفع $failCount ملف" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[✓✓✓] تم الرفع بنجاح!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "الخطوات التالية في Hostinger:" -ForegroundColor Yellow
Write-Host "1. اذهب إلى Python App في hPanel" -ForegroundColor White
Write-Host "2. ثبت المكتبات من hostinger_requirements.txt" -ForegroundColor White
Write-Host "3. أعد إعداد ملف .env" -ForegroundColor White
Write-Host "4. شغّل التطبيق" -ForegroundColor White
Write-Host ""

