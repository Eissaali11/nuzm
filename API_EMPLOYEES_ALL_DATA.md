# 📊 API: جميع بيانات الموظفين الشاملة

## نظرة عامة
هذا الـ endpoint يعيد **جميع بيانات جميع الموظفين** بشكل كامل وشامل في استجابة JSON واحدة منظمة.

---

## 📍 Endpoint Details

```
GET /api/v1/employees/all-data
```

**الوصف:** إرجاع قائمة شاملة بجميع الموظفين مع كافة بياناتهم الشخصية، المواقع الجغرافية، السيارات، الحضور، الرواتب، المستندات، والطلبات.

**المصادقة:** لا تتطلب مصادقة (عامة)

---

## 📥 معاملات الفلترة (Query Parameters)

جميع المعاملات **اختيارية**:

| المعامل | النوع | الوصف | مثال | القيم المتاحة |
|---------|------|-------|------|---------------|
| `department_id` | Integer | فلترة حسب القسم | `5` | أي رقم قسم صحيح |
| `status` | String | حالة الموظف | `active` | `active`, `inactive`, `on_leave` |
| `has_location` | Boolean | فقط من لديهم موقع GPS حديث | `true` | `true`, `false` |
| `with_vehicle` | Boolean | فقط من لديهم سيارة مخصصة | `true` | `true`, `false` |
| `search` | String | البحث بالاسم/الرقم الوظيفي/الرقم الوطني | `أحمد` | أي نص |
| `page` | Integer | رقم الصفحة | `1` | 1 أو أكثر (افتراضي: 1) |
| `per_page` | Integer | عدد النتائج بالصفحة | `50` | 1-200 (افتراضي: 50) |

---

## 📤 هيكل الاستجابة الكامل

### مثال مبسط:
```json
{
  "success": true,
  "metadata": {
    "generated_at": "2024-11-10T21:00:00",
    "total_employees": 150,
    "total_active": 120,
    "employees_with_location": 85,
    "employees_with_vehicle": 45,
    "filters_applied": {
      "department_id": null,
      "status": "active",
      "has_location": null,
      "with_vehicle": null,
      "search": ""
    }
  },
  "employees": [
    {
      // بيانات الموظف الكاملة (شرح مفصل بالأسفل)
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 150,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## 👤 هيكل بيانات الموظف الواحد (Employee Object)

كل موظف يحتوي على **17 قسم** من البيانات:

### 1️⃣ البيانات الشخصية الأساسية

```json
{
  "id": 1,
  "employee_id": "EMP001",
  "name": "أحمد محمد علي",
  "national_id": "1234567890",
  "mobile": "+966501234567",
  "mobile_personal": "+966509876543",
  "email": "ahmad@company.com",
  "job_title": "مهندس برمجيات",
  "status": "active",
  "employee_type": "regular",
  "contract_type": "foreign",
  "birth_date": "1990-05-15",
  "join_date": "2020-01-15",
  "profile_image": "/static/uploads/employees/profile_1.jpg",
  "national_id_image": "/static/uploads/employees/national_id_1.jpg",
  "license_image": "/static/uploads/employees/license_1.jpg",
  "bank_iban_image": "/static/uploads/employees/iban_1.jpg",
  "created_at": "2020-01-15T10:00:00",
  "updated_at": "2024-11-10T15:30:00"
}
```

---

### 2️⃣ الأقسام (Departments)

```json
{
  "departments": [
    {
      "id": 5,
      "name": "تقنية المعلومات",
      "description": "قسم تطوير البرمجيات"
    },
    {
      "id": 8,
      "name": "الموارد البشرية",
      "description": null
    }
  ],
  "primary_department": {
    "id": 5,
    "name": "تقنية المعلومات",
    "description": "قسم تطوير البرمجيات"
  }
}
```

---

### 3️⃣ الجنسية (Nationality)

```json
{
  "nationality": {
    "id": 1,
    "name_ar": "سعودي",
    "name_en": "Saudi",
    "country_code": "SAU"
  }
}
```

---

### 4️⃣ معلومات الراتب (Salary Info)

```json
{
  "salary_info": {
    "basic_salary": 8000.0,
    "daily_wage": 266.67,
    "attendance_bonus": 300.0,
    "has_national_balance": false,
    "bank_iban": "SA0380000000608010167519"
  }
}
```

---

### 5️⃣ معلومات الكفالة (Sponsorship)

```json
{
  "sponsorship": {
    "status": "inside",
    "current_sponsor": "شركة نُظم التقنية"
  }
}
```

---

### 6️⃣ معلومات السكن (Housing)

```json
{
  "housing": {
    "residence_details": "حي النخيل، شارع الملك فهد",
    "residence_location_url": "https://maps.google.com/?q=24.7136,46.6753",
    "housing_images": [
      "/static/uploads/housing/house_1_front.jpg",
      "/static/uploads/housing/house_1_inside.jpg"
    ],
    "housing_drive_links": [
      "https://drive.google.com/file/d/abc123/view"
    ]
  }
}
```

---

### 7️⃣ معلومات العهدة (Custody)

```json
{
  "custody": {
    "has_mobile_custody": true,
    "mobile_type": "iPhone 14 Pro",
    "mobile_imei": "123456789012345"
  }
}
```

---

### 8️⃣ مقاسات الزي (Uniform Sizes)

```json
{
  "uniform_sizes": {
    "pants_size": "L",
    "shirt_size": "XL"
  }
}
```

---

### 9️⃣ حالات المستندات (Documents Status)

```json
{
  "documents_status": {
    "contract_status": "ساري",
    "license_status": "سارية"
  }
}
```

---

### 🔟 الموقع الجغرافي (Location)

#### إذا كان لديه موقع:
```json
{
  "location": {
    "has_location": true,
    "latitude": 24.7136,
    "longitude": 46.6753,
    "accuracy_meters": 10.5,
    "speed_kmh": 45.0,
    "is_moving": true,
    "recorded_at": "2024-11-10T20:55:00",
    "received_at": "2024-11-10T20:55:02",
    "time_ago": "قبل 5 دقائق",
    "minutes_ago": 5,
    "source": "android_app",
    "notes": null,
    "vehicle": {
      "id": 12,
      "plate_number": "ن ج ر 1234",
      "make": "تويوتا",
      "model": "كامري"
    }
  }
}
```

#### إذا لم يكن لديه موقع:
```json
{
  "location": {
    "has_location": false,
    "message": "لا يوجد موقع مسجل"
  }
}
```

**ملاحظات:**
- ✅ `is_moving`: يعتبر متحرك إذا كانت السرعة > 5 km/h
- ✅ `time_ago`: يحسب تلقائياً بالعربية (الآن، قبل X دقيقة، قبل X ساعة، قبل X يوم)
- ✅ `vehicle`: السيارة المرتبطة بهذا الموقع (إن وجدت)

---

### 1️⃣1️⃣ السيارة المخصصة (Assigned Vehicle)

#### إذا كان لديه سيارة:
```json
{
  "assigned_vehicle": {
    "id": 12,
    "plate_number": "ن ج ر 1234",
    "make": "تويوتا",
    "model": "كامري",
    "year": 2022,
    "color": "فضي",
    "status": "in_use",
    "handover_date": "2024-10-01",
    "handover_mileage": 45000
  }
}
```

#### إذا لم يكن لديه سيارة:
```json
{
  "assigned_vehicle": null
}
```

---

### 1️⃣2️⃣ إحصائيات الحضور (Attendance Stats)

```json
{
  "attendance_stats": {
    "last_30_days": {
      "total_days": 25,
      "present": 22,
      "absent": 2,
      "leave": 1,
      "attendance_rate": 88.0
    }
  }
}
```

---

### 1️⃣3️⃣ آخر سجلات الحضور (Recent Attendance)

```json
{
  "recent_attendance": [
    {
      "date": "2024-11-10",
      "status": "present",
      "check_in": "08:00:00",
      "check_out": "17:00:00",
      "notes": null
    },
    {
      "date": "2024-11-09",
      "status": "present",
      "check_in": "08:05:00",
      "check_out": "17:10:00",
      "notes": null
    }
  ]
}
```

---

### 1️⃣4️⃣ آخر راتب (Latest Salary)

```json
{
  "latest_salary": {
    "month": 10,
    "year": 2024,
    "total_amount": 8500.0,
    "base_salary": 8000.0,
    "allowances": 800.0,
    "deductions": 300.0,
    "net_salary": 8500.0,
    "payment_status": "paid",
    "paid_date": "2024-11-01"
  }
}
```

---

### 1️⃣5️⃣ المستندات (Documents)

```json
{
  "documents": {
    "total": 5,
    "expired": 1,
    "expiring_soon": 2,
    "list": [
      {
        "id": 1,
        "document_type": "passport",
        "document_number": "A12345678",
        "issue_date": "2020-01-01",
        "expiry_date": "2025-01-01",
        "file_path": "/static/uploads/documents/passport_1.pdf",
        "status": "valid"
      },
      {
        "id": 2,
        "document_type": "iqama",
        "document_number": "2234567890",
        "issue_date": "2023-01-01",
        "expiry_date": "2024-12-01",
        "file_path": "/static/uploads/documents/iqama_1.pdf",
        "status": "expiring_soon"
      }
    ]
  }
}
```

**حالات المستندات (status):**
- `valid`: صالح (أكثر من 30 يوم)
- `expiring_soon`: ينتهي قريباً (خلال 30 يوم)
- `expired`: منتهي
- `unknown`: غير معروف (لا يوجد تاريخ انتهاء)

---

### 1️⃣6️⃣ إحصائيات الطلبات (Requests Stats)

```json
{
  "requests_stats": {
    "total": 25,
    "pending": 3,
    "approved": 20,
    "rejected": 2,
    "last_request": {
      "id": 156,
      "type": "CAR_WASH",
      "status": "PENDING",
      "created_at": "2024-11-09T14:30:00"
    }
  }
}
```

---

### 1️⃣7️⃣ آخر الطلبات (Recent Requests)

```json
{
  "recent_requests": [
    {
      "id": 156,
      "type": "CAR_WASH",
      "status": "PENDING",
      "title": "طلب غسيل سيارة",
      "amount": 150.0,
      "created_at": "2024-11-09T14:30:00"
    },
    {
      "id": 155,
      "type": "INVOICE",
      "status": "APPROVED",
      "title": "فاتورة بنزين",
      "amount": 200.0,
      "created_at": "2024-11-08T10:15:00"
    }
  ]
}
```

---

## 🎯 أمثلة الاستخدام

### مثال 1: جلب جميع الموظفين النشطين
```
GET /api/v1/employees/all-data?status=active
```

### مثال 2: موظفين قسم تقنية المعلومات لديهم مواقع حديثة
```
GET /api/v1/employees/all-data?department_id=5&has_location=true
```

### مثال 3: البحث عن موظف بالاسم
```
GET /api/v1/employees/all-data?search=أحمد
```

### مثال 4: موظفين لديهم سيارات مخصصة مع ترقيم
```
GET /api/v1/employees/all-data?with_vehicle=true&page=1&per_page=20
```

### مثال 5: جمع فلاتر متعددة
```
GET /api/v1/employees/all-data?department_id=5&status=active&has_location=true&page=2&per_page=30
```

---

## 💻 مثال استجابة كاملة

```json
{
  "success": true,
  "metadata": {
    "generated_at": "2024-11-10T21:10:00",
    "total_employees": 70,
    "total_active": 65,
    "employees_with_location": 45,
    "employees_with_vehicle": 25,
    "filters_applied": {
      "department_id": 5,
      "status": "active",
      "has_location": true,
      "with_vehicle": null,
      "search": ""
    }
  },
  "employees": [
    {
      "id": 1,
      "employee_id": "EMP001",
      "name": "أحمد محمد علي",
      "national_id": "1234567890",
      "mobile": "+966501234567",
      "mobile_personal": "+966509876543",
      "email": "ahmad@company.com",
      "job_title": "مهندس برمجيات",
      "status": "active",
      "employee_type": "regular",
      "contract_type": "foreign",
      "birth_date": "1990-05-15",
      "join_date": "2020-01-15",
      "profile_image": "/static/uploads/employees/profile_1.jpg",
      "national_id_image": "/static/uploads/employees/national_id_1.jpg",
      "license_image": "/static/uploads/employees/license_1.jpg",
      "bank_iban_image": "/static/uploads/employees/iban_1.jpg",
      "created_at": "2020-01-15T10:00:00",
      "updated_at": "2024-11-10T15:30:00",
      
      "departments": [
        {
          "id": 5,
          "name": "تقنية المعلومات",
          "description": "قسم تطوير البرمجيات"
        }
      ],
      "primary_department": {
        "id": 5,
        "name": "تقنية المعلومات",
        "description": "قسم تطوير البرمجيات"
      },
      
      "nationality": {
        "id": 1,
        "name_ar": "سعودي",
        "name_en": "Saudi",
        "country_code": "SAU"
      },
      
      "salary_info": {
        "basic_salary": 8000.0,
        "daily_wage": 266.67,
        "attendance_bonus": 300.0,
        "has_national_balance": false,
        "bank_iban": "SA0380000000608010167519"
      },
      
      "sponsorship": {
        "status": "inside",
        "current_sponsor": "شركة نُظم التقنية"
      },
      
      "housing": {
        "residence_details": "حي النخيل، شارع الملك فهد",
        "residence_location_url": "https://maps.google.com/?q=24.7136,46.6753",
        "housing_images": [
          "/static/uploads/housing/house_1_front.jpg"
        ],
        "housing_drive_links": []
      },
      
      "custody": {
        "has_mobile_custody": true,
        "mobile_type": "iPhone 14 Pro",
        "mobile_imei": "123456789012345"
      },
      
      "uniform_sizes": {
        "pants_size": "L",
        "shirt_size": "XL"
      },
      
      "documents_status": {
        "contract_status": "ساري",
        "license_status": "سارية"
      },
      
      "location": {
        "has_location": true,
        "latitude": 24.7136,
        "longitude": 46.6753,
        "accuracy_meters": 10.5,
        "speed_kmh": 45.0,
        "is_moving": true,
        "recorded_at": "2024-11-10T20:55:00",
        "received_at": "2024-11-10T20:55:02",
        "time_ago": "قبل 5 دقائق",
        "minutes_ago": 5,
        "source": "android_app",
        "notes": null,
        "vehicle": {
          "id": 12,
          "plate_number": "ن ج ر 1234",
          "make": "تويوتا",
          "model": "كامري"
        }
      },
      
      "assigned_vehicle": {
        "id": 12,
        "plate_number": "ن ج ر 1234",
        "make": "تويوتا",
        "model": "كامري",
        "year": 2022,
        "color": "فضي",
        "status": "in_use",
        "handover_date": "2024-10-01",
        "handover_mileage": 45000
      },
      
      "attendance_stats": {
        "last_30_days": {
          "total_days": 25,
          "present": 22,
          "absent": 2,
          "leave": 1,
          "attendance_rate": 88.0
        }
      },
      
      "recent_attendance": [
        {
          "date": "2024-11-10",
          "status": "present",
          "check_in": "08:00:00",
          "check_out": "17:00:00",
          "notes": null
        }
      ],
      
      "latest_salary": {
        "month": 10,
        "year": 2024,
        "total_amount": 8500.0,
        "base_salary": 8000.0,
        "allowances": 800.0,
        "deductions": 300.0,
        "net_salary": 8500.0,
        "payment_status": "paid",
        "paid_date": "2024-11-01"
      },
      
      "documents": {
        "total": 2,
        "expired": 0,
        "expiring_soon": 1,
        "list": [
          {
            "id": 1,
            "document_type": "passport",
            "document_number": "A12345678",
            "issue_date": "2020-01-01",
            "expiry_date": "2025-01-01",
            "file_path": "/static/uploads/documents/passport_1.pdf",
            "status": "valid"
          }
        ]
      },
      
      "requests_stats": {
        "total": 25,
        "pending": 3,
        "approved": 20,
        "rejected": 2,
        "last_request": {
          "id": 156,
          "type": "CAR_WASH",
          "status": "PENDING",
          "created_at": "2024-11-09T14:30:00"
        }
      },
      
      "recent_requests": [
        {
          "id": 156,
          "type": "CAR_WASH",
          "status": "PENDING",
          "title": "طلب غسيل سيارة",
          "amount": 150.0,
          "created_at": "2024-11-09T14:30:00"
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 70,
    "total_pages": 2,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## ⚡ الأداء والتحسينات

- ✅ استخدام `joinedload` لتجنب N+1 queries
- ✅ الحد الأقصى: 200 موظف/طلب
- ✅ الافتراضي: 50 موظف/صفحة
- ✅ تحميل جميع العلاقات في استعلام واحد محسّن
- ✅ حساب الإحصائيات بكفاءة

---

## 📊 ملخص البيانات المتضمنة

| القسم | عدد الحقول | الوصف |
|------|------------|-------|
| البيانات الشخصية | 18 | المعلومات الأساسية والصور |
| الأقسام | متعدد | قائمة جميع الأقسام |
| الجنسية | 4 | معلومات الجنسية |
| الراتب | 5 | معلومات الراتب الأساسية |
| الكفالة | 2 | حالة الكفالة |
| السكن | 4 | عنوان وصور السكن |
| العهدة | 3 | عهدة الجوال |
| الزي | 2 | مقاسات الزي |
| المستندات | 2 | حالة العقد والرخصة |
| الموقع GPS | 13 | آخر موقع بالتفاصيل |
| السيارة المخصصة | 8 | السيارة الحالية |
| إحصائيات الحضور | 5 | آخر 30 يوم |
| سجلات الحضور | متعدد | آخر 7 أيام |
| آخر راتب | 8 | تفاصيل آخر راتب |
| المستندات | متعدد | جميع المستندات مع الصلاحية |
| إحصائيات الطلبات | 5 | ملخص الطلبات |
| آخر الطلبات | متعدد | آخر 5 طلبات |

**إجمالي:** أكثر من **100+ حقل** لكل موظف!

---

## ✅ ملاحظات مهمة

1. ✅ الـ endpoint **لا يتطلب مصادقة** حالياً (يمكن إضافتها لاحقاً)
2. ✅ جميع التواريخ بصيغة **ISO 8601**
3. ✅ الحد الأقصى **200 موظف/طلب**
4. ✅ الترقيم **افتراضي ومُحسّن**
5. ✅ معالجة القيم **null** بشكل آمن
6. ✅ يعيد **metadata** شاملة عن الإحصائيات

---

**آخر تحديث:** 10 نوفمبر 2024  
**الإصدار:** 1.0.0
