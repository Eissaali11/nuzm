@echo off
chcp 65001 >nul
echo ========================================
echo    إعداد مشروع نُظم - نظام إدارة الموظفين
echo ========================================
echo.

REM التحقق من وجود Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    where py >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [خطأ] Python غير مثبت أو غير موجود في PATH
        echo يرجى تثبيت Python من https://www.python.org/downloads/
        echo وتأكد من تحديد "Add Python to PATH" أثناء التثبيت
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

echo [✓] تم العثور على Python
%PYTHON_CMD% --version
echo.

REM إنشاء بيئة افتراضية
echo [1/5] إنشاء بيئة افتراضية...
if not exist "venv" (
    %PYTHON_CMD% -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [خطأ] فشل إنشاء البيئة الافتراضية
        pause
        exit /b 1
    )
    echo [✓] تم إنشاء البيئة الافتراضية
) else (
    echo [✓] البيئة الافتراضية موجودة بالفعل
)
echo.

REM تفعيل البيئة الافتراضية
echo [2/5] تفعيل البيئة الافتراضية...
call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo [خطأ] فشل تفعيل البيئة الافتراضية
    pause
    exit /b 1
)
echo [✓] تم تفعيل البيئة الافتراضية
echo.

REM ترقية pip
echo [3/5] ترقية pip...
python -m pip install --upgrade pip --quiet
echo [✓] تم ترقية pip
echo.

REM تثبيت المتطلبات
echo [4/5] تثبيت المتطلبات من requirements.txt...
echo هذا قد يستغرق بضع دقائق...
python -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [تحذير] حدثت بعض الأخطاء أثناء تثبيت المتطلبات
    echo يمكنك المحاولة مرة أخرى لاحقاً
) else (
    echo [✓] تم تثبيت المتطلبات بنجاح
)
echo.

REM التحقق من ملف .env
echo [5/5] التحقق من ملف .env...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo [✓] تم إنشاء ملف .env من .env.example
        echo [!] يرجى تعديل ملف .env وإضافة بيانات قاعدة البيانات الخاصة بك
    ) else (
        echo [!] ملف .env.example غير موجود
    )
) else (
    echo [✓] ملف .env موجود
)
echo.

echo ========================================
echo    تم إعداد المشروع بنجاح!
echo ========================================
echo.
echo الخطوات التالية:
echo 1. قم بتعديل ملف .env وإضافة بيانات قاعدة البيانات
echo 2. قم بتشغيل: python create_test_data.py
echo 3. قم بتشغيل: python main.py
echo.
echo بيانات الدخول الافتراضية:
echo   البريد: admin@nuzum.sa
echo   كلمة المرور: admin123
echo.
pause

