# 📱 نُظم - Flutter API Documentation
## توثيق API الكامل لتطبيق Flutter

**آخر تحديث:** 10 نوفمبر 2024  
**إصدار API:** v1  
**Base URL:** `https://your-domain.replit.app/api/v1`

---

## 📑 ملخص سريع للـ Endpoints

### 🔐 Authentication
- `POST /auth/login` - تسجيل الدخول

### 🚗 Car Wash (طلبات غسيل السيارات)
- `POST /requests/create-car-wash` - إنشاء طلب غسيل (مع 5 صور)
- `PUT /requests/car-wash/{id}` - تعديل طلب غسيل
- `GET /requests/car-wash` - قائمة طلبات الغسيل مع الفلترة
- `GET /requests/car-wash/{id}` - تفاصيل طلب غسيل موسعة
- `DELETE /requests/car-wash/{id}/media/{media_id}` - حذف صورة

### 🔍 Car Inspection (طلبات فحص السيارات)
- `POST /requests/create-car-inspection` - إنشاء طلب فحص (صور + فيديوهات)
- `PUT /requests/car-inspection/{id}` - تعديل طلب فحص
- `GET /requests/car-inspection` - قائمة طلبات الفحص مع الفلترة
- `DELETE /requests/car-inspection/{id}/media/{media_id}` - حذف ملف

### 🗂️ General Requests
- `GET /requests` - قائمة جميع الطلبات
- `GET /requests/{id}` - تفاصيل طلب
- `DELETE /requests/{id}` - حذف طلب

### ✅ Status Management
- `POST /requests/{id}/approve` - الموافقة على طلب (إداري)
- `POST /requests/{id}/reject` - رفض طلب (إداري)

### 📊 Other
- `GET /requests/statistics` - الإحصائيات
- `GET /vehicles` - قائمة السيارات
- `GET /notifications` - الإشعارات
- `PUT /notifications/{id}/read` - تعليم كمقروء

---

## 🔐 1. Authentication

### تسجيل الدخول
**POST** `/api/v1/auth/login`

```json
// Request
{
  "employee_id": "EMP001",
  "password": "password123"
}

// Response 200 OK
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "employee": {
    "id": 1,
    "employee_id": "EMP001",
    "name": "أحمد محمد",
    "email": "ahmad@example.com",
    "job_title": "مهندس برمجيات",
    "department": "تقنية المعلومات",
    "profile_image": "/static/uploads/employees/profile_1.jpg"
  }
}
```

**Flutter Code:**
```dart
Future<Map<String, dynamic>> login(String employeeId, String password) async {
  final response = await dio.post('/auth/login', data: {
    'employee_id': employeeId,
    'password': password,
  });
  
  if (response.data['success']) {
    final token = response.data['token'];
    // Save token using flutter_secure_storage
    return response.data;
  }
  throw Exception(response.data['message']);
}
```

---

## 🚗 2. Car Wash Endpoints

### 2.1 إنشاء طلب غسيل سيارة
**POST** `/api/v1/requests/create-car-wash`

**Headers:** `Authorization: Bearer {TOKEN}`, `Content-Type: multipart/form-data`

**Form Data:**
```
vehicle_id: 5
service_type: normal|polish|full_clean
scheduled_date: 2024-11-15
notes: ملاحظات (optional)

photo_plate: [FILE]
photo_front: [FILE]
photo_back: [FILE]
photo_right_side: [FILE]
photo_left_side: [FILE]
```

**Response 201:**
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
    "vehicle_plate": "ن ج ر 1234"
  }
}
```

**Flutter Code:**
```dart
Future<int> createCarWashRequest({
  required int vehicleId,
  required String serviceType,
  required DateTime scheduledDate,
  String? notes,
  required File photoPlate,
  required File photoFront,
  required File photoBack,
  required File photoRight,
  required File photoLeft,
}) async {
  final formData = FormData.fromMap({
    'vehicle_id': vehicleId,
    'service_type': serviceType,
    'scheduled_date': DateFormat('yyyy-MM-dd').format(scheduledDate),
    if (notes != null) 'notes': notes,
    'photo_plate': await MultipartFile.fromFile(photoPlate.path),
    'photo_front': await MultipartFile.fromFile(photoFront.path),
    'photo_back': await MultipartFile.fromFile(photoBack.path),
    'photo_right_side': await MultipartFile.fromFile(photoRight.path),
    'photo_left_side': await MultipartFile.fromFile(photoLeft.path),
  });

  final response = await dio.post('/requests/create-car-wash',
    data: formData,
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );

  return response.data['data']['request_id'];
}
```

---

### 2.2 تعديل طلب غسيل سيارة
**PUT** `/api/v1/requests/car-wash/{request_id}`

**Form Data (all optional):**
```
vehicle_id: 5
service_type: polish
scheduled_date: 2024-11-20
notes: ملاحظات محدثة

// صور جديدة (فقط ما تريد تغييره)
photo_plate: [FILE]
photo_front: [FILE]

// حذف صور
delete_media_ids: [1,2,3]
```

**Response 200:**
```json
{
  "success": true,
  "message": "تم تحديث طلب الغسيل بنجاح",
  "request": {
    "id": 123,
    "type": "CAR_WASH",
    "status": "PENDING",
    "vehicle": {"id": 5, "plate_number": "ن ج ر 1234"},
    "service_type": "polish",
    "scheduled_date": "2024-11-20",
    "media_count": 5,
    "updated_at": "2024-11-10T19:30:00"
  }
}
```

---

### 2.3 قائمة طلبات الغسيل
**GET** `/api/v1/requests/car-wash?status=PENDING&page=1&per_page=20`

**Query Parameters:**
- `status` - PENDING|APPROVED|REJECTED|COMPLETED
- `vehicle_id` - رقم السيارة
- `from_date` - YYYY-MM-DD
- `to_date` - YYYY-MM-DD
- `page` - default: 1
- `per_page` - default: 20

**Response 200:**
```json
{
  "success": true,
  "requests": [{
    "id": 123,
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
    "created_at": "2024-11-10T10:30:00"
  }],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 25,
    "pages": 2
  }
}
```

**Flutter Code:**
```dart
Future<List<CarWashRequest>> getCarWashRequests({
  String? status,
  int page = 1,
}) async {
  final response = await dio.get('/requests/car-wash',
    queryParameters: {
      'page': page,
      if (status != null) 'status': status,
    },
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );

  return (response.data['requests'] as List)
      .map((json) => CarWashRequest.fromJson(json))
      .toList();
}
```

---

### 2.4 تفاصيل طلب غسيل
**GET** `/api/v1/requests/car-wash/{request_id}`

**Response 200:**
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
    "notes": "ملاحظات",
    "media_files": [
      {
        "id": 101,
        "media_type": "PLATE",
        "media_type_display": "لوحة السيارة",
        "local_path": "/static/uploads/car_wash/wash_123_plate.jpg",
        "drive_view_url": "https://drive.google.com/...",
        "file_size_kb": 234,
        "uploaded_at": "2024-11-10T10:35:00"
      }
    ],
    "created_at": "2024-11-10T10:30:00",
    "reviewed_at": null,
    "admin_notes": null
  }
}
```

---

### 2.5 حذف صورة من طلب غسيل
**DELETE** `/api/v1/requests/car-wash/{request_id}/media/{media_id}`

**Response 200:**
```json
{
  "success": true,
  "message": "تم حذف الصورة بنجاح",
  "remaining_media_count": 4
}
```

---

## 🔍 3. Car Inspection Endpoints

### 3.1 إنشاء طلب فحص سيارة
**POST** `/api/v1/requests/create-car-inspection`

**Form Data:**
```
vehicle_id: 5
inspection_type: periodic|comprehensive|pre_sale
inspection_date: 2024-11-15
notes: ملاحظات (optional)

files: [FILE1, FILE2, FILE3...] // صور + فيديوهات
```

**Response 201:**
```json
{
  "success": true,
  "message": "تم إنشاء طلب الفحص بنجاح",
  "data": {
    "request_id": 456,
    "type": "car_inspection",
    "status": "pending",
    "inspection_type": "comprehensive",
    "inspection_type_ar": "فحص شامل"
  }
}
```

**Flutter Code:**
```dart
Future<int> createCarInspectionRequest({
  required int vehicleId,
  required String inspectionType,
  required DateTime inspectionDate,
  String? notes,
  required List<File> files,
}) async {
  final formData = FormData.fromMap({
    'vehicle_id': vehicleId,
    'inspection_type': inspectionType,
    'inspection_date': DateFormat('yyyy-MM-dd').format(inspectionDate),
    if (notes != null) 'notes': notes,
    'files': await Future.wait(
      files.map((f) => MultipartFile.fromFile(f.path)),
    ),
  });

  final response = await dio.post('/requests/create-car-inspection',
    data: formData,
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );

  return response.data['data']['request_id'];
}
```

---

### 3.2 تعديل طلب فحص
**PUT** `/api/v1/requests/car-inspection/{request_id}`

**Form Data (all optional):**
```
vehicle_id: 5
inspection_type: comprehensive
inspection_date: 2024-11-20
notes: ملاحظات

files: [FILE1, FILE2]
delete_media_ids: [5,6,7]
```

**Response 200:**
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
      "images_count": 10,
      "videos_count": 2
    }
  }
}
```

---

### 3.3 قائمة طلبات الفحص
**GET** `/api/v1/requests/car-inspection?status=PENDING`

نفس معاملات الفلترة مثل car-wash

**Response 200:**
```json
{
  "success": true,
  "requests": [{
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
  }],
  "pagination": {"page": 1, "total": 15}
}
```

---

### 3.4 حذف ملف من طلب فحص
**DELETE** `/api/v1/requests/car-inspection/{request_id}/media/{media_id}`

**Response 200:**
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

## 🗂️ 4. General Request Management

### 4.1 حذف طلب
**DELETE** `/api/v1/requests/{request_id}`

⚠️ يمكن حذف الطلب فقط إذا كان `PENDING`

**Response 200:**
```json
{"success": true, "message": "تم حذف الطلب بنجاح"}
```

**Response 400:**
```json
{"success": false, "message": "لا يمكن حذف طلب تمت معالجته"}
```

---

### 4.2 قائمة جميع الطلبات
**GET** `/api/v1/requests?type=CAR_WASH&status=PENDING`

**Query Parameters:**
- `page`, `per_page`
- `status` - PENDING|APPROVED|REJECTED|COMPLETED|CLOSED
- `type` - INVOICE|CAR_WASH|CAR_INSPECTION|ADVANCE_PAYMENT

---

### 4.3 تفاصيل طلب (أي نوع)
**GET** `/api/v1/requests/{request_id}`

---

## ✅ 5. Status Management

### 5.1 الموافقة على طلب
**POST** `/api/v1/requests/{request_id}/approve`

**Request (optional):**
```json
{"admin_notes": "تمت الموافقة"}
```

**Response 200:**
```json
{
  "success": true,
  "message": "تمت الموافقة على الطلب",
  "request": {
    "id": 123,
    "status": "APPROVED",
    "reviewed_at": "2024-11-10T19:30:00",
    "reviewed_by": {"id": 1, "name": "أحمد الإداري"}
  }
}
```

**Flutter Code:**
```dart
Future<bool> approveRequest(int requestId, {String? notes}) async {
  final response = await dio.post('/requests/$requestId/approve',
    data: {'admin_notes': notes},
    options: Options(headers: {'Authorization': 'Bearer $token'}),
  );
  return response.data['success'];
}
```

---

### 5.2 رفض طلب
**POST** `/api/v1/requests/{request_id}/reject`

**Request (required):**
```json
{"rejection_reason": "سبب الرفض"}
```

**Response 200:**
```json
{
  "success": true,
  "message": "تم رفض الطلب",
  "request": {
    "id": 123,
    "status": "REJECTED",
    "rejection_reason": "سبب الرفض",
    "reviewed_at": "2024-11-10T19:30:00"
  }
}
```

---

## 📊 6. Statistics & Other

### 6.1 الإحصائيات
**GET** `/api/v1/requests/statistics`

```json
{
  "success": true,
  "statistics": {
    "total": 45,
    "pending": 5,
    "approved": 35,
    "rejected": 3,
    "by_type": {
      "CAR_WASH": 10,
      "CAR_INSPECTION": 8
    }
  }
}
```

---

### 6.2 قائمة السيارات
**GET** `/api/v1/vehicles`

```json
{
  "success": true,
  "vehicles": [{
    "id": 5,
    "plate_number": "ن ج ر 1234",
    "make": "تويوتا",
    "model": "كامري",
    "year": 2022,
    "color": "فضي"
  }]
}
```

---

### 6.3 الإشعارات
**GET** `/api/v1/notifications?unread_only=true`

```json
{
  "success": true,
  "notifications": [{
    "id": 1,
    "request_id": 123,
    "title": "تمت الموافقة على طلبك",
    "message": "تمت الموافقة على طلب غسيل سيارة",
    "type": "APPROVED",
    "is_read": false,
    "created_at": "2024-11-09T14:20:00"
  }],
  "unread_count": 3
}
```

---

### 6.4 تعليم إشعار كمقروء
**PUT** `/api/v1/notifications/{notification_id}/read`

---

## 📱 Flutter Models

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
      mediaFiles: (json['media_files'] as List?)
          ?.map((m) => MediaFile.fromJson(m))
          .toList() ?? [],
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}
```

---

### MediaFile Model:
```dart
class MediaFile {
  final int id;
  final String mediaType;
  final String mediaTypeDisplay;
  final String? localPath;
  final String? driveViewUrl;

  factory MediaFile.fromJson(Map<String, dynamic> json) {
    return MediaFile(
      id: json['id'],
      mediaType: json['media_type'],
      mediaTypeDisplay: json['media_type_display'],
      localPath: json['local_path'],
      driveViewUrl: json['drive_view_url'],
    );
  }
}
```

---

### Vehicle Model:
```dart
class Vehicle {
  final int id;
  final String plateNumber;
  final String make;
  final String model;
  final int? year;
  final String? color;

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
}
```

---

## 📊 Enums

### RequestStatus:
```dart
enum RequestStatus {
  PENDING,    // قيد الانتظار
  APPROVED,   // موافق عليه
  REJECTED,   // مرفوض
  COMPLETED,  // مكتمل
  CLOSED,     // مغلق
}
```

### ServiceType:
```dart
enum ServiceType {
  normal,      // غسيل عادي
  polish,      // تلميع وتنظيف
  full_clean,  // تنظيف شامل
}
```

### InspectionType:
```dart
enum InspectionType {
  periodic,       // فحص دوري
  comprehensive,  // فحص شامل
  pre_sale,       // فحص قبل البيع
}
```

---

## 🔐 Security Notes

1. **JWT Token**: صلاحية 30 يوم - احفظه بـ `flutter_secure_storage`
2. **File Sizes**: صور 10MB، فيديو 500MB
3. **Formats**: PNG, JPG, JPEG, HEIC | MP4, MOV, AVI
4. **Permissions**: بعض endpoints تتطلب صلاحيات إدارية

---

## ⚠️ Error Handling

```dart
try {
  final result = await service.createCarWashRequest(...);
} on DioError catch (e) {
  if (e.response != null) {
    final message = e.response!.data['message'];
    print('Error: $message');
  } else {
    print('Connection error');
  }
}
```

---

**آخر تحديث:** 10 نوفمبر 2024  
**للدعم:** تواصل مع فريق التطوير
