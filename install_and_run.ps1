# سكريبت تثبيت Python وتشغيل المشروع
# Install and Run Script for نُظم Project

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   إعداد وتشغيل مشروع نُظم" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# التحقق من وجود Python
$pythonCmd = $null

# محاولة العثور على Python
$pythonPaths = @(
    "python",
    "py",
    "python3",
    "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe",
    "$env:PROGRAMFILES\Python*\python.exe",
    "$env:PROGRAMFILES(X86)\Python*\python.exe"
)

foreach ($path in $pythonPaths) {
    try {
        if ($path -match "python\.exe$") {
            $found = Get-ChildItem -Path $path -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($found) {
                $pythonCmd = $found.FullName
                break
            }
        } else {
            $result = Get-Command $path -ErrorAction SilentlyContinue
            if ($result) {
                $pythonCmd = $result.Source
                break
            }
        }
    } catch {
        continue
    }
}

if (-not $pythonCmd) {
    Write-Host "[❌] Python غير مثبت!" -ForegroundColor Red
    Write-Host ""
    Write-Host "يرجى تثبيت Python أولاً:" -ForegroundColor Yellow
    Write-Host "1. افتح المتصفح واذهب إلى: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "2. حمّل Python 3.11 أو أحدث" -ForegroundColor Yellow
    Write-Host "3. أثناء التثبيت، تأكد من تحديد: 'Add Python to PATH'" -ForegroundColor Yellow
    Write-Host "4. بعد التثبيت، أعد تشغيل PowerShell ثم شغّل هذا السكريبت مرة أخرى" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "أو يمكنك تثبيت Python من Microsoft Store:" -ForegroundColor Yellow
    Write-Host "  - افتح Microsoft Store" -ForegroundColor Yellow
    Write-Host "  - ابحث عن 'Python 3.12'" -ForegroundColor Yellow
    Write-Host "  - اضغط 'Install'" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

Write-Host "[✓] تم العثور على Python: $pythonCmd" -ForegroundColor Green
& $pythonCmd --version
Write-Host ""

# التحقق من وجود البيئة الافتراضية
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "[1/4] إنشاء البيئة الافتراضية..." -ForegroundColor Cyan
    & $pythonCmd -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[❌] فشل إنشاء البيئة الافتراضية" -ForegroundColor Red
        pause
        exit 1
    }
    Write-Host "[✓] تم إنشاء البيئة الافتراضية" -ForegroundColor Green
} else {
    Write-Host "[✓] البيئة الافتراضية موجودة بالفعل" -ForegroundColor Green
}
Write-Host ""

# تفعيل البيئة الافتراضية
Write-Host "[2/4] تفعيل البيئة الافتراضية..." -ForegroundColor Cyan
$venvPython = "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[❌] لم يتم العثور على Python في البيئة الافتراضية" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "[✓] تم تفعيل البيئة الافتراضية" -ForegroundColor Green
Write-Host ""

# ترقية pip
Write-Host "[3/4] ترقية pip..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip --quiet
Write-Host "[✓] تم ترقية pip" -ForegroundColor Green
Write-Host ""

# تثبيت المتطلبات
Write-Host "[4/4] تثبيت المكتبات من requirements.txt..." -ForegroundColor Cyan
Write-Host "هذا قد يستغرق بضع دقائق..." -ForegroundColor Yellow
& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[⚠️] حدثت بعض الأخطاء أثناء التثبيت" -ForegroundColor Yellow
    Write-Host "يمكنك المحاولة مرة أخرى لاحقاً" -ForegroundColor Yellow
} else {
    Write-Host "[✓] تم تثبيت جميع المكتبات بنجاح" -ForegroundColor Green
}
Write-Host ""

# التحقق من ملف .env
if (-not (Test-Path ".env")) {
    Write-Host "[!] ملف .env غير موجود" -ForegroundColor Yellow
    Write-Host "يرجى إنشاء ملف .env باستخدام ENV_SETUP_GUIDE.md كمرجع" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "للبدء السريع، يمكنك إنشاء ملف .env بالحد الأدنى:" -ForegroundColor Yellow
    Write-Host "  DATABASE_URL=sqlite:///database/nuzum.db" -ForegroundColor Gray
    Write-Host "  SECRET_KEY=change_this_to_a_random_string" -ForegroundColor Gray
    Write-Host "  FLASK_ENV=development" -ForegroundColor Gray
    Write-Host "  FLASK_DEBUG=True" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "[✓] ملف .env موجود" -ForegroundColor Green
}
Write-Host ""

# محاولة تشغيل المشروع
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   تشغيل المشروع..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# إنشاء مجلد database إذا لم يكن موجوداً
if (-not (Test-Path "database")) {
    New-Item -ItemType Directory -Path "database" | Out-Null
}

# تشغيل المشروع
Write-Host "جارٍ تشغيل الخادم على http://localhost:5000" -ForegroundColor Green
Write-Host "اضغط Ctrl+C لإيقاف الخادم" -ForegroundColor Yellow
Write-Host ""

& $venvPython main.py

