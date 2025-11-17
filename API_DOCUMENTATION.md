# وثائق RESTful API - نظام نُظم

## نظرة عامة

نظام نُظم يوفر RESTful API شامل لجميع وظائف النظام بما في ذلك إدارة الموظفين، المركبات، الأقسام، الحضور، الرواتب، والتقارير.

**Base URL:** `http://your-domain.com/api/v1`

## المصادقة

يستخدم النظام JWT tokens للمصادقة. يجب إرسال Token في header كالتالي:

```
Authorization: Bearer <your-token>
```

## استجابة API موحدة

جميع استجابات API تتبع النمط التالي:

### النجاح
```json
{
  "success": true,
  "message": "رسالة النجاح",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "data": { /* البيانات */ },
  "meta": { /* معلومات إضافية مثل pagination */ }
}
```

### الخطأ
```json
{
  "success": false,
  "error": {
    "message": "رسالة الخطأ",
    "code": 400,
    "timestamp": "2024-01-01T00:00:00.000Z",
    "details": ["تفاصيل إضافية"]
  }
}
```

## 🔐 المصادقة والترخيص

### تسجيل دخول المستخدم
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**الاستجابة:**
```json
{
  "success": true,
  "message": "تم تسجيل الدخول بنجاح",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "أحمد محمد",
      "company_id": 1,
      "role": "admin"
    }
  }
}
```

### تسجيل دخول الموظف
```http
POST /api/v1/auth/employee-login
Content-Type: application/json

{
  "employee_id": "4298",
  "national_id": "2489682019"
}
```

## 📊 لوحة المعلومات

### إحصائيات لوحة المعلومات
```http
GET /api/v1/dashboard/stats
Authorization: Bearer <token>
```

**الاستجابة:**
```json
{
  "success": true,
  "data": {
    "statistics": {
      "employees": {
        "total": 150,
        "active": 145,
        "new_this_month": 5
      },
      "vehicles": {
        "total": 50,
        "active": 48,
        "in_workshop": 2
      },
      "departments": {
        "total": 8,
        "with_managers": 6
      },
      "attendance": {
        "present_today": 140,
        "absent_today": 5
      }
    }
  }
}
```

## 👥 إدارة الموظفين

### جلب قائمة الموظفين
```http
GET /api/v1/employees?page=1&per_page=20&search=محمد&department_id=1&status=active&sort_by=name&sort_order=asc
Authorization: Bearer <token>
```

**المعاملات:**
- `page`: رقم الصفحة (افتراضي: 1)
- `per_page`: عدد العناصر في الصفحة (افتراضي: 20، الحد الأقصى: 100)
- `search`: البحث في الاسم، رقم الموظف، أو البريد الإلكتروني
- `department_id`: تصفية حسب القسم
- `status`: تصفية حسب الحالة (active, inactive)
- `sort_by`: الترتيب حسب (name, employee_id, created_at)
- `sort_order`: اتجاه الترتيب (asc, desc)

### جلب موظف محدد
```http
GET /api/v1/employees/{employee_id}
Authorization: Bearer <token>
```

### إضافة موظف جديد
```http
POST /api/v1/employees
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "أحمد محمد علي",
  "employee_id": "4299",
  "national_id": "1234567890",
  "email": "ahmed@example.com",
  "phone": "0501234567",
  "department_id": 1,
  "job_title": "مطور",
  "basic_salary": 8000,
  "hire_date": "2024-01-01",
  "status": "active"
}
```

**الحقول المطلوبة:**
- `name`: اسم الموظف
- `employee_id`: رقم الموظف (فريد)
- `national_id`: رقم الهوية الوطنية (فريد)

### تحديث موظف
```http
PUT /api/v1/employees/{employee_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "أحمد محمد علي المحدث",
  "email": "ahmed.updated@example.com",
  "job_title": "مطور أول",
  "basic_salary": 9000
}
```

### حذف موظف
```http
DELETE /api/v1/employees/{employee_id}
Authorization: Bearer <token>
```

## 🚗 إدارة المركبات

### جلب قائمة المركبات
```http
GET /api/v1/vehicles?page=1&per_page=20&search=123&status=active
Authorization: Bearer <token>
```

### جلب مركبة محددة
```http
GET /api/v1/vehicles/{vehicle_id}
Authorization: Bearer <token>
```

**الاستجابة تتضمن:**
- بيانات المركبة الأساسية
- سجلات التسليم (آخر 10 سجلات)
- سجلات الورشة (آخر 5 سجلات)

## 🏢 إدارة الأقسام

### جلب قائمة الأقسام
```http
GET /api/v1/departments
Authorization: Bearer <token>
```

**الاستجابة:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "قسم تقنية المعلومات",
      "description": "قسم البرمجة والتطوير",
      "employees_count": 15,
      "manager": {
        "id": 5,
        "name": "محمد أحمد",
        "employee_id": "4200"
      }
    }
  ]
}
```

## ⏰ إدارة الحضور

### جلب سجلات الحضور
```http
GET /api/v1/attendance?page=1&per_page=20&employee_id=179&date_from=2024-01-01&date_to=2024-01-31
Authorization: Bearer <token>
```

### تسجيل حضور
```http
POST /api/v1/attendance
Authorization: Bearer <token>
Content-Type: application/json

{
  "employee_id": 179,
  "date": "2024-01-15",
  "status": "present",
  "check_in_time": "08:00",
  "check_out_time": "17:00",
  "notes": "حضور عادي"
}
```

**الحالات المتاحة:**
- `present`: حاضر
- `absent`: غائب
- `late`: متأخر
- `vacation`: إجازة
- `sick`: إجازة مرضية

## 💰 إدارة الرواتب

### جلب رواتب موظف
```http
GET /api/v1/employees/{employee_id}/salaries?page=1&per_page=12
Authorization: Bearer <token>
```

## 📊 التقارير

### تقرير ملخص الموظفين
```http
GET /api/v1/reports/employees/summary
Authorization: Bearer <token>
```

### تقرير الحضور الشهري
```http
GET /api/v1/reports/attendance/monthly?year=2024&month=1
Authorization: Bearer <token>
```

## 🔍 البحث المتقدم

### البحث في النظام
```http
POST /api/v1/search
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "محمد",
  "search_in": ["employees", "vehicles"]
}
```

**خيارات البحث:**
- `employees`: البحث في الموظفين
- `vehicles`: البحث في المركبات

## 🔔 الإشعارات

### جلب الإشعارات
```http
GET /api/v1/notifications
Authorization: Bearer <token>
```

## 🛠️ خدمات مساعدة

### فحص صحة API
```http
GET /api/v1/health
```

### معلومات API
```http
GET /api/v1/info
```

## أكواد الحالة HTTP

- `200`: نجح الطلب
- `201`: تم إنشاء المورد بنجاح
- `400`: خطأ في البيانات المرسلة
- `401`: غير مصرح - يتطلب تسجيل دخول
- `403`: ممنوع - ليس لديك صلاحية
- `404`: المورد غير موجود
- `409`: تعارض - مثل تكرار البيانات
- `500`: خطأ داخلي في الخادم

## أمثلة عملية

### مثال 1: إضافة موظف جديد مع تسجيل حضوره

```bash
# 1. تسجيل الدخول
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@nuzum.sa","password":"admin123"}'

# 2. إضافة موظف (استخدم Token من الخطوة السابقة)
curl -X POST http://localhost:5000/api/v1/employees \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "سالم أحمد محمد",
    "employee_id": "5001",
    "national_id": "1234567890",
    "email": "salem@example.com",
    "department_id": 1,
    "job_title": "محاسب"
  }'

# 3. تسجيل حضور الموظف
curl -X POST http://localhost:5000/api/v1/attendance \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "employee_id": EMPLOYEE_ID_FROM_STEP_2,
    "date": "2024-01-15",
    "status": "present",
    "check_in_time": "08:00"
  }'
```

### مثال 2: إنشاء تقرير شامل

```bash
# الحصول على إحصائيات الشركة
curl -X GET http://localhost:5000/api/v1/dashboard/stats \
  -H "Authorization: Bearer YOUR_TOKEN"

# تقرير ملخص الموظفين
curl -X GET http://localhost:5000/api/v1/reports/employees/summary \
  -H "Authorization: Bearer YOUR_TOKEN"

# تقرير الحضور لشهر معين
curl -X GET "http://localhost:5000/api/v1/reports/attendance/monthly?year=2024&month=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## معالجة الأخطاء

API يوفر رسائل خطأ واضحة باللغة العربية:

```json
{
  "success": false,
  "error": {
    "message": "بيانات مطلوبة مفقودة",
    "code": 400,
    "timestamp": "2024-01-15T10:30:00.000Z",
    "details": [
      "الحقل 'name' مطلوب",
      "الحقل 'employee_id' مطلوب"
    ]
  }
}
```

## Pagination

جميع القوائم تدعم Pagination مع المعلومات التالية:

```json
{
  "data": [...],
  "meta": {
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 150,
      "pages": 8,
      "has_next": true,
      "has_prev": false,
      "next_page": 2,
      "prev_page": null
    }
  }
}
```

## أمان API

- جميع المسارات محمية بـ CSRF protection
- JWT tokens مع انتهاء صلاحية 24 ساعة
- تشفير كلمات المرور
- فلترة البيانات الحساسة (مثل أرقام الهوية)
- معالجة شاملة للأخطاء
- التحقق من صحة البيانات المدخلة

## دعم فني

للحصول على مساعدة أو الإبلاغ عن مشاكل:
- استخدم مسار `/api/v1/health` للتحقق من حالة النظام
- راجع رسائل الخطأ في الاستجابات
- تأكد من صحة JWT token المستخدم

---

# External API - واجهة برمجية خارجية للتطبيقات

## Employee Complete Profile API

### نظرة عامة
API مخصص لتطبيق Flutter لجلب جميع بيانات الموظف في طلب واحد.

### Endpoint
```
POST /api/external/employee-complete-profile
```

### المصادقة
يستخدم مفتاح API ثابت يُرسل في جسم الطلب (بدون JWT).

### Request Body

#### الحقول المطلوبة
```json
{
  "api_key": "test_location_key_2025",
  "job_number": "5216"
}
```

#### فلاتر اختيارية

**Option 1: فلترة بالشهر**
```json
{
  "api_key": "test_location_key_2025",
  "job_number": "5216",
  "month": "2025-11"
}
```

**Option 2: فلترة بمدى تاريخ**
```json
{
  "api_key": "test_location_key_2025",
  "job_number": "5216",
  "start_date": "2025-10-01",
  "end_date": "2025-10-31"
}
```

### Response Format

#### استجابة ناجحة (200)
```json
{
  "success": true,
  "message": "تم جلب البيانات بنجاح",
  "data": {
    "employee": {
      "job_number": "5216",
      "name": "Basil Alfateh",
      "national_id": "1234567890",
      "birth_date": "1990-01-01",
      "hire_date": "2020-01-01",
      "nationality": "Saudi",
      "department": "IT Department",
      "position": "Software Developer",
      "phone": "+966501234567",
      "email": "basil@example.com",
      "is_driver": false,
      "photos": {
        "personal": "http://nuzum.site/static/uploads/profile.jpg",
        "id": "http://nuzum.site/static/uploads/national_id.jpg",
        "license": null
      }
    },
    "current_car": {
      "car_id": "123",
      "plate_number": "ABC-1234",
      "model": "Toyota Camry",
      "color": "White",
      "status": "available",
      "assigned_date": "2025-01-15"
    },
    "previous_cars": [...],
    "attendance": [
      {
        "date": "2025-11-08",
        "check_in": "08:00",
        "check_out": "17:00",
        "status": "present",
        "hours_worked": 9.0,
        "notes": null
      }
    ],
    "salaries": [
      {
        "salary_id": "SAL-2025-11",
        "month": "2025-11",
        "amount": 5000.0,
        "currency": "SAR",
        "status": "paid"
      }
    ],
    "operations": [
      {
        "operation_id": "OP-789",
        "type": "delivery",
        "date": "2025-01-15T08:30:00",
        "car_plate_number": "ABC-1234",
        "status": "completed"
      }
    ],
    "statistics": {
      "attendance": {
        "total_days": 30,
        "present_days": 28,
        "attendance_rate": 93.33
      },
      "salaries": {
        "total_amount": 60000.0,
        "average_amount": 5000.0
      },
      "cars": {
        "current_car": true,
        "total_cars": 3
      },
      "operations": {
        "total_operations": 15,
        "completed_count": 15
      }
    }
  }
}
```

#### استجابات الأخطاء

**401 - Unauthorized**
```json
{
  "success": false,
  "message": "غير مصرح. يرجى التحقق من المفتاح",
  "error": "Invalid API key"
}
```

**404 - Not Found**
```json
{
  "success": false,
  "message": "الموظف غير موجود",
  "error": "Employee not found"
}
```

### قواعد الفلترة

1. **month**: يأخذ أولوية على start_date/end_date
2. **start_date, end_date**: يجب إرسالهما معاً
3. **بدون فلترة**: آخر 30 يوم للحضور، آخر 12 شهر للرواتب

### مثال Flutter/Dart

```dart
Future<Map<String, dynamic>> getEmployeeProfile({
  required String jobNumber,
  String? month,
}) async {
  final url = Uri.parse('http://nuzum.site/api/external/employee-complete-profile');
  
  final response = await http.post(
    url,
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'api_key': 'test_location_key_2025',
      'job_number': jobNumber,
      if (month != null) 'month': month,
    }),
  );

  return jsonDecode(response.body);
}
```

### API Configuration

- **Primary Domain**: `http://nuzum.site`
- **Backup Domain**: `https://eissahr.replit.app`
- **Test API Key**: `test_location_key_2025`

---

# 🚗 Vehicle Details API - تفاصيل السيارات للتطبيق الخارجي

## نظرة عامة
هذه الـ API endpoints مخصصة للتطبيق الخارجي (Flutter mobile app) لجلب تفاصيل السيارات المربوطة بالموظفين مع كافة المعلومات والوثائق.

---

## 1. جلب تفاصيل السيارة المربوطة بالموظف

### Endpoint
```
GET /api/employees/{employee_id}/vehicle
```

### الوصف
يجلب كافة تفاصيل السيارة المربوطة بموظف معين، بما في ذلك:
- معلومات السيارة الأساسية (الموديل، اللون، رقم اللوحة، إلخ)
- صور الاستمارة والتأمين
- تواريخ انتهاء التفويض والفحص الدوري والاستمارة
- سجلات التسليم والاستلام الكاملة مع الصور
- معلومات السائق الحالي

### Parameters
- `employee_id` (integer, required): رقم الموظف في النظام

### مثال على الطلب
```bash
GET http://nuzum.site/api/employees/180/vehicle
```

### مثال على الاستجابة الناجحة (200 OK)
```json
{
  "success": true,
  "employee": {
    "id": 180,
    "employee_id": "1910",
    "name": "HUSSAM AL DAIN",
    "mobile": "966591014696",
    "mobile_personal": "966563960177",
    "job_title": "courier",
    "department": "Aramex Courier"
  },
  "vehicle": {
    "id": 10,
    "plate_number": "3189-ب س ن",
    "make": "نيسان",
    "model": "ارفان",
    "year": 2021,
    "color": "برند ارامكس",
    "type_of_car": "باص",
    "status": "in_project",
    "status_arabic": "نشطة مع سائق",
    "driver_name": "HUSSAM AL DAIN",
    "project": "Aramex Coruer",
    "department": null,
    "notes": "...",
    "authorization_expiry_date": "2026-02-16",
    "registration_expiry_date": "2026-10-07",
    "inspection_expiry_date": "2026-07-10",
    "registration_form_image": "http://nuzum.site/static/uploads/registration.jpg",
    "insurance_file": "http://nuzum.site/static/uploads/insurance.pdf",
    "license_image": "http://nuzum.site/static/uploads/license.jpg",
    "plate_image": "http://nuzum.site/static/uploads/plate.jpg",
    "drive_folder_link": "https://drive.google.com/..."
  },
  "handover_records": [
    {
      "id": 196,
      "handover_type": "delivery",
      "handover_type_arabic": "تسليم",
      "handover_date": "2025-10-15",
      "handover_time": "14:02",
      "mileage": 150000,
      "vehicle_plate_number": "3189-ب س ن",
      "vehicle_type": "نيسان ارفان 2021",
      "project_name": "Aramex",
      "city": "المجمعه",
      "person_name": "HUSSAM AL DAIN",
      "supervisor_name": "أحمد",
      "fuel_level": "1/2",
      "notes": "...",
      "form_link": "https://acrobat.adobe.com/...",
      "pdf_link": "http://nuzum.site/vehicles/handover/196/pdf/public",
      "driver_signature": "http://nuzum.site/static/signatures/xxx.png",
      "supervisor_signature": "http://nuzum.site/static/signatures/yyy.png",
      "damage_diagram": "http://nuzum.site/static/diagrams/zzz.png",
      "checklist": {
        "spare_tire": true,
        "fire_extinguisher": true,
        "first_aid_kit": true,
        "warning_triangle": true,
        "tools": true,
        "oil_leaks": false,
        "gear_issue": false,
        "clutch_issue": false,
        "engine_issue": false,
        "windows_issue": false,
        "tires_issue": false,
        "body_issue": false,
        "electricity_issue": false,
        "lights_issue": false,
        "ac_issue": false
      },
      "images": [
        {
          "id": 1768,
          "url": "http://nuzum.site/static/uploads/handover/image1.jpg",
          "uploaded_at": "2025-10-15 12:47:42"
        }
      ],
      "drive_pdf_link": "https://drive.google.com/file/..."
    }
  ],
  "handover_count": 4
}
```

### رموز الاستجابة
- `200 OK`: تم جلب البيانات بنجاح
- `404 Not Found`: الموظف غير موجود أو لا توجد سيارة مربوطة به
- `500 Internal Server Error`: حدث خطأ في الخادم

### مثال على استجابة الخطأ (404)
```json
{
  "success": false,
  "message": "لا توجد سيارة مربوطة بهذا الموظف حالياً"
}
```

---

## 2. جلب تفاصيل السيارة بواسطة ID السيارة

### Endpoint
```
GET /api/vehicles/{vehicle_id}/details
```

### الوصف
يجلب كافة تفاصيل سيارة معينة بواسطة رقمها في النظام، بما في ذلك معلومات السائق الحالي وسجلات التسليم والاستلام.

### Parameters
- `vehicle_id` (integer, required): رقم السيارة في النظام

### مثال على الطلب
```bash
GET http://nuzum.site/api/vehicles/10/details
```

### مثال على الاستجابة الناجحة (200 OK)
```json
{
  "success": true,
  "vehicle": {
    "id": 10,
    "plate_number": "3189-ب س ن",
    "make": "نيسان",
    "model": "ارفان",
    "year": 2021,
    "authorization_expiry_date": "2026-02-16",
    "registration_expiry_date": "2026-10-07",
    "inspection_expiry_date": "2026-07-10",
    "registration_form_image": "http://nuzum.site/static/uploads/...",
    "insurance_file": "http://nuzum.site/static/uploads/..."
  },
  "current_driver": {
    "id": 180,
    "employee_id": "1910",
    "name": "HUSSAM AL DAIN",
    "mobile": "966591014696",
    "mobile_personal": "966563960177",
    "job_title": "courier",
    "department": "Aramex Courier"
  },
  "handover_records": [...],
  "handover_count": 4
}
```

---

## حقول البيانات المُرجعة

### حقول السيارة (Vehicle)
| الحقل | النوع | الوصف |
|------|------|-------|
| `id` | integer | رقم السيارة في النظام |
| `plate_number` | string | رقم اللوحة |
| `make` | string | الشركة المصنعة |
| `model` | string | الموديل |
| `year` | integer | سنة الصنع |
| `color` | string | اللون |
| `type_of_car` | string | نوع السيارة |
| `status` | string | الحالة (بالإنجليزية) |
| `status_arabic` | string | الحالة (بالعربية) |
| `driver_name` | string | اسم السائق الحالي |
| `project` | string | اسم المشروع |
| `authorization_expiry_date` | string (YYYY-MM-DD) | **تاريخ انتهاء التفويض** |
| `registration_expiry_date` | string (YYYY-MM-DD) | **تاريخ انتهاء الاستمارة** |
| `inspection_expiry_date` | string (YYYY-MM-DD) | **تاريخ انتهاء الفحص الدوري** |
| `registration_form_image` | string (URL) | **رابط صورة الاستمارة** |
| `insurance_file` | string (URL) | **رابط ملف التأمين** |
| `license_image` | string (URL) | رابط صورة الرخصة |
| `plate_image` | string (URL) | رابط صورة اللوحة |
| `drive_folder_link` | string (URL) | رابط مجلد Google Drive |

### حقول سجل التسليم/الاستلام (Handover Record)
| الحقل | النوع | الوصف |
|------|------|-------|
| `id` | integer | رقم السجل |
| `handover_type` | string | نوع العملية (delivery/receipt) |
| `handover_type_arabic` | string | نوع العملية بالعربية (تسليم/استلام) |
| `handover_date` | string (YYYY-MM-DD) | تاريخ التسليم/الاستلام |
| `handover_time` | string (HH:MM) | وقت التسليم/الاستلام |
| `mileage` | integer | عداد الكيلومترات |
| `vehicle_plate_number` | string | رقم لوحة السيارة |
| `project_name` | string | اسم المشروع |
| `city` | string | المدينة |
| `person_name` | string | اسم المستلم/المسلم |
| `supervisor_name` | string | اسم المشرف |
| `fuel_level` | string | مستوى الوقود |
| `form_link` | string (URL) | **رابط نموذج Adobe** |
| `pdf_link` | string (URL) | **رابط PDF لعرض النموذج مباشرة** |
| `driver_signature` | string (URL) | رابط توقيع السائق |
| `supervisor_signature` | string (URL) | رابط توقيع المشرف |
| `damage_diagram` | string (URL) | رابط مخطط الأضرار |
| `checklist` | object | قائمة الفحص (انظر أدناه) |
| `images` | array | **مصفوفة صور السيارة** |
| `drive_pdf_link` | string (URL) | رابط PDF في Google Drive |

### قائمة الفحص (Checklist)
جميع الحقول من نوع boolean:
- `spare_tire`: إطار احتياطي ✓
- `fire_extinguisher`: طفاية حريق ✓
- `first_aid_kit`: حقيبة إسعافات أولية ✓
- `warning_triangle`: مثلث تحذير ✓
- `tools`: عدة أدوات ✓
- `oil_leaks`: تسريب زيت ✗
- `gear_issue`: مشكلة في الجير ✗
- `clutch_issue`: مشكلة في الكلتش ✗
- `engine_issue`: مشكلة في المحرك ✗
- `windows_issue`: مشكلة في الشبابيك ✗
- `tires_issue`: مشكلة في الإطارات ✗
- `body_issue`: مشكلة في الهيكل ✗
- `electricity_issue`: مشكلة كهربائية ✗
- `lights_issue`: مشكلة في الإضاءة ✗
- `ac_issue`: مشكلة في المكيف ✗

---

## ملاحظات مهمة

1. **الصور والملفات**: جميع الروابط المُرجعة للصور والملفات هي روابط مباشرة يمكن استخدامها في التطبيق.

2. **التواريخ**: جميع التواريخ بصيغة `YYYY-MM-DD` (مثل: 2026-02-16).

3. **القيم الفارغة**: قد تكون بعض الحقول `null` إذا لم تكن البيانات متوفرة.

4. **الترميز**: جميع النصوص العربية مُرمزة بشكل صحيح بـ UTF-8.

5. **الأمان**: يُنصح بإضافة آلية مصادقة (JWT أو API Key) لحماية الـ endpoints في الإصدارات المستقبلية.

---

## أمثلة استخدام في Flutter

### مثال 1: جلب بيانات السيارة للموظف
```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

Future<Map<String, dynamic>> getEmployeeVehicle(int employeeId) async {
  final response = await http.get(
    Uri.parse('http://nuzum.site/api/employees/$employeeId/vehicle'),
  );

  if (response.statusCode == 200) {
    return json.decode(utf8.decode(response.bodyBytes));
  } else {
    throw Exception('فشل جلب بيانات السيارة');
  }
}
```

### مثال 2: عرض تواريخ انتهاء الوثائق الهامة
```dart
Widget buildExpiryDates(Map<String, dynamic> vehicle) {
  return Card(
    child: Column(
      children: [
        ListTile(
          leading: Icon(Icons.event_available, color: Colors.blue),
          title: Text('تاريخ انتهاء التفويض'),
          subtitle: Text(vehicle['authorization_expiry_date'] ?? 'غير محدد'),
          trailing: _buildExpiryBadge(vehicle['authorization_expiry_date']),
        ),
        Divider(),
        ListTile(
          leading: Icon(Icons.description, color: Colors.orange),
          title: Text('تاريخ انتهاء الفحص الدوري'),
          subtitle: Text(vehicle['inspection_expiry_date'] ?? 'غير محدد'),
          trailing: _buildExpiryBadge(vehicle['inspection_expiry_date']),
        ),
        Divider(),
        ListTile(
          leading: Icon(Icons.assignment, color: Colors.green),
          title: Text('تاريخ انتهاء الاستمارة'),
          subtitle: Text(vehicle['registration_expiry_date'] ?? 'غير محدد'),
          trailing: _buildExpiryBadge(vehicle['registration_expiry_date']),
        ),
      ],
    ),
  );
}

Widget _buildExpiryBadge(String? expiryDate) {
  if (expiryDate == null) return SizedBox.shrink();
  
  final expiry = DateTime.parse(expiryDate);
  final now = DateTime.now();
  final daysLeft = expiry.difference(now).inDays;
  
  Color badgeColor;
  if (daysLeft < 30) {
    badgeColor = Colors.red;
  } else if (daysLeft < 90) {
    badgeColor = Colors.orange;
  } else {
    badgeColor = Colors.green;
  }
  
  return Container(
    padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
    decoration: BoxDecoration(
      color: badgeColor,
      borderRadius: BorderRadius.circular(12),
    ),
    child: Text(
      '$daysLeft يوم',
      style: TextStyle(color: Colors.white, fontSize: 12),
    ),
  );
}
```

### مثال 3: عرض صور نماذج التسليم/الاستلام
```dart
Widget buildHandoverImages(List<dynamic> images) {
  return GridView.builder(
    shrinkWrap: true,
    physics: NeverScrollableScrollPhysics(),
    gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
      crossAxisCount: 3,
      crossAxisSpacing: 8,
      mainAxisSpacing: 8,
    ),
    itemCount: images.length,
    itemBuilder: (context, index) {
      return GestureDetector(
        onTap: () {
          // فتح الصورة بشكل كامل
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => FullImageView(imageUrl: images[index]['url']),
            ),
          );
        },
        child: Image.network(
          images[index]['url'],
          fit: BoxFit.cover,
          loadingBuilder: (context, child, loadingProgress) {
            if (loadingProgress == null) return child;
            return Center(child: CircularProgressIndicator());
          },
        ),
      );
    },
  );
}
```

### مثال 4: فتح PDF لنموذج التسليم/الاستلام
```dart
import 'package:url_launcher/url_launcher.dart';

Widget buildHandoverPdfButton(Map<String, dynamic> handover) {
  return ElevatedButton.icon(
    onPressed: () async {
      final pdfUrl = handover['pdf_link'];
      if (pdfUrl != null) {
        final uri = Uri.parse(pdfUrl);
        if (await canLaunchUrl(uri)) {
          await launchUrl(uri, mode: LaunchMode.externalApplication);
        } else {
          // عرض رسالة خطأ
          print('لا يمكن فتح الرابط');
        }
      }
    },
    icon: Icon(Icons.picture_as_pdf),
    label: Text('عرض نموذج PDF'),
    style: ElevatedButton.styleFrom(
      backgroundColor: Colors.red,
      foregroundColor: Colors.white,
    ),
  );
}
```

### مثال 5: عرض قائمة الفحص (Checklist)
```dart
Widget buildChecklist(Map<String, dynamic> checklist) {
  return Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text('قائمة الفحص', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
      SizedBox(height: 8),
      _buildCheckItem('إطار احتياطي', checklist['spare_tire']),
      _buildCheckItem('طفاية حريق', checklist['fire_extinguisher']),
      _buildCheckItem('حقيبة إسعافات', checklist['first_aid_kit']),
      _buildCheckItem('مثلث تحذير', checklist['warning_triangle']),
      _buildCheckItem('عدة أدوات', checklist['tools']),
      Divider(),
      Text('المشاكل:', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
      _buildIssueItem('تسريب زيت', checklist['oil_leaks']),
      _buildIssueItem('مشكلة في الجير', checklist['gear_issue']),
      _buildIssueItem('مشكلة في المحرك', checklist['engine_issue']),
      _buildIssueItem('مشكلة في المكيف', checklist['ac_issue']),
    ],
  );
}

Widget _buildCheckItem(String label, bool? hasIt) {
  return ListTile(
    dense: true,
    leading: Icon(
      hasIt == true ? Icons.check_circle : Icons.cancel,
      color: hasIt == true ? Colors.green : Colors.red,
    ),
    title: Text(label),
  );
}

Widget _buildIssueItem(String label, bool? hasIssue) {
  if (hasIssue != true) return SizedBox.shrink();
  return ListTile(
    dense: true,
    leading: Icon(Icons.warning, color: Colors.red),
    title: Text(label, style: TextStyle(color: Colors.red)),
  );
}
```

---

## الدعم والمساعدة
للمزيد من المعلومات أو المساعدة، يرجى التواصل مع فريق التطوير.