# تشغيل سريع للمشروع

## ⚠️ Python مطلوب أولاً!

إذا كان Python مثبتاً، شغّل:
```powershell
.\install_and_run.ps1
```

إذا لم يكن Python مثبتاً، اتبع الخطوات في `كيفية_التشغيل.md`

## الإعداد السريع (بعد تثبيت Python)

```powershell
# 1. إنشاء وتفعيل البيئة الافتراضية
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. تثبيت المكتبات
pip install -r requirements.txt

# 3. إنشاء ملف .env (الحد الأدنى)
@"
DATABASE_URL=sqlite:///database/nuzum.db
SECRET_KEY=your_secret_key_here
FLASK_ENV=development
FLASK_DEBUG=True
"@ | Out-File -FilePath .env -Encoding utf8

# 4. تشغيل المشروع
python main.py
```

المشروع سيعمل على: **http://localhost:5000**

