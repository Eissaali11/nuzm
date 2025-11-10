# خطة API لطلبات غسيل السيارات وفحص السيارات
## Car Wash & Car Inspection API Plan

---

## 📋 الوضع الحالي (Current Status)

### ✅ Endpoints الموجودة حالياً:

#### 1. إنشاء طلبات (Create):
- **POST** `/api/v1/requests/create-car-wash` ✅
  - دعم multipart/form-data
  - رفع 5 صور (لوحة، أمام، خلف، يمين، يسار)
  
- **POST** `/api/v1/requests/create-car-inspection` ✅
  - دعم multipart/form-data
  - رفع صور وفيديوهات متعددة

#### 2. عرض الطلبات (View):
- **GET** `/api/v1/requests` ✅
  - فلترة بـ `type=CAR_WASH` أو `type=CAR_INSPECTION`
  - فلترة بـ `status=PENDING/APPROVED/REJECTED`
  
- **GET** `/api/v1/requests/{request_id}` ✅
  - تفاصيل الطلب مع الصور/الفيديوهات

#### 3. رفع ملفات إضافية (Upload):
- **POST** `/api/v1/requests/{request_id}/upload` ✅
  - رفع ملفات إضافية لطلب موجود

---

## ❌ الـ Endpoints الناقصة (Missing)

### 1. التعديل (Update):
- ❌ **PUT** `/api/v1/requests/car-wash/{request_id}`
- ❌ **PUT** `/api/v1/requests/car-inspection/{request_id}`

### 2. الحذف (Delete):
- ❌ **DELETE** `/api/v1/requests/{request_id}`
- ❌ **DELETE** `/api/v1/requests/car-wash/{request_id}/media/{media_id}`
- ❌ **DELETE** `/api/v1/requests/car-inspection/{request_id}/media/{media_id}`

### 3. إدارة الحالة (Status Management):
- ❌ **POST** `/api/v1/requests/{request_id}/approve`
- ❌ **POST** `/api/v1/requests/{request_id}/reject`

### 4. قوائم مخصصة (Custom Lists):
- ❌ **GET** `/api/v1/requests/car-wash` - قائمة طلبات الغسيل فقط
- ❌ **GET** `/api/v1/requests/car-inspection` - قائمة طلبات الفحص فقط

---

## 🎯 الخطة المقترحة (Proposed Plan)

سنقوم بإضافة 10 endpoints جديدة لتغطية جميع العمليات:

---

## 📝 التوثيق التفصيلي (Detailed Documentation)

---

### 1️⃣ تعديل طلب غسيل سيارة
**PUT** `/api/v1/requests/car-wash/{request_id}`

#### Request Headers:
```
Authorization: Bearer {JWT_TOKEN}
Content-Type: multipart/form-data
```

#### Request Body (multipart/form-data):
```
vehicle_id: 5
service_type: normal|polish|full_clean
scheduled_date: 2024-11-15
notes: ملاحظات إضافية (اختياري)

// صور جديدة (اختياري)
photo_plate: [FILE]
photo_front: [FILE]
photo_back: [FILE]
photo_right_side: [FILE]
photo_left_side: [FILE]

// حذف صور موجودة (اختياري)
delete_media_ids: [1,2,3]
```

#### Response (200 OK):
```json
{
  "success": true,
  "message": "تم تحديث طلب الغسيل بنجاح",
  "request": {
    "id": 15,
    "type": "CAR_WASH",
    "status": "PENDING",
    "vehicle": {
      "id": 5,
      "plate_number": "ن ج ر 1234"
    },
    "service_type": "polish",
    "scheduled_date": "2024-11-15",
    "media_count": 5,
    "updated_at": "2024-11-10T19:30:00"
  }
}
```

#### Flutter Example:
```dart
Future<bool> updateCarWashRequest(int requestId, {
  required int vehicleId,
  required String serviceType,
  required String scheduledDate,
  String? notes,
  File? photoPlate,
  File? photoFront,
  File? photoBack,
  File? photoRight,
  File? photoLeft,
  List<int>? deleteMediaIds,
}) async {
  final dio = Dio();
  
  FormData formData = FormData.fromMap({
    'vehicle_id': vehicleId,
    'service_type': serviceType,
    'scheduled_date': scheduledDate,
    if (notes != null) 'notes': notes,
    if (photoPlate != null) 'photo_plate': await MultipartFile.fromFile(photoPlate.path),
    if (photoFront != null) 'photo_front': await MultipartFile.fromFile(photoFront.path),
    if (photoBack != null) 'photo_back': await MultipartFile.fromFile(photoBack.path),
    if (photoRight != null) 'photo_right_side': await MultipartFile.fromFile(photoRight.path),
    if (photoLeft != null) 'photo_left_side': await MultipartFile.fromFile(photoLeft.path),
    if (deleteMediaIds != null && deleteMediaIds.isNotEmpty) 
      'delete_media_ids': deleteMediaIds.join(','),
  });

  try {
    final response = await dio.put(
      '$baseUrl/api/v1/requests/car-wash/$requestId',
      data: formData,
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return response.data['success'];
  } catch (e) {
    print('Error: $e');
    return false;
  }
}
```

---

### 2️⃣ تعديل طلب فحص سيارة
**PUT** `/api/v1/requests/car-inspection/{request_id}`

#### Request Body (multipart/form-data):
```
vehicle_id: 5
inspection_type: periodic|comprehensive|pre_sale
inspection_date: 2024-11-15
notes: ملاحظات الفحص (اختياري)

// ملفات جديدة (صور + فيديوهات)
files[]: [FILE1, FILE2, FILE3...]

// حذف ملفات موجودة
delete_media_ids: [1,2,3]
```

#### Response (200 OK):
```json
{
  "success": true,
  "message": "تم تحديث طلب الفحص بنجاح",
  "request": {
    "id": 20,
    "type": "CAR_INSPECTION",
    "status": "PENDING",
    "vehicle": {
      "id": 5,
      "plate_number": "ن ج ر 1234"
    },
    "inspection_type": "comprehensive",
    "inspection_date": "2024-11-15",
    "media": {
      "images_count": 8,
      "videos_count": 2
    },
    "updated_at": "2024-11-10T19:30:00"
  }
}
```

---

### 3️⃣ حذف طلب
**DELETE** `/api/v1/requests/{request_id}`

#### Notes:
- يمكن حذف الطلب فقط إذا كان بحالة `PENDING`
- يتم حذف جميع الملفات المرتبطة تلقائياً

#### Response (200 OK):
```json
{
  "success": true,
  "message": "تم حذف الطلب بنجاح"
}
```

#### Response (400 Bad Request):
```json
{
  "success": false,
  "message": "لا يمكن حذف طلب تمت معالجته"
}
```

#### Flutter Example:
```dart
Future<bool> deleteRequest(int requestId) async {
  try {
    final response = await dio.delete(
      '$baseUrl/api/v1/requests/$requestId',
      options: Options(headers: {'Authorization': 'Bearer $token'}),
    );
    return response.data['success'];
  } catch (e) {
    print('Error: $e');
    return false;
  }
}
```

---

### 4️⃣ حذف صورة من طلب غسيل
**DELETE** `/api/v1/requests/car-wash/{request_id}/media/{media_id}`

#### Response (200 OK):
```json
{
  "success": true,
  "message": "تم حذف الصورة بنجاح",
  "remaining_media_count": 4
}
```

---

### 5️⃣ حذف ملف من طلب فحص
**DELETE** `/api/v1/requests/car-inspection/{request_id}/media/{media_id}`

#### Response (200 OK):
```json
{
  "success": true,
  "message": "تم حذف الملف بنجاح",
  "remaining_media": {
    "images_count": 7,
    "videos_count": 2
  }
}
```

---

### 6️⃣ الموافقة على طلب
**POST** `/api/v1/requests/{request_id}/approve`

#### Request Body (JSON):
```json
{
  "admin_notes": "تمت الموافقة - لا ملاحظات" // اختياري
}
```

#### Response (200 OK):
```json
{
  "success": true,
  "message": "تمت الموافقة على الطلب",
  "request": {
    "id": 15,
    "status": "APPROVED",
    "reviewed_at": "2024-11-10T19:30:00",
    "reviewed_by": {
      "id": 1,
      "name": "أحمد الإداري"
    }
  }
}
```

#### Response (400 Bad Request):
```json
{
  "success": false,
  "message": "الطلب تمت معالجته مسبقاً"
}
```

---

### 7️⃣ رفض طلب
**POST** `/api/v1/requests/{request_id}/reject`

#### Request Body (JSON):
```json
{
  "rejection_reason": "السبب المفصل للرفض" // إجباري
}
```

#### Response (200 OK):
```json
{
  "success": true,
  "message": "تم رفض الطلب",
  "request": {
    "id": 15,
    "status": "REJECTED",
    "rejection_reason": "السبب المفصل للرفض",
    "reviewed_at": "2024-11-10T19:30:00",
    "reviewed_by": {
      "id": 1,
      "name": "أحمد الإداري"
    }
  }
}
```

---

### 8️⃣ قائمة طلبات الغسيل فقط
**GET** `/api/v1/requests/car-wash`

#### Query Parameters:
- `status` (optional): PENDING|APPROVED|REJECTED|COMPLETED
- `vehicle_id` (optional): رقم السيارة
- `from_date` (optional): YYYY-MM-DD
- `to_date` (optional): YYYY-MM-DD
- `page` (default: 1)
- `per_page` (default: 20)

#### Response (200 OK):
```json
{
  "success": true,
  "requests": [
    {
      "id": 15,
      "status": "PENDING",
      "status_display": "قيد الانتظار",
      "employee": {
        "id": 10,
        "name": "خالد أحمد",
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
      "updated_at": "2024-11-10T19:30:00"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 25,
    "pages": 2
  }
}
```

#### Flutter Example:
```dart
Future<List<CarWashRequest>> getCarWashRequests({
  String? status,
  int? vehicleId,
  String? fromDate,
  String? toDate,
  int page = 1,
}) async {
  final queryParams = {
    if (status != null) 'status': status,
    if (vehicleId != null) 'vehicle_id': vehicleId.toString(),
    if (fromDate != null) 'from_date': fromDate,
    if (toDate != null) 'to_date': toDate,
    'page': page.toString(),
  };

  final uri = Uri.parse('$baseUrl/api/v1/requests/car-wash')
      .replace(queryParameters: queryParams);

  final response = await dio.get(
    uri.toString(),
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );

  return (response.data['requests'] as List)
      .map((json) => CarWashRequest.fromJson(json))
      .toList();
}
```

---

### 9️⃣ قائمة طلبات الفحص فقط
**GET** `/api/v1/requests/car-inspection`

#### Query Parameters:
نفس المعايير السابقة

#### Response (200 OK):
```json
{
  "success": true,
  "requests": [
    {
      "id": 20,
      "status": "APPROVED",
      "status_display": "موافق عليه",
      "employee": {
        "id": 10,
        "name": "خالد أحمد"
      },
      "vehicle": {
        "id": 5,
        "plate_number": "ن ج ر 1234"
      },
      "inspection_type": "comprehensive",
      "inspection_type_display": "فحص شامل",
      "inspection_date": "2024-11-15",
      "media": {
        "images_count": 8,
        "videos_count": 2,
        "total_size_mb": 45.3
      },
      "created_at": "2024-11-10T10:30:00",
      "reviewed_at": "2024-11-10T14:20:00"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 15,
    "pages": 1
  }
}
```

---

### 🔟 تفاصيل طلب غسيل مع الصور
**GET** `/api/v1/requests/car-wash/{request_id}`

#### Response (200 OK):
```json
{
  "success": true,
  "request": {
    "id": 15,
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
    "notes": "ملاحظات إضافية",
    "media_files": [
      {
        "id": 101,
        "media_type": "PLATE",
        "media_type_display": "لوحة السيارة",
        "local_path": "/static/uploads/car_wash/wash_15_photo_plate_a1b2c3d4.jpg",
        "drive_view_url": "https://drive.google.com/file/d/...",
        "file_size_kb": 234,
        "uploaded_at": "2024-11-10T10:35:00"
      },
      {
        "id": 102,
        "media_type": "FRONT",
        "media_type_display": "صورة أمامية",
        "local_path": "/static/uploads/car_wash/wash_15_photo_front_x5y6z7w8.jpg",
        "drive_view_url": "https://drive.google.com/file/d/...",
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

---

## 🎨 هيكل البيانات للـ Flutter Models

### CarWashRequest Model:
```dart
class CarWashRequest {
  final int id;
  final String status;
  final String statusDisplay;
  final Employee employee;
  final Vehicle vehicle;
  final String serviceType;
  final String serviceTypeDisplay;
  final DateTime scheduledDate;
  final String? notes;
  final List<MediaFile> mediaFiles;
  final DateTime createdAt;
  final DateTime? updatedAt;
  final DateTime? reviewedAt;
  final User? reviewedBy;
  final String? adminNotes;

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
    required this.mediaFiles,
    required this.createdAt,
    this.updatedAt,
    this.reviewedAt,
    this.reviewedBy,
    this.adminNotes,
  });

  factory CarWashRequest.fromJson(Map<String, dynamic> json) {
    return CarWashRequest(
      id: json['id'],
      status: json['status'],
      statusDisplay: json['status_display'],
      employee: Employee.fromJson(json['employee']),
      vehicle: Vehicle.fromJson(json['vehicle']),
      serviceType: json['service_type'],
      serviceTypeDisplay: json['service_type_display'],
      scheduledDate: DateTime.parse(json['scheduled_date']),
      notes: json['notes'],
      mediaFiles: (json['media_files'] as List)
          .map((m) => MediaFile.fromJson(m))
          .toList(),
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: json['updated_at'] != null 
          ? DateTime.parse(json['updated_at']) : null,
      reviewedAt: json['reviewed_at'] != null 
          ? DateTime.parse(json['reviewed_at']) : null,
      reviewedBy: json['reviewed_by'] != null 
          ? User.fromJson(json['reviewed_by']) : null,
      adminNotes: json['admin_notes'],
    );
  }
}
```

### MediaFile Model:
```dart
class MediaFile {
  final int id;
  final String mediaType;
  final String mediaTypeDisplay;
  final String localPath;
  final String? driveViewUrl;
  final int fileSizeKb;
  final DateTime uploadedAt;

  MediaFile({
    required this.id,
    required this.mediaType,
    required this.mediaTypeDisplay,
    required this.localPath,
    this.driveViewUrl,
    required this.fileSizeKb,
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
}
```

---

## 📊 حالات الطلبات (Request Status)

```dart
enum RequestStatus {
  PENDING,      // قيد الانتظار
  APPROVED,     // موافق عليه
  REJECTED,     // مرفوض
  COMPLETED,    // مكتمل
  CLOSED,       // مغلق
}

// Helper function
String getStatusDisplay(String status) {
  switch (status) {
    case 'PENDING': return 'قيد الانتظار';
    case 'APPROVED': return 'موافق عليه';
    case 'REJECTED': return 'مرفوض';
    case 'COMPLETED': return 'مكتمل';
    case 'CLOSED': return 'مغلق';
    default: return status;
  }
}
```

---

## 🚗 أنواع خدمات الغسيل

```dart
enum ServiceType {
  normal,        // غسيل عادي
  polish,        // تلميع وتنظيف
  full_clean,    // تنظيف شامل
}

String getServiceTypeDisplay(String type) {
  switch (type) {
    case 'normal': return 'غسيل عادي';
    case 'polish': return 'تلميع وتنظيف';
    case 'full_clean': return 'تنظيف شامل';
    default: return type;
  }
}
```

---

## 🔍 أنواع الفحص

```dart
enum InspectionType {
  periodic,       // فحص دوري
  comprehensive,  // فحص شامل
  pre_sale,       // فحص قبل البيع
}

String getInspectionTypeDisplay(String type) {
  switch (type) {
    case 'periodic': return 'فحص دوري';
    case 'comprehensive': return 'فحص شامل';
    case 'pre_sale': return 'فحص قبل البيع';
    default: return type;
  }
}
```

---

## 🔐 ملاحظات الأمان

1. **JWT Token**: جميع الـ endpoints تتطلب توكن صالح
2. **الصلاحيات**:
   - الموظف: يستطيع فقط إنشاء/تعديل/حذف طلباته
   - الإداري: يستطيع الموافقة/الرفض على جميع الطلبات
3. **حجم الملفات**: الحد الأقصى 500MB لكل ملف
4. **الصيغ المدعومة**:
   - صور: PNG, JPG, JPEG, HEIC
   - فيديو: MP4, MOV, AVI

---

## ✅ خطوات التنفيذ المقترحة

### المرحلة 1: CRUD الأساسية (يوم 1)
1. ✅ PUT /requests/car-wash/{id}
2. ✅ PUT /requests/car-inspection/{id}
3. ✅ DELETE /requests/{id}

### المرحلة 2: إدارة الملفات (يوم 1)
4. ✅ DELETE /requests/car-wash/{id}/media/{media_id}
5. ✅ DELETE /requests/car-inspection/{id}/media/{media_id}

### المرحلة 3: إدارة الحالات (يوم 1)
6. ✅ POST /requests/{id}/approve
7. ✅ POST /requests/{id}/reject

### المرحلة 4: القوائم المخصصة (يوم 1)
8. ✅ GET /requests/car-wash
9. ✅ GET /requests/car-inspection
10. ✅ GET /requests/car-wash/{id} (تفاصيل موسعة)

### المرحلة 5: التوثيق والاختبار (يوم 2)
- تحديث EMPLOYEE_REQUESTS_API.md
- اختبار جميع الـ endpoints
- إنشاء مجموعة Postman Collection

---

## 📞 الدعم

للأسئلة أو المشاكل، الرجاء التواصل مع فريق التطوير.

---

**آخر تحديث:** 10 نوفمبر 2024
