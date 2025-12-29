# ربط المشروع بـ Hostinger بشكل مباشر

## 🔗 الطرق المتاحة للربط المباشر

### 1️⃣ ربط Git (الطريقة الموصى بها - تلقائي)

#### إعداد Git Repository

```bash
# في المشروع المحلي
cd C:\Users\TWc\nuzm

# تهيئة Git (إذا لم يكن موجوداً)
git init

# إضافة جميع الملفات
git add .

# عمل commit أولي
git commit -m "Initial commit for Hostinger deployment"

# إضافة Remote Repository
# (أنشئ repository على GitHub/GitLab/Bitbucket أولاً)
git remote add origin https://github.com/yourusername/nuzum.git

# رفع الكود
git push -u origin main
```

#### ربط Hostinger بـ Git Repository

1. **في hPanel**:
   - اذهب إلى `Advanced` → `Git`
   - اضغط `Create Repository`
   - أدخل رابط Git Repository
   - اختر `Branch`: `main` أو `master`
   - اختر `Directory`: `public_html/nuzum`

2. **إعداد Auto-Deploy**:
   - فعّل `Auto Deploy`
   - سيتم تحديث الموقع تلقائياً عند الـ push

#### سكريبت التحديث التلقائي

أنشئ ملف `.github/workflows/deploy.yml` (إذا كنت تستخدم GitHub):

```yaml
name: Deploy to Hostinger

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to Hostinger via FTP
        uses: SamKirkland/FTP-Deploy-Action@4.0.0
        with:
          server: ftp.yourdomain.com
          username: ${{ secrets.FTP_USERNAME }}
          password: ${{ secrets.FTP_PASSWORD }}
          local-dir: ./
          server-dir: /public_html/nuzum/
          exclude: |
            **/.git*
            **/.git*/**
            **/venv/**
            **/__pycache__/**
            **/*.pyc
            **/.env.local
            **/node_modules/**
```

---

### 2️⃣ ربط FTP مباشر (FileZilla أو WinSCP)

#### إعدادات FTP في Hostinger

1. **في hPanel**:
   - اذهب إلى `Files` → `FTP Accounts`
   - أنشئ FTP Account جديد أو استخدم الموجود
   - احفظ: **Host**, **Username**, **Password**, **Port**

#### استخدام FileZilla

1. **تحميل FileZilla**: https://filezilla-project.org/
2. **فتح FileZilla**:
   - **Host**: `ftp.yourdomain.com` أو IP
   - **Username**: اسم المستخدم
   - **Password**: كلمة المرور
   - **Port**: `21` (أو `22` لـ SFTP)
   - اضغط `Quickconnect`

3. **رفع الملفات**:
   - **Local site** (يسار): مجلد المشروع المحلي
   - **Remote site** (يمين): `public_html/nuzum/`
   - اسحب الملفات من اليسار إلى اليمين

#### استخدام WinSCP (Windows)

1. **تحميل WinSCP**: https://winscp.net/
2. **إنشاء Session**:
   - **File protocol**: `FTP` أو `SFTP`
   - **Host name**: `ftp.yourdomain.com`
   - **User name**: اسم المستخدم
   - **Password**: كلمة المرور
   - احفظ الجلسة

3. **رفع الملفات**:
   - اسحب الملفات من اليسار إلى اليمين

---

### 3️⃣ ربط قاعدة البيانات عن بُعد

#### إعدادات قاعدة البيانات في Hostinger

1. **في hPanel**:
   - اذهب إلى `Databases` → `MySQL Databases`
   - أنشئ قاعدة بيانات جديدة
   - احفظ: **Database Name**, **Username**, **Password**, **Host**

#### الاتصال من المشروع المحلي

عدّل ملف `.env.local`:

```env
# قاعدة البيانات على Hostinger
DATABASE_URL=mysql://username:password@yourdomain.com:3306/database_name

# أو إذا كان Hostinger يسمح بالاتصال الخارجي
DATABASE_URL=mysql://username:password@your-server-ip:3306/database_name
```

**ملاحظة**: قد تحتاج إلى تفعيل "Remote MySQL" في hPanel

#### تفعيل Remote MySQL في Hostinger

1. **في hPanel**:
   - اذهب إلى `Databases` → `Remote MySQL`
   - أضف IP جهازك (ابحث عن IP: https://whatismyipaddress.com/)
   - أو أضف `%` للسماح من أي IP (غير آمن للإنتاج)

---

### 4️⃣ ربط مباشر عبر SSH (إذا كان متاحاً)

#### الاتصال عبر SSH

```bash
# في Terminal أو PowerShell
ssh username@your-server-ip

# أو إذا كان Hostinger يوفر SSH
ssh username@yourdomain.com -p 22
```

#### رفع الملفات عبر SCP

```bash
# رفع مجلد كامل
scp -r C:\Users\TWc\nuzm\* username@yourdomain.com:/public_html/nuzum/

# رفع ملف واحد
scp app.py username@yourdomain.com:/public_html/nuzum/
```

---

### 5️⃣ استخدام VS Code Remote (أحدث طريقة)

#### تثبيت Extension

1. **في VS Code**:
   - افتح Extensions
   - ابحث عن `Remote - SSH` أو `FTP-Sync`
   - ثبت Extension

#### إعداد FTP-Sync

1. **أنشئ ملف `.vscode/ftp-sync.json`**:

```json
{
    "protocol": "ftp",
    "host": "ftp.yourdomain.com",
    "port": 21,
    "username": "your_username",
    "password": "your_password",
    "remotePath": "/public_html/nuzum/",
    "localPath": "./",
    "secure": false,
    "passive": true,
    "debug": false,
    "privateKeyPath": null,
    "passphrase": null,
    "agent": null,
    "allow": [],
    "ignore": [
        "**/.git/**",
        "**/venv/**",
        "**/__pycache__/**",
        "**/*.pyc",
        "**/.env.local",
        "**/node_modules/**"
    ],
    "generatedList": {
        "uploadOnSave": true,
        "downloadOnOpen": false,
        "watcher": {
            "files": "**/*",
            "autoUpload": true,
            "autoDelete": false
        }
    }
}
```

2. **استخدام**:
   - احفظ أي ملف → سيتم رفعه تلقائياً
   - أو اضغط `Ctrl+Shift+P` → `FTP-Sync: Upload`

---

## 🚀 سكريبت رفع تلقائي (PowerShell)

أنشئ ملف `deploy_to_hostinger.ps1`:

```powershell
# سكريبت رفع تلقائي إلى Hostinger
param(
    [string]$FtpHost = "ftp.yourdomain.com",
    [string]$FtpUser = "your_username",
    [string]$FtpPass = "your_password",
    [string]$RemotePath = "/public_html/nuzum/"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   رفع المشروع إلى Hostinger" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# الملفات التي يجب استثناؤها
$excludePatterns = @(
    "venv",
    "__pycache__",
    "*.pyc",
    ".env.local",
    ".git",
    "node_modules"
)

# إنشاء قائمة الملفات للرفع
$filesToUpload = Get-ChildItem -Recurse -File | Where-Object {
    $excluded = $false
    foreach ($pattern in $excludePatterns) {
        if ($_.FullName -like "*$pattern*") {
            $excluded = $true
            break
        }
    }
    return -not $excluded
}

Write-Host "جارٍ رفع $($filesToUpload.Count) ملف..." -ForegroundColor Yellow

# استخدام WinSCP أو FTP command
# يمكنك استخدام مكتبة .NET للـ FTP
Add-Type -AssemblyName System.Net.Http

# أو استخدم WinSCP .NET assembly
# تحميل من: https://winscp.net/eng/download.php

Write-Host "[✓] تم الرفع بنجاح!" -ForegroundColor Green
```

---

## 📋 قائمة التحقق للربط المباشر

### ✅ قبل البدء:
- [ ] لديك بيانات FTP من Hostinger
- [ ] أنشأت قاعدة بيانات MySQL
- [ ] لديك Python App في hPanel (اختياري)
- [ ] أعددت ملف `.env` بقاعدة البيانات الصحيحة

### ✅ خطوات الربط:
- [ ] اختر طريقة الربط (Git/FTP/SSH)
- [ ] رفع الملفات (استثناء venv و __pycache__)
- [ ] إعداد قاعدة البيانات
- [ ] اختبار الاتصال

---

## 🔧 إعدادات متقدمة

### ربط Git مع Auto-Deploy

```bash
# في المشروع المحلي
git add .
git commit -m "Update for Hostinger"
git push origin main

# سيتم التحديث تلقائياً في Hostinger
```

### ربط قاعدة البيانات المحلية بـ Hostinger

في `.env.local`:
```env
# للاختبار: استخدم قاعدة بيانات Hostinger
DATABASE_URL=mysql://hostinger_user:password@yourdomain.com:3306/hostinger_db
```

### Sync تلقائي مع Watch

استخدم `watchdog` في Python:

```bash
pip install watchdog
```

أنشئ `sync_watch.py`:
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import ftplib
import os

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            print(f"File changed: {event.src_path}")
            # رفع الملف عبر FTP
            # ... كود الرفع

observer = Observer()
observer.schedule(MyHandler(), path='.', recursive=True)
observer.start()
```

---

## 📞 ملاحظات مهمة

1. **الأمان**: لا ترفع ملف `.env.local` أبداً
2. **الأداء**: استخدم Git للرفع التلقائي بدلاً من FTP
3. **النسخ الاحتياطي**: احتفظ بنسخة محلية دائماً
4. **الاختبار**: اختبر على بيئة تجريبية أولاً

---

## 🎯 الطريقة الموصى بها

**للربط المباشر**: استخدم **Git + Auto-Deploy** في Hostinger
- أسرع
- تلقائي
- آمن
- سهل التحديث

**للرفع اليدوي**: استخدم **FileZilla** أو **WinSCP**

