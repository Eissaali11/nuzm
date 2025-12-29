# إصلاح مشكلة Python في PATH

## المشكلة
Python مثبت لكنه غير موجود في PATH.

## الحلول

### الحل 1: إعادة تشغيل PowerShell (الأسهل)
1. **أغلق PowerShell الحالي تماماً**
2. **افتح PowerShell جديد**
3. جرب: `python --version`

### الحل 2: إضافة Python يدوياً إلى PATH

#### إذا كان Python من Microsoft Store:
عادة يكون في: `%LOCALAPPDATA%\Microsoft\WindowsApps`

#### إذا كان Python من python.org:
عادة يكون في: `%LOCALAPPDATA%\Programs\Python\Python3XX`

**خطوات الإضافة:**
1. افتح **إعدادات Windows** (Win + I)
2. ابحث عن **"Environment Variables"** أو **"متغيرات البيئة"**
3. اضغط على **"Environment Variables"**
4. في **"User variables"**، اختر **"Path"** واضغط **"Edit"**
5. اضغط **"New"** وأضف مسار Python:
   - `C:\Users\TWc\AppData\Local\Programs\Python\Python3XX`
   - أو `C:\Users\TWc\AppData\Local\Microsoft\WindowsApps`
6. اضغط **OK** في جميع النوافذ
7. **أعد تشغيل PowerShell**

### الحل 3: استخدام المسار الكامل

إذا كان Python مثبتاً، يمكنك استخدام المسار الكامل:

```powershell
# البحث عن Python
Get-ChildItem -Path "$env:LOCALAPPDATA\Programs\Python" -Recurse -Filter "python.exe" | Select-Object -First 1

# ثم استخدام المسار الكامل
& "C:\Users\TWc\AppData\Local\Programs\Python\Python3XX\python.exe" --version
```

### الحل 4: إعادة تثبيت Python مع PATH

1. افتح **Microsoft Store**
2. ابحث عن **Python 3.12**
3. **Uninstall** ثم **Install** مرة أخرى
4. تأكد من أن **"Add Python to PATH"** مفعل (إذا كان من python.org)

## التحقق من التثبيت

بعد إعادة تشغيل PowerShell:
```powershell
python --version
py --version
python -m pip --version
```

إذا عملت هذه الأوامر، يمكنك تشغيل:
```powershell
.\install_and_run.ps1
```

