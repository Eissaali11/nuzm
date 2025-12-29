# نشر المشروع على CloudPanel (eissa.site)

## ✅ تم إنشاء الموقع: eissa.site

## 📋 الخطوات التالية

### 1️⃣ رفع الملفات

#### الطريقة الأولى: Git (الأسهل)

1. **في CloudPanel**:
   - اضغط `Manage` بجانب الموقع
   - اذهب إلى `Git` أو `Deployment`
   - أضف Repository: `https://github.com/Eissaali11/nuzm.git`
   - Branch: `main`
   - فعّل Auto-Deploy

2. **هنا في Cursor**:
   ```powershell
   git push origin main
   ```

#### الطريقة الثانية: رفع مباشر

1. **في CloudPanel**:
   - اضغط `Manage` بجانب الموقع
   - اذهب إلى `File Manager`
   - ارفع الملفات إلى المجلد الجذر

### 2️⃣ إعداد Python App

1. **في CloudPanel** → `Manage` → `Python`:
   - Python Version: `3.11` أو `3.12`
   - Requirements: انسخ محتوى `hostinger_requirements.txt`
   - Start Command:
     ```
     gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 120 main:app
     ```

### 3️⃣ إعداد قاعدة البيانات

1. **في CloudPanel** → `Databases`:
   - أنشئ قاعدة بيانات MySQL
   - احفظ: Database Name, Username, Password, Host

### 4️⃣ إعداد ملف .env

في File Manager، أنشئ ملف `.env`:

```env
DATABASE_URL=mysql://username:password@localhost:3306/database_name
SECRET_KEY=your_secret_key_here
FLASK_ENV=production
FLASK_DEBUG=False
```

### 5️⃣ إنشاء الجداول

في CloudPanel Terminal أو Python Console:

```python
from app import app, db
with app.app_context():
    db.create_all()
    print("Done!")
```

### 6️⃣ تشغيل التطبيق

- في CloudPanel → `Manage` → اضغط `Restart` أو `Start`

---

## ✅ تم! افتح: https://eissa.site

