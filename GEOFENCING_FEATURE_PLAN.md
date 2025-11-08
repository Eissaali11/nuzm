# 📍 خطة تطوير ميزة الدوائر الجغرافية (Geofencing)

> مستوحاة من تطبيق Life360 - نظام تتبع ذكي للموظفين مع ربط صارم بالأقسام

---

## 🎯 الفكرة الأساسية

### ما هي الدوائر الجغرافية؟

الدوائر الجغرافية (Geofencing) هي مناطق افتراضية **مرتبطة بقسم معين** يتم رسمها على الخريطة. يمكن معرفة موظفي القسم داخل الدائرة ومن هو خارجها، مع إمكانية **تسجيل حضور جماعي فقط لموظفي القسم المرتبط** بضغطة زر واحدة.

### ⚠️ **القاعدة الأساسية:**
**الدائرة مرتبطة بقسم واحد فقط** → يتم تسجيل الحضور **فقط لموظفي هذا القسم** الموجودين داخل الدائرة.

### مثال عملي:

#### دائرة "مشروع برج المملكة" 🏢
- **مرتبطة بقسم**: الهندسة
- **الموقع**: الرياض - حي العليا
- **نصف القطر**: 500 متر
- **الموظفين المؤهلين للحضور**: فقط موظفو قسم الهندسة

**السيناريو:**
```
الموظفين داخل الدائرة:
✅ أحمد محمد (قسم: الهندسة) ← سيُسجل حضوره
✅ خالد علي (قسم: الهندسة) ← سيُسجل حضوره
❌ فهد سعد (قسم: المبيعات) ← لن يُسجل حضوره (قسم مختلف)
❌ سعد أحمد (قسم: المحاسبة) ← لن يُسجل حضوره (قسم مختلف)
```

#### دائرة "المكتب الرئيسي" 🏛️
- **مرتبطة بقسم**: الإدارة
- **الموقع**: الرياض - العليا
- **نصف القطر**: 200 متر
- **الموظفين المؤهلين للحضور**: فقط موظفو قسم الإدارة

#### دائرة "المستودع الشمالي" 📦
- **مرتبطة بقسم**: اللوجستيات
- **الموقع**: الرياض - الشمال
- **نصف القطر**: 300 متر
- **الموظفين المؤهلين للحضور**: فقط موظفو قسم اللوجستيات

---

## 🎯 الميزات المطلوبة

### 1️⃣ إنشاء وإدارة الدوائر

#### عند إنشاء دائرة جديدة:
```
┌─────────────────────────────────────────────┐
│  إضافة دائرة جغرافية جديدة                 │
├─────────────────────────────────────────────┤
│  اسم الدائرة: [مشروع برج المملكة      ]   │
│  النوع: [مشروع ▼]                          │
│  القسم المرتبط: [الهندسة ▼] ← **إلزامي**  │
│                                             │
│  الموقع على الخريطة: [انقر لتحديد]        │
│  نصف القطر: [500] متر                      │
│  اللون: [🟣 #667eea]                       │
│                                             │
│  [إنشاء الدائرة]                           │
└─────────────────────────────────────────────┘
```

**ملاحظة مهمة**: لا يمكن إنشاء دائرة بدون ربطها بقسم.

### 2️⃣ الكشف التلقائي (حسب القسم)

النظام يعرض فقط **موظفي القسم المرتبط** مع حالتهم:
- **✅ داخل الدائرة** (أخضر) - موظف من القسم وداخل النطاق
- **⚠️ خارج الدائرة** (أصفر) - موظف من القسم لكن خارج النطاق
- **🔒 موظفو أقسام أخرى** - يتم إخفاؤهم أو عرضهم بلون رمادي للمعلومة فقط

### 3️⃣ سجل الأحداث
- تسجيل **دخول/خروج** لجميع الموظفين (بغض النظر عن القسم) للتتبع
- لكن **تسجيل الحضور** فقط لموظفي القسم المرتبط

### 4️⃣ **زر تسجيل الحضور الجماعي** ⭐ (الميزة الرئيسية)

```
┌──────────────────────────────────────────────────────────────┐
│  📍 دائرة: مشروع برج المملكة                                │
│  🏢 القسم: الهندسة | 📏 نصف القطر: 500 متر                 │
├──────────────────────────────────────────────────────────────┤
│  👥 موظفو قسم الهندسة داخل الدائرة: 5 موظفين               │
│                                                              │
│  ┌────────────────────────────────────────────┐             │
│  │  ✅ تسجيل حضور جماعي (5 موظفين)          │ ← **الزر**  │
│  └────────────────────────────────────────────┘             │
│                                                              │
│  الموظفين المؤهلين (قسم الهندسة):                          │
│  ✅ أحمد محمد (مهندس إنشائي) - داخل - 120م                │
│  ✅ خالد علي (مهندس معماري) - داخل - 85م                   │
│  ✅ سعيد حسن (مهندس كهرباء) - داخل - 200م                  │
│  ✅ محمد عمر (مهندس ميكانيكا) - داخل - 150م                │
│  ✅ فهد عبدالله (مهندس مدني) - داخل - 300م                 │
│                                                              │
│  ─────────────────────────────────────────────────────       │
│  موظفون آخرون داخل الدائرة (أقسام أخرى):                   │
│  🔒 ياسر سعد (قسم المبيعات) - لن يُسجل حضوره               │
│  🔒 عمر فهد (قسم المحاسبة) - لن يُسجل حضوره                │
└──────────────────────────────────────────────────────────────┘
```

#### عند الضغط على الزر:
1. ✅ يتم تسجيل حضور **فقط** لموظفي قسم "الهندسة" الموجودين داخل الدائرة
2. ❌ لا يتم تسجيل حضور للموظفين من أقسام أخرى (حتى لو كانوا داخل الدائرة)
3. ✅ يظهر إشعار: "تم تسجيل حضور 5 موظفين من قسم الهندسة"
4. ✅ يتم تخطي من سجل حضوره مسبقاً اليوم

### 5️⃣ الإشعارات (اختيارية)
- إشعار عند دخول/خروج موظف من القسم المرتبط
- تقرير يومي بحركة موظفي القسم
- تنبيه للتأخير لموظفي القسم

### 6️⃣ عرض صورة القمر الصناعي
- زر لتبديل بين الخريطة العادية وصورة القمر الصناعي
- استخدام **Mapbox Satellite** للوضوح

### 7️⃣ نسخ رابط الموقع للمشاركة
- إنشاء **رابط مؤقت** لمشاركة موقع الدائرة
- ينتهي بعد 24 ساعة

### 8️⃣ عرض صور الموظفين على الخريطة
- صورة دائرية صغيرة (64×64 بكسل)
- تمييز موظفي القسم المرتبط بلون مختلف

---

## 🏗️ البنية التقنية

### قاعدة البيانات

#### 1. جدول الدوائر (geofences)
```sql
CREATE TABLE geofences (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,                    -- اسم الدائرة
    type VARCHAR(50) DEFAULT 'project',            -- نوع (project, office, warehouse)
    description TEXT,                               -- وصف
    center_latitude NUMERIC(9, 6) NOT NULL,        -- خط العرض
    center_longitude NUMERIC(9, 6) NOT NULL,       -- خط الطول
    radius_meters INTEGER NOT NULL,                -- نصف القطر
    color VARCHAR(20) DEFAULT '#667eea',           -- لون الدائرة
    is_active BOOLEAN DEFAULT TRUE,                -- هل نشطة؟
    
    -- ⭐ **الحقل الأساسي: ربط صارم بقسم واحد**
    department_id INTEGER NOT NULL REFERENCES department(id) ON DELETE CASCADE,
    
    notify_on_entry BOOLEAN DEFAULT FALSE,         -- إشعار عند الدخول
    notify_on_exit BOOLEAN DEFAULT FALSE,          -- إشعار عند الخروج
    
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_radius CHECK (radius_meters > 0 AND radius_meters <= 10000),
    CONSTRAINT valid_type CHECK (type IN ('project', 'office', 'warehouse', 'other'))
);

-- فهرس لتسريع البحث بالقسم
CREATE INDEX idx_geofence_department ON geofences(department_id, is_active);
```

**ملاحظة**: `department_id` الآن **NOT NULL** - يجب ربط كل دائرة بقسم.

#### 2. جدول الأحداث (geofence_events)
```sql
CREATE TABLE geofence_events (
    id SERIAL PRIMARY KEY,
    geofence_id INTEGER REFERENCES geofences(id) ON DELETE CASCADE,
    employee_id INTEGER REFERENCES employee(id) ON DELETE CASCADE,
    event_type VARCHAR(30) NOT NULL,               -- enter, exit, bulk_check_in
    location_latitude NUMERIC(9, 6),
    location_longitude NUMERIC(9, 6),
    distance_from_center INTEGER,
    recorded_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    source VARCHAR(20) DEFAULT 'auto',             -- auto, bulk
    attendance_id INTEGER REFERENCES attendance(id),
    notes TEXT,
    
    CONSTRAINT valid_event_type CHECK (
        event_type IN ('enter', 'exit', 'bulk_check_in')
    )
);

-- فهارس للأداء
CREATE INDEX idx_geofence_events_time ON geofence_events(recorded_at DESC);
CREATE INDEX idx_geofence_events_employee ON geofence_events(employee_id, recorded_at DESC);
CREATE INDEX idx_geofence_events_geofence ON geofence_events(geofence_id, recorded_at DESC);
```

**تبسيط**: تم إزالة جدول `geofence_membership` لأننا نعتمد على **ربط القسم** مباشرة.

---

## 💻 التنفيذ المقترح

### 1. Models في Flask

```python
class Geofence(db.Model):
    """دائرة جغرافية مرتبطة بقسم"""
    __tablename__ = 'geofences'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), default='project')
    description = db.Column(db.Text)
    center_latitude = db.Column(db.Numeric(9, 6), nullable=False)
    center_longitude = db.Column(db.Numeric(9, 6), nullable=False)
    radius_meters = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(20), default='#667eea')
    is_active = db.Column(db.Boolean, default=True)
    
    # ⭐ **ربط إلزامي بقسم واحد**
    department_id = db.Column(db.Integer, db.ForeignKey('department.id', ondelete='CASCADE'), nullable=False)
    
    notify_on_entry = db.Column(db.Boolean, default=False)
    notify_on_exit = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    department = db.relationship('Department', backref='geofences')
    events = db.relationship('GeofenceEvent', backref='geofence', cascade='all, delete-orphan')
    
    def get_department_employees_inside(self):
        """
        جلب موظفي القسم المرتبط الموجودين داخل الدائرة فقط
        """
        from models import Employee, EmployeeLocation
        
        employees_inside = []
        
        # ⭐ **جلب موظفي القسم المرتبط فقط**
        department_employees = Employee.query.join(employee_departments).filter(
            employee_departments.c.department_id == self.department_id
        ).all()
        
        for employee in department_employees:
            # جلب آخر موقع للموظف
            latest_location = EmployeeLocation.query.filter_by(
                employee_id=employee.id
            ).order_by(EmployeeLocation.recorded_at.desc()).first()
            
            if latest_location:
                # التحقق من وجوده داخل الدائرة
                distance = self.calculate_distance(
                    latest_location.latitude,
                    latest_location.longitude
                )
                
                if distance <= self.radius_meters:
                    employees_inside.append({
                        'employee': employee,
                        'location': latest_location,
                        'distance': distance
                    })
        
        return employees_inside
    
    def get_all_employees_inside(self):
        """
        جلب جميع الموظفين داخل الدائرة (من جميع الأقسام)
        للعرض فقط - لن يتم تسجيل حضور لهم
        """
        from models import Employee, EmployeeLocation
        
        all_employees_inside = []
        
        # جلب جميع الموظفين
        all_employees = Employee.query.all()
        
        for employee in all_employees:
            latest_location = EmployeeLocation.query.filter_by(
                employee_id=employee.id
            ).order_by(EmployeeLocation.recorded_at.desc()).first()
            
            if latest_location:
                distance = self.calculate_distance(
                    latest_location.latitude,
                    latest_location.longitude
                )
                
                if distance <= self.radius_meters:
                    # التحقق من القسم
                    is_from_linked_department = any(
                        dept.id == self.department_id 
                        for dept in employee.departments
                    )
                    
                    all_employees_inside.append({
                        'employee': employee,
                        'location': latest_location,
                        'distance': distance,
                        'is_eligible': is_from_linked_department  # ⭐ مؤهل للحضور
                    })
        
        return all_employees_inside
    
    def calculate_distance(self, lat, lon):
        """حساب المسافة من مركز الدائرة باستخدام Haversine"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000  # نصف قطر الأرض بالأمتار
        
        lat1 = radians(float(self.center_latitude))
        lon1 = radians(float(self.center_longitude))
        lat2 = radians(lat)
        lon2 = radians(lon)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c


class GeofenceEvent(db.Model):
    """حدث دخول/خروج/تسجيل جماعي"""
    __tablename__ = 'geofence_events'
    
    id = db.Column(db.Integer, primary_key=True)
    geofence_id = db.Column(db.Integer, db.ForeignKey('geofences.id', ondelete='CASCADE'))
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id', ondelete='CASCADE'))
    event_type = db.Column(db.String(30), nullable=False)
    location_latitude = db.Column(db.Numeric(9, 6))
    location_longitude = db.Column(db.Numeric(9, 6))
    distance_from_center = db.Column(db.Integer)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    source = db.Column(db.String(20), default='auto')
    attendance_id = db.Column(db.Integer, db.ForeignKey('attendance.id'))
    notes = db.Column(db.Text)
    
    # العلاقات
    employee = db.relationship('Employee', backref='geofence_events')
```

### 2. Route لتسجيل الحضور الجماعي (مُحدّث)

```python
@geofences_bp.route('/<int:geofence_id>/bulk-check-in', methods=['POST'])
@login_required
def bulk_check_in(geofence_id):
    """
    تسجيل حضور جماعي فقط لموظفي القسم المرتبط بالدائرة
    """
    
    geofence = Geofence.query.get_or_404(geofence_id)
    
    # ⭐ **جلب موظفي القسم المرتبط فقط**
    employees_inside = geofence.get_department_employees_inside()
    
    if not employees_inside:
        return jsonify({
            'success': False,
            'message': f'لا يوجد موظفين من قسم "{geofence.department.name}" داخل الدائرة حالياً'
        })
    
    checked_in = []
    already_checked = []
    errors = []
    
    for emp_data in employees_inside:
        employee = emp_data['employee']
        location = emp_data['location']
        
        # التحقق من عدم وجود حضور مسجل اليوم
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        existing_attendance = Attendance.query.filter(
            Attendance.employee_id == employee.id,
            Attendance.check_in_time >= today_start
        ).first()
        
        if existing_attendance:
            already_checked.append(employee.name)
            continue
        
        try:
            # تسجيل الحضور
            attendance = Attendance(
                employee_id=employee.id,
                check_in_time=datetime.utcnow(),
                status='present',
                notes=f'تسجيل جماعي من دائرة: {geofence.name} (قسم: {geofence.department.name})'
            )
            db.session.add(attendance)
            db.session.flush()  # للحصول على attendance.id
            
            # تسجيل حدث في الدائرة
            event = GeofenceEvent(
                geofence_id=geofence.id,
                employee_id=employee.id,
                event_type='bulk_check_in',
                location_latitude=location.latitude,
                location_longitude=location.longitude,
                distance_from_center=int(emp_data['distance']),
                source='bulk',
                attendance_id=attendance.id,
                notes=f'تسجيل جماعي بواسطة {current_user.username} - قسم: {geofence.department.name}'
            )
            db.session.add(event)
            
            checked_in.append(employee.name)
            
        except Exception as e:
            errors.append(f'{employee.name}: {str(e)}')
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'department_name': geofence.department.name,
        'checked_in_count': len(checked_in),
        'already_checked_count': len(already_checked),
        'error_count': len(errors),
        'checked_in': checked_in,
        'already_checked': already_checked,
        'errors': errors,
        'message': f'تم تسجيل حضور {len(checked_in)} موظف من قسم "{geofence.department.name}" بنجاح'
    })
```

---

## 🗓️ خطة التنفيذ

### **المرحلة 1: البنية الأساسية** (أسبوع 1)
- [ ] إنشاء جدول `geofences` مع ربط إلزامي بالقسم
- [ ] إنشاء جدول `geofence_events`
- [ ] إنشاء Models في Flask
- [ ] إنشاء Routes الأساسية

### **المرحلة 2: المعالجة التلقائية** (أسبوع 2)
- [ ] كشف تلقائي للدخول/الخروج (لجميع الموظفين)
- [ ] تسجيل الأحداث (للتتبع)
- [ ] حساب المسافات بكفاءة (Haversine)

### **المرحلة 3: الواجهة والخريطة** (أسبوع 3)
- [ ] صفحة إدارة الدوائر
- [ ] نموذج إنشاء دائرة (مع اختيار القسم إلزامياً)
- [ ] رسم الدوائر على الخريطة (Leaflet.js)
- [ ] **عرض موظفي القسم داخل/خارج الدائرة**
- [ ] **زر تسجيل الحضور الجماعي** ⭐
- [ ] عرض صور الموظفين على الخريطة
- [ ] تبديل صورة القمر الصناعي (Mapbox Satellite)

### **المرحلة 4: الميزات الإضافية** (أسبوع 4)
- [ ] روابط المشاركة المؤقتة
- [ ] الإشعارات (اختيارية)
- [ ] التقارير والإحصائيات (حسب القسم)
- [ ] سجل الدخول والخروج التاريخي

---

## 💡 الفروقات الأساسية

### ✅ **التحديث الرئيسي:**

| الميزة | **النسخة السابقة** | **النسخة الحالية** |
|--------|-------------------|-------------------|
| ربط الدائرة بقسم | اختياري (nullable) | **إلزامي (NOT NULL)** |
| تسجيل الحضور | لجميع من في الدائرة | **فقط لموظفي القسم المرتبط** |
| عرض الموظفين | جميع من في الدائرة | **تمييز موظفي القسم** |
| جدول الأعضاء | geofence_membership | **تم إلغاؤه - نستخدم ربط القسم** |

### 🎯 **الفائدة:**
- **تحكم أفضل**: كل دائرة خاصة بقسم واحد
- **وضوح أكبر**: لا يوجد لبس في من يُسجل حضوره
- **بنية أبسط**: لا حاجة لجدول geofence_membership
- **أمان أعلى**: لا يمكن تسجيل حضور لموظف من قسم خاطئ

---

**تاريخ التحديث**: 08 نوفمبر 2025  
**الإصدار**: 3.0 (ربط صارم بالأقسام)  
**الحالة**: جاهز للتنفيذ ✅
