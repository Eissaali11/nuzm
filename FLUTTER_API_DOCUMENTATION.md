# 📱 Flutter API - دليل تطبيق نُظم
## توثيق كامل لجميع endpoints طلبات الموظفين

**Base URL:** `https://your-domain.replit.app/api/v1`

**Authentication:** جميع الطلبات تتطلب JWT Token في الـ Header:
```dart
headers: {
  'Authorization': 'Bearer $jwtToken'
}
```

---

## 📋 فهرس المحتويات
1. [المصادقة (Login)](#1-المصادقة-login)
2. [طلب فاتورة (Invoice)](#2-طلب-فاتورة-invoice)
3. [طلب غسيل سيارة (Car Wash)](#3-طلب-غسيل-سيارة-car-wash)
4. [طلب فحص وتوثيق سيارة (Car Inspection)](#4-طلب-فحص-وتوثيق-سيارة-car-inspection)
5. [طلب سلفة (Advance Payment)](#5-طلب-سلفة-advance-payment)
6. [رفع الملفات (Upload Files)](#6-رفع-الملفات-upload-files)
7. [حذف طلب (Delete Request)](#7-حذف-طلب-delete-request)

---

## 1. المصادقة (Login)

### Endpoint
```
POST /auth/login-mobile
```

### Request Body (JSON)
```json
{
  "employee_id": "1910",
  "national_id": "2469288936"
}
```

### Response
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "employee": {
    "id": 180,
    "name": "محمد أحمد",
    "employee_id": "1910",
    "department": "قسم المبيعات"
  }
}
```

### Dart Example
```dart
Future<String> login(String employeeId, String nationalId) async {
  final response = await dio.post(
    '/auth/login-mobile',
    data: {
      'employee_id': employeeId,
      'national_id': nationalId,
    },
  );
  
  if (response.data['success']) {
    return response.data['token'];
  }
  throw Exception(response.data['message']);
}
```

---

## 2. طلب فاتورة (Invoice)

### Endpoint
```
POST /requests/create-invoice
```

### Request (FormData)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `vendor_name` | String | ✅ نعم | اسم المورد / المحل |
| `amount` | String | ✅ نعم | المبلغ (رقم) |
| `invoice_image` | File | ✅ نعم | صورة الفاتورة |

**⚠️ مهم:** اسم حقل الصورة **يجب** أن يكون `invoice_image` (وليس `image`)

### Supported Image Formats
- JPG, JPEG, PNG, PDF
- الحد الأقصى: **10 MB**

### Response
```json
{
  "success": true,
  "message": "تم رفع الفاتورة بنجاح",
  "data": {
    "request_id": 124,
    "type": "invoice",
    "status": "pending",
    "vendor_name": "محل الأجهزة",
    "amount": 500.0
  }
}
```

### Dart Example
```dart
Future<void> createInvoice({
  required String vendorName,
  required double amount,
  required File imageFile,
}) async {
  // ضغط الصورة قبل الرفع
  final compressedImage = await compressImage(imageFile);
  
  final formData = FormData.fromMap({
    'vendor_name': vendorName,
    'amount': amount.toString(),
    'invoice_image': await MultipartFile.fromFile(
      compressedImage.path,
      filename: 'invoice_${DateTime.now().millisecondsSinceEpoch}.jpg',
    ),
  });

  final response = await dio.post(
    '/requests/create-invoice',
    data: formData,
    options: Options(
      headers: {'Authorization': 'Bearer $token'},
    ),
  );

  if (!response.data['success']) {
    throw Exception(response.data['message']);
  }
}
```

---

## 3. طلب غسيل سيارة (Car Wash)

### Endpoint
```
POST /requests/create-car-wash
```

### Request (FormData)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `vehicle_id` | String | ✅ نعم | رقم السيارة في النظام |
| `service_type` | String | ✅ نعم | نوع الخدمة: `normal`, `polish`, `full_clean` |
| `photo_plate` | File | ✅ نعم | صورة اللوحة |
| `photo_front` | File | ✅ نعم | صورة أمامية |
| `photo_back` | File | ✅ نعم | صورة خلفية |
| `photo_right_side` | File | ✅ نعم | صورة جانب أيمن |
| `photo_left_side` | File | ✅ نعم | صورة جانب أيسر |
| `requested_date` | String | ❌ اختياري | التاريخ المطلوب (YYYY-MM-DD) |
| `notes` | String | ❌ اختياري | ملاحظات إضافية |

**⚠️ أسماء الصور الصحيحة:**
```dart
✅ 'photo_plate'       // صحيح
✅ 'photo_front'       // صحيح
✅ 'photo_back'        // صحيح
✅ 'photo_right_side'  // صحيح
✅ 'photo_left_side'   // صحيح

❌ 'plate_image'       // خطأ
❌ 'front_image'       // خطأ
❌ 'back_image'        // خطأ
```

### Service Types
- `normal` - غسيل عادي
- `polish` - تلميع
- `full_clean` - تنظيف شامل

### Supported Formats
- JPG, JPEG, PNG
- الحد الأقصى لكل صورة: **10 MB**

### Response
```json
{
  "success": true,
  "message": "تم إنشاء طلب الغسيل بنجاح",
  "data": {
    "request_id": 125,
    "type": "car_wash",
    "status": "pending",
    "vehicle_plate": "ABC-1234"
  }
}
```

### Dart Example
```dart
Future<void> createCarWashRequest({
  required int vehicleId,
  required String serviceType,
  required File platePhoto,
  required File frontPhoto,
  required File backPhoto,
  required File rightPhoto,
  required File leftPhoto,
  String? requestedDate,
  String? notes,
}) async {
  // ضغط جميع الصور
  final compressedPlate = await compressImage(platePhoto);
  final compressedFront = await compressImage(frontPhoto);
  final compressedBack = await compressImage(backPhoto);
  final compressedRight = await compressImage(rightPhoto);
  final compressedLeft = await compressImage(leftPhoto);

  final formData = FormData.fromMap({
    'vehicle_id': vehicleId.toString(),
    'service_type': serviceType,
    'photo_plate': await MultipartFile.fromFile(
      compressedPlate.path,
      filename: 'plate_${DateTime.now().millisecondsSinceEpoch}.jpg',
    ),
    'photo_front': await MultipartFile.fromFile(
      compressedFront.path,
      filename: 'front_${DateTime.now().millisecondsSinceEpoch}.jpg',
    ),
    'photo_back': await MultipartFile.fromFile(
      compressedBack.path,
      filename: 'back_${DateTime.now().millisecondsSinceEpoch}.jpg',
    ),
    'photo_right_side': await MultipartFile.fromFile(
      compressedRight.path,
      filename: 'right_${DateTime.now().millisecondsSinceEpoch}.jpg',
    ),
    'photo_left_side': await MultipartFile.fromFile(
      compressedLeft.path,
      filename: 'left_${DateTime.now().millisecondsSinceEpoch}.jpg',
    ),
    if (requestedDate != null) 'requested_date': requestedDate,
    if (notes != null) 'notes': notes,
  });

  final response = await dio.post(
    '/requests/create-car-wash',
    data: formData,
    options: Options(
      headers: {'Authorization': 'Bearer $token'},
    ),
  );

  if (!response.data['success']) {
    throw Exception(response.data['message']);
  }
}
```

---

## 4. طلب فحص وتوثيق سيارة (Car Inspection)

### ⚡ هذا الطلب يتم على مرحلتين:

### **المرحلة 1: إنشاء الطلب**

#### Endpoint
```
POST /requests/create-car-inspection
```

#### Request Body (JSON)
```json
{
  "vehicle_id": 456,
  "inspection_type": "delivery",
  "description": "وصف الفحص (اختياري)"
}
```

#### Inspection Types
- `delivery` - فحص تسليم
- `receipt` - فحص استلام

#### Response
```json
{
  "success": true,
  "message": "تم إنشاء طلب الفحص بنجاح",
  "data": {
    "request_id": 126,
    "type": "car_inspection",
    "status": "pending",
    "inspection_type": "delivery",
    "inspection_type_ar": "فحص تسليم",
    "vehicle_plate": "ABC-1234",
    "upload_instructions": {
      "max_images": 20,
      "max_videos": 3,
      "max_image_size_mb": 10,
      "max_video_size_mb": 500,
      "supported_formats": {
        "images": ["jpg", "jpeg", "png", "heic"],
        "videos": ["mp4", "mov"]
      },
      "upload_endpoint": "/api/v1/requests/126/upload"
    }
  }
}
```

### **المرحلة 2: رفع الصور والفيديوهات**

#### Endpoint
```
POST /requests/{request_id}/upload
```

#### Request (FormData)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `files` | File[] | ✅ نعم | قائمة الملفات (صور أو فيديو) |

**ملاحظات مهمة:**
- يمكن رفع **حتى 20 صورة**
- يمكن رفع **حتى 3 فيديوهات**
- حجم الصورة: **حتى 10 MB**
- حجم الفيديو: **حتى 500 MB**

#### Supported Formats
**صور:** JPG, JPEG, PNG, HEIC  
**فيديو:** MP4, MOV

#### Response
```json
{
  "success": true,
  "uploaded_files": [
    {
      "filename": "inspection_video.mp4",
      "drive_url": "https://drive.google.com/file/d/...",
      "file_id": "1A2B3C4D5E"
    },
    {
      "filename": "damage_photo.jpg",
      "drive_url": "https://drive.google.com/file/d/...",
      "file_id": "6F7G8H9I0J"
    }
  ],
  "google_drive_folder_url": "https://drive.google.com/drive/folders/...",
  "message": "تم رفع 2 ملف بنجاح إلى Google Drive"
}
```

### Dart Example
```dart
// المرحلة 1: إنشاء الطلب
Future<int> createCarInspection({
  required int vehicleId,
  required String inspectionType, // 'delivery' or 'receipt'
  String? description,
}) async {
  final response = await dio.post(
    '/requests/create-car-inspection',
    data: {
      'vehicle_id': vehicleId,
      'inspection_type': inspectionType,
      if (description != null) 'description': description,
    },
    options: Options(
      headers: {'Authorization': 'Bearer $token'},
    ),
  );

  if (response.data['success']) {
    return response.data['data']['request_id'];
  }
  throw Exception(response.data['message']);
}

// المرحلة 2: رفع الملفات
Future<void> uploadInspectionFiles({
  required int requestId,
  required List<File> files, // صور وفيديوهات
}) async {
  final formData = FormData();

  for (var file in files) {
    final isVideo = file.path.toLowerCase().endsWith('.mp4') || 
                   file.path.toLowerCase().endsWith('.mov');
    
    File processedFile = file;
    
    // ضغط الصور فقط (الفيديو يُرفع كما هو)
    if (!isVideo) {
      processedFile = await compressImage(file);
    }

    formData.files.add(MapEntry(
      'files',
      await MultipartFile.fromFile(
        processedFile.path,
        filename: basename(processedFile.path),
      ),
    ));
  }

  final response = await dio.post(
    '/requests/$requestId/upload',
    data: formData,
    options: Options(
      headers: {'Authorization': 'Bearer $token'},
    ),
    onSendProgress: (sent, total) {
      print('Progress: ${(sent / total * 100).toStringAsFixed(0)}%');
    },
  );

  if (!response.data['success']) {
    throw Exception(response.data['message']);
  }
}

// الاستخدام الكامل
Future<void> submitCarInspectionWithMedia({
  required int vehicleId,
  required String inspectionType,
  required List<File> mediaFiles,
  String? description,
}) async {
  try {
    // 1. إنشاء الطلب
    final requestId = await createCarInspection(
      vehicleId: vehicleId,
      inspectionType: inspectionType,
      description: description,
    );

    // 2. رفع الملفات
    await uploadInspectionFiles(
      requestId: requestId,
      files: mediaFiles,
    );

    print('✅ تم إنشاء طلب الفحص ورفع الملفات بنجاح');
  } catch (e) {
    print('❌ خطأ: $e');
    rethrow;
  }
}
```

---

## 5. طلب سلفة (Advance Payment)

### Endpoint
```
POST /requests/create-advance-payment
```

### Request Body (JSON)
```json
{
  "amount": 5000,
  "reason": "سبب طلب السلفة",
  "installments": 10
}
```

### Response
```json
{
  "success": true,
  "message": "تم إنشاء طلب السلفة بنجاح",
  "data": {
    "request_id": 127,
    "type": "advance_payment",
    "status": "pending",
    "amount": 5000.0,
    "installments": 10,
    "installment_amount": 500.0
  }
}
```

### Dart Example
```dart
Future<void> createAdvancePayment({
  required double amount,
  required String reason,
  int? installments,
}) async {
  final response = await dio.post(
    '/requests/create-advance-payment',
    data: {
      'amount': amount,
      'reason': reason,
      if (installments != null) 'installments': installments,
    },
    options: Options(
      headers: {'Authorization': 'Bearer $token'},
    ),
  );

  if (!response.data['success']) {
    throw Exception(response.data['message']);
  }
}
```

---

## 6. رفع الملفات (Upload Files)

### استخدام عام لرفع ملفات إضافية

#### Endpoint
```
POST /requests/{request_id}/upload
```

#### Request (FormData)
```dart
FormData.fromMap({
  'files': [
    await MultipartFile.fromFile(file1.path),
    await MultipartFile.fromFile(file2.path),
  ]
})
```

#### Supported File Types
- **صور:** PNG, JPG, JPEG, HEIC
- **فيديو:** MP4, MOV, AVI
- **مستندات:** PDF

#### Size Limits
- حجم الملف الواحد: **حتى 500 MB**

---

## 7. حذف طلب (Delete Request)

### Endpoint
```
DELETE /requests/{request_id}
```

### Response
```json
{
  "success": true,
  "message": "تم حذف الطلب بنجاح"
}
```

### Dart Example
```dart
Future<void> deleteRequest(int requestId) async {
  final response = await dio.delete(
    '/requests/$requestId',
    options: Options(
      headers: {'Authorization': 'Bearer $token'},
    ),
  );

  if (!response.data['success']) {
    throw Exception(response.data['message']);
  }
}
```

---

## 🛠️ Utility Functions

### ضغط الصور (Image Compression)
```dart
import 'package:flutter_image_compress/flutter_image_compress.dart';

Future<File> compressImage(File file) async {
  final dir = await getTemporaryDirectory();
  final targetPath = '${dir.path}/compressed_${DateTime.now().millisecondsSinceEpoch}.jpg';

  final result = await FlutterImageCompress.compressAndGetFile(
    file.absolute.path,
    targetPath,
    quality: 70,
    minWidth: 1024,
    minHeight: 1024,
  );

  return File(result!.path);
}
```

### معالجة الأخطاء (Error Handling)
```dart
Future<void> handleApiCall(Future<void> Function() apiCall) async {
  try {
    await apiCall();
  } on DioException catch (e) {
    if (e.response?.statusCode == 400) {
      final message = e.response?.data['message'] ?? 'خطأ في البيانات';
      throw Exception(message);
    } else if (e.response?.statusCode == 401) {
      // إعادة المصادقة
      throw Exception('انتهت صلاحية الجلسة، الرجاء تسجيل الدخول مرة أخرى');
    } else if (e.response?.statusCode == 413) {
      throw Exception('حجم الملف كبير جداً. الرجاء ضغط الصورة أو اختيار ملف أصغر');
    } else {
      throw Exception('حدث خطأ في الاتصال بالخادم');
    }
  }
}
```

---

## ❗ أخطاء شائعة وحلولها

### 1. خطأ 400 - Bad Request
**السبب:** أسماء الحقول غير صحيحة أو بيانات ناقصة

**الحل:**
- تأكد من استخدام الأسماء الصحيحة للحقول
- تحقق من إرسال جميع الحقول المطلوبة

### 2. خطأ 401 - Unauthorized
**السبب:** JWT Token منتهي الصلاحية أو غير صحيح

**الحل:**
```dart
// إعادة تسجيل الدخول
final newToken = await login(employeeId, nationalId);
// حفظ التوكن الجديد
```

### 3. خطأ 413 - Payload Too Large
**السبب:** حجم الملف كبير جداً

**الحل:**
```dart
// زيادة نسبة الضغط
final result = await FlutterImageCompress.compressAndGetFile(
  file.path,
  targetPath,
  quality: 50, // تقليل الجودة إلى 50%
  minWidth: 800,
  minHeight: 800,
);
```

### 4. خطأ 404 - Not Found
**السبب:** السيارة أو الطلب غير موجود

**الحل:**
- تحقق من صحة `vehicle_id` أو `request_id`

---

## 📊 ملخص الحقول المهمة

### طلب الفاتورة
```
✅ invoice_image (وليس image)
```

### طلب الغسيل
```
✅ photo_plate
✅ photo_front
✅ photo_back
✅ photo_right_side
✅ photo_left_side
```

### طلب الفحص
```
✅ files[] (قائمة ملفات متعددة)
✅ يدعم صور + فيديو معاً
```

---

## 🔐 أمان إضافي

### تخزين JWT Token
```dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

final storage = FlutterSecureStorage();

// حفظ التوكن
await storage.write(key: 'jwt_token', value: token);

// استرجاع التوكن
final token = await storage.read(key: 'jwt_token');
```

---

**آخر تحديث:** 10 نوفمبر 2025  
**الإصدار:** 1.0.0

**للدعم الفني:**
راجع ملف `EMPLOYEE_REQUESTS_API.md` للتفاصيل الكاملة
