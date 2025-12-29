@echo off
chcp 65001 >nul
echo ========================================
echo    تشغيل مشروع نُظم
echo ========================================
echo.

REM التحقق من وجود Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    where py >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [خطأ] Python غير مثبت
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

REM تفعيل البيئة الافتراضية
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM تشغيل المشروع
echo [✓] جاري تشغيل المشروع...
echo [✓] سيتم فتح المتصفح على http://localhost:5000
echo.
%PYTHON_CMD% main.py

pause

