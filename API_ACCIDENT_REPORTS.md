# API Documentation - Vehicle Accident Reports (تقارير حوادث المركبات)

## نظرة عامة
واجهة برمجية (API) لإرسال تقارير حوادث المركبات من تطبيق Flutter إلى نظام نُظم، مع نظام مراجعة وموافقة من قبل إدارة العمليات.

## المتطلبات
- تطبيق Flutter
- رمز JWT صالح للمصادقة
- صلاحيات لإرسال تقارير الحوادث

## Base URL
```
Production: https://nuzum.site
Development: http://localhost:5000
```

## المصادقة (Authentication)
جميع endpoints تتطلب JWT token في header:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

## Endpoints

### 1. إرسال تقرير حادث جديد

**Endpoint:** `POST /api/v1/accident-reports/submit`

**Content-Type:** `multipart/form-data`

**الحقول المطلوبة:**

| الحقل | النوع | مطلوب | الوصف |
|------|------|------|------|
| vehicle_id | integer | ✅ | رقم المركبة |
| accident_date | string (YYYY-MM-DD) | ✅ | تاريخ الحادث |
| driver_name | string | ✅ | اسم السائق |
| description | string | ✅ | وصف الحادث |
| driver_phone | string | ✅ | رقم الهاتف المربوط بأبشر |
| driver_id_image | file | ✅ | صورة الهوية (JPG, PNG, HEIC) |
| driver_license_image | file | ✅ | صورة الرخصة (JPG, PNG, HEIC) |
| accident_report_file | file | ✅ | تقرير الحادث (PDF أو صورة) |

**الحقول الاختيارية:**

| الحقل | النوع | الوصف |
|------|------|------|
| accident_time | string (HH:MM) | وقت الحادث (24 ساعة) |
| accident_images[] | files | صور الحادث (متعددة، حتى 10 صور) |
| location | string | موقع الحادث |
| latitude | decimal | خط العرض |
| longitude | decimal | خط الطول |
| severity | string | الخطورة: "بسيط" / "متوسط" / "خطير" |
| vehicle_condition | string | حالة المركبة بعد الحادث |
| police_report | boolean | هل يوجد محضر شرطة؟ |
| police_report_number | string | رقم محضر الشرطة |
| notes | string | ملاحظات إضافية |

**أنواع الملفات المسموحة:**
- الصور: PNG, JPG, JPEG, HEIC, HEIF
- المستندات: PDF, PNG, JPG, JPEG, HEIC, HEIF
- الحجم الأقصى: 50 MB لكل ملف

**مثال على الطلب (cURL):**
```bash
curl -X POST "https://nuzum.site/api/v1/accident-reports/submit" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "vehicle_id=123" \
  -F "accident_date=2025-11-25" \
  -F "accident_time=14:30" \
  -F "driver_name=أحمد محمد" \
  -F "driver_phone=0501234567" \
  -F "description=حادث تصادم بسيط" \
  -F "driver_id_image=@id_card.jpg" \
  -F "driver_license_image=@license.jpg" \
  -F "accident_report_file=@report.pdf" \
  -F "accident_images[]=@accident1.jpg" \
  -F "accident_images[]=@accident2.jpg" \
  -F "latitude=24.7136" \
  -F "longitude=46.6753" \
  -F "severity=متوسط"
```

**استجابة ناجحة (200):**
```json
{
  "success": true,
  "message": "تم إرسال تقرير الحادث بنجاح وفي انتظار المراجعة",
  "accident_id": 456,
  "review_status": "pending",
  "uploaded_images": 2,
  "uploaded_files": {
    "driver_id_image": true,
    "driver_license_image": true,
    "accident_report_file": true
  }
}
```

**أخطاء محتملة:**

**401 - Unauthorized:**
```json
{
  "error": "Unauthorized",
  "message": "Missing or invalid JWT token"
}
```

**400 - Bad Request:**
```json
{
  "error": "Missing required field",
  "message": "الرجاء تقديم vehicle_id"
}
```

**404 - Not Found:**
```json
{
  "error": "Vehicle not found",
  "message": "المركبة غير موجودة"
}
```

**413 - File Too Large:**
```json
{
  "error": "File too large",
  "message": "حجم الملف يتجاوز 50 ميجابايت"
}
```

## مثال كامل باستخدام Flutter/Dart

```dart
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:path/path.dart';

class AccidentReportService {
  final String baseUrl = 'https://nuzum.site';
  final String jwtToken;

  AccidentReportService({required this.jwtToken});

  Future<Map<String, dynamic>> submitAccidentReport({
    required int vehicleId,
    required String accidentDate,
    required String driverName,
    required String driverPhone,
    required String description,
    required File driverIdImage,
    required File driverLicenseImage,
    required File accidentReportFile,
    String? accidentTime,
    List<File>? accidentImages,
    String? location,
    double? latitude,
    double? longitude,
    String? severity,
    String? vehicleCondition,
    bool? policeReport,
    String? policeReportNumber,
    String? notes,
  }) async {
    var request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/api/v1/accident-reports/submit'),
    );

    // إضافة headers
    request.headers['Authorization'] = 'Bearer $jwtToken';

    // إضافة الحقول المطلوبة
    request.fields['vehicle_id'] = vehicleId.toString();
    request.fields['accident_date'] = accidentDate;
    request.fields['driver_name'] = driverName;
    request.fields['driver_phone'] = driverPhone;
    request.fields['description'] = description;

    // إضافة الحقول الاختيارية
    if (accidentTime != null) request.fields['accident_time'] = accidentTime;
    if (location != null) request.fields['location'] = location;
    if (latitude != null) request.fields['latitude'] = latitude.toString();
    if (longitude != null) request.fields['longitude'] = longitude.toString();
    if (severity != null) request.fields['severity'] = severity;
    if (vehicleCondition != null) request.fields['vehicle_condition'] = vehicleCondition;
    if (policeReport != null) request.fields['police_report'] = policeReport.toString();
    if (policeReportNumber != null) request.fields['police_report_number'] = policeReportNumber;
    if (notes != null) request.fields['notes'] = notes;

    // إضافة صورة الهوية
    request.files.add(await http.MultipartFile.fromPath(
      'driver_id_image',
      driverIdImage.path,
      filename: basename(driverIdImage.path),
    ));

    // إضافة صورة الرخصة
    request.files.add(await http.MultipartFile.fromPath(
      'driver_license_image',
      driverLicenseImage.path,
      filename: basename(driverLicenseImage.path),
    ));

    // إضافة تقرير الحادث
    request.files.add(await http.MultipartFile.fromPath(
      'accident_report_file',
      accidentReportFile.path,
      filename: basename(accidentReportFile.path),
    ));

    // إضافة صور الحادث
    if (accidentImages != null && accidentImages.isNotEmpty) {
      for (var image in accidentImages) {
        request.files.add(await http.MultipartFile.fromPath(
          'accident_images[]',
          image.path,
          filename: basename(image.path),
        ));
      }
    }

    // إرسال الطلب
    try {
      var response = await request.send();
      var responseBody = await response.stream.bytesToString();
      
      if (response.statusCode == 200) {
        return {
          'success': true,
          'data': jsonDecode(responseBody),
        };
      } else {
        return {
          'success': false,
          'error': jsonDecode(responseBody),
        };
      }
    } catch (e) {
      return {
        'success': false,
        'error': 'Network error: $e',
      };
    }
  }
}

// مثال على الاستخدام
void main() async {
  var service = AccidentReportService(jwtToken: 'YOUR_JWT_TOKEN');
  
  var result = await service.submitAccidentReport(
    vehicleId: 123,
    accidentDate: '2025-11-25',
    accidentTime: '14:30',
    driverName: 'أحمد محمد',
    driverPhone: '0501234567',
    description: 'حادث تصادم بسيط في شارع الملك فهد',
    driverIdImage: File('/path/to/id_card.jpg'),
    driverLicenseImage: File('/path/to/license.jpg'),
    accidentReportFile: File('/path/to/report.pdf'),
    accidentImages: [
      File('/path/to/accident1.jpg'),
      File('/path/to/accident2.jpg'),
    ],
    latitude: 24.7136,
    longitude: 46.6753,
    severity: 'متوسط',
  );

  if (result['success']) {
    print('تم إرسال التقرير بنجاح!');
    print('رقم التقرير: ${result['data']['accident_id']}');
  } else {
    print('فشل الإرسال: ${result['error']}');
  }
}
```

## دورة عمل المراجعة

1. **الإرسال (Submit)**: السائق يرسل التقرير من التطبيق → `review_status = 'pending'`
2. **قيد المراجعة (Under Review)**: إدارة العمليات تبدأ المراجعة → `review_status = 'under_review'`
3. **الموافقة (Approved)**: تمت الموافقة → `review_status = 'approved'` → يُضاف للسجل الدائم
4. **الرفض (Rejected)**: تم الرفض → `review_status = 'rejected'` → مع ملاحظات

## حالات التقرير (Review Status)

| الحالة | الوصف | اللون |
|-------|------|------|
| pending | في انتظار المراجعة | أصفر |
| under_review | قيد المراجعة | أزرق |
| approved | تمت الموافقة | أخضر |
| rejected | مرفوض | أحمر |

## ملاحظات مهمة

### ضغط الصور
- يتم ضغط الصور تلقائياً على السيرفر
- الحد الأقصى: 1920×1920 بكسل
- الجودة: 85%
- التنسيق النهائي: JPEG

### التخزين
- يتم تخزين الملفات في: `static/uploads/accidents/{accident_id}/`
- كل تقرير له مجلد منفصل
- المسارات النسبية تُحفظ في قاعدة البيانات

### الأمان
- جميع الطلبات تتطلب JWT صالح
- التحقق من نوع وحجم الملفات
- التحقق من وجود المركبة
- التحقق من صلاحيات الموظف

### معالجة الأخطاء
```dart
try {
  var result = await service.submitAccidentReport(...);
  if (result['success']) {
    // النجاح
    showSuccessMessage(result['data']['message']);
  } else {
    // الفشل
    showErrorMessage(result['error']['message']);
  }
} catch (e) {
  // خطأ في الشبكة
  showErrorMessage('تأكد من الاتصال بالإنترنت');
}
```

## معلومات الاتصال والدعم
- الموقع: https://nuzum.site
- البريد الإلكتروني: support@nuzum.site
- الوثائق: https://nuzum.site/docs

---

**آخر تحديث:** 25 نوفمبر 2025  
**الإصدار:** 1.0.0
