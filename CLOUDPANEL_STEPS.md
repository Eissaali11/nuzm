# خطوات النشر على CloudPanel - eissa.site

## ✅ الموقع: eissa.site
## 📁 المسار: /home/eissa/htdocs/eissa.site

---

## 🚀 الخطوات (بالترتيب)

### 1️⃣ رفع الملفات

#### الطريقة الأولى: Git (الأسهل - موصى بها)

1. **في CloudPanel**:
   - من صفحة Settings الحالية
   - اذهب إلى تبويب `Git` (أو `Deployment`)
   - أضف Repository:
     - **URL**: `https://github.com/Eissaali11/nuzm.git`
     - **Branch**: `main`
   - فعّل **Auto-Deploy**
   - احفظ

2. **هنا في Cursor**:
   ```powershell
   git push origin main
   ```
   ✅ سيتم سحب الملفات تلقائياً!

#### الطريقة الثانية: File Manager

1. **في CloudPanel**:
   - اذهب إلى تبويب `File Manager`
   - افتح المجلد: `/home/eissa/htdocs/eissa.site`
   - ارفع جميع الملفات (استثناء: `venv/`, `node_modules/`)

---

### 2️⃣ إعداد Python App

1. **في CloudPanel** → `Manage` → `Python`:
   - **Python Version**: `3.11` أو `3.12`
   - **Requirements**: انسخ محتوى `hostinger_requirements.txt`
   - **Start Command**:
     ```
     gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 120 main:app
     ```
   - احفظ

---

### 3️⃣ إنشاء قاعدة البيانات

1. **في CloudPanel** → تبويب `Databases`:
   - اضغط `Create Database`
   - اختر **MySQL**
   - أدخل:
     - **Database Name**: `nuzum_db` (أو أي اسم)
     - **Username**: `nuzum_user` (أو أي اسم)
     - **Password**: كلمة مرور قوية
   - احفظ المعلومات

---

### 4️⃣ إعداد ملف .env

1. **في CloudPanel** → `File Manager`:
   - افتح المجلد: `/home/eissa/htdocs/eissa.site`
   - أنشئ ملف جديد باسم `.env`
   - أضف المحتوى:

```env
DATABASE_URL=mysql://nuzum_user:your_password@localhost:3306/nuzum_db
SECRET_KEY=your_very_secret_key_here_change_this
SESSION_SECRET=your_session_secret_here
FLASK_ENV=production
FLASK_DEBUG=False

# إعدادات أخرى (اختياري)
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
SENDGRID_API_KEY=
```

**⚠️ مهم**: استبدل `your_password` و `your_very_secret_key_here_change_this` بقيم حقيقية!

---

### 5️⃣ إنشاء المجلدات المطلوبة

في `File Manager`، أنشئ:
- `database/`
- `static/uploads/`
- `static/uploads/employees/`
- `static/uploads/vehicles/`

---

### 6️⃣ إنشاء جداول قاعدة البيانات

1. **في CloudPanel** → `Manage` → `Terminal` (أو Python Console):
   
   ```bash
   cd /home/eissa/htdocs/eissa.site
   source venv/bin/activate
   python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database tables created!')"
   ```

---

### 7️⃣ تشغيل التطبيق

1. **في CloudPanel** → `Manage` → `Python`:
   - اضغط **Restart** أو **Start**
   - تحقق من **Logs** للتأكد من عدم وجود أخطاء

---

### 8️⃣ تفعيل SSL

1. **في CloudPanel** → تبويب `SSL/TLS`:
   - اضغط **Let's Encrypt**
   - أدخل البريد الإلكتروني
   - اضغط **Install**

---

## ✅ تم! افتح: https://eissa.site

---

## 📋 قائمة التحقق

- [ ] رفع الملفات (Git أو File Manager)
- [ ] إعداد Python App
- [ ] إنشاء قاعدة بيانات MySQL
- [ ] إنشاء ملف `.env`
- [ ] إنشاء المجلدات المطلوبة
- [ ] إنشاء جداول قاعدة البيانات
- [ ] تشغيل التطبيق
- [ ] تفعيل SSL

---

## 🆘 استكشاف الأخطاء

### التطبيق لا يعمل
→ تحقق من **Logs** في Python App

### خطأ في قاعدة البيانات
→ تحقق من معلومات `.env`

### Static files لا تعمل
→ تحقق من مسار `/static` في Nginx/Vhost

---

**ابدأ بالخطوة 1 (ربط Git) - الأسهل! 🚀**

