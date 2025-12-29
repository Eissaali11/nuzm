# سكريبت ربط مباشر بـ Hostinger API
# Direct Hostinger API Deployment Script

param(
    [Parameter(Mandatory=$false)]
    [string]$ApiToken = "5om43f07eSdSuSDBnXS3X53O17BviwydAd9myIEY5eb1e381",
    
    [Parameter(Mandatory=$false)]
    [string]$Domain = "eissa.site",
    
    [Parameter(Mandatory=$false)]
    [string]$Action = "deploy"  # deploy, status, files
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   ربط مباشر بـ Hostinger API" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Headers للـ API
$headers = @{
    "Authorization" = "Bearer $ApiToken"
    "Content-Type" = "application/json"
    "Accept" = "application/json"
}

# Base URL للـ API
$baseUrl = "https://developers.hostinger.com/api"

function Invoke-HostingerAPI {
    param(
        [string]$Endpoint,
        [string]$Method = "GET",
        [object]$Body = $null
    )
    
    try {
        $uri = "$baseUrl$Endpoint"
        Write-Host "📡 الاتصال بـ: $uri" -ForegroundColor Gray
        
        $params = @{
            Uri = $uri
            Method = $Method
            Headers = $headers
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
        }
        
        $response = Invoke-RestMethod @params
        return $response
    } catch {
        Write-Host "❌ خطأ: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            Write-Host "   التفاصيل: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
        }
        return $null
    }
}

# اختبار الاتصال
Write-Host "[1/4] اختبار الاتصال بـ Hostinger API..." -ForegroundColor Cyan
$testResponse = Invoke-HostingerAPI -Endpoint "/vps/v1/virtual-machines"

if ($testResponse) {
    Write-Host "[✓] الاتصال ناجح!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[❌] فشل الاتصال. تحقق من API Token" -ForegroundColor Red
    exit 1
}

# الحصول على معلومات VPS
Write-Host "[2/4] جلب معلومات VPS..." -ForegroundColor Cyan
$vpsInfo = Invoke-HostingerAPI -Endpoint "/vps/v1/virtual-machines"

if ($vpsInfo) {
    Write-Host "[✓] تم جلب معلومات VPS" -ForegroundColor Green
    if ($vpsInfo.data) {
        Write-Host "   عدد VPS: $($vpsInfo.data.Count)" -ForegroundColor Gray
    }
    Write-Host ""
}

# رفع الملفات (إذا كان متاحاً)
if ($Action -eq "deploy") {
    Write-Host "[3/4] إعداد الملفات للرفع..." -ForegroundColor Cyan
    
    # جمع الملفات (استثناء venv, node_modules, etc.)
    $excludePatterns = @("venv", "__pycache__", "*.pyc", ".env.local", ".git", "node_modules")
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
    
    Write-Host "[✓] تم العثور على $($filesToUpload.Count) ملف" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "[4/4] ملاحظة: رفع الملفات يتطلب FTP أو SSH" -ForegroundColor Yellow
    Write-Host "   استخدم Git أو FTP للرفع المباشر" -ForegroundColor Yellow
    Write-Host ""
}

# معلومات الاتصال
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   معلومات الاتصال" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "API Token: $($ApiToken.Substring(0, 20))..." -ForegroundColor Gray
Write-Host "Domain: $Domain" -ForegroundColor Gray
Write-Host ""
Write-Host "للرفع المباشر، استخدم:" -ForegroundColor Yellow
Write-Host "1. Git (الأسهل): git push origin main" -ForegroundColor White
Write-Host "2. FTP: استخدم FileZilla مع بيانات FTP" -ForegroundColor White
Write-Host "3. SSH: استخدم SCP أو rsync" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan

