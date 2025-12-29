# إعدادات CloudPanel الحالية - eissa.site

## ✅ الإعدادات الحالية

- **Domain**: eissa.site
- **Site User**: eissa
- **IP Address**: 72.62.149.127
- **Root Directory**: `/home/eissa/htdocs/eissa.site`
- **Python Version**: 3.12 ✅
- **App Port**: 8090

---

## 🚀 الخطوات التالية (بالترتيب)

### 1️⃣ رفع الملفات

#### الطريقة الأسهل: Git

1. **في CloudPanel**:
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

#### أو رفع مباشر:
- اذهب إلى `File Manager`
- ارفع الملفات إلى `/home/eissa/htdocs/eissa.site`

---

### 2️⃣ إعداد Python App

بعد رفع الملفات:

1. **في CloudPanel** → `Manage` → `Python`:
   - **Requirements**: انسخ محتوى `hostinger_requirements.txt` والصقه
   - **Start Command**:
     ```
     gunicorn --bind 0.0.0.0:8090 --workers 2 --timeout 120 main:app
     ```
     ⚠️ **مهم**: استخدم المنفذ `8090` (ليس 8000) لأن App Port = 8090
   - احفظ

---

### 3️⃣ إنشاء قاعدة البيانات

1. **في CloudPanel** → تبويب `Databases`:
   - اضغط `Create Database`
   - اختر **MySQL**
   - أدخل:
     - **Database Name**: `nuzum_db`
     - **Username**: `nuzum_user`
     - **Password**: (كلمة مرور قوية)
   - احفظ المعلومات

---

### 4️⃣ إعداد ملف .env

1. **في CloudPanel** → `File Manager`:
   - افتح: `/home/eissa/htdocs/eissa.site`
   - أنشئ ملف `.env`
   - أضف:

```env
DATABASE_URL=mysql://nuzum_user:your_password@localhost:3306/nuzum_db
SECRET_KEY=your_very_secret_key_here_change_this_in_production
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

**⚠️ مهم**: استبدل:
- `your_password` → كلمة مرور قاعدة البيانات
- `your_very_secret_key_here_change_this_in_production` → مفتاح سري قوي

---

### 5️⃣ إنشاء المجلدات

في `File Manager`، أنشئ:
- `database/`
- `static/uploads/`
- `static/uploads/employees/`
- `static/uploads/vehicles/`

---

### 6️⃣ إنشاء جداول قاعدة البيانات

1. **في CloudPanel** → `Manage` → `Terminal` (أو SSH):
   
   ```bash
   cd /home/eissa/htdocs/eissa.site
   python3.12 -m venv venv
   source venv/bin/activate
   pip install -r hostinger_requirements.txt
   python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Done!')"
   ```

---

### 7️⃣ تشغيل التطبيق

1. **في CloudPanel** → `Manage` → `Python`:
   - اضغط **Restart** أو **Start**
   - تحقق من **Logs**

---

### 8️⃣ تفعيل SSL

1. **في CloudPanel** → تبويب `SSL/TLS`:
   - اضغط **Let's Encrypt**
   - أدخل البريد الإلكتروني
   - اضغط **Install**

---

## ⚠️ ملاحظات مهمة

1. **المنفذ**: استخدم `8090` في Start Command (ليس 8000)
2. **Python Version**: 3.12 ✅ (مثبت بالفعل)
3. **المسار**: `/home/eissa/htdocs/eissa.site`

---

## 📋 قائمة التحقق

- [ ] رفع الملفات (Git أو File Manager)
- [ ] إعداد Python Requirements
- [ ] إعداد Start Command (بمنفذ 8090)
- [ ] إنشاء قاعدة بيانات MySQL
- [ ] إنشاء ملف `.env`
- [ ] إنشاء المجلدات المطلوبة
- [ ] إنشاء جداول قاعدة البيانات
- [ ] تشغيل التطبيق
- [ ] تفعيل SSL

---

## 🎯 ابدأ الآن

**الخطوة 1**: اذهب إلى تبويب `Git` في CloudPanel واربط Repository!

