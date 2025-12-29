#!/bin/bash
# سكريبت بدء التطبيق على Hostinger

# تفعيل البيئة الافتراضية
source venv/bin/activate

# تشغيل Gunicorn
# Hostinger عادة يستخدم متغير PORT أو منفذ محدد
if [ -n "$PORT" ]; then
    gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --max-requests 1000 --max-requests-jitter 50 main:app
else
    # إذا لم يكن PORT محدد، استخدم 5000
    gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 --max-requests 1000 --max-requests-jitter 50 main:app
fi

