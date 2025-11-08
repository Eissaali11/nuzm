# 📱 دليل إعداد API الدائم لتطبيق الأندرويد

> كيفية الحصول على رابط API دائم واستخدامه في تطبيق Flutter/Android

---

## 🎯 الهدف

تحويل تطبيق الأندرويد من استخدام رابط API مؤقت إلى رابط **دائم** يضمن استمرار الاتصال.

---

## 📋 الخطوات

### 1️⃣ نشر تطبيقك على Replit (Publishing)

#### أ. من لوحة تحكم Replit:
1. افتح مشروعك على Replit
2. اضغط على زر **"Publish"** أو **"Deploy"** في الأعلى
3. اختر **"Production Deployment"**
4. انتظر حتى تكتمل عملية النشر

#### ب. الدومين الدائم لنظام نُظم:

**الدومين المخصص (الأساسي):**
```
http://nuzum.site
```

**دومين Replit (البديل):**
```
https://eissahr.replit.app
```

---

### 2️⃣ تحديث كود Flutter/Dart

#### أ. افتح ملف `android_app_api_service.dart`

#### ب. عدّل قيم `ApiConfig`:

```dart
class ApiConfig {
  /// 🔗 الدومين المخصص لنظام نُظم
  static const String baseUrl = 'http://nuzum.site';
  
  /// 🔑 مفتاح API من لوحة التحكم
  static const String apiKey = 'test_location_key_2025';
  
  // ... باقي الإعدادات
}
```

#### ج. ملاحظة: تم تعيين الدومين مسبقاً

---

### 3️⃣ اختبار الاتصال

#### من تطبيق الأندرويد:

```dart
// اختبار الاتصال قبل بدء التتبع
void testApiConnection() async {
  final isConnected = await ApiService.testConnection();
  
  if (isConnected) {
    print('✅ API جاهز للاستخدام');
    // ابدأ تتبع الموقع
  } else {
    print('❌ تحقق من إعدادات API');
  }
}
```

#### من المتصفح (للتأكد):

افتح الرابط التالي في المتصفح:
```
http://nuzum.site/api/external/test
```

أو الدومين البديل:
```
https://eissahr.replit.app/api/external/test
```

**الاستجابة المتوقعة:**
```json
{
  "success": true,
  "message": "External API is working!",
  "endpoints": {
    "employee_location": "/api/external/employee-location [POST]"
  }
}
```

---

## 🔑 إعداد مفتاح API الآمن

### في Replit:

1. اذهب إلى **Secrets** (الأيقونة 🔒 في القائمة الجانبية)
2. أضف Secret جديد:
   - **Key**: `LOCATION_API_KEY`
   - **Value**: `your_secure_key_here_2025`
3. احفظ المفتاح

### في تطبيق Android:

#### الطريقة الآمنة (باستخدام BuildConfig):

1. في `build.gradle` (app level):
```gradle
android {
    defaultConfig {
        buildConfigField "String", "API_KEY", "\"your_secure_key_here_2025\""
        buildConfigField "String", "BASE_URL", "\"http://nuzum.site\""
    }
}
```

2. في كود Dart:
```dart
class ApiConfig {
  static const String baseUrl = String.fromEnvironment(
    'BASE_URL',
    defaultValue: 'http://nuzum.site',
  );
  
  static const String apiKey = String.fromEnvironment(
    'API_KEY',
    defaultValue: 'test_location_key_2025',
  );
}
```

---

## 📍 استخدام API في التطبيق

### مثال كامل - إرسال موقع:

```dart
import 'package:geolocator/geolocator.dart';
import 'api_service.dart';

class LocationTracker {
  final String jobNumber; // الرقم الوظيفي
  
  LocationTracker(this.jobNumber);
  
  /// بدء تتبع الموقع التلقائي
  Future<void> startTracking() async {
    // التحقق من الأذونات
    final permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      await Geolocator.requestPermission();
    }
    
    // إعدادات التتبع
    const locationSettings = LocationSettings(
      accuracy: LocationAccuracy.high,
      distanceFilter: 100, // إرسال كل 100 متر
      timeLimit: Duration(minutes: 15), // أو كل 15 دقيقة
    );
    
    // بدء التتبع
    Geolocator.getPositionStream(locationSettings: locationSettings)
        .listen((Position position) {
      sendCurrentLocation(position);
    });
  }
  
  /// إرسال موقع واحد
  Future<void> sendCurrentLocation(Position position) async {
    final response = await ApiService.sendLocation(
      jobNumber: jobNumber,
      latitude: position.latitude,
      longitude: position.longitude,
      accuracy: position.accuracy,
      notes: 'تحديث تلقائي',
    );
    
    if (response.success) {
      print('✅ تم إرسال الموقع: ${response.data?.employeeName}');
      print('🆔 رقم السجل: ${response.data?.locationId}');
    } else {
      print('❌ فشل الإرسال: ${response.error}');
      // يمكن حفظ الموقع محلياً وإعادة المحاولة لاحقاً
    }
  }
  
  /// إرسال موقع يدوي (عند الضغط على زر)
  Future<void> sendManualLocation() async {
    final position = await Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.high,
    );
    
    await sendCurrentLocation(position);
  }
}
```

### الاستخدام في Widget:

```dart
class LocationScreen extends StatefulWidget {
  @override
  _LocationScreenState createState() => _LocationScreenState();
}

class _LocationScreenState extends State<LocationScreen> {
  late LocationTracker tracker;
  bool isTracking = false;
  
  @override
  void initState() {
    super.initState();
    tracker = LocationTracker('EMP001'); // رقم الموظف
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('تتبع الموقع')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // زر اختبار الاتصال
            ElevatedButton.icon(
              icon: Icon(Icons.wifi),
              label: Text('اختبار الاتصال'),
              onPressed: () async {
                final connected = await ApiService.testConnection();
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(
                      connected ? '✅ الاتصال ناجح' : '❌ فشل الاتصال',
                    ),
                  ),
                );
              },
            ),
            
            SizedBox(height: 20),
            
            // زر بدء/إيقاف التتبع
            ElevatedButton.icon(
              icon: Icon(isTracking ? Icons.stop : Icons.play_arrow),
              label: Text(isTracking ? 'إيقاف التتبع' : 'بدء التتبع'),
              onPressed: () {
                setState(() {
                  if (isTracking) {
                    // إيقاف التتبع
                    isTracking = false;
                  } else {
                    // بدء التتبع
                    tracker.startTracking();
                    isTracking = true;
                  }
                });
              },
            ),
            
            SizedBox(height: 20),
            
            // زر إرسال يدوي
            ElevatedButton.icon(
              icon: Icon(Icons.send),
              label: Text('إرسال الموقع الحالي'),
              onPressed: () => tracker.sendManualLocation(),
            ),
          ],
        ),
      ),
    );
  }
}
```

---

## ⚙️ إعدادات متقدمة

### 1. التعامل مع الأخطاء وإعادة المحاولة

```dart
class LocationQueueManager {
  final List<PendingLocation> _queue = [];
  
  /// حفظ موقع فاشل للمحاولة لاحقاً
  void saveFailedLocation(String jobNumber, double lat, double lng) {
    _queue.add(PendingLocation(
      jobNumber: jobNumber,
      latitude: lat,
      longitude: lng,
      timestamp: DateTime.now(),
    ));
  }
  
  /// إعادة إرسال المواقع المعلقة
  Future<void> retryPendingLocations() async {
    for (var location in _queue.toList()) {
      final response = await ApiService.sendLocation(
        jobNumber: location.jobNumber,
        latitude: location.latitude,
        longitude: location.longitude,
      );
      
      if (response.success) {
        _queue.remove(location);
        print('✅ تم إرسال موقع معلق بنجاح');
      }
    }
  }
}

class PendingLocation {
  final String jobNumber;
  final double latitude;
  final double longitude;
  final DateTime timestamp;
  
  PendingLocation({
    required this.jobNumber,
    required this.latitude,
    required this.longitude,
    required this.timestamp,
  });
}
```

### 2. توفير استهلاك البطارية

```dart
const smartLocationSettings = LocationSettings(
  accuracy: LocationAccuracy.medium, // دقة متوسطة (توفير)
  distanceFilter: 200, // إرسال كل 200 متر
  timeLimit: Duration(minutes: 30), // كل 30 دقيقة
);

// إيقاف التتبع عند بطارية منخفضة
void checkBatteryAndTrack() async {
  final battery = await Battery().batteryLevel;
  
  if (battery < 15) {
    print('⚠️ بطارية منخفضة - تم إيقاف التتبع');
    stopTracking();
  }
}
```

---

## 🔧 استكشاف الأخطاء

### المشكلة: لا يعمل API

**الحلول:**
1. ✅ تأكد من نشر التطبيق على Replit (Published)
2. ✅ تحقق من الدومين في `ApiConfig.baseUrl`
3. ✅ اختبر الرابط في المتصفح: `your-domain/api/external/test`

### المشكلة: خطأ 401 (مفتاح خاطئ)

**الحلول:**
1. ✅ تحقق من مطابقة `ApiConfig.apiKey` مع `LOCATION_API_KEY` في Secrets
2. ✅ تأكد من عدم وجود مسافات إضافية في المفتاح

### المشكلة: خطأ 404 (موظف غير موجود)

**الحلول:**
1. ✅ تأكد من صحة `jobNumber` المُرسل
2. ✅ تحقق من وجود الموظف في قاعدة البيانات
3. ✅ راجع حقل `employee_id` في جدول الموظفين

---

## 📊 مراقبة الأداء

### في لوحة التحكم (Web Dashboard):

1. **صفحة تتبع المواقع**: `/employees/tracking-dashboard`
   - عرض جميع المواقع المستلمة
   - فلترة حسب القسم والموظف
   - تحديث تلقائي كل 30 ثانية

2. **تاريخ المواقع**: `/employees/<id>/track-history`
   - عرض مسار الموظف على الخريطة
   - إحصائيات تفصيلية
   - تصدير إلى PDF/Excel

3. **الدوائر الجغرافية**: `/geofences`
   - إدارة المناطق المحددة
   - إشعارات الدخول/الخروج
   - تقارير تحليلية

---

## 🎯 نصائح للإنتاج

### 1. الأمان
- ✅ غيّر مفتاح API الافتراضي
- ✅ استخدم HTTPS دائماً
- ✅ لا تحفظ المفتاح في Git

### 2. الأداء
- ✅ أرسل المواقع كل 15-30 دقيقة
- ✅ استخدم WorkManager للعمل في الخلفية
- ✅ وفّر استهلاك البطارية

### 3. الموثوقية
- ✅ احفظ المواقع محلياً قبل الإرسال
- ✅ أعد المحاولة عند الفشل
- ✅ تحقق من جودة الإشارة قبل الإرسال

---

## 📞 الدعم

للمساعدة والاستفسارات:
- 📧 راجع التوثيق الكامل في `LOCATION_API_DOCS.md`
- 🔧 افحص السجلات في لوحة تحكم Replit
- 📱 استخدم نقطة الاختبار للتحقق من الاتصال

---

**تم بواسطة**: نظام نُظم - إدارة شاملة للشركات السعودية 🇸🇦
