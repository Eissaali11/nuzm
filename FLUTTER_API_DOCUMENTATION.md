# 📱 نُظم - دليل API الشامل لتطبيق Flutter
## التوثيق الكامل لربط تطبيق Flutter مع نظام نُظم

**آخر تحديث:** 10 نوفمبر 2024  
**إصدار API:** v1.0  
**Base URL:** `https://your-domain.replit.app/api/v1`

---

## 📋 فهرس سريع

| الفئة | عدد الـ Endpoints | الصفحة |
|------|------------------|--------|
| 🔐 المصادقة | 1 | [الانتقال](#auth) |
| 🚗 غسيل السيارات | 5 | [الانتقال](#car-wash) |
| 🔍 فحص السيارات | 4 | [الانتقال](#car-inspection) |
| 📋 إدارة الطلبات العامة | 3 | [الانتقال](#general) |
| ✅ الموافقة/الرفض | 2 | [الانتقال](#status) |
| 📊 الإحصائيات | 7 | [الانتقال](#stats) |

**إجمالي الـ Endpoints: 28**

---

<a name="auth"></a>
## 🔐 1. المصادقة والتسجيل

### 1.1 تسجيل الدخول

**الغرض:** تسجيل دخول الموظف والحصول على JWT Token للاستخدام في جميع الطلبات اللاحقة.

```
POST /api/v1/auth/login
```

#### 📥 البيانات المطلوبة (Request Body - JSON)

| الحقل | النوع | إلزامي | الوصف | مثال |
|------|------|--------|-------|------|
| `employee_id` | String | ✅ نعم | الرقم الوظيفي للموظف | "EMP001" |
| `password` | String | ✅ نعم | كلمة المرور | "pass123" |

#### 📤 الاستجابة الناجحة (200 OK)

```json
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJlbXBsb3llZV9pZCI6MSwiZXhwIjoxNzM...",
  "employee": {
    "id": 1,
    "employee_id": "EMP001",
    "name": "أحمد محمد علي",
    "email": "ahmad@company.com",
    "job_title": "مهندس برمجيات",
    "department": "تقنية المعلومات",
    "profile_image": "/static/uploads/employees/profile_1.jpg"
  }
}
```

#### ❌ الاستجابة عند الفشل (401 Unauthorized)

```json
{
  "success": false,
  "message": "الرقم الوظيفي أو كلمة المرور غير صحيحة"
}
```

#### 💻 كود Flutter الكامل

```dart
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AuthService {
  final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  
  AuthService(this._dio);

  /// تسجيل الدخول
  /// يأخذ: employeeId (الرقم الوظيفي), password (كلمة المرور)
  /// يرجع: بيانات الموظف + Token
  Future<Employee> login({
    required String employeeId,
    required String password,
  }) async {
    try {
      final response = await _dio.post(
        '/auth/login',
        data: {
          'employee_id': employeeId,
          'password': password,
        },
      );

      if (response.data['success'] == true) {
        // حفظ التوكن بشكل آمن
        final token = response.data['token'] as String;
        await _storage.write(key: 'auth_token', value: token);
        
        // تحليل بيانات الموظف
        final employeeData = response.data['employee'];
        return Employee.fromJson(employeeData);
      } else {
        throw Exception(response.data['message']);
      }
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw Exception('الرقم الوظيفي أو كلمة المرور غير صحيحة');
      }
      throw Exception('خطأ في الاتصال بالخادم');
    }
  }

  /// الحصول على التوكن المحفوظ
  Future<String?> getToken() async {
    return await _storage.read(key: 'auth_token');
  }

  /// تسجيل الخروج
  Future<void> logout() async {
    await _storage.delete(key: 'auth_token');
  }
}
```

#### 📝 ملاحظات مهمة
- ✅ Token صالح لمدة **30 يوم**
- ✅ يجب حفظ التوكن باستخدام `flutter_secure_storage`
- ✅ يجب إرسال التوكن مع كل طلب في الـ Header: `Authorization: Bearer {TOKEN}`

---

<a name="car-wash"></a>
## 🚗 2. طلبات غسيل السيارات

### 2.1 إنشاء طلب غسيل سيارة جديد

**الغرض:** إنشاء طلب غسيل سيارة مع رفع 5 صور إلزامية (لوحة، أمامية، خلفية، يمين، يسار).

```
POST /api/v1/requests/create-car-wash
Authorization: Bearer {TOKEN}
Content-Type: multipart/form-data
```

#### 📥 البيانات المطلوبة (Form Data)

| الحقل | النوع | إلزامي | الوصف | مثال/قيم |
|------|------|--------|-------|---------|
| `vehicle_id` | Integer | ✅ نعم | رقم السيارة من قاعدة البيانات | 5 |
| `service_type` | String | ✅ نعم | نوع الخدمة | `normal`, `polish`, `full_clean` |
| `scheduled_date` | Date | ✅ نعم | تاريخ الموعد المطلوب | "2024-11-15" |
| `notes` | String | ❌ لا | ملاحظات إضافية | "يرجى الاهتمام بالتنظيف الداخلي" |
| `photo_plate` | File | ✅ نعم | صورة لوحة السيارة | image.jpg |
| `photo_front` | File | ✅ نعم | صورة أمامية للسيارة | image.jpg |
| `photo_back` | File | ✅ نعم | صورة خلفية للسيارة | image.jpg |
| `photo_right_side` | File | ✅ نعم | صورة الجانب الأيمن | image.jpg |
| `photo_left_side` | File | ✅ نعم | صورة الجانب الأيسر | image.jpg |

#### 🎯 أنواع الخدمات (service_type)

| القيمة | الاسم بالعربية | الوصف |
|-------|----------------|-------|
| `normal` | غسيل عادي | غسيل خارجي فقط |
| `polish` | تلميع وتنظيف | غسيل + تلميع |
| `full_clean` | تنظيف شامل | غسيل + تلميع + تنظيف داخلي |

#### 📤 الاستجابة الناجحة (201 Created)

```json
{
  "success": true,
  "message": "تم إنشاء طلب الغسيل بنجاح",
  "data": {
    "request_id": 123,
    "type": "car_wash",
    "status": "pending",
    "service_type": "polish",
    "service_type_ar": "تلميع وتنظيف",
    "vehicle_plate": "ن ج ر 1234",
    "created_at": "2024-11-10T19:30:00"
  }
}
```

#### 💻 كود Flutter الكامل

```dart
import 'package:dio/dio.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';

class CarWashService {
  final Dio _dio;
  final String _token;

  CarWashService(this._dio, this._token);

  /// إنشاء طلب غسيل سيارة جديد
  /// 
  /// المعاملات:
  /// - vehicleId: رقم السيارة (من قائمة السيارات)
  /// - serviceType: نوع الخدمة (normal, polish, full_clean)
  /// - scheduledDate: تاريخ الموعد
  /// - notes: ملاحظات إضافية (اختياري)
  /// - الصور الخمس الإلزامية
  /// 
  /// يرجع: رقم الطلب الجديد
  Future<int> createCarWashRequest({
    required int vehicleId,
    required ServiceType serviceType,
    required DateTime scheduledDate,
    String? notes,
    required File photoPlate,
    required File photoFront,
    required File photoBack,
    required File photoRightSide,
    required File photoLeftSide,
  }) async {
    // التحقق من وجود جميع الصور
    if (!await photoPlate.exists() || 
        !await photoFront.exists() ||
        !await photoBack.exists() ||
        !await photoRightSide.exists() ||
        !await photoLeftSide.exists()) {
      throw Exception('يجب اختيار جميع الصور الخمس');
    }

    // إنشاء FormData
    final formData = FormData.fromMap({
      'vehicle_id': vehicleId,
      'service_type': serviceType.value, // normal, polish, or full_clean
      'scheduled_date': scheduledDate.toIso8601String().split('T')[0], // YYYY-MM-DD
      if (notes != null && notes.isNotEmpty) 'notes': notes,
      
      // رفع الصور
      'photo_plate': await MultipartFile.fromFile(
        photoPlate.path,
        filename: 'plate_${DateTime.now().millisecondsSinceEpoch}.jpg',
      ),
      'photo_front': await MultipartFile.fromFile(
        photoFront.path,
        filename: 'front_${DateTime.now().millisecondsSinceEpoch}.jpg',
      ),
      'photo_back': await MultipartFile.fromFile(
        photoBack.path,
        filename: 'back_${DateTime.now().millisecondsSinceEpoch}.jpg',
      ),
      'photo_right_side': await MultipartFile.fromFile(
        photoRightSide.path,
        filename: 'right_${DateTime.now().millisecondsSinceEpoch}.jpg',
      ),
      'photo_left_side': await MultipartFile.fromFile(
        photoLeftSide.path,
        filename: 'left_${DateTime.now().millisecondsSinceEpoch}.jpg',
      ),
    });

    try {
      final response = await _dio.post(
        '/requests/create-car-wash',
        data: formData,
        options: Options(
          headers: {'Authorization': 'Bearer $_token'},
        ),
        onSendProgress: (sent, total) {
          // يمكنك عرض progress bar هنا
          final progress = (sent / total * 100).toStringAsFixed(0);
          print('Progress: $progress%');
        },
      );

      if (response.data['success'] == true) {
        return response.data['data']['request_id'] as int;
      } else {
        throw Exception(response.data['message']);
      }
    } on DioException catch (e) {
      if (e.response != null) {
        throw Exception(e.response!.data['message']);
      }
      throw Exception('فشل الاتصال بالخادم');
    }
  }
}

// Enum لأنواع الخدمات
enum ServiceType {
  normal('normal', 'غسيل عادي'),
  polish('polish', 'تلميع وتنظيف'),
  fullClean('full_clean', 'تنظيف شامل');

  final String value;
  final String displayName;
  const ServiceType(this.value, this.displayName);
}
```

#### 📝 ملاحظات مهمة
- ✅ الصور الخمس **إلزامية**، الطلب سيفشل إذا نقصت صورة واحدة
- ✅ حجم الصورة الواحدة: حتى **10 MB**
- ✅ الصيغ المدعومة: JPG, JPEG, PNG, HEIC
- ✅ يتم حفظ الصور **محلياً** و**على Google Drive** تلقائياً

---

### 2.2 تعديل طلب غسيل سيارة موجود

**الغرض:** تعديل بيانات طلب غسيل موجود، مع إمكانية تغيير الصور أو حذفها.

```
PUT /api/v1/requests/car-wash/{request_id}
Authorization: Bearer {TOKEN}
Content-Type: multipart/form-data
```

#### 📥 البيانات المطلوبة (Form Data - كلها اختيارية)

| الحقل | النوع | إلزامي | الوصف | مثال |
|------|------|--------|-------|------|
| `vehicle_id` | Integer | ❌ لا | تغيير السيارة | 7 |
| `service_type` | String | ❌ لا | تغيير نوع الخدمة | "full_clean" |
| `scheduled_date` | Date | ❌ لا | تغيير التاريخ | "2024-11-20" |
| `notes` | String | ❌ لا | تعديل الملاحظات | "ملاحظات جديدة" |
| `photo_plate` | File | ❌ لا | تغيير صورة اللوحة | image.jpg |
| `photo_front` | File | ❌ لا | تغيير الصورة الأمامية | image.jpg |
| `photo_back` | File | ❌ لا | تغيير الصورة الخلفية | image.jpg |
| `photo_right_side` | File | ❌ لا | تغيير صورة اليمين | image.jpg |
| `photo_left_side` | File | ❌ لا | تغيير صورة اليسار | image.jpg |
| `delete_media_ids` | Array[Int] | ❌ لا | أرقام الصور المراد حذفها | [101, 102] |

#### 📤 الاستجابة الناجحة (200 OK)

```json
{
  "success": true,
  "message": "تم تحديث طلب الغسيل بنجاح",
  "request": {
    "id": 123,
    "type": "CAR_WASH",
    "status": "PENDING",
    "vehicle": {
      "id": 5,
      "plate_number": "ن ج ر 1234"
    },
    "service_type": "polish",
    "scheduled_date": "2024-11-20",
    "media_count": 5,
    "updated_at": "2024-11-10T20:15:00"
  }
}
```

#### 💻 كود Flutter

```dart
/// تعديل طلب غسيل موجود
/// 
/// المعاملات (كلها اختيارية):
/// - requestId: رقم الطلب المراد تعديله
/// - vehicleId: تغيير السيارة
/// - serviceType: تغيير نوع الخدمة
/// - scheduledDate: تغيير التاريخ
/// - notes: تعديل الملاحظات
/// - الصور: فقط الصور التي تريد تغييرها
/// - deleteMediaIds: أرقام الصور المراد حذفها
/// 
/// يرجع: true إذا نجح التعديل
Future<bool> updateCarWashRequest({
  required int requestId,
  int? vehicleId,
  ServiceType? serviceType,
  DateTime? scheduledDate,
  String? notes,
  File? photoPlate,
  File? photoFront,
  File? photoBack,
  File? photoRightSide,
  File? photoLeftSide,
  List<int>? deleteMediaIds,
}) async {
  final formData = FormData.fromMap({
    if (vehicleId != null) 'vehicle_id': vehicleId,
    if (serviceType != null) 'service_type': serviceType.value,
    if (scheduledDate != null) 
      'scheduled_date': scheduledDate.toIso8601String().split('T')[0],
    if (notes != null) 'notes': notes,
    
    // رفع الصور الجديدة (فقط الموجودة)
    if (photoPlate != null)
      'photo_plate': await MultipartFile.fromFile(photoPlate.path),
    if (photoFront != null)
      'photo_front': await MultipartFile.fromFile(photoFront.path),
    if (photoBack != null)
      'photo_back': await MultipartFile.fromFile(photoBack.path),
    if (photoRightSide != null)
      'photo_right_side': await MultipartFile.fromFile(photoRightSide.path),
    if (photoLeftSide != null)
      'photo_left_side': await MultipartFile.fromFile(photoLeftSide.path),
    
    // حذف صور محددة
    if (deleteMediaIds != null && deleteMediaIds.isNotEmpty)
      'delete_media_ids': deleteMediaIds,
  });

  try {
    final response = await _dio.put(
      '/requests/car-wash/$requestId',
      data: formData,
      options: Options(headers: {'Authorization': 'Bearer $_token'}),
    );

    return response.data['success'] == true;
  } catch (e) {
    throw Exception('فشل تحديث الطلب: $e');
  }
}
```

#### 📝 ملاحظات
- ✅ يمكنك إرسال **فقط الحقول التي تريد تغييرها**
- ✅ الصور الجديدة ستحل محل القديمة **فقط للنوع المحدد**
- ✅ يمكنك حذف صور محددة عبر `delete_media_ids`

---

### 2.3 قائمة طلبات الغسيل مع الفلترة

**الغرض:** الحصول على قائمة بجميع طلبات الغسيل مع إمكانية الفلترة والبحث.

```
GET /api/v1/requests/car-wash
Authorization: Bearer {TOKEN}
```

#### 📥 معاملات الفلترة (Query Parameters - كلها اختيارية)

| المعامل | النوع | الوصف | القيم/مثال |
|---------|------|--------|-----------|
| `status` | String | الفلترة حسب الحالة | `PENDING`, `APPROVED`, `REJECTED`, `COMPLETED` |
| `vehicle_id` | Integer | الفلترة حسب السيارة | 5 |
| `from_date` | Date | من تاريخ | "2024-11-01" |
| `to_date` | Date | إلى تاريخ | "2024-11-30" |
| `page` | Integer | رقم الصفحة | 1 (default) |
| `per_page` | Integer | عدد النتائج بالصفحة | 20 (default) |

#### 📤 الاستجابة الناجحة (200 OK)

```json
{
  "success": true,
  "requests": [
    {
      "id": 123,
      "status": "PENDING",
      "status_display": "قيد الانتظار",
      "employee": {
        "id": 10,
        "name": "خالد أحمد محمد",
        "job_number": "EMP010"
      },
      "vehicle": {
        "id": 5,
        "plate_number": "ن ج ر 1234",
        "make": "تويوتا",
        "model": "كامري"
      },
      "service_type": "polish",
      "service_type_display": "تلميع وتنظيف",
      "scheduled_date": "2024-11-15",
      "media_count": 5,
      "created_at": "2024-11-10T10:30:00",
      "updated_at": "2024-11-10T14:20:00"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "pages": 3
  }
}
```

#### 💻 كود Flutter

```dart
/// الحصول على قائمة طلبات الغسيل مع الفلترة
/// 
/// المعاملات (كلها اختيارية):
/// - status: فلترة حسب الحالة
/// - vehicleId: فلترة حسب السيارة
/// - fromDate: من تاريخ
/// - toDate: إلى تاريخ
/// - page: رقم الصفحة
/// - perPage: عدد النتائج
/// 
/// يرجع: قائمة بطلبات الغسيل + معلومات الترقيم
Future<PaginatedCarWashRequests> getCarWashRequests({
  RequestStatus? status,
  int? vehicleId,
  DateTime? fromDate,
  DateTime? toDate,
  int page = 1,
  int perPage = 20,
}) async {
  // بناء معاملات الاستعلام
  final queryParams = <String, dynamic>{
    'page': page,
    'per_page': perPage,
    if (status != null) 'status': status.value,
    if (vehicleId != null) 'vehicle_id': vehicleId,
    if (fromDate != null) 'from_date': fromDate.toIso8601String().split('T')[0],
    if (toDate != null) 'to_date': toDate.toIso8601String().split('T')[0],
  };

  try {
    final response = await _dio.get(
      '/requests/car-wash',
      queryParameters: queryParams,
      options: Options(headers: {'Authorization': 'Bearer $_token'}),
    );

    if (response.data['success'] == true) {
      final requests = (response.data['requests'] as List)
          .map((json) => CarWashRequest.fromJson(json))
          .toList();
      
      final pagination = Pagination.fromJson(response.data['pagination']);
      
      return PaginatedCarWashRequests(
        requests: requests,
        pagination: pagination,
      );
    } else {
      throw Exception(response.data['message']);
    }
  } catch (e) {
    throw Exception('فشل تحميل الطلبات: $e');
  }
}

// Model للترقيم
class Pagination {
  final int page;
  final int perPage;
  final int total;
  final int pages;

  Pagination({
    required this.page,
    required this.perPage,
    required this.total,
    required this.pages,
  });

  factory Pagination.fromJson(Map<String, dynamic> json) {
    return Pagination(
      page: json['page'],
      perPage: json['per_page'],
      total: json['total'],
      pages: json['pages'],
    );
  }
}

class PaginatedCarWashRequests {
  final List<CarWashRequest> requests;
  final Pagination pagination;

  PaginatedCarWashRequests({
    required this.requests,
    required this.pagination,
  });
}
```

---

### 2.4 تفاصيل طلب غسيل كاملة

**الغرض:** الحصول على جميع تفاصيل طلب غسيل محدد، بما في ذلك جميع الصور.

```
GET /api/v1/requests/car-wash/{request_id}
Authorization: Bearer {TOKEN}
```

#### 📥 المعاملات

| المعامل | الموقع | إلزامي | الوصف |
|---------|--------|--------|-------|
| `request_id` | URL Path | ✅ نعم | رقم الطلب |

#### 📤 الاستجابة (200 OK)

```json
{
  "success": true,
  "request": {
    "id": 123,
    "type": "CAR_WASH",
    "status": "PENDING",
    "status_display": "قيد الانتظار",
    "employee": {
      "id": 10,
      "name": "خالد أحمد",
      "job_number": "EMP010",
      "department": "تقنية المعلومات"
    },
    "vehicle": {
      "id": 5,
      "plate_number": "ن ج ر 1234",
      "make": "تويوتا",
      "model": "كامري",
      "year": 2022,
      "color": "فضي"
    },
    "service_type": "polish",
    "service_type_display": "تلميع وتنظيف",
    "scheduled_date": "2024-11-15",
    "notes": "يرجى الاهتمام بالتنظيف الداخلي",
    "media_files": [
      {
        "id": 101,
        "media_type": "PLATE",
        "media_type_display": "لوحة السيارة",
        "local_path": "/static/uploads/car_wash/wash_123_photo_plate_a1b2c3.jpg",
        "drive_view_url": "https://drive.google.com/file/d/1ABC.../view",
        "file_size_kb": 234,
        "uploaded_at": "2024-11-10T10:35:00"
      },
      {
        "id": 102,
        "media_type": "FRONT",
        "media_type_display": "صورة أمامية",
        "local_path": "/static/uploads/car_wash/wash_123_photo_front_x5y6z7.jpg",
        "drive_view_url": null,
        "file_size_kb": 456,
        "uploaded_at": "2024-11-10T10:35:00"
      }
    ],
    "created_at": "2024-11-10T10:30:00",
    "updated_at": "2024-11-10T19:30:00",
    "reviewed_at": null,
    "reviewed_by": null,
    "admin_notes": null
  }
}
```

#### 💻 كود Flutter

```dart
/// الحصول على تفاصيل طلب غسيل كاملة
/// 
/// المعاملات:
/// - requestId: رقم الطلب
/// 
/// يرجع: تفاصيل الطلب الكاملة مع جميع الصور
Future<CarWashRequestDetails> getCarWashRequestDetails(int requestId) async {
  try {
    final response = await _dio.get(
      '/requests/car-wash/$requestId',
      options: Options(headers: {'Authorization': 'Bearer $_token'}),
    );

    if (response.data['success'] == true) {
      return CarWashRequestDetails.fromJson(response.data['request']);
    } else {
      throw Exception(response.data['message']);
    }
  } on DioException catch (e) {
    if (e.response?.statusCode == 404) {
      throw Exception('الطلب غير موجود');
    }
    throw Exception('فشل تحميل التفاصيل');
  }
}
```

---

### 2.5 حذف صورة من طلب غسيل

**الغرض:** حذف صورة واحدة محددة من طلب الغسيل.

```
DELETE /api/v1/requests/car-wash/{request_id}/media/{media_id}
Authorization: Bearer {TOKEN}
```

#### 📥 المعاملات

| المعامل | الموقع | إلزامي | الوصف |
|---------|--------|--------|-------|
| `request_id` | URL Path | ✅ نعم | رقم الطلب |
| `media_id` | URL Path | ✅ نعم | رقم الصورة |

#### 📤 الاستجابة (200 OK)

```json
{
  "success": true,
  "message": "تم حذف الصورة بنجاح",
  "remaining_media_count": 4
}
```

#### 💻 كود Flutter

```dart
/// حذف صورة من طلب غسيل
/// 
/// المعاملات:
/// - requestId: رقم الطلب
/// - mediaId: رقم الصورة المراد حذفها
/// 
/// يرجع: true إذا نجح الحذف
Future<bool> deleteCarWashMedia(int requestId, int mediaId) async {
  try {
    final response = await _dio.delete(
      '/requests/car-wash/$requestId/media/$mediaId',
      options: Options(headers: {'Authorization': 'Bearer $_token'}),
    );

    return response.data['success'] == true;
  } catch (e) {
    throw Exception('فشل حذف الصورة: $e');
  }
}
```

---

<a name="car-inspection"></a>
## 🔍 3. طلبات فحص السيارات

### 3.1 إنشاء طلب فحص سيارة جديد

**الغرض:** إنشاء طلب فحص سيارة مع رفع صور وفيديوهات متعددة.

```
POST /api/v1/requests/create-car-inspection
Authorization: Bearer {TOKEN}
Content-Type: multipart/form-data
```

#### 📥 البيانات المطلوبة

| الحقل | النوع | إلزامي | الوصف | مثال/قيم |
|------|------|--------|-------|---------|
| `vehicle_id` | Integer | ✅ نعم | رقم السيارة | 5 |
| `inspection_type` | String | ✅ نعم | نوع الفحص | `periodic`, `comprehensive`, `pre_sale` |
| `inspection_date` | Date | ✅ نعم | تاريخ الفحص | "2024-11-15" |
| `notes` | String | ❌ لا | ملاحظات الفحص | "فحص قبل السفر" |
| `files` | File[] | ✅ نعم | صور وفيديوهات (1-20 صورة، 0-3 فيديو) | [file1, file2, ...] |

#### 🎯 أنواع الفحص (inspection_type)

| القيمة | الاسم بالعربية | الوصف |
|-------|----------------|-------|
| `periodic` | فحص دوري | الفحص الدوري المعتاد |
| `comprehensive` | فحص شامل | فحص شامل لجميع أجزاء السيارة |
| `pre_sale` | فحص قبل البيع | فحص شامل قبل بيع السيارة |

#### 📤 الاستجابة (201 Created)

```json
{
  "success": true,
  "message": "تم إنشاء طلب الفحص بنجاح",
  "data": {
    "request_id": 456,
    "type": "car_inspection",
    "status": "pending",
    "inspection_type": "comprehensive",
    "inspection_type_ar": "فحص شامل",
    "vehicle_plate": "ن ج ر 1234",
    "media_uploaded": {
      "images": 10,
      "videos": 2
    }
  }
}
```

#### 💻 كود Flutter

```dart
/// إنشاء طلب فحص سيارة جديد
/// 
/// المعاملات:
/// - vehicleId: رقم السيارة
/// - inspectionType: نوع الفحص
/// - inspectionDate: تاريخ الفحص
/// - notes: ملاحظات (اختياري)
/// - files: قائمة بالصور والفيديوهات (حتى 20 صورة + 3 فيديو)
/// 
/// القيود:
/// - الصور: JPG, PNG, HEIC - حتى 10MB للصورة
/// - الفيديو: MP4, MOV - حتى 500MB للفيديو
/// 
/// يرجع: رقم الطلب الجديد
Future<int> createCarInspectionRequest({
  required int vehicleId,
  required InspectionType inspectionType,
  required DateTime inspectionDate,
  String? notes,
  required List<File> files,
}) async {
  // التحقق من عدد الملفات
  final images = files.where((f) => _isImage(f.path)).toList();
  final videos = files.where((f) => _isVideo(f.path)).toList();
  
  if (images.isEmpty) {
    throw Exception('يجب رفع صورة واحدة على الأقل');
  }
  if (images.length > 20) {
    throw Exception('الحد الأقصى 20 صورة');
  }
  if (videos.length > 3) {
    throw Exception('الحد الأقصى 3 فيديوهات');
  }

  // إنشاء FormData
  final formData = FormData.fromMap({
    'vehicle_id': vehicleId,
    'inspection_type': inspectionType.value,
    'inspection_date': inspectionDate.toIso8601String().split('T')[0],
    if (notes != null && notes.isNotEmpty) 'notes': notes,
    
    // رفع جميع الملفات
    'files': await Future.wait(
      files.map((file) => MultipartFile.fromFile(
        file.path,
        filename: file.path.split('/').last,
      )),
    ),
  });

  try {
    final response = await _dio.post(
      '/requests/create-car-inspection',
      data: formData,
      options: Options(
        headers: {'Authorization': 'Bearer $_token'},
      ),
      onSendProgress: (sent, total) {
        final progress = (sent / total * 100).toStringAsFixed(0);
        print('Uploading: $progress%');
      },
    );

    if (response.data['success'] == true) {
      return response.data['data']['request_id'] as int;
    } else {
      throw Exception(response.data['message']);
    }
  } catch (e) {
    throw Exception('فشل إنشاء الطلب: $e');
  }
}

// Helper functions
bool _isImage(String path) {
  final ext = path.split('.').last.toLowerCase();
  return ['jpg', 'jpeg', 'png', 'heic'].contains(ext);
}

bool _isVideo(String path) {
  final ext = path.split('.').last.toLowerCase();
  return ['mp4', 'mov', 'avi'].contains(ext);
}

// Enum لأنواع الفحص
enum InspectionType {
  periodic('periodic', 'فحص دوري'),
  comprehensive('comprehensive', 'فحص شامل'),
  preSale('pre_sale', 'فحص قبل البيع');

  final String value;
  final String displayName;
  const InspectionType(this.value, this.displayName);
}
```

#### 📝 ملاحظات
- ✅ حد أقصى **20 صورة** و **3 فيديوهات**
- ✅ حجم الصورة: حتى **10 MB**
- ✅ حجم الفيديو: حتى **500 MB**
- ✅ الصيغ المدعومة:
  - صور: JPG, JPEG, PNG, HEIC
  - فيديو: MP4, MOV, AVI

---

### 3.2 تعديل طلب فحص سيارة

**الغرض:** تعديل بيانات طلب فحص موجود وإضافة/حذف ملفات.

```
PUT /api/v1/requests/car-inspection/{request_id}
Authorization: Bearer {TOKEN}
Content-Type: multipart/form-data
```

#### 📥 البيانات (كلها اختيارية)

| الحقل | النوع | إلزامي | الوصف |
|------|------|--------|-------|
| `vehicle_id` | Integer | ❌ لا | تغيير السيارة |
| `inspection_type` | String | ❌ لا | تغيير نوع الفحص |
| `inspection_date` | Date | ❌ لا | تغيير التاريخ |
| `notes` | String | ❌ لا | تعديل الملاحظات |
| `files` | File[] | ❌ لا | إضافة ملفات جديدة |
| `delete_media_ids` | Array[Int] | ❌ لا | حذف ملفات محددة |

#### 📤 الاستجابة (200 OK)

```json
{
  "success": true,
  "message": "تم تحديث طلب الفحص بنجاح",
  "request": {
    "id": 456,
    "type": "CAR_INSPECTION",
    "status": "PENDING",
    "vehicle": {"id": 5, "plate_number": "ن ج ر 1234"},
    "inspection_type": "comprehensive",
    "inspection_date": "2024-11-20",
    "media": {
      "images_count": 12,
      "videos_count": 2
    },
    "updated_at": "2024-11-10T20:30:00"
  }
}
```

#### 💻 كود Flutter

```dart
/// تعديل طلب فحص موجود
Future<bool> updateCarInspectionRequest({
  required int requestId,
  int? vehicleId,
  InspectionType? inspectionType,
  DateTime? inspectionDate,
  String? notes,
  List<File>? newFiles,
  List<int>? deleteMediaIds,
}) async {
  final formData = FormData.fromMap({
    if (vehicleId != null) 'vehicle_id': vehicleId,
    if (inspectionType != null) 'inspection_type': inspectionType.value,
    if (inspectionDate != null) 
      'inspection_date': inspectionDate.toIso8601String().split('T')[0],
    if (notes != null) 'notes': notes,
    
    if (newFiles != null && newFiles.isNotEmpty)
      'files': await Future.wait(
        newFiles.map((f) => MultipartFile.fromFile(f.path)),
      ),
    
    if (deleteMediaIds != null && deleteMediaIds.isNotEmpty)
      'delete_media_ids': deleteMediaIds,
  });

  try {
    final response = await _dio.put(
      '/requests/car-inspection/$requestId',
      data: formData,
      options: Options(headers: {'Authorization': 'Bearer $_token'}),
    );

    return response.data['success'] == true;
  } catch (e) {
    throw Exception('فشل التحديث: $e');
  }
}
```

---

### 3.3 قائمة طلبات الفحص

**الغرض:** الحصول على قائمة بطلبات الفحص مع الفلترة.

```
GET /api/v1/requests/car-inspection?status=PENDING&page=1
Authorization: Bearer {TOKEN}
```

المعاملات نفسها مثل طلبات الغسيل.

#### 📤 الاستجابة

```json
{
  "success": true,
  "requests": [
    {
      "id": 456,
      "status": "APPROVED",
      "status_display": "موافق عليه",
      "employee": {"id": 10, "name": "خالد أحمد"},
      "vehicle": {
        "id": 5,
        "plate_number": "ن ج ر 1234",
        "make": "تويوتا",
        "model": "كامري"
      },
      "inspection_type": "comprehensive",
      "inspection_type_display": "فحص شامل",
      "inspection_date": "2024-11-15",
      "media": {
        "images_count": 10,
        "videos_count": 2,
        "total_count": 12
      },
      "created_at": "2024-11-10T10:30:00"
    }
  ],
  "pagination": {"page": 1, "total": 15}
}
```

---

### 3.4 حذف ملف من طلب فحص

```
DELETE /api/v1/requests/car-inspection/{request_id}/media/{media_id}
Authorization: Bearer {TOKEN}
```

#### 📤 الاستجابة

```json
{
  "success": true,
  "message": "تم حذف الملف بنجاح",
  "remaining_media": {
    "images_count": 9,
    "videos_count": 2
  }
}
```

---

<a name="general"></a>
## 📋 4. إدارة الطلبات العامة

### 4.1 حذف طلب (أي نوع)

**الغرض:** حذف طلب كامل (يعمل فقط مع الطلبات ذات حالة PENDING).

```
DELETE /api/v1/requests/{request_id}
Authorization: Bearer {TOKEN}
```

#### ⚠️ شرط مهم
يمكن حذف الطلب **فقط** إذا كان بحالة `PENDING` (قيد الانتظار).

#### 📤 الاستجابة الناجحة (200 OK)

```json
{
  "success": true,
  "message": "تم حذف الطلب بنجاح"
}
```

#### ❌ الاستجابة عند الفشل (400 Bad Request)

```json
{
  "success": false,
  "message": "لا يمكن حذف طلب تمت معالجته"
}
```

#### 💻 كود Flutter

```dart
/// حذف طلب
/// 
/// المعاملات:
/// - requestId: رقم الطلب المراد حذفه
/// 
/// ملاحظة: يعمل فقط مع الطلبات بحالة PENDING
/// 
/// يرجع: true إذا نجح الحذف
/// يرمي Exception إذا كان الطلب معالج بالفعل
Future<bool> deleteRequest(int requestId) async {
  try {
    final response = await _dio.delete(
      '/requests/$requestId',
      options: Options(headers: {'Authorization': 'Bearer $_token'}),
    );

    return response.data['success'] == true;
  } on DioException catch (e) {
    if (e.response?.statusCode == 400) {
      // الطلب تمت معالجته ولا يمكن حذفه
      throw Exception(e.response?.data['message'] ?? 'لا يمكن حذف هذا الطلب');
    } else if (e.response?.statusCode == 404) {
      throw Exception('الطلب غير موجود');
    }
    throw Exception('فشل حذف الطلب');
  }
}
```

---

### 4.2 قائمة جميع الطلبات

**الغرض:** الحصول على جميع طلبات الموظف (جميع الأنواع).

```
GET /api/v1/requests?type=CAR_WASH&status=PENDING&page=1
Authorization: Bearer {TOKEN}
```

#### 📥 معاملات الفلترة

| المعامل | القيم | الوصف |
|---------|------|-------|
| `type` | `INVOICE`, `CAR_WASH`, `CAR_INSPECTION`, `ADVANCE_PAYMENT` | نوع الطلب |
| `status` | `PENDING`, `APPROVED`, `REJECTED`, `COMPLETED`, `CLOSED` | الحالة |
| `page` | Integer | رقم الصفحة |
| `per_page` | Integer | عدد النتائج |

#### 📤 الاستجابة

```json
{
  "success": true,
  "requests": [
    {
      "id": 1,
      "type": "CAR_WASH",
      "type_display": "غسيل سيارة",
      "status": "PENDING",
      "status_display": "قيد الانتظار",
      "title": "طلب غسيل سيارة",
      "description": "غسيل وتلميع شامل",
      "amount": 150.00,
      "created_at": "2024-11-09T10:30:00"
    }
  ],
  "pagination": {"page": 1, "total": 45, "pages": 3}
}
```

---

### 4.3 تفاصيل طلب (أي نوع)

```
GET /api/v1/requests/{request_id}
Authorization: Bearer {TOKEN}
```

تعيد تفاصيل الطلب بغض النظر عن نوعه.

---

<a name="status"></a>
## ✅ 5. إدارة حالة الطلبات (للإداريين)

### 5.1 الموافقة على طلب

**الغرض:** الموافقة على طلب من قبل المسؤول/الإداري.

```
POST /api/v1/requests/{request_id}/approve
Authorization: Bearer {TOKEN}
Content-Type: application/json
```

#### 📥 البيانات (اختيارية)

| الحقل | النوع | إلزامي | الوصف |
|------|------|--------|-------|
| `admin_notes` | String | ❌ لا | ملاحظات الإداري |

#### 📤 الاستجابة (200 OK)

```json
{
  "success": true,
  "message": "تمت الموافقة على الطلب",
  "request": {
    "id": 123,
    "status": "APPROVED",
    "reviewed_at": "2024-11-10T19:30:00",
    "reviewed_by": {
      "id": 1,
      "name": "أحمد الإداري"
    }
  }
}
```

#### 💻 كود Flutter

```dart
/// الموافقة على طلب (للإداريين فقط)
/// 
/// المعاملات:
/// - requestId: رقم الطلب
/// - adminNotes: ملاحظات الإداري (اختياري)
/// 
/// يرجع: true إذا تمت الموافقة
Future<bool> approveRequest(int requestId, {String? adminNotes}) async {
  try {
    final response = await _dio.post(
      '/requests/$requestId/approve',
      data: {
        if (adminNotes != null && adminNotes.isNotEmpty) 
          'admin_notes': adminNotes,
      },
      options: Options(headers: {'Authorization': 'Bearer $_token'}),
    );

    return response.data['success'] == true;
  } on DioException catch (e) {
    if (e.response?.statusCode == 403) {
      throw Exception('ليس لديك صلاحية الموافقة على الطلبات');
    }
    throw Exception('فشلت عملية الموافقة');
  }
}
```

---

### 5.2 رفض طلب

**الغرض:** رفض طلب مع ذكر السبب.

```
POST /api/v1/requests/{request_id}/reject
Authorization: Bearer {TOKEN}
Content-Type: application/json
```

#### 📥 البيانات (إلزامية)

| الحقل | النوع | إلزامي | الوصف |
|------|------|--------|-------|
| `rejection_reason` | String | ✅ نعم | سبب الرفض (مطلوب) |

#### 📤 الاستجابة (200 OK)

```json
{
  "success": true,
  "message": "تم رفض الطلب",
  "request": {
    "id": 123,
    "status": "REJECTED",
    "rejection_reason": "السبب المفصل للرفض",
    "reviewed_at": "2024-11-10T19:30:00",
    "reviewed_by": {"id": 1, "name": "أحمد الإداري"}
  }
}
```

#### 💻 كود Flutter

```dart
/// رفض طلب (للإداريين فقط)
/// 
/// المعاملات:
/// - requestId: رقم الطلب
/// - rejectionReason: سبب الرفض (إلزامي)
/// 
/// يرجع: true إذا تم الرفض
Future<bool> rejectRequest(int requestId, String rejectionReason) async {
  if (rejectionReason.trim().isEmpty) {
    throw Exception('يجب ذكر سبب الرفض');
  }

  try {
    final response = await _dio.post(
      '/requests/$requestId/reject',
      data: {'rejection_reason': rejectionReason},
      options: Options(headers: {'Authorization': 'Bearer $_token'}),
    );

    return response.data['success'] == true;
  } on DioException catch (e) {
    if (e.response?.statusCode == 403) {
      throw Exception('ليس لديك صلاحية رفض الطلبات');
    }
    throw Exception('فشلت عملية الرفض');
  }
}
```

---

<a name="stats"></a>
## 📊 6. الإحصائيات والبيانات المساعدة

### 6.1 إحصائيات الطلبات

```
GET /api/v1/requests/statistics
Authorization: Bearer {TOKEN}
```

#### 📤 الاستجابة

```json
{
  "success": true,
  "statistics": {
    "total": 45,
    "pending": 5,
    "approved": 35,
    "rejected": 3,
    "completed": 2,
    "closed": 0,
    "by_type": {
      "INVOICE": 20,
      "CAR_WASH": 10,
      "CAR_INSPECTION": 8,
      "ADVANCE_PAYMENT": 7
    }
  }
}
```

---

### 6.2 قائمة السيارات

```
GET /api/v1/vehicles
Authorization: Bearer {TOKEN}
```

#### 📤 الاستجابة

```json
{
  "success": true,
  "vehicles": [
    {
      "id": 5,
      "plate_number": "ن ج ر 1234",
      "make": "تويوتا",
      "model": "كامري",
      "year": 2022,
      "color": "فضي"
    }
  ]
}
```

---

### 6.3 الإشعارات

```
GET /api/v1/notifications?unread_only=true&page=1
Authorization: Bearer {TOKEN}
```

#### 📥 معاملات الاستعلام

| المعامل | النوع | الوصف | القيم |
|---------|------|-------|------|
| `unread_only` | Boolean | فقط غير المقروءة | true/false |
| `page` | Integer | رقم الصفحة | 1 |
| `per_page` | Integer | عدد النتائج | 20 |

#### 📤 الاستجابة

```json
{
  "success": true,
  "notifications": [
    {
      "id": 1,
      "request_id": 123,
      "title": "تمت الموافقة على طلبك",
      "message": "تمت الموافقة على طلب غسيل سيارة",
      "type": "APPROVED",
      "is_read": false,
      "created_at": "2024-11-09T14:20:00"
    }
  ],
  "unread_count": 3,
  "pagination": {"page": 1, "total": 12}
}
```

---

### 6.4 تعليم إشعار كمقروء

```
PUT /api/v1/notifications/{notification_id}/read
Authorization: Bearer {TOKEN}
```

---

### 6.5 تعليم جميع الإشعارات كمقروءة

```
PUT /api/v1/notifications/mark-all-read
Authorization: Bearer {TOKEN}
```

#### 📤 الاستجابة

```json
{
  "success": true,
  "message": "تم تعليم جميع الإشعارات كمقروءة",
  "marked_count": 5
}
```

---

## 📱 7. Models كاملة للـ Flutter

### 7.1 Employee Model

```dart
class Employee {
  final int id;
  final String employeeId;
  final String name;
  final String? email;
  final String? jobTitle;
  final String? department;
  final String? profileImage;

  Employee({
    required this.id,
    required this.employeeId,
    required this.name,
    this.email,
    this.jobTitle,
    this.department,
    this.profileImage,
  });

  factory Employee.fromJson(Map<String, dynamic> json) {
    return Employee(
      id: json['id'],
      employeeId: json['employee_id'] ?? json['job_number'],
      name: json['name'],
      email: json['email'],
      jobTitle: json['job_title'],
      department: json['department'],
      profileImage: json['profile_image'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'employee_id': employeeId,
      'name': name,
      'email': email,
      'job_title': jobTitle,
      'department': department,
      'profile_image': profileImage,
    };
  }
}
```

---

### 7.2 Vehicle Model

```dart
class Vehicle {
  final int id;
  final String plateNumber;
  final String make;
  final String model;
  final int? year;
  final String? color;

  Vehicle({
    required this.id,
    required this.plateNumber,
    required this.make,
    required this.model,
    this.year,
    this.color,
  });

  factory Vehicle.fromJson(Map<String, dynamic> json) {
    return Vehicle(
      id: json['id'],
      plateNumber: json['plate_number'],
      make: json['make'],
      model: json['model'],
      year: json['year'],
      color: json['color'],
    );
  }

  String get displayName => '$make $model';
  String get fullName => '$make $model ${year ?? ""}';
}
```

---

### 7.3 CarWashRequest Model

```dart
class CarWashRequest {
  final int id;
  final RequestStatus status;
  final String statusDisplay;
  final Employee employee;
  final Vehicle vehicle;
  final ServiceType serviceType;
  final String serviceTypeDisplay;
  final DateTime scheduledDate;
  final String? notes;
  final List<MediaFile>? mediaFiles;
  final DateTime createdAt;
  final DateTime? updatedAt;
  final DateTime? reviewedAt;
  final String? adminNotes;
  final int? mediaCount;

  CarWashRequest({
    required this.id,
    required this.status,
    required this.statusDisplay,
    required this.employee,
    required this.vehicle,
    required this.serviceType,
    required this.serviceTypeDisplay,
    required this.scheduledDate,
    this.notes,
    this.mediaFiles,
    required this.createdAt,
    this.updatedAt,
    this.reviewedAt,
    this.adminNotes,
    this.mediaCount,
  });

  factory CarWashRequest.fromJson(Map<String, dynamic> json) {
    return CarWashRequest(
      id: json['id'],
      status: RequestStatus.fromString(json['status']),
      statusDisplay: json['status_display'],
      employee: Employee.fromJson(json['employee']),
      vehicle: Vehicle.fromJson(json['vehicle']),
      serviceType: ServiceType.fromString(json['service_type']),
      serviceTypeDisplay: json['service_type_display'],
      scheduledDate: DateTime.parse(json['scheduled_date']),
      notes: json['notes'],
      mediaFiles: json['media_files'] != null
          ? (json['media_files'] as List)
              .map((m) => MediaFile.fromJson(m))
              .toList()
          : null,
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: json['updated_at'] != null 
          ? DateTime.parse(json['updated_at']) 
          : null,
      reviewedAt: json['reviewed_at'] != null 
          ? DateTime.parse(json['reviewed_at']) 
          : null,
      adminNotes: json['admin_notes'],
      mediaCount: json['media_count'],
    );
  }
}
```

---

### 7.4 MediaFile Model

```dart
class MediaFile {
  final int id;
  final String mediaType;
  final String mediaTypeDisplay;
  final String? localPath;
  final String? driveViewUrl;
  final int? fileSizeKb;
  final DateTime uploadedAt;

  MediaFile({
    required this.id,
    required this.mediaType,
    required this.mediaTypeDisplay,
    this.localPath,
    this.driveViewUrl,
    this.fileSizeKb,
    required this.uploadedAt,
  });

  factory MediaFile.fromJson(Map<String, dynamic> json) {
    return MediaFile(
      id: json['id'],
      mediaType: json['media_type'],
      mediaTypeDisplay: json['media_type_display'],
      localPath: json['local_path'],
      driveViewUrl: json['drive_view_url'],
      fileSizeKb: json['file_size_kb'],
      uploadedAt: DateTime.parse(json['uploaded_at']),
    );
  }

  // URL الصورة (يفضل Drive، وإلا المحلية)
  String? get imageUrl => driveViewUrl ?? localPath;
  
  // حجم الملف بشكل مقروء
  String get fileSizeDisplay {
    if (fileSizeKb == null) return 'غير معروف';
    if (fileSizeKb! < 1024) return '$fileSizeKb KB';
    return '${(fileSizeKb! / 1024).toStringAsFixed(1)} MB';
  }
}
```

---

### 7.5 Enums

```dart
// حالات الطلبات
enum RequestStatus {
  PENDING,
  APPROVED,
  REJECTED,
  COMPLETED,
  CLOSED;

  static RequestStatus fromString(String value) {
    return RequestStatus.values.firstWhere(
      (e) => e.name == value,
      orElse: () => RequestStatus.PENDING,
    );
  }

  String get displayName {
    switch (this) {
      case RequestStatus.PENDING:
        return 'قيد الانتظار';
      case RequestStatus.APPROVED:
        return 'موافق عليه';
      case RequestStatus.REJECTED:
        return 'مرفوض';
      case RequestStatus.COMPLETED:
        return 'مكتمل';
      case RequestStatus.CLOSED:
        return 'مغلق';
    }
  }

  Color get color {
    switch (this) {
      case RequestStatus.PENDING:
        return Colors.orange;
      case RequestStatus.APPROVED:
        return Colors.green;
      case RequestStatus.REJECTED:
        return Colors.red;
      case RequestStatus.COMPLETED:
        return Colors.blue;
      case RequestStatus.CLOSED:
        return Colors.grey;
    }
  }
}

// أنواع خدمات الغسيل
enum ServiceType {
  normal('normal', 'غسيل عادي'),
  polish('polish', 'تلميع وتنظيف'),
  fullClean('full_clean', 'تنظيف شامل');

  final String value;
  final String displayName;
  const ServiceType(this.value, this.displayName);

  static ServiceType fromString(String value) {
    return ServiceType.values.firstWhere(
      (e) => e.value == value,
      orElse: () => ServiceType.normal,
    );
  }
}

// أنواع الفحص
enum InspectionType {
  periodic('periodic', 'فحص دوري'),
  comprehensive('comprehensive', 'فحص شامل'),
  preSale('pre_sale', 'فحص قبل البيع');

  final String value;
  final String displayName;
  const InspectionType(this.value, this.displayName);

  static InspectionType fromString(String value) {
    return InspectionType.values.firstWhere(
      (e) => e.value == value,
      orElse: () => InspectionType.periodic,
    );
  }
}
```

---

## 🔐 8. الأمان والقيود

### 8.1 المصادقة
- ✅ جميع الـ endpoints (ماعدا login) تتطلب JWT Token
- ✅ أرسل التوكن في الـ Header: `Authorization: Bearer {TOKEN}`
- ✅ صلاحية التوكن: 30 يوم

### 8.2 حدود الملفات
| نوع الملف | الحد الأقصى للحجم | الصيغ المدعومة |
|-----------|-------------------|----------------|
| صور | 10 MB | JPG, JPEG, PNG, HEIC |
| فيديو | 500 MB | MP4, MOV, AVI |

### 8.3 حدود الطلبات
- غسيل السيارات: **5 صور إلزامية** (لا أكثر ولا أقل)
- فحص السيارات: حتى **20 صورة** + **3 فيديوهات**

---

## ⚠️ 9. معالجة الأخطاء

### مثال شامل لمعالجة الأخطاء

```dart
Future<T> handleRequest<T>(Future<T> Function() request) async {
  try {
    return await request();
  } on DioException catch (e) {
    // أخطاء من السيرفر
    if (e.response != null) {
      final statusCode = e.response!.statusCode;
      final message = e.response!.data['message'] ?? 'حدث خطأ';
      
      switch (statusCode) {
        case 400:
          throw BadRequestException(message);
        case 401:
          throw UnauthorizedException('انتهت صلاحية الجلسة');
        case 403:
          throw ForbiddenException('ليس لديك صلاحية');
        case 404:
          throw NotFoundException('البيانات غير موجودة');
        case 500:
          throw ServerException('خطأ في الخادم');
        default:
          throw Exception(message);
      }
    }
    
    // أخطاء الاتصال
    if (e.type == DioExceptionType.connectionTimeout) {
      throw ConnectionException('انتهى وقت الاتصال');
    }
    if (e.type == DioExceptionType.receiveTimeout) {
      throw ConnectionException('انتهى وقت الاستجابة');
    }
    
    throw ConnectionException('فشل الاتصال بالخادم');
  } catch (e) {
    rethrow;
  }
}

// استخدام
Future<void> createRequest() async {
  try {
    await handleRequest(() => service.createCarWashRequest(...));
    // نجح
  } on UnauthorizedException {
    // إعادة تسجيل الدخول
  } on BadRequestException catch (e) {
    // عرض رسالة الخطأ للمستخدم
    showError(e.message);
  } catch (e) {
    // خطأ غير متوقع
    showError('حدث خطأ غير متوقع');
  }
}
```

---

## 🎯 10. أمثلة عملية كاملة

### مثال 1: تطبيق كامل لإنشاء طلب غسيل

```dart
// Screen لإنشاء طلب غسيل
class CreateCarWashScreen extends StatefulWidget {
  @override
  _CreateCarWashScreenState createState() => _CreateCarWashScreenState();
}

class _CreateCarWashScreenState extends State<CreateCarWashScreen> {
  final _formKey = GlobalKey<FormState>();
  final ImagePicker _picker = ImagePicker();
  
  int? selectedVehicleId;
  ServiceType selectedServiceType = ServiceType.normal;
  DateTime selectedDate = DateTime.now().add(Duration(days: 1));
  String notes = '';
  
  File? photoPlate;
  File? photoFront;
  File? photoBack;
  File? photoRight;
  File? photoLeft;
  
  bool isLoading = false;

  Future<void> _pickImage(ImageSource source, Function(File) onPicked) async {
    final XFile? image = await _picker.pickImage(source: source);
    if (image != null) {
      onPicked(File(image.path));
      setState(() {});
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    
    // التحقق من الصور
    if (photoPlate == null || photoFront == null || 
        photoBack == null || photoRight == null || photoLeft == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('يرجى التقاط جميع الصور الخمس')),
      );
      return;
    }

    setState(() => isLoading = true);

    try {
      final service = CarWashService(dio, token);
      final requestId = await service.createCarWashRequest(
        vehicleId: selectedVehicleId!,
        serviceType: selectedServiceType,
        scheduledDate: selectedDate,
        notes: notes.isNotEmpty ? notes : null,
        photoPlate: photoPlate!,
        photoFront: photoFront!,
        photoBack: photoBack!,
        photoRightSide: photoRight!,
        photoLeftSide: photoLeft!,
      );

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('تم إنشاء الطلب بنجاح (#$requestId)')),
      );
      
      Navigator.pop(context, true);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('خطأ: $e')),
      );
    } finally {
      setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('طلب غسيل سيارة')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: EdgeInsets.all(16),
          children: [
            // اختيار السيارة
            DropdownButtonFormField<int>(
              decoration: InputDecoration(labelText: 'اختر السيارة'),
              value: selectedVehicleId,
              items: vehicles.map((v) => DropdownMenuItem(
                value: v.id,
                child: Text(v.displayName),
              )).toList(),
              onChanged: (value) => setState(() => selectedVehicleId = value),
              validator: (value) => value == null ? 'مطلوب' : null,
            ),
            
            // نوع الخدمة
            DropdownButtonFormField<ServiceType>(
              decoration: InputDecoration(labelText: 'نوع الخدمة'),
              value: selectedServiceType,
              items: ServiceType.values.map((type) => DropdownMenuItem(
                value: type,
                child: Text(type.displayName),
              )).toList(),
              onChanged: (value) => setState(() => selectedServiceType = value!),
            ),
            
            // التاريخ
            ListTile(
              title: Text('التاريخ'),
              subtitle: Text(DateFormat('yyyy-MM-dd').format(selectedDate)),
              trailing: Icon(Icons.calendar_today),
              onTap: () async {
                final date = await showDatePicker(
                  context: context,
                  initialDate: selectedDate,
                  firstDate: DateTime.now(),
                  lastDate: DateTime.now().add(Duration(days: 90)),
                );
                if (date != null) setState(() => selectedDate = date);
              },
            ),
            
            // الصور
            Text('الصور المطلوبة', style: TextStyle(fontWeight: FontWeight.bold)),
            _buildPhotoTile('صورة اللوحة', photoPlate, (f) => photoPlate = f),
            _buildPhotoTile('صورة أمامية', photoFront, (f) => photoFront = f),
            _buildPhotoTile('صورة خلفية', photoBack, (f) => photoBack = f),
            _buildPhotoTile('صورة اليمين', photoRight, (f) => photoRight = f),
            _buildPhotoTile('صورة اليسار', photoLeft, (f) => photoLeft = f),
            
            // ملاحظات
            TextField(
              decoration: InputDecoration(labelText: 'ملاحظات (اختياري)'),
              maxLines: 3,
              onChanged: (value) => notes = value,
            ),
            
            SizedBox(height: 20),
            
            // زر الإرسال
            ElevatedButton(
              onPressed: isLoading ? null : _submit,
              child: isLoading 
                  ? CircularProgressIndicator() 
                  : Text('إنشاء الطلب'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPhotoTile(String title, File? file, Function(File) onPicked) {
    return ListTile(
      title: Text(title),
      subtitle: file != null ? Text('تم الاختيار') : Text('لم يتم الاختيار'),
      trailing: file != null ? Icon(Icons.check_circle, color: Colors.green) : null,
      leading: file != null 
          ? Image.file(file, width: 50, height: 50, fit: BoxFit.cover)
          : Icon(Icons.camera_alt),
      onTap: () => _pickImage(ImageSource.camera, onPicked),
    );
  }
}
```

---

## 📞 الدعم

للأسئلة أو المشاكل الفنية، تواصل مع فريق التطوير.

---

**آخر تحديث:** 10 نوفمبر 2024  
**الإصدار:** 1.0.0  
**إجمالي الـ Endpoints:** 28
