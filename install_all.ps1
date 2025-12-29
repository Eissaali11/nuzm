# سكريبت تثبيت تلقائي لجميع المتطلبات
# Install All Requirements Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   إعداد مشروع نُظم - تثبيت تلقائي" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# التحقق من وجود Python
$pythonCmd = $null

# محاولة العثور على Python
$pythonPaths = @(
    "python",
    "python3",
    "py"
)

foreach ($cmd in $pythonPaths) {
    try {
        $result = Get-Command $cmd -ErrorAction Stop
        $version = & $cmd --version 2>&1
        if ($LASTEXITCODE -eq 0 -or $version -match "Python") {
            $pythonCmd = $cmd
            Write-Host "[✓] تم العثور على Python: $version" -ForegroundColor Green
            break
        }
    } catch {
        continue
    }
}

# إذا لم يتم العثور على Python
if (-not $pythonCmd) {
    Write-Host "[!] Python غير مثبت أو غير موجود في PATH" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "جاري محاولة التثبيت التلقائي..." -ForegroundColor Yellow
    
    # محاولة استخدام winget
    try {
        $wingetCheck = Get-Command winget -ErrorAction Stop
        Write-Host "[*] جاري تثبيت Python باستخدام winget..." -ForegroundColor Yellow
        winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
        Start-Sleep -Seconds 5
        
        # تحديث PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        # إعادة المحاولة
        $pythonCmd = "python"
        $version = & python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[✓] تم تثبيت Python بنجاح: $version" -ForegroundColor Green
        }
    } catch {
        Write-Host "[✗] فشل التثبيت التلقائي" -ForegroundColor Red
        Write-Host ""
        Write-Host "يرجى تثبيت Python يدوياً:" -ForegroundColor Yellow
        Write-Host "1. قم بتحميل Python 3.11+ من: https://www.python.org/downloads/" -ForegroundColor Yellow
        Write-Host "2. تأكد من تحديد 'Add Python to PATH' أثناء التثبيت" -ForegroundColor Yellow
        Write-Host "3. أعد تشغيل PowerShell بعد التثبيت" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "أو قم بتشغيل هذا السكريبت مرة أخرى بعد تثبيت Python" -ForegroundColor Yellow
        exit 1
    }
}

if (-not $pythonCmd) {
    Write-Host "[✗] لا يمكن المتابعة بدون Python" -ForegroundColor Red
    exit 1
}

Write-Host ""

# إنشاء البيئة الافتراضية
Write-Host "[1/4] إنشاء البيئة الافتراضية..." -ForegroundColor Cyan
if (-not (Test-Path "venv")) {
    & $pythonCmd -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[✗] فشل إنشاء البيئة الافتراضية" -ForegroundColor Red
        exit 1
    }
    Write-Host "[✓] تم إنشاء البيئة الافتراضية" -ForegroundColor Green
} else {
    Write-Host "[✓] البيئة الافتراضية موجودة بالفعل" -ForegroundColor Green
}
Write-Host ""

# تفعيل البيئة الافتراضية
Write-Host "[2/4] تفعيل البيئة الافتراضية..." -ForegroundColor Cyan
$activateScript = "venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "[✓] تم تفعيل البيئة الافتراضية" -ForegroundColor Green
} else {
    Write-Host "[✗] ملف التفعيل غير موجود" -ForegroundColor Red
    exit 1
}
Write-Host ""

# ترقية pip
Write-Host "[3/4] ترقية pip..." -ForegroundColor Cyan
& python -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "[✓] تم ترقية pip" -ForegroundColor Green
} else {
    Write-Host "[!] تحذير: فشل ترقية pip، سيتم المتابعة..." -ForegroundColor Yellow
}
Write-Host ""

# تثبيت المتطلبات
Write-Host "[4/4] تثبيت مكتبات Python من requirements.txt..." -ForegroundColor Cyan
Write-Host "هذا قد يستغرق بضع دقائق..." -ForegroundColor Yellow
& python -m pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "[✓] تم تثبيت جميع المكتبات بنجاح!" -ForegroundColor Green
} else {
    Write-Host "[!] حدثت بعض الأخطاء أثناء التثبيت" -ForegroundColor Yellow
    Write-Host "يمكنك المحاولة مرة أخرى لاحقاً" -ForegroundColor Yellow
}
Write-Host ""

# التحقق من ملف .env
Write-Host "[*] التحقق من ملف .env..." -ForegroundColor Cyan
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "[✓] تم إنشاء ملف .env من .env.example" -ForegroundColor Green
        Write-Host "[!] يرجى تعديل ملف .env وإضافة بيانات قاعدة البيانات" -ForegroundColor Yellow
    } else {
        Write-Host "[!] ملف .env.example غير موجود" -ForegroundColor Yellow
        Write-Host "[!] ستحتاج إلى إنشاء ملف .env يدوياً" -ForegroundColor Yellow
    }
} else {
    Write-Host "[✓] ملف .env موجود" -ForegroundColor Green
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   تم إعداد المشروع بنجاح!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "الخطوات التالية:" -ForegroundColor Yellow
Write-Host "1. قم بتعديل ملف .env وإضافة بيانات قاعدة البيانات" -ForegroundColor White
Write-Host "2. قم بتشغيل: python create_test_data.py" -ForegroundColor White
Write-Host "3. قم بتشغيل: python main.py" -ForegroundColor White
Write-Host ""
Write-Host "بيانات الدخول الافتراضية:" -ForegroundColor Yellow
Write-Host "  البريد: admin@nuzum.sa" -ForegroundColor White
Write-Host "  كلمة المرور: admin123" -ForegroundColor White
Write-Host ""

