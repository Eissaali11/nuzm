# تعليمات إعداد مشروع نُظم

## المتطلبات الأساسية

### 1. تثبيت Python
- قم بتحميل Python من [python.org](https://www.python.org/downloads/)
- اختر الإصدار 3.8 أو أحدث
- أثناء التثبيت، تأكد من تحديد خيار "Add Python to PATH"

### 2. التحقق من تثبيت Python
افتح PowerShell أو Command Prompt وقم بتشغيل:
```bash
python --version
```
أو
```bash
py --version
```

## خطوات الإعداد

### الخطوة 1: الانتقال إلى مجلد المشروع
```bash
cd C:\Users\TWc\nuzm
```

### الخطوة 2: إنشاء بيئة افتراضية (Virtual Environment)
```bash
python -m venv venv
```

### الخطوة 3: تفعيل البيئة الافتراضية
في PowerShell:
```bash
.\venv\Scripts\Activate.ps1
```

أو في Command Prompt:
```bash
venv\Scripts\activate
```

### الخطوة 4: تثبيت المتطلبات
```bash
pip install -r requirements.txt
```

### الخطوة 5: إعداد ملف .env
تم إنشاء ملف `.env` من `.env.example`. قم بتعديله حسب احتياجاتك:

**للتطوير المحلي (SQLite):**
```env
DATABASE_URL=sqlite:///nuzum_local.db
SECRET_KEY=your_secret_key_here
FLASK_ENV=development
FLASK_DEBUG=True
```

**للإنتاج (MySQL):**
```env
DATABASE_URL=mysql://username:password@localhost:3306/database_name
SECRET_KEY=your_secret_key_here
FLASK_ENV=production
FLASK_DEBUG=False
```

### الخطوة 6: إنشاء قاعدة البيانات والبيانات التجريبية
```bash
python create_test_data.py
```

### الخطوة 7: تشغيل المشروع
```bash
python main.py
```

أو
```bash
python app.py
```

سيتم تشغيل الخادم على: `http://localhost:5000`

## بيانات الدخول الافتراضية

- **البريد الإلكتروني**: admin@nuzum.sa
- **كلمة المرور**: admin123

## ملاحظات مهمة

1. **قاعدة البيانات**: 
   - للتطوير المحلي، استخدم SQLite (لا يحتاج إعداد)
   - للإنتاج، تحتاج إلى تثبيت وإعداد MySQL

2. **المتغيرات البيئية**:
   - Firebase و Twilio اختيارية للتطوير المحلي
   - يمكنك تركها كقيم افتراضية للتجربة

3. **المشاكل الشائعة**:
   - إذا ظهرت رسالة "python is not recognized"، تأكد من إضافة Python إلى PATH
   - إذا فشل تثبيت المتطلبات، حاول ترقية pip: `python -m pip install --upgrade pip`

## اختبار API

بعد تشغيل المشروع، يمكنك اختبار API:
```bash
curl http://localhost:5000/api/v1/health
```

أو استخدم Postman مع ملف `NUZUM_API_Collection.postman_collection.json`

