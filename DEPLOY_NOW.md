# رفع المشروع مباشرة إلى Hostinger

## 🚀 الطريقة السريعة

### الخطوة 1: احصل على بيانات FTP من Hostinger

1. **سجل الدخول إلى hPanel**
2. **اذهب إلى**: `Files` → `FTP Accounts`
3. **احفظ**:
   - **FTP Host**: (مثلاً: `ftp.yourdomain.com`)
   - **FTP Username**: (اسم المستخدم)
   - **FTP Password**: (كلمة المرور)
   - **Port**: (عادة `21`)

### الخطوة 2: شغّل سكريبت الرفع

في PowerShell هنا في Cursor، شغّل:

```powershell
.\quick_deploy.ps1 -FtpHost "ftp.yourdomain.com" -FtpUser "your_username" -FtpPass "your_password" -RemotePath "/public_html/nuzum/"
```

**أو** إذا كان لديك ملف إعدادات:

```powershell
# أنشئ ملف .hostinger_config.json أولاً
.\deploy_to_hostinger.ps1
```

---

## 📋 مثال كامل

```powershell
# مثال:
.\quick_deploy.ps1 `
    -FtpHost "ftp.nuzum.site" `
    -FtpUser "u800258840" `
    -FtpPass "your_password_here" `
    -RemotePath "/public_html/nuzum/"
```

---

## ⚡ أو استخدم Git (الأسهل)

إذا كان Git مربوط في Hostinger:

```powershell
git push origin main
```

سيتم التحديث تلقائياً!

---

## 📝 ملاحظات

- **لا ترفع**: `venv/`, `node_modules/`, `.env.local`
- **سيتم استثناؤها تلقائياً** في السكريبت
- **بعد الرفع**: اذهب إلى Python App في hPanel وأعد الإعداد

---

**جاهز للرفع؟** شغّل الأمر أعلاه! 🚀

