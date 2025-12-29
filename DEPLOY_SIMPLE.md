# 🚀 رفع المشروع إلى Hostinger - الطريقة الأسهل

## ✅ الخطوات البسيطة (3 دقائق فقط!)

### الخطوة 1: في Hostinger hPanel

1. **سجل الدخول** إلى hPanel
2. **اذهب إلى**: `Advanced` → `Git`
3. **اضغط**: `Create Repository` أو `Add Repository`
4. **أدخل**:
   ```
   Repository URL: https://github.com/Eissaali11/nuzm.git
   Branch: main
   Directory: public_html/nuzum
   ```
5. **فعّل**: ✅ `Auto Deploy`
6. **احفظ**

### الخطوة 2: هنا في Cursor

بعد ربط Git في Hostinger، شغّل:

```powershell
git push origin main
```

**✅ تم!** سيتم تحديث الموقع تلقائياً!

---

## 🎯 ماذا يحدث بعد ذلك؟

- ✅ سيتم سحب جميع الملفات من GitHub تلقائياً
- ✅ كلما فعلت `git push`، سيتم التحديث تلقائياً
- ✅ لا حاجة لرفع يدوي بعد الآن!

---

## 📋 الخطوات التالية في Hostinger

بعد ربط Git:

1. **اذهب إلى**: `Advanced` → `Python App`
2. **أنشئ Python App** (إذا لم يكن موجوداً):
   - App Name: `nuzum`
   - Python Version: `3.11` أو `3.12`
   - App Root: `public_html/nuzum`
3. **في Requirements**: انسخ محتوى `hostinger_requirements.txt`
4. **في Start Command**:
   ```
   gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 main:app
   ```
5. **أنشئ قاعدة بيانات MySQL** في `Databases`
6. **أنشئ ملف `.env`** في File Manager مع:
   ```
   DATABASE_URL=mysql://username:password@localhost:3306/database_name
   SECRET_KEY=your_secret_key_here
   FLASK_ENV=production
   FLASK_DEBUG=False
   ```
7. **اضغط Restart** في Python App

---

## ✅ تم! افتح موقعك الآن

---

**ملاحظة**: هذه الطريقة أفضل لأن:
- ✅ تلقائية 100%
- ✅ آمنة (لا تحتاج بيانات FTP)
- ✅ سريعة
- ✅ سهلة التحديث لاحقاً

