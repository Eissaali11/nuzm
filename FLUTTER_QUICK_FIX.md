# 🔧 إصلاح سريع لخطأ 404 في تطبيق Flutter

## المشكلة
```
❌ Primary server error: 404
❌ الخدمة غير موجودة
```

## الحل السريع ✅

### 1️⃣ افتح ملف `employee_api_service.dart` في تطبيق Flutter

### 2️⃣ ابحث عن هذا السطر:
```dart
static const String primaryUrl = 'http://nuzum.site/api/external/employee-complete-profile';
```

### 3️⃣ استبدله بهذا:
```dart
static const String primaryUrl = 'https://d72f2aef-918c-4148-9723-15870f8c7cf6-00-2c1ygyxvqoldk.riker.replit.dev/api/external/employee-complete-profile';
```

### 4️⃣ ابحث عن السطر الاحتياطي:
```dart
static const String backupUrl = 'https://eissahr.replit.app/api/external/employee-complete-profile';
```

### 5️⃣ استبدله بهذا:
```dart
static const String backupUrl = 'http://localhost:5000/api/external/employee-complete-profile';
```

---

## ✅ الكود الكامل المُحدث

```dart
class EmployeeApiService {
  // الروابط المُحدثة
  static const String primaryUrl = 'https://d72f2aef-918c-4148-9723-15870f8c7cf6-00-2c1ygyxvqoldk.riker.replit.dev/api/external/employee-complete-profile';
  static const String backupUrl = 'http://localhost:5000/api/external/employee-complete-profile';
  static const String apiKey = 'test_location_key_2025';
  
  // باقي الكود يبقى كما هو...
}
```

---

## 🧪 اختبار الاتصال

بعد التحديث، قم بإعادة تشغيل التطبيق:

```bash
flutter clean
flutter pub get
flutter run
```

يجب أن ترى:
```
✅ الاتصال ناجح!
✅ تم جلب البيانات بنجاح
```

---

## 📝 ملاحظات مهمة

- ✅ استخدم **HTTPS** وليس HTTP
- ✅ الدومين الحالي صالح للتطوير والاختبار
- ✅ جميع البيانات حقيقية وليست وهمية
- ✅ مفتاح API: `test_location_key_2025`

---

## 🆘 إذا استمرت المشكلة

تحقق من:
1. اتصال الإنترنت
2. صلاحيات الشبكة في التطبيق
3. أن مفتاح API صحيح: `test_location_key_2025`
4. أن رقم الموظف موجود في قاعدة البيانات

---

**تم التحديث**: 9 نوفمبر 2025
