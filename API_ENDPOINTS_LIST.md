# 📋 قائمة شاملة بجميع روابط API المتاحة

## 🌐 Base URL
```
https://eissahr.replit.app
```

**Backup URL:**
```
https://d72f2aef-918c-4148-9723-15870f8c7cf6-00-2c1ygyxvqoldk.riker.replit.dev
```

---

## 🔐 1. المصادقة (Authentication)

### تسجيل الدخول
```
POST /api/v1/auth/login
```

**Request Body:**
```json
{
  "employee_id": "5216",
  "national_id": "1234567890"
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "employee": {
    "id": 1,
    "employee_id": "5216",
    "name": "اسم الموظف",
    "email": "email@example.com",
    "job_title": "المسمى الوظيفي",
    "department": "القسم",
    "mobile": "0501234567",
    "status": "active",
    "profile_image": "/static/uploads/profiles/image.jpg"
  }
}
```

**ملاحظة هامة:** النظام يستخدم `employee_id` (رقم الموظف) + `national_id` (رقم الهوية الوطنية) للمصادقة بدلاً من كلمة المرور.

**cURL Example:**
```bash
curl -X POST https://eissahr.replit.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "5216",
    "national_id": "1234567890"
  }'
```

---

## 📋 2. الطلبات (Requests)

### 2.1 جلب قائمة الطلبات
```
GET /api/v1/requests
```

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Query Parameters (Optional):**
```
?type=advance_payment          // نوع الطلب
?status=pending                // حالة الطلب
?date_from=2025-01-01         // من تاريخ
?date_to=2025-01-31           // إلى تاريخ
```

**Response:**
```json
{
  "success": true,
  "message": "تم جلب الطلبات بنجاح",
  "requests": [
    {
      "id": 1,
      "type": "advance_payment",
      "title": "طلب سلفة",
      "status": "pending",
      "amount": 5000.00,
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

**cURL Example:**
```bash
curl -X GET "https://eissahr.replit.app/api/v1/requests?status=pending" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### 2.2 جلب تفاصيل طلب معين
```
GET /api/v1/requests/{request_id}
```

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "type": "advance_payment",
    "title": "طلب سلفة",
    "status": "pending",
    "amount": 5000.00,
    "created_at": "2025-01-15T10:30:00Z",
    "admin_notes": "ملاحظات الإدارة",
    "advance_data": {
      "requested_amount": 5000.00,
      "installments": 3,
      "reason": "سبب الطلب"
    }
  }
}
```

**cURL Example:**
```bash
curl -X GET https://eissahr.replit.app/api/v1/requests/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### 2.3 إنشاء طلب جديد
```
POST /api/v1/requests
```

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request Body (مثال لطلب سلفة):**
```json
{
  "type": "advance_payment",
  "title": "طلب سلفة",
  "amount": 5000.00,
  "advance_data": {
    "requested_amount": 5000.00,
    "installments": 3,
    "reason": "احتياج شخصي"
  }
}
```

**Request Body (مثال لطلب فاتورة):**
```json
{
  "type": "invoice",
  "title": "فاتورة شراء",
  "amount": 500.00,
  "invoice_data": {
    "vendor_name": "اسم المورد",
    "description": "وصف الفاتورة"
  }
}
```

**Request Body (مثال لطلب غسيل سيارة):**
```json
{
  "type": "car_wash",
  "title": "طلب غسيل سيارة",
  "car_wash_data": {
    "vehicle_id": 1,
    "service_type": "full_clean",
    "requested_date": "2025-01-20",
    "notes": "ملاحظات إضافية"
  }
}
```

**Request Body (مثال لطلب فحص سيارة):**
```json
{
  "type": "car_inspection",
  "title": "طلب فحص سيارة",
  "car_inspection_data": {
    "vehicle_id": 1,
    "inspection_type": "delivery",
    "description": "فحص قبل الاستلام"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "تم إنشاء الطلب بنجاح",
  "data": {
    "request_id": 123,
    "status": "pending"
  }
}
```

**cURL Example:**
```bash
curl -X POST https://eissahr.replit.app/api/v1/requests \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "advance_payment",
    "title": "طلب سلفة",
    "amount": 5000.00,
    "advance_data": {
      "requested_amount": 5000.00,
      "installments": 3,
      "reason": "احتياج شخصي"
    }
  }'
```

---

### 2.4 رفع ملفات لطلب
```
POST /api/v1/requests/{request_id}/upload
```

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
files: file[] (يمكن رفع ملف أو عدة ملفات)
```

**Supported Formats:**
- Images: PNG, JPG, JPEG, HEIC
- Videos: MP4, MOV, AVI
- Documents: PDF

**Max File Sizes:**
- Images: 10 MB
- Videos: 500 MB
- Documents: 10 MB

**Response:**
```json
{
  "success": true,
  "message": "تم رفع الملفات بنجاح",
  "data": {
    "uploaded_count": 3,
    "files": [
      {
        "filename": "image1.jpg",
        "url": "https://example.com/uploads/image1.jpg",
        "type": "image"
      }
    ]
  }
}
```

**cURL Example:**
```bash
curl -X POST https://eissahr.replit.app/api/v1/requests/1/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "files=@/path/to/image1.jpg" \
  -F "files=@/path/to/image2.jpg"
```

---

### 2.5 إحصائيات الطلبات
```
GET /api/v1/requests/statistics
```

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "success": true,
  "statistics": {
    "total_requests": 50,
    "pending_requests": 10,
    "approved_requests": 30,
    "rejected_requests": 5,
    "completed_requests": 5,
    "total_amount": 150000.00
  }
}
```

**cURL Example:**
```bash
curl -X GET https://eissahr.replit.app/api/v1/requests/statistics \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### 2.6 أنواع الطلبات المتاحة
```
GET /api/v1/requests/types
```

**لا يحتاج توكن**

**Response:**
```json
{
  "success": true,
  "types": [
    {
      "id": "advance_payment",
      "name_ar": "طلب سلفة",
      "name_en": "Advance Payment",
      "description": "طلب سلفة مالية"
    },
    {
      "id": "invoice",
      "name_ar": "فاتورة",
      "name_en": "Invoice",
      "description": "رفع فاتورة للاعتماد"
    },
    {
      "id": "car_wash",
      "name_ar": "غسيل سيارة",
      "name_en": "Car Wash",
      "description": "طلب غسيل سيارة"
    },
    {
      "id": "car_inspection",
      "name_ar": "فحص سيارة",
      "name_en": "Car Inspection",
      "description": "طلب فحص وتوثيق سيارة"
    }
  ]
}
```

**cURL Example:**
```bash
curl -X GET https://eissahr.replit.app/api/v1/requests/types
```

---

### 2.7 إنشاء طلب سلفة (Shortcut Endpoint)
```
POST /api/v1/requests/create-advance-payment
```

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "amount": 5000.00,
  "reason": "احتياج شخصي",
  "installments": 3
}
```

**Response:**
```json
{
  "success": true,
  "message": "تم إنشاء طلب السلفة بنجاح",
  "data": {
    "request_id": 124,
    "type": "advance_payment",
    "status": "pending",
    "amount": 5000.00
  }
}
```

**cURL Example:**
```bash
curl -X POST https://eissahr.replit.app/api/v1/requests/create-advance-payment \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 5000.00,
    "reason": "احتياج شخصي",
    "installments": 3
  }'
```

---

### 2.8 إنشاء طلب فاتورة (Shortcut Endpoint)
```
POST /api/v1/requests/create-invoice
```

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
vendor_name: اسم المورد (required)
amount: 500.00 (required)
invoice_image: file (required - PNG/JPG/PDF)
```

**Response:**
```json
{
  "success": true,
  "message": "تم رفع الفاتورة بنجاح. استخدم endpoint /upload لرفع الصورة",
  "data": {
    "request_id": 125,
    "type": "invoice",
    "status": "pending",
    "vendor_name": "مورد ABC",
    "amount": 500.00,
    "upload_endpoint": "/api/v1/requests/125/upload"
  }
}
```

**cURL Example:**
```bash
curl -X POST https://eissahr.replit.app/api/v1/requests/create-invoice \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "vendor_name=مورد ABC" \
  -F "amount=500.00" \
  -F "invoice_image=@/path/to/invoice.jpg"
```

**ملاحظة:** بعد إنشاء الطلب، استخدم `/api/v1/requests/{request_id}/upload` لرفع صورة الفاتورة.

---

### 2.9 إنشاء طلب غسيل سيارة (Shortcut Endpoint)
```
POST /api/v1/requests/create-car-wash
```

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
vehicle_id: 1 (required)
service_type: "full_clean" (required)
requested_date: "2025-11-15" (optional)
notes: "ملاحظات إضافية" (optional)
photo_plate: file (optional)
photo_front: file (optional)
photo_back: file (optional)
photo_right_side: file (optional)
photo_left_side: file (optional)
```

**Response:**
```json
{
  "success": true,
  "message": "تم إنشاء طلب غسيل السيارة بنجاح",
  "data": {
    "request_id": 126,
    "type": "car_wash",
    "status": "pending",
    "vehicle_plate": "ABC 123",
    "service_type": "full_clean"
  }
}
```

**cURL Example:**
```bash
curl -X POST https://eissahr.replit.app/api/v1/requests/create-car-wash \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "vehicle_id=1" \
  -F "service_type=full_clean" \
  -F "requested_date=2025-11-15" \
  -F "photo_plate=@/path/to/plate.jpg" \
  -F "photo_front=@/path/to/front.jpg"
```

---

### 2.10 إنشاء طلب فحص سيارة (Shortcut Endpoint)
```
POST /api/v1/requests/create-car-inspection
```

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
vehicle_id: 1 (required)
inspection_type: "delivery" (required - delivery/return/periodic)
description: "وصف الفحص" (optional)
inspection_images: file[] (optional - multiple files)
inspection_videos: file[] (optional - multiple files)
```

**Response:**
```json
{
  "success": true,
  "message": "تم إنشاء طلب فحص السيارة بنجاح",
  "data": {
    "request_id": 127,
    "type": "car_inspection",
    "status": "pending",
    "vehicle_plate": "ABC 123",
    "inspection_type": "delivery"
  }
}
```

**cURL Example:**
```bash
curl -X POST https://eissahr.replit.app/api/v1/requests/create-car-inspection \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "vehicle_id=1" \
  -F "inspection_type=delivery" \
  -F "description=فحص قبل الاستلام" \
  -F "inspection_images=@/path/to/img1.jpg" \
  -F "inspection_images=@/path/to/img2.jpg"
```

---

## 🚗 3. المركبات (Vehicles)

### جلب قائمة المركبات المخصصة للموظف
```
GET /api/v1/vehicles
```

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "success": true,
  "vehicles": [
    {
      "id": 1,
      "plate_number": "ABC 123",
      "model": "Toyota Camry",
      "year": 2020,
      "color": "أبيض",
      "status": "assigned",
      "handover_date": "2025-01-01"
    }
  ]
}
```

**cURL Example:**
```bash
curl -X GET https://eissahr.replit.app/api/v1/vehicles \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🔔 4. الإشعارات (Notifications)

### 4.1 جلب الإشعارات
```
GET /api/v1/notifications
```

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Query Parameters (Optional):**
```
?status=unread    // 'all' or 'unread'
```

**Response:**
```json
{
  "success": true,
  "notifications": [
    {
      "id": 1,
      "title": "تم اعتماد طلبك",
      "message": "تم اعتماد طلب السلفة رقم 123",
      "type": "request_approved",
      "is_read": false,
      "created_at": "2025-01-15T10:30:00Z",
      "data": {
        "request_id": 123,
        "request_type": "advance_payment"
      }
    }
  ],
  "unread_count": 5
}
```

**cURL Example:**
```bash
curl -X GET "https://eissahr.replit.app/api/v1/notifications?status=unread" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### 4.2 تحديد إشعار كمقروء
```
PUT /api/v1/notifications/{notification_id}/read
```

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "success": true,
  "message": "تم تحديد الإشعار كمقروء"
}
```

**cURL Example:**
```bash
curl -X PUT https://eissahr.replit.app/api/v1/notifications/1/read \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### 4.3 تحديد جميع الإشعارات كمقروءة
```
PUT /api/v1/notifications/mark-all-read
```

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "success": true,
  "message": "تم تحديد جميع الإشعارات كمقروءة",
  "data": {
    "updated_count": 15
  }
}
```

**cURL Example:**
```bash
curl -X PUT https://eissahr.replit.app/api/v1/notifications/mark-all-read \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 📊 5. بيانات الموظف (Employee Data)

### 5.1 الملف الشامل للموظف (موصى به - محمي بـ JWT)
```
POST /api/v1/employee/complete-profile
```

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request Body (اختياري):**
```json
{
  "month": "2025-01",
  "start_date": "2025-01-01",
  "end_date": "2025-01-31"
}
```

**ملاحظة:** لا حاجة لإرسال `job_number` - يتم الحصول على بيانات الموظف تلقائياً من الـ JWT token.

**Response:**
```json
{
  "success": true,
  "data": {
    "employee": {
      "id": 123,
      "name": "اسم الموظف",
      "job_number": "5216",
      "department": "القسم",
      "position": "المنصب",
      "email": "email@example.com",
      "phone": "0501234567"
    },
    "current_car": {
      "car_id": 456,
      "plate_number": "ABC 123",
      "model": "Toyota Camry",
      "year": 2020,
      "color": "أبيض"
    },
    "previous_cars": [],
    "attendance": [
      {
        "date": "2025-01-15",
        "check_in": "08:00:00",
        "check_out": "17:00:00",
        "status": "present"
      }
    ],
    "salaries": [
      {
        "month": "2025-01",
        "basic_salary": 8000.00,
        "allowances": 2000.00,
        "deductions": 500.00,
        "net_salary": 9500.00
      }
    ],
    "operations": [],
    "statistics": {
      "total_attendance_days": 20,
      "total_absence_days": 2,
      "salaries": {
        "last_salary": 9500.00,
        "average_salary": 9200.00
      }
    }
  }
}
```

**cURL Example:**
```bash
# الحصول على Token أولاً
TOKEN=$(curl -s -X POST https://eissahr.replit.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"employee_id":"5216","national_id":"1234567890"}' \
  | jq -r '.token')

# استدعاء الملف الشامل
curl -X POST https://eissahr.replit.app/api/v1/employee/complete-profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

### 5.2 الملف الشامل للموظف (طريقة قديمة - غير موصى بها)
```
POST /api/external/employee-complete-profile
```

⚠️ **تحذير:** هذا الـ endpoint يستخدم API key ثابت وأقل أماناً. يُنصح باستخدام `/api/v1/employee/complete-profile` المحمي بـ JWT.

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "job_number": "5216",
  "api_key": "your_location_api_key"
}
```

**Response:** نفس الاستجابة السابقة

---

### 5.3 تحديث موقع الموظف (GPS)
```
POST /api/external/employee-location
```

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "employee_id": "5216",
  "latitude": 24.7136,
  "longitude": 46.6753,
  "timestamp": "2025-01-15T10:30:00Z",
  "accuracy": 10.5,
  "speed": 60.0,
  "heading": 180.0,
  "api_key": "your_api_key"
}
```

**Response:**
```json
{
  "success": true,
  "message": "تم حفظ الموقع بنجاح",
  "geofence_events": [
    {
      "type": "entry",
      "location": "المكتب الرئيسي",
      "timestamp": "2025-01-15T10:30:00Z"
    }
  ]
}
```

**cURL Example:**
```bash
curl -X POST https://eissahr.replit.app/api/external/employee-location \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "5216",
    "latitude": 24.7136,
    "longitude": 46.6753,
    "timestamp": "2025-01-15T10:30:00Z",
    "api_key": "your_api_key"
  }'
```

---

## 🧪 6. اختبار API (Testing)

### اختبار الاتصال
```
GET /api/external/test
```

**لا يحتاج توكن**

**Response:**
```json
{
  "success": true,
  "message": "API is working correctly",
  "timestamp": "2025-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

**cURL Example:**
```bash
curl -X GET https://eissahr.replit.app/api/external/test
```

---

## 📈 7. API داخلي (Internal API) - للإدارة فقط

### 7.1 قائمة الموظفين
```
GET /api/employees
```

**يحتاج تسجيل دخول Admin**

---

### 7.2 قائمة الأقسام
```
GET /api/departments
```

**يحتاج تسجيل دخول Admin**

---

### 7.3 المستندات المنتهية الصلاحية
```
GET /api/documents/expiring/{days}
```

**يحتاج تسجيل دخول Admin**

---

### 7.4 إحصائيات الجنسيات
```
GET /api/employees/nationality/stats
```

**يحتاج تسجيل دخول Admin**

---

## 💰 8. الالتزامات المالية (Financial Liabilities)

### 8.1 جلب قائمة الالتزامات المالية
```
GET /api/v1/employee/liabilities
```

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Query Parameters (Optional):**
```
?status=active          // الحالة: 'active', 'paid', 'cancelled', 'all' (default: 'all')
?type=damage           // النوع: 'damage', 'debt', 'advance_repayment', 'other'
?page=1                // رقم الصفحة (default: 1)
?per_page=20           // عدد العناصر في الصفحة (default: 20)
```

**Status Values:**
- `active`: التزامات نشطة (غير مدفوعة بالكامل)
- `paid`: التزامات مدفوعة بالكامل
- `cancelled`: التزامات ملغاة
- `all`: جميع الالتزامات

**Type Values:**
- `damage`: تلفيات
- `debt`: ديون
- `advance_repayment`: سداد سلفة
- `other`: أخرى

**Response:**
```json
{
  "success": true,
  "message": "تم جلب الالتزامات المالية بنجاح",
  "data": {
    "liabilities": [
      {
        "id": 1,
        "type": "advance_repayment",
        "description": "استرجاع سلفة مالية",
        "total_amount": 5000.00,
        "paid_amount": 1000.00,
        "remaining_amount": 4000.00,
        "status": "active",
        "created_at": "2025-01-15T10:30:00Z",
        "installments": [
          {
            "id": 1,
            "installment_number": 1,
            "amount": 1000.00,
            "due_date": "2025-02-01",
            "paid_date": "2025-02-01",
            "status": "paid"
          },
          {
            "id": 2,
            "installment_number": 2,
            "amount": 1000.00,
            "due_date": "2025-03-01",
            "paid_date": null,
            "status": "pending"
          }
        ]
      }
    ],
    "summary": {
      "total_liabilities": 3,
      "total_amount": 15000.00,
      "paid_amount": 3000.00,
      "remaining_amount": 12000.00
    },
    "pagination": {
      "current_page": 1,
      "per_page": 20,
      "total_pages": 1,
      "total_count": 3
    }
  }
}
```

**cURL Example:**
```bash
curl -X GET "https://eissahr.replit.app/api/v1/employee/liabilities?status=active" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### 8.2 جلب الملخص المالي الشامل
```
GET /api/v1/employee/financial-summary
```

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "success": true,
  "message": "تم جلب الملخص المالي بنجاح",
  "data": {
    "liabilities": {
      "total_active": 3,
      "total_amount": 15000.00,
      "paid_amount": 3000.00,
      "remaining_amount": 12000.00,
      "by_type": {
        "advance_repayment": {
          "count": 2,
          "total": 10000.00,
          "remaining": 8000.00
        },
        "damage": {
          "count": 1,
          "total": 5000.00,
          "remaining": 4000.00
        }
      }
    },
    "requests": {
      "total_requests": 25,
      "pending_requests": 5,
      "approved_requests": 15,
      "rejected_requests": 3,
      "completed_requests": 2,
      "total_amount": 50000.00
    },
    "installments": {
      "upcoming_installments": [
        {
          "liability_id": 1,
          "installment_number": 2,
          "amount": 1000.00,
          "due_date": "2025-03-01",
          "days_until_due": 15
        }
      ],
      "overdue_installments": [],
      "next_payment_date": "2025-03-01",
      "next_payment_amount": 1000.00
    }
  }
}
```

**cURL Example:**
```bash
curl -X GET https://eissahr.replit.app/api/v1/employee/financial-summary \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🔒 الأمان (Security)

### JWT Token Structure
```json
{
  "employee_id": "5216",
  "exp": 1705315800,
  "iat": 1705312200
}
```

**Token Expiry:** ساعة واحدة (3600 ثانية)

### Headers المطلوبة
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json
```

---

## ⚠️ معالجة الأخطاء (Error Handling)

### رموز الحالة (Status Codes)
| Code | المعنى | متى يحدث |
|------|--------|----------|
| 200 | نجاح | العملية نجحت |
| 201 | تم الإنشاء | تم إنشاء مورد جديد |
| 400 | خطأ في البيانات | بيانات مرسلة غير صحيحة |
| 401 | غير مصرح | توكن مفقود أو منتهي |
| 404 | غير موجود | المورد المطلوب غير موجود |
| 500 | خطأ في الخادم | خطأ داخلي في السيرفر |

### تنسيق رسالة الخطأ
```json
{
  "success": false,
  "message": "رسالة الخطأ بالعربية",
  "error": "تفاصيل إضافية (اختياري)"
}
```

---

## 📱 استخدام في Flutter

### مثال كامل للتطبيق
```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class ApiService {
  static const String baseUrl = 'https://eissahr.replit.app';
  String? _token;
  
  // تسجيل الدخول
  Future<void> login(String employeeId, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/v1/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'employee_id': employeeId,
        'password': password,
      }),
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      _token = data['token'];
    }
  }
  
  // جلب الطلبات
  Future<List<dynamic>> getRequests() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/v1/requests'),
      headers: {
        'Authorization': 'Bearer $_token',
        'Content-Type': 'application/json',
      },
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return data['requests'];
    }
    return [];
  }
  
  // إنشاء طلب سلفة
  Future<Map<String, dynamic>> createAdvancePayment({
    required double amount,
    required int installments,
    String? reason,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/v1/requests'),
      headers: {
        'Authorization': 'Bearer $_token',
        'Content-Type': 'application/json',
      },
      body: json.encode({
        'type': 'advance_payment',
        'title': 'طلب سلفة',
        'amount': amount,
        'advance_data': {
          'requested_amount': amount,
          'installments': installments,
          'reason': reason ?? '',
        },
      }),
    );
    
    return json.decode(response.body);
  }
  
  // رفع ملف
  Future<void> uploadFile(int requestId, String filePath) async {
    var request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/api/v1/requests/$requestId/upload'),
    );
    
    request.headers['Authorization'] = 'Bearer $_token';
    request.files.add(await http.MultipartFile.fromPath('files', filePath));
    
    await request.send();
  }
}
```

---

## 🎯 ملخص سريع

### Endpoints الأساسية للتطبيق
```
✅ POST   /api/v1/auth/login                 - تسجيل الدخول
✅ GET    /api/v1/requests                   - قائمة الطلبات
✅ GET    /api/v1/requests/{id}              - تفاصيل طلب
✅ POST   /api/v1/requests                   - إنشاء طلب
✅ POST   /api/v1/requests/{id}/upload       - رفع ملفات
✅ GET    /api/v1/vehicles                   - قائمة السيارات
✅ GET    /api/v1/notifications              - الإشعارات
✅ PUT    /api/v1/notifications/{id}/read    - تحديد كمقروء
✅ POST   /api/external/employee-complete-profile - الملف الشامل
✅ POST   /api/external/employee-location    - تحديث الموقع
```

### Endpoints المفقودة (يجب تطويرها)
```
❌ GET    /api/v1/employee/liabilities             - الالتزامات المالية
❌ GET    /api/v1/employee/financial-summary       - الملخص المالي
❌ POST   /api/v1/requests/create-advance-payment  - طلب سلفة متخصص
❌ POST   /api/v1/requests/create-invoice          - رفع فاتورة متخصص
❌ POST   /api/v1/requests/create-car-wash         - طلب غسيل متخصص
❌ POST   /api/v1/requests/create-car-inspection   - طلب فحص متخصص
❌ PUT    /api/v1/notifications/mark-all-read      - تحديد الكل كمقروء
```

---

**آخر تحديث:** 2025-01-15  
**الإصدار:** 1.0  
**الحالة:** جاهز للاستخدام ✅
