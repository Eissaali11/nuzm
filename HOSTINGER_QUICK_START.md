# دليل سريع لنشر نُظم على Hostinger

## ⚡ خطوات سريعة (5 دقائق)

### 1️⃣ إعداد Python App في hPanel
- `Advanced` → `Python App` → `Create New App`
- **App Name**: `nuzum`
- **Python Version**: `3.11` أو `3.12`
- **App Root**: `public_html/nuzum`

### 2️⃣ رفع الملفات
- استخدم **File Manager** أو **FTP**
- ارفع جميع الملفات إلى `public_html/nuzum/`
- **لا ترفع**: `venv/`, `__pycache__/`, `.env.local`

### 3️⃣ إنشاء قاعدة البيانات
- `Databases` → `MySQL Databases` → `Create Database`
- احفظ: **Database Name**, **Username**, **Password**, **Host**

### 4️⃣ إعداد .env
في File Manager، أنشئ/عدّل ملف `.env`:

```env
DATABASE_URL=mysql://username:password@localhost:3306/database_name
SECRET_KEY=your_secret_key_here
FLASK_ENV=production
FLASK_DEBUG=False
```

### 5️⃣ تثبيت المكتبات
- في `Python App` → `Requirements`
- انسخ محتوى `hostinger_requirements.txt` والصقه
- احفظ

### 6️⃣ إعداد Start Command
في `Python App` → `Start Command`:

```bash
gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 main:app
```

### 7️⃣ إنشاء المجلدات
في File Manager، أنشئ:
- `database/`
- `static/uploads/`
- `static/uploads/employees/`

### 8️⃣ إنشاء الجداول
في `Python App` → `Python Console`:

```python
from app import app, db
with app.app_context():
    db.create_all()
    print("Done!")
```

### 9️⃣ تشغيل التطبيق
- اضغط **"Restart"** في Python App
- تحقق من **Logs**

### 🔟 ربط الدومين
- في Python App → `Add Domain`
- أدخل الدومين الخاص بك

---

## ✅ تم! افتح `https://yourdomain.com`

---

## 📋 قائمة الملفات المهمة

- ✅ `HOSTINGER_DEPLOYMENT.md` - دليل مفصل
- ✅ `hostinger_requirements.txt` - متطلبات Python
- ✅ `hostinger_start.sh` - سكريبت البدء
- ✅ `.htaccess` - إعدادات Apache (اختياري)
- ✅ `Procfile` - إعدادات Gunicorn

---

## 🆘 مشاكل شائعة

### التطبيق لا يعمل
→ تحقق من **Logs** في Python App

### خطأ في قاعدة البيانات
→ تحقق من معلومات `.env`

### Static files لا تعمل
→ تحقق من مسار `/static`

---

**للمزيد من التفاصيل**: راجع `HOSTINGER_DEPLOYMENT.md`

