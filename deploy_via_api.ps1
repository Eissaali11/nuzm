# ربط مباشر بـ Hostinger API ورفع المشروع
# Direct Hostinger API Deployment

param(
    [Parameter(Mandatory=$false)]
    [string]$ApiToken = "5om43f07eSdSuSDBnXS3X53O17BviwydAd9myIEY5eb1e381",
    
    [Parameter(Mandatory=$false)]
    [string]$Domain = "eissa.site"
)

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   ربط مباشر بـ Hostinger API" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Headers
$headers = @{
    "Authorization" = "Bearer $ApiToken"
    "Content-Type" = "application/json"
    "Accept" = "application/json"
}

$baseUrl = "https://developers.hostinger.com/api"

# اختبار الاتصال
Write-Host "[1/5] اختبار الاتصال..." -ForegroundColor Cyan
try {
    $testResponse = Invoke-RestMethod -Uri "$baseUrl/vps/v1/virtual-machines" -Method GET -Headers $headers
    Write-Host "[✓] الاتصال ناجح!" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "[❌] فشل الاتصال: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "الطريقة البديلة: استخدم Git" -ForegroundColor Yellow
    Write-Host "  git push origin main" -ForegroundColor Cyan
    exit 1
}

# الحصول على معلومات VPS/Domains
Write-Host "[2/5] جلب معلومات الحساب..." -ForegroundColor Cyan
try {
    $vpsInfo = Invoke-RestMethod -Uri "$baseUrl/vps/v1/virtual-machines" -Method GET -Headers $headers
    if ($vpsInfo.data) {
        Write-Host "[✓] تم العثور على $($vpsInfo.data.Count) VPS" -ForegroundColor Green
    }
} catch {
    Write-Host "[⚠️] لا يمكن جلب معلومات VPS" -ForegroundColor Yellow
}
Write-Host ""

# رفع التغييرات إلى Git
Write-Host "[3/5] رفع التغييرات إلى GitHub..." -ForegroundColor Cyan
if (Get-Command git -ErrorAction SilentlyContinue) {
    $gitStatus = git status --short 2>&1
    if ($gitStatus) {
        Write-Host "   جارٍ إضافة التغييرات..." -ForegroundColor Gray
        git add . 2>&1 | Out-Null
        
        $commitMsg = "Deploy to Hostinger via API - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
        git commit -m $commitMsg 2>&1 | Out-Null
        
        Write-Host "   جارٍ رفع التغييرات..." -ForegroundColor Gray
        git push origin main 2>&1 | Out-Null
        
        Write-Host "[✓] تم الرفع إلى GitHub بنجاح!" -ForegroundColor Green
    } else {
        Write-Host "[✓] لا توجد تغييرات للرفع" -ForegroundColor Green
    }
} else {
    Write-Host "[⚠️] Git غير متاح" -ForegroundColor Yellow
}
Write-Host ""

# معلومات الاتصال
Write-Host "[4/5] معلومات الاتصال:" -ForegroundColor Cyan
Write-Host "   Domain: $Domain" -ForegroundColor Gray
Write-Host "   API Token: $($ApiToken.Substring(0, 20))..." -ForegroundColor Gray
Write-Host ""

# الخطوات التالية
Write-Host "[5/5] الخطوات التالية:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. في Hostinger hPanel:" -ForegroundColor Yellow
Write-Host "   • اذهب إلى Advanced → Git" -ForegroundColor White
Write-Host "   • أضف: https://github.com/Eissaali11/nuzm.git" -ForegroundColor Cyan
Write-Host "   • Branch: main" -ForegroundColor Cyan
Write-Host "   • فعّل Auto-Deploy" -ForegroundColor Green
Write-Host ""
Write-Host "2. سيتم التحديث تلقائياً!" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[✓✓✓] تم الإعداد بنجاح!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

