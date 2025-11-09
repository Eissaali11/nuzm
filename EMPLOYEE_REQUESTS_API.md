# Employee Requests API Documentation
## نظام طلبات الموظفين - توثيق API

تم تصميم هذا الـ API للتكامل مع تطبيق Flutter لنظام طلبات الموظفين.

**Base URL:** `/api/v1`

---

## 📌 Authentication (المصادقة)

جميع endpoints (باستثناء تسجيل الدخول) تتطلب JWT Token في الـ Header:

```
Authorization: Bearer YOUR_JWT_TOKEN
```

---

## 1. تسجيل الدخول
**POST** `/api/v1/auth/login`

### Request Body:
```json
{
  "employee_id": "EMP001",
  "password": "password123"
}
```

### Response (200 OK):
```json
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

### Response Codes:
- `200 OK` - تم تسجيل الدخول بنجاح
- `400 Bad Request` - بيانات ناقصة
- `401 Unauthorized` - بيانات دخول خاطئة

---

## 2. قائمة الطلبات
**GET** `/api/v1/requests`

### Query Parameters:
- `page` (int, default: 1) - رقم الصفحة
- `per_page` (int, default: 20) - عدد العناصر في الصفحة
- `status` (string, optional) - فلترة حسب الحالة: `PENDING`, `APPROVED`, `REJECTED`, `COMPLETED`, `CLOSED`
- `type` (string, optional) - فلترة حسب النوع: `INVOICE`, `CAR_WASH`, `CAR_INSPECTION`, `ADVANCE_PAYMENT`

### Response (200 OK):
```json
{
  "success": true,
  "requests": [
    {
      "id": 1,
      "type": "INVOICE",
      "type_display": "فاتورة",
      "status": "PENDING",
      "status_display": "قيد الانتظار",
      "title": "فاتورة شراء معدات",
      "description": "شراء جهاز كمبيوتر محمول",
      "amount": 5000.00,
      "created_at": "2024-11-09T10:30:00",
      "updated_at": "2024-11-09T10:30:00",
      "reviewed_at": null,
      "admin_notes": null,
      "google_drive_folder_url": "https://drive.google.com/drive/folders/..."
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

---

## 3. تفاصيل طلب معين
**GET** `/api/v1/requests/{request_id}`

### Response (200 OK):
```json
{
  "success": true,
  "request": {
    "id": 1,
    "type": "CAR_WASH",
    "type_display": "غسيل سيارة",
    "status": "APPROVED",
    "status_display": "موافق عليه",
    "title": "طلب غسيل سيارة",
    "description": "غسيل وتلميع شامل",
    "amount": 150.00,
    "created_at": "2024-11-09T10:30:00",
    "updated_at": "2024-11-09T14:20:00",
    "reviewed_at": "2024-11-09T14:20:00",
    "admin_notes": "تمت الموافقة",
    "google_drive_folder_url": "https://drive.google.com/drive/folders/...",
    "details": {
      "service_type": "غسيل وتلميع",
      "scheduled_date": "2024-11-10",
      "vehicle": {
        "id": 5,
        "plate_number": "ن ج ر 1234",
        "make": "تويوتا",
        "model": "كامري"
      },
      "media_files": [
        {
          "id": 1,
          "file_type": "image",
          "drive_file_id": "1abc...",
          "drive_view_url": "https://drive.google.com/...",
          "uploaded_at": "2024-11-09T10:35:00"
        }
      ]
    }
  }
}
```

### Response Codes:
- `200 OK` - نجح الاستعلام
- `404 Not Found` - الطلب غير موجود

---

## 4. إنشاء طلب جديد
**POST** `/api/v1/requests`

### Request Body Examples:

#### فاتورة (INVOICE):
```json
{
  "type": "INVOICE",
  "title": "فاتورة شراء مستلزمات",
  "description": "شراء أدوات مكتبية",
  "amount": 850.00,
  "details": {
    "vendor_name": "مكتبة الرياض",
    "invoice_date": "2024-11-09"
  }
}
```

#### غسيل سيارة (CAR_WASH):
```json
{
  "type": "CAR_WASH",
  "title": "طلب غسيل سيارة",
  "description": "غسيل عادي",
  "amount": 80.00,
  "details": {
    "vehicle_id": 5,
    "service_type": "غسيل عادي",
    "scheduled_date": "2024-11-10"
  }
}
```

#### فحص سيارة (CAR_INSPECTION):
```json
{
  "type": "CAR_INSPECTION",
  "title": "طلب فحص دوري",
  "description": "فحص شامل",
  "amount": 200.00,
  "details": {
    "vehicle_id": 5,
    "inspection_type": "فحص دوري",
    "inspection_date": "2024-11-10"
  }
}
```

#### سلفة (ADVANCE_PAYMENT):
```json
{
  "type": "ADVANCE_PAYMENT",
  "title": "طلب سلفة",
  "description": "سلفة لحالة طارئة",
  "amount": 3000.00,
  "details": {
    "requested_amount": 3000.00,
    "reason": "حالة طارئة - علاج",
    "installments": 6,
    "installment_amount": 500.00
  }
}
```

### Response (201 Created):
```json
{
  "success": true,
  "request_id": 123,
  "message": "تم إنشاء الطلب بنجاح"
}
```

### Response Codes:
- `201 Created` - تم إنشاء الطلب بنجاح
- `400 Bad Request` - بيانات ناقصة أو خاطئة

---

## 5. رفع ملفات (صور/فيديوهات)
**POST** `/api/v1/requests/{request_id}/upload`

### Content-Type:
`multipart/form-data`

### Form Data:
- `files[]`: ملف أو عدة ملفات (صور: PNG, JPG, JPEG, HEIC | فيديو: MP4, MOV, AVI)
- الحد الأقصى لكل ملف: **500MB**

### Example (cURL):
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "files[]=@image1.jpg" \
  -F "files[]=@image2.jpg" \
  -F "files[]=@video.mp4" \
  http://localhost:5000/api/v1/requests/123/upload
```

### Example (Flutter - dio package):
```dart
import 'package:dio/dio.dart';

Future<void> uploadFiles(int requestId, List<File> files) async {
  final dio = Dio();
  
  FormData formData = FormData.fromMap({
    'files': files.map((file) => 
      MultipartFile.fromFileSync(file.path, filename: file.path.split('/').last)
    ).toList(),
  });

  try {
    final response = await dio.post(
      'http://localhost:5000/api/v1/requests/$requestId/upload',
      data: formData,
      options: Options(
        headers: {
          'Authorization': 'Bearer $jwtToken',
        },
      ),
    );
    
    print('تم رفع الملفات: ${response.data}');
  } catch (e) {
    print('خطأ: $e');
  }
}
```

### Response (200 OK):
```json
{
  "success": true,
  "uploaded_files": [
    {
      "filename": "image1.jpg",
      "drive_url": "https://drive.google.com/file/d/...",
      "file_id": "1abc..."
    },
    {
      "filename": "video.mp4",
      "drive_url": "https://drive.google.com/file/d/...",
      "file_id": "1xyz..."
    }
  ],
  "google_drive_folder_url": "https://drive.google.com/drive/folders/...",
  "message": "تم رفع 2 ملف بنجاح إلى Google Drive"
}
```

### ملاحظات هامة:
- جميع الملفات يتم رفعها إلى **Google Drive فقط**
- لا يتم حفظ الملفات محلياً في السيرفر (temporary files only)
- يتم إنشاء مجلد خاص لكل طلب على Drive تلقائياً
- البنية: `نُظم / طلبات الموظفين / [نوع الطلب] / [رقم الطلب] - [اسم الموظف] - [التاريخ]`

### Response Codes:
- `200 OK` - تم رفع الملفات بنجاح
- `404 Not Found` - الطلب غير موجود
- `503 Service Unavailable` - خدمة Google Drive غير متاحة

---

## 6. الإحصائيات
**GET** `/api/v1/requests/statistics`

### Response (200 OK):
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

## 7. أنواع الطلبات المتاحة
**GET** `/api/v1/requests/types`

⚠️ **لا يتطلب توكن** - متاح للجميع

### Response (200 OK):
```json
{
  "success": true,
  "types": [
    {
      "value": "INVOICE",
      "label_ar": "فاتورة"
    },
    {
      "value": "CAR_WASH",
      "label_ar": "غسيل سيارة"
    },
    {
      "value": "CAR_INSPECTION",
      "label_ar": "فحص وتوثيق سيارة"
    },
    {
      "value": "ADVANCE_PAYMENT",
      "label_ar": "سلفة مالية"
    }
  ]
}
```

---

## 8. قائمة السيارات
**GET** `/api/v1/vehicles`

### Response (200 OK):
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

## 9. الإشعارات
**GET** `/api/v1/notifications`

### Query Parameters:
- `unread_only` (boolean, default: false) - عرض غير المقروءة فقط
- `page` (int, default: 1)
- `per_page` (int, default: 20)

### Response (200 OK):
```json
{
  "success": true,
  "notifications": [
    {
      "id": 1,
      "request_id": 123,
      "title": "تمت الموافقة على طلبك",
      "message": "تمت الموافقة على طلب فاتورة",
      "type": "APPROVED",
      "is_read": false,
      "created_at": "2024-11-09T14:20:00"
    }
  ],
  "unread_count": 3,
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 12,
    "pages": 1
  }
}
```

---

## 10. تعليم إشعار كمقروء
**PUT** `/api/v1/notifications/{notification_id}/read`

### Response (200 OK):
```json
{
  "success": true,
  "message": "تم تعليم الإشعار كمقروء"
}
```

---

## 📊 Request Status (حالات الطلبات)

| Status | الحالة بالعربية |
|--------|----------------|
| `PENDING` | قيد الانتظار |
| `APPROVED` | موافق عليه |
| `REJECTED` | مرفوض |
| `COMPLETED` | مكتمل |
| `CLOSED` | مغلق |

---

## 📋 Request Types (أنواع الطلبات)

| Type | النوع بالعربية | الوصف |
|------|---------------|--------|
| `INVOICE` | فاتورة | طلب صرف فاتورة |
| `CAR_WASH` | غسيل سيارة | طلب غسيل سيارة (5 صور مطلوبة) |
| `CAR_INSPECTION` | فحص سيارة | فحص وتوثيق سيارة (صور + فيديوهات) |
| `ADVANCE_PAYMENT` | سلفة مالية | طلب سلفة مالية |

---

## ⚠️ Error Responses

### 401 Unauthorized:
```json
{
  "success": false,
  "message": "التوكن مفقود"
}
```

### 404 Not Found:
```json
{
  "success": false,
  "message": "الطلب غير موجود"
}
```

### 503 Service Unavailable:
```json
{
  "success": false,
  "message": "خدمة Google Drive غير متاحة حالياً"
}
```

---

## 🔐 Security Notes

1. **JWT Token Expiry:** 30 يوم
2. **Max File Size:** 500MB لكل ملف
3. **Allowed File Types:** PNG, JPG, JPEG, HEIC, MP4, MOV, AVI, PDF
4. **CSRF Protection:** معطلة للـ API endpoints
5. **Rate Limiting:** لا يوجد حالياً (يُنصح بإضافته في الإنتاج)

---

## 🚀 Flutter Integration Example

### 1. Login:
```dart
Future<String?> login(String employeeId, String password) async {
  final response = await http.post(
    Uri.parse('$baseUrl/api/v1/auth/login'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'employee_id': employeeId,
      'password': password,
    }),
  );

  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    return data['token'];
  }
  return null;
}
```

### 2. Get Requests:
```dart
Future<List<Request>> getRequests({String? status}) async {
  final queryParams = status != null ? '?status=$status' : '';
  
  final response = await http.get(
    Uri.parse('$baseUrl/api/v1/requests$queryParams'),
    headers: {
      'Authorization': 'Bearer $jwtToken',
    },
  );

  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    return (data['requests'] as List)
        .map((json) => Request.fromJson(json))
        .toList();
  }
  return [];
}
```

### 3. Create Request:
```dart
Future<int?> createRequest(Map<String, dynamic> requestData) async {
  final response = await http.post(
    Uri.parse('$baseUrl/api/v1/requests'),
    headers: {
      'Authorization': 'Bearer $jwtToken',
      'Content-Type': 'application/json',
    },
    body: jsonEncode(requestData),
  );

  if (response.statusCode == 201) {
    final data = jsonDecode(response.body);
    return data['request_id'];
  }
  return null;
}
```

---

## 📱 Testing with Postman/cURL

### Login:
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"employee_id": "EMP001", "password": "password123"}'
```

### Get Requests:
```bash
curl -X GET http://localhost:5000/api/v1/requests \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Create Request:
```bash
curl -X POST http://localhost:5000/api/v1/requests \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "INVOICE",
    "title": "فاتورة مستلزمات",
    "amount": 500,
    "details": {
      "vendor_name": "متجر الرياض",
      "invoice_date": "2024-11-09"
    }
  }'
```

---

## 💾 Google Drive Storage Structure

```
نُظم/
└── طلبات الموظفين/
    ├── الفواتير/
    │   └── [رقم الطلب] - [اسم الموظف] - [التاريخ]/
    │       └── invoice.jpg
    ├── طلبات غسيل السيارات/
    │   └── [رقم الطلب] - [رقم السيارة] - [التاريخ]/
    │       ├── اللوحة.jpg
    │       ├── الأمام.jpg
    │       ├── الخلف.jpg
    │       ├── الجنب_الأيمن.jpg
    │       └── الجنب_الأيسر.jpg
    ├── فحص وتوثيق السيارات/
    │   └── [رقم الطلب] - [رقم السيارة] - [التاريخ]/
    │       ├── صورة_1.jpg
    │       ├── صورة_2.jpg
    │       └── فيديو_1.mp4
    └── طلبات السلف/
        └── [رقم الطلب] - [اسم الموظف] - [التاريخ]/
```

---

## 📞 Support

للدعم الفني أو الاستفسارات، يرجى التواصل مع فريق التطوير.

**Version:** 1.0.0  
**Last Updated:** November 9, 2024
