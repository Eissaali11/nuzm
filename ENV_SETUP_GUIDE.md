# دليل إعداد ملف .env

## إنشاء ملف .env

قم بإنشاء ملف `.env` في المجلد الرئيسي للمشروع واملأه بالمتغيرات التالية:

```env
# ============================================
# إعدادات قاعدة البيانات
# ============================================
# للتطوير المحلي (SQLite):
DATABASE_URL=sqlite:///database/nuzum.db

# للإنتاج (MySQL):
# DATABASE_URL=mysql://username:password@localhost:3306/database_name

# للإنتاج (PostgreSQL):
# DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# ============================================
# إعدادات Flask
# ============================================
SECRET_KEY=your_secret_key_here_change_this_in_production
SESSION_SECRET=your_session_secret_key_here_change_this
FLASK_ENV=development
FLASK_DEBUG=True

# ============================================
# إعدادات WhatsApp Cloud API (اختياري)
# ============================================
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_API_VERSION=v19.0

# ============================================
# إعدادات Twilio (اختياري)
# ============================================
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# ============================================
# إعدادات SendGrid (اختياري)
# ============================================
SENDGRID_API_KEY=your_sendgrid_api_key

# ============================================
# إعدادات Firebase (اختياري)
# ============================================
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_APP_ID=your_firebase_app_id
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_STORAGE_BUCKET=your_project.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=your_sender_id

# ============================================
# إعدادات Location API (للتطبيق المحمول)
# ============================================
LOCATION_API_KEY=test_location_key_2025

# ============================================
# إعدادات OpenAI (إذا كان مستخدماً)
# ============================================
OPENAI_API_KEY=your_openai_api_key

# ============================================
# إعدادات التطبيق العامة
# ============================================
APP_NAME=نُظم - نظام إدارة الموظفين
APP_VERSION=1.0.0
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=52428800

# المنطقة الزمنية
TZ=Asia/Riyadh
```

## ملاحظات مهمة

1. **المتغيرات الإلزامية**: فقط `DATABASE_URL` و `SECRET_KEY` مطلوبان للبدء
2. **المتغيرات الاختيارية**: باقي المتغيرات اختيارية ويمكن تركها فارغة إذا لم تكن تستخدم الميزات المرتبطة بها
3. **WhatsApp**: إذا لم تقم بإعداد `WHATSAPP_ACCESS_TOKEN` و `WHATSAPP_PHONE_NUMBER_ID`، سيتم تعطيل ميزات واتساب تلقائياً
4. **الأمان**: تأكد من تغيير `SECRET_KEY` في بيئة الإنتاج

## للبدء السريع

أدنى إعداد مطلوب:

```env
DATABASE_URL=sqlite:///database/nuzum.db
SECRET_KEY=change_this_to_a_random_string
FLASK_ENV=development
FLASK_DEBUG=True
```

