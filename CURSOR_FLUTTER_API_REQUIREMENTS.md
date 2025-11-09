# 📱 متطلبات API لتطبيق Flutter - دليل التطوير الشامل

## 🎯 نظرة عامة

هذا الدليل موجه لفريق تطوير تطبيق Flutter باستخدام Cursor AI. يحتوي على جميع المتطلبات التقنية والمعمارية لربط التطبيق مع نظام نُظم.

---

## 🏗️ البنية المعمارية الموصى بها

### 1. هيكلة API Endpoints

#### النهج المعتمد: Hybrid Approach
- **Endpoints موحدة** للعمليات الأساسية (CRUD)
- **Endpoints متخصصة** لكل نوع طلب (توفر validation محسّن)
- **Service Layer** منفصل للـ business logic

```
/api/external/v1/
├── auth/
│   └── login                    [POST] تسجيل الدخول
├── requests/
│   ├── /                        [GET] جلب قائمة الطلبات
│   ├── /<id>                    [GET] تفاصيل طلب
│   ├── /                        [POST] إنشاء طلب (endpoint موحد)
│   ├── /create-advance-payment  [POST] طلب سلفة (متخصص)
│   ├── /create-invoice          [POST] رفع فاتورة (متخصص)
│   ├── /create-car-wash         [POST] طلب غسيل (متخصص)
│   ├── /create-car-inspection   [POST] طلب فحص (متخصص)
│   ├── /<id>/upload             [POST] رفع ملفات عام
│   ├── /<id>/upload-image       [POST] رفع صورة (متخصص)
│   └── /<id>/upload-video       [POST] رفع فيديو (متخصص)
├── employee/
│   ├── /liabilities             [GET] الالتزامات المالية
│   ├── /financial-summary       [GET] الملخص المالي
│   └── /complete-profile        [POST] الملف الشامل
├── notifications/
│   ├── /                        [GET] جلب الإشعارات
│   ├── /<id>/mark-read          [PUT] تحديد كمقروء
│   └── /mark-all-read           [PUT] تحديد الكل كمقروء
└── vehicles/
    └── /                        [GET] قائمة السيارات
```

---

## 🗄️ Database Schema المطلوب

### 1. جداول الالتزامات المالية (جديدة)

#### Table: `employee_liabilities`
```sql
CREATE TABLE employee_liabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    liability_type VARCHAR(50) NOT NULL,  -- 'advance_payment', 'loan', 'penalty'
    total_amount DECIMAL(10,2) NOT NULL,
    remaining_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',  -- 'active', 'paid', 'cancelled'
    start_date DATE NOT NULL,
    due_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (employee_id) REFERENCES employee(id) ON DELETE CASCADE,
    INDEX idx_employee_status (employee_id, status),
    INDEX idx_status_due_date (status, due_date)
);
```

#### Table: `liability_installments`
```sql
CREATE TABLE liability_installments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    liability_id INTEGER NOT NULL,
    installment_number INTEGER NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    due_date DATE NOT NULL,
    paid_amount DECIMAL(10,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'paid', 'overdue', 'cancelled'
    paid_date TIMESTAMP,
    payment_reference VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (liability_id) REFERENCES employee_liabilities(id) ON DELETE CASCADE,
    INDEX idx_liability_status (liability_id, status),
    INDEX idx_due_date (due_date),
    UNIQUE KEY unique_installment (liability_id, installment_number)
);
```

#### Relationships
```python
# في models.py
class EmployeeLiability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    liability_type = db.Column(db.String(50), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    remaining_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='active')
    
    # Relationships
    employee = db.relationship('Employee', backref='liabilities')
    installments = db.relationship('LiabilityInstallment', backref='liability', lazy='dynamic')
    
class LiabilityInstallment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    liability_id = db.Column(db.Integer, db.ForeignKey('employee_liabilities.id'), nullable=False)
    installment_number = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='pending')
```

---

## 📝 API Endpoints - التفاصيل الكاملة

### 🔐 1. المصادقة

#### POST `/api/external/v1/auth/login`
**الوصف:** تسجيل دخول الموظف والحصول على JWT Token

**Request Body:**
```json
{
  "employee_id": "5216",
  "password": "your_password"
}
```

**Response (Success 200):**
```json
{
  "success": true,
  "message": "تم تسجيل الدخول بنجاح",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "refresh_token_string",
    "expires_in": 3600,
    "employee": {
      "id": 123,
      "name": "اسم الموظف",
      "employee_id": "5216",
      "department": "القسم",
      "position": "المنصب"
    }
  }
}
```

**Response (Error 401):**
```json
{
  "success": false,
  "error": "رقم الموظف أو كلمة المرور غير صحيحة"
}
```

**التنفيذ:**
```dart
// في Flutter
Future<LoginResponse> login(String employeeId, String password) async {
  final response = await http.post(
    Uri.parse('$baseUrl/api/external/v1/auth/login'),
    headers: {'Content-Type': 'application/json'},
    body: json.encode({
      'employee_id': employeeId,
      'password': password,
    }),
  );
  
  if (response.statusCode == 200) {
    final data = json.decode(response.body);
    // حفظ token في secure storage
    await secureStorage.write(key: 'jwt_token', value: data['data']['token']);
    return LoginResponse.fromJson(data);
  }
  throw Exception('فشل تسجيل الدخول');
}
```

---

### 💳 2. الالتزامات المالية (جديد - يحتاج تطوير)

#### GET `/api/external/v1/employee/liabilities`
**الوصف:** جلب قائمة التزامات الموظف المالية (سلف، أقساط، غرامات)

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Query Parameters (Optional):**
```
?status=active      // 'active', 'paid', 'all'
?type=advance       // 'advance_payment', 'loan', 'penalty'
```

**Response (Success 200):**
```json
{
  "success": true,
  "data": {
    "total_liabilities": 15000.00,
    "active_liabilities": 10000.00,
    "paid_liabilities": 5000.00,
    "liabilities": [
      {
        "id": 1,
        "type": "advance_payment",
        "type_ar": "سلفة",
        "total_amount": 5000.00,
        "remaining_amount": 3333.33,
        "paid_amount": 1666.67,
        "status": "active",
        "status_ar": "نشط",
        "start_date": "2025-01-01",
        "due_date": "2025-04-01",
        "installments_total": 3,
        "installments_paid": 1,
        "installments": [
          {
            "id": 1,
            "installment_number": 1,
            "amount": 1666.67,
            "due_date": "2025-02-01",
            "status": "paid",
            "status_ar": "مدفوع",
            "paid_date": "2025-01-28",
            "paid_amount": 1666.67
          },
          {
            "id": 2,
            "installment_number": 2,
            "amount": 1666.67,
            "due_date": "2025-03-01",
            "status": "pending",
            "status_ar": "قيد الانتظار",
            "paid_date": null,
            "paid_amount": 0
          }
        ],
        "next_due_date": "2025-03-01",
        "next_due_amount": 1666.67
      }
    ]
  }
}
```

**Business Logic المطلوب:**
```python
# في services/employee_finance_service.py

class EmployeeFinanceService:
    @staticmethod
    def get_employee_liabilities(employee_id, status_filter=None):
        """جلب التزامات الموظف مع حساب الأقساط"""
        query = EmployeeLiability.query.filter_by(employee_id=employee_id)
        
        if status_filter and status_filter != 'all':
            query = query.filter_by(status=status_filter)
        
        liabilities = query.order_by(EmployeeLiability.created_at.desc()).all()
        
        result = []
        total_liabilities = 0
        active_liabilities = 0
        paid_liabilities = 0
        
        for liability in liabilities:
            # حساب الأقساط
            installments_data = []
            for inst in liability.installments:
                installments_data.append({
                    'id': inst.id,
                    'installment_number': inst.installment_number,
                    'amount': float(inst.amount),
                    'due_date': inst.due_date.isoformat(),
                    'status': inst.status,
                    'status_ar': get_status_arabic(inst.status),
                    'paid_date': inst.paid_date.isoformat() if inst.paid_date else None,
                    'paid_amount': float(inst.paid_amount)
                })
            
            # حساب الإحصائيات
            total_liabilities += float(liability.total_amount)
            if liability.status == 'active':
                active_liabilities += float(liability.remaining_amount)
            elif liability.status == 'paid':
                paid_liabilities += float(liability.total_amount)
            
            # القسط القادم
            next_installment = liability.installments.filter_by(status='pending').order_by(
                LiabilityInstallment.due_date).first()
            
            result.append({
                'id': liability.id,
                'type': liability.liability_type,
                'type_ar': get_liability_type_arabic(liability.liability_type),
                'total_amount': float(liability.total_amount),
                'remaining_amount': float(liability.remaining_amount),
                'paid_amount': float(liability.total_amount - liability.remaining_amount),
                'status': liability.status,
                'status_ar': get_status_arabic(liability.status),
                'start_date': liability.start_date.isoformat(),
                'due_date': liability.due_date.isoformat() if liability.due_date else None,
                'installments_total': liability.installments.count(),
                'installments_paid': liability.installments.filter_by(status='paid').count(),
                'installments': installments_data,
                'next_due_date': next_installment.due_date.isoformat() if next_installment else None,
                'next_due_amount': float(next_installment.amount) if next_installment else 0
            })
        
        return {
            'total_liabilities': total_liabilities,
            'active_liabilities': active_liabilities,
            'paid_liabilities': paid_liabilities,
            'liabilities': result
        }
```

**التنفيذ في Flutter:**
```dart
class LiabilityService {
  Future<LiabilitiesResponse> getLiabilities({String? status}) async {
    final token = await secureStorage.read(key: 'jwt_token');
    final queryParams = status != null ? '?status=$status' : '';
    
    final response = await http.get(
      Uri.parse('$baseUrl/api/external/v1/employee/liabilities$queryParams'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
    );
    
    if (response.statusCode == 200) {
      return LiabilitiesResponse.fromJson(json.decode(response.body));
    }
    throw Exception('فشل جلب الالتزامات');
  }
}

// Models
class LiabilitiesResponse {
  final bool success;
  final LiabilitiesData data;
  
  factory LiabilitiesResponse.fromJson(Map<String, dynamic> json) {
    return LiabilitiesResponse(
      success: json['success'],
      data: LiabilitiesData.fromJson(json['data']),
    );
  }
}

class LiabilitiesData {
  final double totalLiabilities;
  final double activeLiabilities;
  final double paidLiabilities;
  final List<Liability> liabilities;
  
  factory LiabilitiesData.fromJson(Map<String, dynamic> json) {
    return LiabilitiesData(
      totalLiabilities: json['total_liabilities'].toDouble(),
      activeLiabilities: json['active_liabilities'].toDouble(),
      paidLiabilities: json['paid_liabilities'].toDouble(),
      liabilities: (json['liabilities'] as List)
          .map((l) => Liability.fromJson(l))
          .toList(),
    );
  }
}
```

---

#### GET `/api/external/v1/employee/financial-summary`
**الوصف:** الملخص المالي الشامل للموظف

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response (Success 200):**
```json
{
  "success": true,
  "data": {
    "current_balance": 5000.00,
    "total_earnings": 50000.00,
    "total_deductions": 45000.00,
    "active_liabilities": 10000.00,
    "paid_liabilities": 5000.00,
    "pending_requests": 3,
    "approved_requests": 10,
    "rejected_requests": 2,
    "last_salary": {
      "amount": 8500.00,
      "month": "2025-01",
      "paid_date": "2025-01-25"
    },
    "upcoming_installment": {
      "amount": 1666.67,
      "due_date": "2025-03-01",
      "liability_type": "advance_payment"
    },
    "monthly_summary": {
      "total_income": 8500.00,
      "total_deductions": 2000.00,
      "installments": 1666.67,
      "net_income": 4833.33
    }
  }
}
```

**Business Logic:**
```python
class EmployeeFinanceService:
    @staticmethod
    def get_financial_summary(employee_id):
        """حساب الملخص المالي الشامل"""
        employee = Employee.query.get(employee_id)
        
        # الالتزامات
        liabilities_data = EmployeeFinanceService.get_employee_liabilities(employee_id)
        
        # آخر راتب
        last_salary = Salary.query.filter_by(employee_id=employee_id)\
            .order_by(Salary.created_at.desc()).first()
        
        # الطلبات
        requests_stats = {
            'pending': EmployeeRequest.query.filter_by(
                employee_id=employee_id, status='pending').count(),
            'approved': EmployeeRequest.query.filter_by(
                employee_id=employee_id, status='approved').count(),
            'rejected': EmployeeRequest.query.filter_by(
                employee_id=employee_id, status='rejected').count()
        }
        
        # القسط القادم
        next_installment = LiabilityInstallment.query.join(EmployeeLiability)\
            .filter(
                EmployeeLiability.employee_id == employee_id,
                LiabilityInstallment.status == 'pending'
            ).order_by(LiabilityInstallment.due_date).first()
        
        # إجمالي المكتسبات والخصومات
        total_earnings = db.session.query(func.sum(Salary.total_earnings))\
            .filter(Salary.employee_id == employee_id).scalar() or 0
        total_deductions = db.session.query(func.sum(Salary.total_deductions))\
            .filter(Salary.employee_id == employee_id).scalar() or 0
        
        return {
            'current_balance': float(total_earnings - total_deductions),
            'total_earnings': float(total_earnings),
            'total_deductions': float(total_deductions),
            'active_liabilities': liabilities_data['active_liabilities'],
            'paid_liabilities': liabilities_data['paid_liabilities'],
            'pending_requests': requests_stats['pending'],
            'approved_requests': requests_stats['approved'],
            'rejected_requests': requests_stats['rejected'],
            'last_salary': {
                'amount': float(last_salary.net_salary) if last_salary else 0,
                'month': last_salary.month if last_salary else None,
                'paid_date': last_salary.created_at.isoformat() if last_salary else None
            } if last_salary else None,
            'upcoming_installment': {
                'amount': float(next_installment.amount),
                'due_date': next_installment.due_date.isoformat(),
                'liability_type': next_installment.liability.liability_type
            } if next_installment else None
        }
```

---

### 📋 3. الطلبات المتخصصة (جديد)

#### POST `/api/external/v1/requests/create-advance-payment`
**الوصف:** إنشاء طلب سلفة جديد مع validation محسّن

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "requested_amount": 5000.00,
  "installments": 3,
  "reason": "سبب الطلب (اختياري)"
}
```

**Response (Success 201):**
```json
{
  "success": true,
  "message": "تم إنشاء طلب السلفة بنجاح",
  "data": {
    "request_id": 123,
    "type": "advance_payment",
    "status": "pending",
    "requested_amount": 5000.00,
    "installments": 3,
    "monthly_installment": 1666.67,
    "estimated_approval_date": "2025-01-20",
    "pdf_url": "https://example.com/pdf/advance_123.pdf"
  }
}
```

**Validation Rules:**
```python
def validate_advance_payment_request(employee_id, requested_amount, installments):
    """التحقق من صحة طلب السلفة"""
    employee = Employee.query.get(employee_id)
    
    # التحقق من الحد الأقصى للسلفة (مثلاً: 3 أضعاف الراتب)
    if employee.salary:
        max_advance = employee.salary * 3
        if requested_amount > max_advance:
            return False, f"الحد الأقصى للسلفة هو {max_advance} ريال"
    
    # التحقق من عدم وجود سلف نشطة
    active_advances = EmployeeLiability.query.filter_by(
        employee_id=employee_id,
        liability_type='advance_payment',
        status='active'
    ).count()
    
    if active_advances > 0:
        return False, "لديك سلفة نشطة بالفعل، يجب سدادها أولاً"
    
    # التحقق من عدد الأقساط
    if installments < 1 or installments > 12:
        return False, "عدد الأقساط يجب أن يكون بين 1 و 12"
    
    # التحقق من قيمة القسط الشهري
    monthly_installment = requested_amount / installments
    if monthly_installment > (employee.salary * 0.4):
        return False, "قيمة القسط الشهري تتجاوز 40% من الراتب"
    
    return True, "صحيح"
```

**التنفيذ:**
```python
@api_employee_requests.route('/requests/create-advance-payment', methods=['POST'])
@token_required
def create_advance_payment_request(current_employee):
    """إنشاء طلب سلفة متخصص"""
    data = request.get_json()
    
    # Validation
    is_valid, message = validate_advance_payment_request(
        current_employee.id,
        data.get('requested_amount'),
        data.get('installments')
    )
    
    if not is_valid:
        return jsonify({'success': False, 'error': message}), 400
    
    # إنشاء الطلب
    new_request = EmployeeRequest(
        employee_id=current_employee.id,
        request_type='advance_payment',
        title=f"طلب سلفة - {data.get('requested_amount')} ريال",
        status='pending',
        amount=data.get('requested_amount')
    )
    
    # حفظ تفاصيل السلفة
    advance_data = {
        'requested_amount': data.get('requested_amount'),
        'installments': data.get('installments'),
        'monthly_installment': data.get('requested_amount') / data.get('installments'),
        'reason': data.get('reason', '')
    }
    # حفظ في JSON field أو جدول منفصل
    
    db.session.add(new_request)
    db.session.commit()
    
    # إنشاء PDF (اختياري)
    # pdf_url = generate_advance_payment_pdf(new_request)
    
    return jsonify({
        'success': True,
        'message': 'تم إنشاء طلب السلفة بنجاح',
        'data': {
            'request_id': new_request.id,
            'type': 'advance_payment',
            'status': 'pending',
            'requested_amount': float(data.get('requested_amount')),
            'installments': data.get('installments'),
            'monthly_installment': float(advance_data['monthly_installment'])
        }
    }), 201
```

---

#### POST `/api/external/v1/requests/create-invoice`
**الوصف:** رفع فاتورة مع صورة

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
vendor_name: string
amount: float
description: string (optional)
invoice_image: file (JPEG/PNG, max 10MB)
```

**Response (Success 201):**
```json
{
  "success": true,
  "message": "تم رفع الفاتورة بنجاح",
  "data": {
    "request_id": 124,
    "type": "invoice",
    "status": "pending",
    "vendor_name": "اسم المورد",
    "amount": 500.00,
    "image_url": "https://example.com/uploads/invoice_124.jpg"
  }
}
```

---

#### POST `/api/external/v1/requests/create-car-wash`
**الوصف:** إنشاء طلب غسيل سيارة مع صور

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
vehicle_id: integer
service_type: string ('normal', 'polish', 'full_clean')
requested_date: string (YYYY-MM-DD) (optional)
photo_plate: file (required)
photo_front: file (required)
photo_back: file (required)
photo_right_side: file (required)
photo_left_side: file (required)
notes: string (optional)
```

**Response (Success 201):**
```json
{
  "success": true,
  "message": "تم إنشاء طلب الغسيل بنجاح",
  "data": {
    "request_id": 125,
    "type": "car_wash",
    "status": "pending",
    "vehicle_plate": "ABC 123",
    "service_type": "full_clean",
    "service_type_ar": "تنظيف شامل",
    "requested_date": "2025-01-20",
    "images_count": 5,
    "estimated_cost": 150.00
  }
}
```

**Validation Rules:**
```python
def validate_car_wash_request(employee_id, vehicle_id, service_type, files):
    """التحقق من طلب غسيل السيارة"""
    
    # التحقق من السيارة
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        return False, "السيارة غير موجودة"
    
    # التحقق من أن السيارة مخصصة للموظف
    current_handover = VehicleHandover.query.filter_by(
        vehicle_id=vehicle_id,
        employee_id=employee_id,
        handover_type='delivery',
        return_date=None
    ).first()
    
    if not current_handover:
        return False, "السيارة غير مخصصة لك حالياً"
    
    # التحقق من نوع الخدمة
    valid_service_types = ['normal', 'polish', 'full_clean']
    if service_type not in valid_service_types:
        return False, f"نوع الخدمة غير صحيح. الأنواع المتاحة: {', '.join(valid_service_types)}"
    
    # التحقق من الصور المطلوبة
    required_photos = ['photo_plate', 'photo_front', 'photo_back', 'photo_right_side', 'photo_left_side']
    missing_photos = [photo for photo in required_photos if photo not in files]
    
    if missing_photos:
        return False, f"الصور التالية مطلوبة: {', '.join(missing_photos)}"
    
    # التحقق من عدم وجود طلب نشط
    active_wash = EmployeeRequest.query.filter_by(
        employee_id=employee_id,
        request_type='car_wash',
        status='pending'
    ).join(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    if active_wash:
        return False, "لديك طلب غسيل نشط لهذه السيارة"
    
    return True, "صحيح"
```

---

#### POST `/api/external/v1/requests/create-car-inspection`
**الوصف:** إنشاء طلب فحص وتوثيق سيارة

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "vehicle_id": 456,
  "inspection_type": "delivery",  // 'delivery' or 'receipt'
  "description": "وصف الفحص (اختياري)",
  "location": "موقع الفحص (اختياري)"
}
```

**Response (Success 201):**
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
    "vehicle_plate": "ABC 123",
    "upload_instructions": {
      "max_images": 20,
      "max_videos": 3,
      "max_image_size_mb": 10,
      "max_video_size_mb": 500,
      "supported_formats": {
        "images": ["jpg", "jpeg", "png", "heic"],
        "videos": ["mp4", "mov"]
      }
    }
  }
}
```

**بعد إنشاء الطلب، يمكن رفع الصور والفيديوهات:**

---

### 📤 4. رفع الملفات المتخصصة

#### POST `/api/external/v1/requests/<request_id>/upload-image`
**الوصف:** رفع صورة واحدة لطلب فحص السيارة

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
image: file (JPEG/PNG/HEIC, max 10MB)
description: string (optional)
```

**Response (Success 200):**
```json
{
  "success": true,
  "message": "تم رفع الصورة بنجاح",
  "data": {
    "image_url": "https://example.com/uploads/inspection_126_1.jpg",
    "image_id": "img_001",
    "total_images": 5,
    "remaining_slots": 15
  }
}
```

---

#### POST `/api/external/v1/requests/<request_id>/upload-video`
**الوصف:** رفع فيديو لطلب فحص السيارة

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
```
video: file (MP4/MOV, max 500MB)
description: string (optional)
```

**Response (Success 200):**
```json
{
  "success": true,
  "message": "تم رفع الفيديو بنجاح",
  "data": {
    "video_url": "https://example.com/uploads/inspection_126_video1.mp4",
    "video_id": "vid_001",
    "file_size_mb": 45.2,
    "duration_seconds": 30,
    "total_videos": 2,
    "remaining_slots": 1
  }
}
```

**معالجة الملفات الكبيرة في Flutter:**
```dart
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

class FileUploadService {
  // رفع فيديو كبير مع progress tracking
  Future<VideoUploadResponse> uploadVideo(
    int requestId, 
    File videoFile,
    {Function(double)? onProgress}
  ) async {
    final token = await secureStorage.read(key: 'jwt_token');
    final uri = Uri.parse('$baseUrl/api/external/v1/requests/$requestId/upload-video');
    
    var request = http.MultipartRequest('POST', uri);
    request.headers['Authorization'] = 'Bearer $token';
    
    // إضافة الملف
    var stream = http.ByteStream(videoFile.openRead());
    var length = await videoFile.length();
    
    var multipartFile = http.MultipartFile(
      'video',
      stream,
      length,
      filename: basename(videoFile.path),
      contentType: MediaType('video', 'mp4'),
    );
    
    request.files.add(multipartFile);
    
    // تتبع التقدم
    var streamedResponse = await request.send();
    
    if (streamedResponse.statusCode == 200) {
      final responseBody = await streamedResponse.stream.bytesToString();
      return VideoUploadResponse.fromJson(json.decode(responseBody));
    }
    
    throw Exception('فشل رفع الفيديو');
  }
  
  // رفع عدة صور دفعة واحدة
  Future<List<ImageUploadResponse>> uploadMultipleImages(
    int requestId,
    List<File> images
  ) async {
    final results = <ImageUploadResponse>[];
    
    for (var image in images) {
      try {
        final response = await uploadImage(requestId, image);
        results.add(response);
      } catch (e) {
        print('فشل رفع صورة: $e');
      }
    }
    
    return results;
  }
}
```

---

### 🔔 5. الإشعارات

#### PUT `/api/external/v1/notifications/mark-all-read`
**الوصف:** تحديد جميع الإشعارات كمقروءة

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response (Success 200):**
```json
{
  "success": true,
  "message": "تم تحديد جميع الإشعارات كمقروءة",
  "data": {
    "updated_count": 15,
    "unread_count": 0
  }
}
```

---

## 🔒 الأمان والمصادقة

### JWT Token Management

**تخزين آمن في Flutter:**
```dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AuthService {
  final storage = FlutterSecureStorage();
  
  // حفظ token
  Future<void> saveToken(String token) async {
    await storage.write(key: 'jwt_token', value: token);
    await storage.write(
      key: 'token_expiry', 
      value: DateTime.now().add(Duration(hours: 1)).toIso8601String()
    );
  }
  
  // جلب token
  Future<String?> getToken() async {
    final token = await storage.read(key: 'jwt_token');
    final expiry = await storage.read(key: 'token_expiry');
    
    if (token == null || expiry == null) return null;
    
    // التحقق من انتهاء الصلاحية
    if (DateTime.parse(expiry).isBefore(DateTime.now())) {
      await logout();
      return null;
    }
    
    return token;
  }
  
  // حذف token
  Future<void> logout() async {
    await storage.delete(key: 'jwt_token');
    await storage.delete(key: 'token_expiry');
  }
}
```

**Interceptor للـ HTTP requests:**
```dart
import 'package:dio/dio.dart';

class AuthInterceptor extends Interceptor {
  final AuthService authService;
  
  AuthInterceptor(this.authService);
  
  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await authService.getToken();
    
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    
    return handler.next(options);
  }
  
  @override
  void onError(DioError err, ErrorInterceptorHandler handler) {
    if (err.response?.statusCode == 401) {
      // Token منتهي أو غير صالح
      authService.logout();
      // الانتقال لصفحة تسجيل الدخول
    }
    
    return handler.next(err);
  }
}
```

---

## 🎨 UI/UX Recommendations

### 1. واجهة الالتزامات المالية
```dart
class LiabilitiesScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('التزاماتي المالية')),
      body: FutureBuilder<LiabilitiesResponse>(
        future: liabilityService.getLiabilities(),
        builder: (context, snapshot) {
          if (snapshot.hasData) {
            return Column(
              children: [
                // بطاقات الإحصائيات
                _buildStatisticsCards(snapshot.data!),
                
                // قائمة الالتزامات
                Expanded(
                  child: ListView.builder(
                    itemCount: snapshot.data!.data.liabilities.length,
                    itemBuilder: (context, index) {
                      return _buildLiabilityCard(
                        snapshot.data!.data.liabilities[index]
                      );
                    },
                  ),
                ),
              ],
            );
          }
          return CircularProgressIndicator();
        },
      ),
    );
  }
  
  Widget _buildStatisticsCards(LiabilitiesResponse data) {
    return Row(
      children: [
        _buildStatCard(
          'الالتزامات النشطة',
          '${data.data.activeLiabilities} ر.س',
          Colors.orange,
          Icons.pending_actions,
        ),
        _buildStatCard(
          'الالتزامات المسددة',
          '${data.data.paidLiabilities} ر.س',
          Colors.green,
          Icons.check_circle,
        ),
      ],
    );
  }
  
  Widget _buildLiabilityCard(Liability liability) {
    return Card(
      child: ExpansionTile(
        title: Text(liability.typeAr),
        subtitle: Text(
          'المبلغ المتبقي: ${liability.remainingAmount} ر.س'
        ),
        children: [
          // تفاصيل الأقساط
          ...liability.installments.map((inst) => 
            ListTile(
              leading: Icon(
                inst.status == 'paid' 
                  ? Icons.check_circle 
                  : Icons.schedule,
                color: inst.status == 'paid' 
                  ? Colors.green 
                  : Colors.orange,
              ),
              title: Text('القسط ${inst.installmentNumber}'),
              subtitle: Text('${inst.amount} ر.س - ${inst.dueDate}'),
              trailing: Text(inst.statusAr),
            ),
          ).toList(),
        ],
      ),
    );
  }
}
```

### 2. واجهة إنشاء طلب سلفة
```dart
class CreateAdvancePaymentScreen extends StatefulWidget {
  @override
  _CreateAdvancePaymentScreenState createState() =>
      _CreateAdvancePaymentScreenState();
}

class _CreateAdvancePaymentScreenState 
    extends State<CreateAdvancePaymentScreen> {
  
  final _formKey = GlobalKey<FormState>();
  final _amountController = TextEditingController();
  int _installments = 3;
  String _reason = '';
  bool _isLoading = false;
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('طلب سلفة جديد')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: EdgeInsets.all(16),
          children: [
            // حقل المبلغ
            TextFormField(
              controller: _amountController,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(
                labelText: 'المبلغ المطلوب (ر.س)',
                border: OutlineInputBorder(),
              ),
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'الرجاء إدخال المبلغ';
                }
                final amount = double.tryParse(value);
                if (amount == null || amount <= 0) {
                  return 'المبلغ غير صحيح';
                }
                return null;
              },
            ),
            
            SizedBox(height: 16),
            
            // عدد الأقساط
            Text('عدد الأقساط', style: TextStyle(fontSize: 16)),
            Slider(
              value: _installments.toDouble(),
              min: 1,
              max: 12,
              divisions: 11,
              label: '$_installments أقساط',
              onChanged: (value) {
                setState(() {
                  _installments = value.toInt();
                });
              },
            ),
            
            // معاينة القسط الشهري
            if (_amountController.text.isNotEmpty)
              Card(
                color: Colors.blue.shade50,
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Column(
                    children: [
                      Text('القسط الشهري المتوقع:'),
                      Text(
                        '${(double.parse(_amountController.text) / _installments).toStringAsFixed(2)} ر.س',
                        style: TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                          color: Colors.blue,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            
            SizedBox(height: 16),
            
            // سبب الطلب
            TextFormField(
              maxLines: 3,
              decoration: InputDecoration(
                labelText: 'سبب الطلب (اختياري)',
                border: OutlineInputBorder(),
              ),
              onChanged: (value) => _reason = value,
            ),
            
            SizedBox(height: 24),
            
            // زر الإرسال
            ElevatedButton(
              onPressed: _isLoading ? null : _submitRequest,
              child: _isLoading
                  ? CircularProgressIndicator()
                  : Text('إرسال الطلب'),
              style: ElevatedButton.styleFrom(
                padding: EdgeInsets.symmetric(vertical: 16),
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Future<void> _submitRequest() async {
    if (!_formKey.currentState!.validate()) return;
    
    setState(() => _isLoading = true);
    
    try {
      final response = await requestService.createAdvancePayment(
        amount: double.parse(_amountController.text),
        installments: _installments,
        reason: _reason,
      );
      
      // عرض رسالة نجاح
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('تم إرسال الطلب بنجاح')),
      );
      
      // العودة للصفحة السابقة
      Navigator.pop(context, response.data.requestId);
      
    } catch (e) {
      // عرض رسالة خطأ
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('فشل إرسال الطلب: $e')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }
}
```

---

## ⚡ تحسينات الأداء

### 1. Caching Strategy
```dart
import 'package:hive/hive.dart';

class CacheService {
  // تخزين مؤقت للبيانات
  Future<void> cacheLiabilities(LiabilitiesResponse data) async {
    final box = await Hive.openBox('liabilities_cache');
    await box.put('data', data.toJson());
    await box.put('timestamp', DateTime.now().toIso8601String());
  }
  
  Future<LiabilitiesResponse?> getCachedLiabilities() async {
    final box = await Hive.openBox('liabilities_cache');
    final timestamp = box.get('timestamp');
    
    if (timestamp == null) return null;
    
    // التحقق من صلاحية البيانات (مثلاً: ساعة واحدة)
    final cacheTime = DateTime.parse(timestamp);
    if (DateTime.now().difference(cacheTime).inHours > 1) {
      return null;
    }
    
    final data = box.get('data');
    return data != null ? LiabilitiesResponse.fromJson(data) : null;
  }
}
```

### 2. Pagination للقوائم الكبيرة
```dart
class InfiniteScrollListView extends StatefulWidget {
  @override
  _InfiniteScrollListViewState createState() =>
      _InfiniteScrollListViewState();
}

class _InfiniteScrollListViewState extends State<InfiniteScrollListView> {
  final ScrollController _scrollController = ScrollController();
  List<Request> _requests = [];
  int _page = 1;
  bool _isLoading = false;
  bool _hasMore = true;
  
  @override
  void initState() {
    super.initState();
    _loadMore();
    _scrollController.addListener(() {
      if (_scrollController.position.pixels ==
          _scrollController.position.maxScrollExtent) {
        _loadMore();
      }
    });
  }
  
  Future<void> _loadMore() async {
    if (_isLoading || !_hasMore) return;
    
    setState(() => _isLoading = true);
    
    try {
      final response = await requestService.getRequests(page: _page);
      
      setState(() {
        _requests.addAll(response.requests);
        _page++;
        _hasMore = response.hasMore;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      controller: _scrollController,
      itemCount: _requests.length + (_hasMore ? 1 : 0),
      itemBuilder: (context, index) {
        if (index == _requests.length) {
          return Center(child: CircularProgressIndicator());
        }
        return RequestCard(request: _requests[index]);
      },
    );
  }
}
```

---

## 📦 Dependencies المطلوبة في Flutter

```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # HTTP & Networking
  http: ^1.1.0
  dio: ^5.3.3  # للـ interceptors والتحميل المتقدم
  
  # State Management
  provider: ^6.1.1
  riverpod: ^2.4.5
  
  # Storage
  flutter_secure_storage: ^9.0.0  # للـ JWT tokens
  hive: ^2.2.3  # للتخزين المؤقت
  hive_flutter: ^1.1.0
  
  # File Handling
  image_picker: ^1.0.4
  file_picker: ^6.0.0
  path_provider: ^2.1.1
  
  # UI Components
  cached_network_image: ^3.3.0
  shimmer: ^3.0.0  # للـ loading placeholders
  intl: ^0.18.1  # للتواريخ والأرقام
  
  # Video Player
  video_player: ^2.8.1
  chewie: ^1.7.1  # video player UI
  
  # Utilities
  connectivity_plus: ^5.0.1  # للتحقق من الاتصال
  permission_handler: ^11.0.1
```

---

## 🧪 اختبار API

### Postman Collection
```json
{
  "info": {
    "name": "نُظم API - Flutter",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{jwt_token}}",
        "type": "string"
      }
    ]
  },
  "item": [
    {
      "name": "1. تسجيل الدخول",
      "request": {
        "method": "POST",
        "header": [],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"employee_id\": \"5216\",\n  \"password\": \"password123\"\n}",
          "options": {
            "raw": {
              "language": "json"
            }
          }
        },
        "url": {
          "raw": "{{base_url}}/api/external/v1/auth/login",
          "host": ["{{base_url}}"],
          "path": ["api", "external", "v1", "auth", "login"]
        }
      }
    },
    {
      "name": "2. جلب الالتزامات المالية",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/api/external/v1/employee/liabilities?status=active",
          "host": ["{{base_url}}"],
          "path": ["api", "external", "v1", "employee", "liabilities"],
          "query": [
            {
              "key": "status",
              "value": "active"
            }
          ]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "https://eissahr.replit.app",
      "type": "string"
    },
    {
      "key": "jwt_token",
      "value": "",
      "type": "string"
    }
  ]
}
```

---

## 📚 Resources

### Documentation Links
- [Flutter HTTP Package](https://pub.dev/packages/http)
- [Dio Documentation](https://pub.dev/packages/dio)
- [Flutter Secure Storage](https://pub.dev/packages/flutter_secure_storage)
- [JWT.io](https://jwt.io/)

### API Testing Tools
- Postman
- Insomnia
- cURL commands

---

## ✅ Checklist للتطوير

### Backend (Replit)
- [ ] إنشاء models للالتزامات المالية
- [ ] إنشاء service layer للـ financial logic
- [ ] تنفيذ endpoint الالتزامات المالية
- [ ] تنفيذ endpoint الملخص المالي
- [ ] تنفيذ endpoints الطلبات المتخصصة
- [ ] تنفيذ endpoints رفع الملفات المتخصصة
- [ ] إضافة validation rules
- [ ] اختبار جميع الـ endpoints
- [ ] توثيق API بشكل كامل

### Frontend (Flutter)
- [ ] إعداد project structure
- [ ] تنفيذ authentication service
- [ ] تنفيذ HTTP client مع interceptors
- [ ] تنفيذ models وdata classes
- [ ] تنفيذ UI للالتزامات المالية
- [ ] تنفيذ UI لإنشاء الطلبات
- [ ] تنفيذ رفع الملفات
- [ ] إضافة caching strategy
- [ ] اختبار على أجهزة مختلفة
- [ ] اختبار أداء التطبيق

---

**آخر تحديث:** 2025-01-15  
**الإصدار:** 2.0  
**الحالة:** جاهز للتطوير 🚀
