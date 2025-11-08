# 🚀 البدء السريع - تطبيق تتبع الموظفين

> دليل سريع لتشغيل API واستخدامه في 5 دقائق

---

## 📱 للمطورين - استخدام API في التطبيق

### الخطوة 1: انسخ ملف الخدمة
انسخ ملف `android_app_api_service.dart` إلى مشروع Flutter الخاص بك.

### الخطوة 2: الدومينات الجاهزة ✅
```dart
// الدومينات محددة مسبقاً:
baseUrl = 'http://nuzum.site'           // الأساسي
// أو
baseUrl = 'https://eissahr.replit.app'  // البديل
```

### الخطوة 3: الاستخدام

```dart
// اختبار الاتصال
final connected = await ApiService.testConnection();

// إرسال الموقع
final response = await ApiService.sendLocation(
  jobNumber: 'EMP001',
  latitude: 24.7136,
  longitude: 46.6753,
);

if (response.success) {
  print('✅ تم الإرسال: ${response.data?.employeeName}');
}
```

---

## 🧪 اختبار سريع

### من المتصفح:

**1. اختبار API:**
```
http://nuzum.site/api/external/test
```

**2. صفحة الاختبار التفاعلية:**
افتح ملف `test_location_api.html` في المتصفح

### باستخدام cURL:

```bash
# اختبار الاتصال
curl http://nuzum.site/api/external/test

# إرسال موقع تجريبي
curl -X POST http://nuzum.site/api/external/employee-location \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "test_location_key_2025",
    "job_number": "EMP001",
    "latitude": 24.7136,
    "longitude": 46.6753,
    "accuracy": 10.5
  }'
```

---

## 📊 عرض البيانات في لوحة التحكم

### 1. تتبع حي مباشر:
```
http://nuzum.site/employees/tracking-dashboard
```

### 2. تاريخ موظف محدد:
```
http://nuzum.site/employees/<رقم_الموظف>/track-history
```

### 3. إدارة الدوائر الجغرافية:
```
http://nuzum.site/geofences
```

---

## 🔑 المفاتيح والإعدادات

### مفتاح API الحالي:
```
test_location_key_2025
```

### لتغيير المفتاح:
1. اذهب إلى Replit Secrets (🔒)
2. عدّل `LOCATION_API_KEY`
3. حدّث التطبيق بالمفتاح الجديد

---

## 📝 البيانات المطلوبة

| الحقل | إلزامي | مثال |
|------|--------|------|
| api_key | ✅ | test_location_key_2025 |
| job_number | ✅ | EMP001 |
| latitude | ✅ | 24.7136 |
| longitude | ✅ | 46.6753 |
| accuracy | ❌ | 10.5 |
| notes | ❌ | تحديث تلقائي |

---

## ✅ أكواد الاستجابة

| الكود | المعنى |
|------|--------|
| 200 | ✅ نجح - تم حفظ الموقع |
| 400 | ❌ بيانات ناقصة أو خاطئة |
| 401 | 🔒 مفتاح API خاطئ |
| 404 | 👤 موظف غير موجود |
| 500 | ⚙️ خطأ في الخادم |

---

## 🎯 أمثلة عملية

### Python (للاختبار):
```python
import requests

url = "http://nuzum.site/api/external/employee-location"
data = {
    "api_key": "test_location_key_2025",
    "job_number": "EMP001",
    "latitude": 24.7136,
    "longitude": 46.6753
}

response = requests.post(url, json=data)
print(response.json())
```

### JavaScript (للويب):
```javascript
const response = await fetch('http://nuzum.site/api/external/employee-location', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    api_key: 'test_location_key_2025',
    job_number: 'EMP001',
    latitude: 24.7136,
    longitude: 46.6753
  })
});

const data = await response.json();
console.log(data);
```

---

## 🔧 حل المشاكل السريع

### المشكلة: لا يعمل API
**الحل:**
1. جرّب الدومين البديل: `https://eissahr.replit.app`
2. تأكد من الإنترنت
3. افتح رابط الاختبار في المتصفح

### المشكلة: موظف غير موجود (404)
**الحل:**
1. تحقق من الرقم الوظيفي في قاعدة البيانات
2. تأكد من تطابق `job_number` مع `employee_id`

### المشكلة: مفتاح خاطئ (401)
**الحل:**
استخدم المفتاح الصحيح: `test_location_key_2025`

---

## 📞 مساعدة إضافية

- 📖 **التوثيق الكامل**: `LOCATION_API_DOCS.md`
- 🔧 **دليل الإعداد**: `API_SETUP_GUIDE.md`
- 🧪 **صفحة الاختبار**: `test_location_api.html`

---

**نظام نُظم** - إدارة شاملة للموظفين 🇸🇦
