# دليل نشر مشروع نُظم على Hostinger

## 📋 المتطلبات

- حساب Hostinger مع Python App أو VPS
- قاعدة بيانات MySQL (متوفرة في Hostinger)
- Python 3.11 أو أحدث
- Domain name (اسم نطاق)

## 🚀 الطريقة الأولى: Python App في hPanel (موصى بها)

### الخطوة 1: إعداد Python App في hPanel

1. **سجل الدخول إلى hPanel**
2. **اذهب إلى**: `Advanced` → `Python App`
3. **أنشئ Python App جديد**:
   - **App Name**: `nuzum` (أو أي اسم تريده)
   - **Python Version**: `3.11` أو `3.12`
   - **App Root**: اختر المجلد الذي سترفع فيه الملفات (مثلاً: `public_html/nuzum`)

### الخطوة 2: رفع الملفات

#### باستخدام File Manager:
1. **اذهب إلى**: `Files` → `File Manager`
2. **انتقل إلى مجلد Python App** (مثلاً: `public_html/nuzum`)
3. **ارفع جميع ملفات المشروع** باستثناء:
   - `venv/` (مجلد البيئة الافتراضية)
   - `__pycache__/`
   - `*.pyc`
   - `.env.local` (استخدم `.env` للإنتاج)

#### باستخدام FTP:
```bash
# استخدم FileZilla أو أي عميل FTP
# ارفع الملفات إلى: /public_html/nuzum/
```

### الخطوة 3: إنشاء قاعدة البيانات MySQL

1. **اذهب إلى**: `Databases` → `MySQL Databases`
2. **أنشئ قاعدة بيانات جديدة**:
   - **Database Name**: `nuzum_db` (أو أي اسم)
   - **Database User**: `nuzum_user` (أو أي اسم)
   - **Password**: كلمة مرور قوية
   - **Host**: عادة `localhost` أو `127.0.0.1`
3. **احفظ المعلومات** (ستحتاجها لاحقاً)

### الخطوة 4: إعداد متغيرات البيئة

1. **في File Manager**، افتح ملف `.env` (أو أنشئه إذا لم يكن موجوداً)
2. **أضف المتغيرات التالية**:

```env
# قاعدة البيانات MySQL
DATABASE_URL=mysql://nuzum_user:your_password@localhost:3306/nuzum_db

# إعدادات Flask
SECRET_KEY=your_very_secret_key_here_change_this
SESSION_SECRET=your_session_secret_here
FLASK_ENV=production
FLASK_DEBUG=False

# إعدادات WhatsApp (اختياري)
WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_API_VERSION=v19.0

# إعدادات Twilio (اختياري)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_number

# إعدادات SendGrid (اختياري)
SENDGRID_API_KEY=your_sendgrid_key

# إعدادات Firebase (اختياري)
FIREBASE_API_KEY=your_firebase_key
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_APP_ID=your_firebase_app_id

# إعدادات التطبيق
APP_NAME=نُظم - نظام إدارة الموظفين
TZ=Asia/Riyadh

# إعدادات النشر
SERVER_NAME=yourdomain.com
PREFERRED_URL_SCHEME=https
```

### الخطوة 5: تثبيت المكتبات

1. **في hPanel**، اذهب إلى `Python App`
2. **اختر التطبيق** الذي أنشأته
3. **في قسم "Requirements"**، أضف محتوى `requirements.txt`:
   - افتح `requirements.txt` من المشروع
   - انسخ المحتوى
   - الصقه في حقل Requirements في hPanel
4. **احفظ التغييرات**

### الخطوة 6: إعداد ملف Start Command

في `Python App` → `Start Command`، أضف:

```bash
gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --max-requests 1000 --max-requests-jitter 50 main:app
```

أو إذا كان Hostinger يستخدم منفذ محدد:

```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 main:app
```

### الخطوة 7: إنشاء مجلدات مطلوبة

في File Manager، أنشئ المجلدات التالية:

```
database/
static/uploads/
static/uploads/employees/
static/uploads/vehicles/
```

### الخطوة 8: إنشاء جداول قاعدة البيانات

1. **في hPanel**، اذهب إلى `Python App`
2. **افتح Python Console** أو **Terminal**
3. **شغّل**:

```python
from app import app, db
with app.app_context():
    db.create_all()
    print("Database tables created successfully!")
```

### الخطوة 9: تشغيل التطبيق

1. **في Python App**، اضغط **"Restart"** أو **"Start"**
2. **تحقق من Logs** للتأكد من عدم وجود أخطاء

### الخطوة 10: ربط الدومين

1. **في Python App**، اضغط **"Add Domain"**
2. **أدخل الدومين** الخاص بك
3. **احفظ التغييرات**

---

## 🖥️ الطريقة الثانية: VPS (إذا كان لديك VPS من Hostinger)

### الخطوة 1: الاتصال بالخادم

```bash
ssh username@your-server-ip
```

### الخطوة 2: تثبيت المتطلبات

```bash
# تحديث النظام
sudo apt update && sudo apt upgrade -y

# تثبيت Python و pip
sudo apt install python3.11 python3.11-venv python3-pip -y

# تثبيت MySQL
sudo apt install mysql-server -y

# تثبيت Nginx
sudo apt install nginx -y
```

### الخطوة 3: رفع الملفات

```bash
# استخدم SCP أو Git
scp -r /path/to/project/* username@server:/var/www/nuzum/

# أو استخدم Git
cd /var/www/nuzum
git clone your-repository-url .
```

### الخطوة 4: إعداد البيئة الافتراضية

```bash
cd /var/www/nuzum
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### الخطوة 5: إعداد قاعدة البيانات

```bash
# إنشاء قاعدة بيانات
sudo mysql -u root -p
```

في MySQL:

```sql
CREATE DATABASE nuzum_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'nuzum_user'@'localhost' IDENTIFIED BY 'your_strong_password';
GRANT ALL PRIVILEGES ON nuzum_db.* TO 'nuzum_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### الخطوة 6: إعداد Systemd Service

```bash
sudo nano /etc/systemd/system/nuzum.service
```

أضف:

```ini
[Unit]
Description=Nuzum Employee Management System
After=network.target mysql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/nuzum
Environment="PATH=/var/www/nuzum/venv/bin"
ExecStart=/var/www/nuzum/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 120 --access-logfile - --error-logfile - main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### الخطوة 7: إعداد Nginx

```bash
sudo nano /etc/nginx/sites-available/nuzum
```

أضف:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    location /static {
        alias /var/www/nuzum/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /uploads {
        alias /var/www/nuzum/static/uploads;
        expires 7d;
    }
}
```

تفعيل الموقع:

```bash
sudo ln -s /etc/nginx/sites-available/nuzum /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### الخطوة 8: تشغيل الخدمة

```bash
sudo systemctl daemon-reload
sudo systemctl enable nuzum
sudo systemctl start nuzum
sudo systemctl status nuzum
```

### الخطوة 9: إعداد SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## ✅ التحقق من النشر

1. **افتح المتصفح** واذهب إلى: `https://yourdomain.com`
2. **تحقق من الصفحة الرئيسية**
3. **جرب تسجيل الدخول**:
   - البريد: `admin@nuzum.sa`
   - كلمة المرور: `admin123` (بعد إنشاء البيانات التجريبية)

---

## 🔧 استكشاف الأخطاء

### المشكلة: التطبيق لا يعمل
- **تحقق من Logs** في Python App
- **تحقق من Start Command**
- **تأكد من تثبيت جميع المكتبات**

### المشكلة: خطأ في قاعدة البيانات
- **تحقق من معلومات الاتصال** في `.env`
- **تأكد من أن قاعدة البيانات موجودة**
- **تحقق من صلاحيات المستخدم**

### المشكلة: Static files لا تعمل
- **تحقق من مسار `/static`**
- **تأكد من الصلاحيات** (755 للمجلدات)

### المشكلة: SSL لا يعمل
- **تحقق من إعدادات Nginx**
- **تأكد من ربط الدومين بشكل صحيح**

---

## 📝 ملاحظات مهمة

1. **لا ترفع ملف `.env.local`** - استخدم `.env` فقط
2. **لا ترفع مجلد `venv/`** - سيتم إنشاؤه تلقائياً
3. **تأكد من تغيير `SECRET_KEY`** في الإنتاج
4. **فعّل SSL** دائماً في الإنتاج
5. **قم بعمل نسخة احتياطية** من قاعدة البيانات بانتظام

---

## 🔄 التحديثات المستقبلية

بعد تحديث الكود:

1. **ارفع الملفات الجديدة**
2. **في Python App**: اضغط **"Restart"**
3. **أو في VPS**:
   ```bash
   sudo systemctl restart nuzum
   ```

---

## 📞 الدعم

إذا واجهت مشاكل:
1. راجع **Logs** في Python App
2. تحقق من **documentation** في Hostinger
3. راجع ملفات **cloudpanel_setup_guide.md** للمزيد من التفاصيل

