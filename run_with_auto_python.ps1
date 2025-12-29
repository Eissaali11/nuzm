# سكريبت ذكي للعثور على Python وتشغيل المشروع
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   البحث عن Python وتشغيل المشروع" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$pythonPath = $null

# البحث في مسارات شائعة
$searchPaths = @(
    "python",
    "py",
    "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python*\pythonw.exe",
    "$env:PROGRAMFILES\Python*\python.exe",
    "$env:PROGRAMFILES(X86)\Python*\python.exe",
    "$env:LOCALAPPDATA\Microsoft\WindowsApps\python.exe",
    "$env:LOCALAPPDATA\Microsoft\WindowsApps\python3.exe"
)

Write-Host "جارٍ البحث عن Python..." -ForegroundColor Yellow

foreach ($path in $searchPaths) {
    try {
        if ($path -match "python\.exe$|pythonw\.exe$|python3\.exe$") {
            # مسار مباشر
            $found = Get-ChildItem -Path $path -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($found -and (Test-Path $found.FullName)) {
                $testResult = & $found.FullName --version 2>&1
                if ($LASTEXITCODE -eq 0 -and $testResult -notmatch "was not found|not recognized") {
                    $pythonPath = $found.FullName
                    Write-Host "[✓] تم العثور على Python: $pythonPath" -ForegroundColor Green
                    Write-Host "   الإصدار: $testResult" -ForegroundColor Gray
                    break
                }
            }
        } else {
            # أمر في PATH
            $cmd = Get-Command $path -ErrorAction SilentlyContinue
            if ($cmd) {
                $testResult = & $cmd.Source --version 2>&1
                if ($LASTEXITCODE -eq 0 -and $testResult -notmatch "was not found|not recognized") {
                    $pythonPath = $cmd.Source
                    Write-Host "[✓] تم العثور على Python: $pythonPath" -ForegroundColor Green
                    Write-Host "   الإصدار: $testResult" -ForegroundColor Gray
                    break
                }
            }
        }
    } catch {
        continue
    }
}

if (-not $pythonPath) {
    Write-Host "[❌] لم يتم العثور على Python!" -ForegroundColor Red
    Write-Host ""
    Write-Host "يرجى:" -ForegroundColor Yellow
    Write-Host "1. إعادة تشغيل PowerShell (بعد تثبيت Python)" -ForegroundColor White
    Write-Host "2. أو إضافة Python إلى PATH يدوياً" -ForegroundColor White
    Write-Host "3. راجع ملف FIX_PYTHON_PATH.md للتفاصيل" -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}

Write-Host ""

# التحقق من pip
Write-Host "جارٍ التحقق من pip..." -ForegroundColor Yellow
$pipCheck = & $pythonPath -m pip --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[❌] pip غير متاح في هذا التثبيت" -ForegroundColor Red
    Write-Host "يرجى تثبيت Python كامل من python.org أو Microsoft Store" -ForegroundColor Yellow
    pause
    exit 1
}
Write-Host "[✓] pip متاح" -ForegroundColor Green
Write-Host ""

# إنشاء البيئة الافتراضية
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "[1/4] إنشاء البيئة الافتراضية..." -ForegroundColor Cyan
    & $pythonPath -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[❌] فشل إنشاء البيئة الافتراضية" -ForegroundColor Red
        Write-Host "تأكد من أن Python يحتوي على وحدة venv" -ForegroundColor Yellow
        pause
        exit 1
    }
    Write-Host "[✓] تم إنشاء البيئة الافتراضية" -ForegroundColor Green
} else {
    Write-Host "[✓] البيئة الافتراضية موجودة" -ForegroundColor Green
}
Write-Host ""

# تفعيل البيئة وتثبيت المكتبات
$venvPython = "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[❌] لم يتم العثور على Python في البيئة الافتراضية" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "[2/4] ترقية pip..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip --quiet
Write-Host "[✓] تم ترقية pip" -ForegroundColor Green
Write-Host ""

Write-Host "[3/4] تثبيت المكتبات من requirements.txt..." -ForegroundColor Cyan
Write-Host "هذا قد يستغرق بضع دقائق..." -ForegroundColor Yellow
& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[⚠️] حدثت بعض الأخطاء أثناء التثبيت" -ForegroundColor Yellow
    Write-Host "يمكنك المحاولة مرة أخرى لاحقاً" -ForegroundColor Yellow
} else {
    Write-Host "[✓] تم تثبيت المكتبات بنجاح" -ForegroundColor Green
}
Write-Host ""

# التحقق من ملف .env
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.local") {
        Copy-Item ".env.local" ".env"
        Write-Host "[✓] تم نسخ .env.local إلى .env" -ForegroundColor Green
    } else {
        Write-Host "[!] ملف .env غير موجود - سيتم استخدام الإعدادات الافتراضية" -ForegroundColor Yellow
    }
} else {
    Write-Host "[✓] ملف .env موجود" -ForegroundColor Green
}
Write-Host ""

# إنشاء مجلد database
if (-not (Test-Path "database")) {
    New-Item -ItemType Directory -Path "database" | Out-Null
    Write-Host "[✓] تم إنشاء مجلد database" -ForegroundColor Green
}
Write-Host ""

# تشغيل المشروع
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   تشغيل المشروع..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "المشروع يعمل على: http://localhost:5000" -ForegroundColor Green
Write-Host "اضغط Ctrl+C لإيقاف الخادم" -ForegroundColor Yellow
Write-Host ""

& $venvPython main.py

