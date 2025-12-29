@echo off
chcp 65001 >nul
echo ========================================
echo    تشغيل مشروع نُظم
echo ========================================
echo.

cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [خطأ] البيئة الافتراضية غير موجودة
    echo يرجى تشغيل: .\run_with_auto_python.ps1
    pause
    exit /b 1
)

echo [✓] جارٍ تشغيل الخادم...
echo.
echo المشروع سيعمل على: http://localhost:5000
echo اضغط Ctrl+C لإيقاف الخادم
echo.

venv\Scripts\python.exe main.py

pause

