# 📍 خطة تطوير ميزة الدوائر الجغرافية (Geofencing)

> مستوحاة من تطبيق Life360 - نظام تتبع ذكي للموظفين داخل مناطق محددة

---

## 🎯 الفكرة الأساسية

### ما هي الدوائر الجغرافية؟

الدوائر الجغرافية (Geofencing) هي مناطق افتراضية يتم رسمها على الخريطة. يمكن معرفة من هو داخل الدائرة ومن هو خارجها، مع إمكانية **تسجيل حضور جماعي** لجميع الموظفين داخل الدائرة بضغطة زر واحدة.

### مثال عملي:
- **دائرة المشروع الأول**: نطاق 500 متر حول موقع المشروع
- **دائرة المكتب الرئيسي**: نطاق 200 متر حول المكتب
- **دائرة المستودع**: نطاق 300 متر حول المستودع

---

## 🎯 الميزات المطلوبة

### 1️⃣ رسم الدوائر على الخريطة
- إنشاء دوائر بأحجام مختلفة (200-500-1000 متر)
- تخصيص لون لكل دائرة
- ربط الدائرة بقسم أو مشروع معين
- تعيين موظفين محددين لكل دائرة

### 2️⃣ الكشف التلقائي عن الموظفين داخل/خارج الدائرة
- **✅ داخل الدائرة** (أخضر) - الموظف موجود داخل النطاق
- **⚠️ خارج الدائرة** (أصفر) - الموظف خارج النطاق
- **❌ بعيد جداً** (أحمر) - الموظف بعيد عن المنطقة

### 3️⃣ سجل الأحداث (الدخول والخروج)
- تسجيل تلقائي لوقت **دخول** الموظف للدائرة
- تسجيل تلقائي لوقت **خروج** الموظف من الدائرة
- حساب **مدة البقاء** داخل الدائرة
- عرض تاريخ كامل للدخول والخروج

### 4️⃣ **زر تسجيل الحضور الجماعي** ⭐ (الميزة الرئيسية)

#### الفكرة:
- في صفحة إدارة الدوائر، يظهر **زر كبير** بجانب كل دائرة
- عند الضغط على الزر، يتم:
  1. **الكشف عن جميع الموظفين داخل الدائرة حالياً**
  2. **تسجيل حضور لهم جميعاً دفعة واحدة**
  3. **عرض قائمة بأسماء من تم تسجيل حضورهم**

#### مثال الواجهة:
```
┌─────────────────────────────────────────────────────────────┐
│  دائرة: مشروع برج المملكة                                  │
│  📍 الرياض - حي العليا                                     │
│  👥 الموظفين داخل الدائرة: 8 موظفين                       │
│                                                             │
│  [✅ تسجيل حضور جماعي]  [📊 عرض السجل]  [⚙️ إعدادات]     │
│                                                             │
│  الموظفين الحاليين داخل الدائرة:                          │
│  • أحمد محمد (مهندس) - ✅ داخل                            │
│  • خالد علي (فني) - ✅ داخل                               │
│  • فهد سعد (مشرف) - ✅ داخل                               │
│  • ... (5 آخرين)                                          │
└─────────────────────────────────────────────────────────────┘
```

### 5️⃣ الإشعارات
- **إشعار عند الدخول/الخروج** (اختياري للمدير)
- **تقرير يومي** بحركة الموظفين في الدوائر
- **تنبيه للتأخير** إذا لم يصل موظف للدائرة في الوقت المحدد

### 6️⃣ عرض صورة القمر الصناعي
- زر لتبديل بين الخريطة العادية وصورة القمر الصناعي
- استخدام **Mapbox Satellite** للحصول على صور واضحة
- رؤية دقيقة للمباني والشوارع

### 7️⃣ نسخ رابط الموقع للمشاركة
- إنشاء **رابط مؤقت** لمشاركة موقع الدائرة
- الرابط يفتح خريطة تفاعلية بدون الحاجة لتسجيل دخول
- الرابط ينتهي بعد 24 ساعة للأمان

### 8️⃣ عرض صور الموظفين على الخريطة
- إذا كان للموظف صورة شخصية، تظهر على الخريطة
- صورة دائرية صغيرة (64×64 بكسل)
- صورة افتراضية للموظفين بدون صور

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
    notify_on_entry BOOLEAN DEFAULT FALSE,         -- إشعار عند الدخول
    notify_on_exit BOOLEAN DEFAULT FALSE,          -- إشعار عند الخروج
    department_id INTEGER REFERENCES department(id),
    project_id INTEGER,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_radius CHECK (radius_meters > 0 AND radius_meters <= 10000),
    CONSTRAINT valid_type CHECK (type IN ('project', 'office', 'warehouse', 'other'))
);
```

#### 2. جدول الأعضاء (geofence_membership)
```sql
CREATE TABLE geofence_membership (
    id SERIAL PRIMARY KEY,
    geofence_id INTEGER REFERENCES geofences(id) ON DELETE CASCADE,
    employee_id INTEGER REFERENCES employee(id) ON DELETE CASCADE,
    active_from TIMESTAMP DEFAULT NOW(),
    active_to TIMESTAMP,
    priority INTEGER DEFAULT 1,                    -- الأولوية عند التداخل
    assigned_by INTEGER REFERENCES users(id),
    assigned_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(geofence_id, employee_id)
);
```

#### 3. جدول الأحداث (geofence_events)
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
    source VARCHAR(20) DEFAULT 'auto',             -- auto, manual, bulk
    attendance_id INTEGER REFERENCES attendance(id),
    notes TEXT,
    
    CONSTRAINT valid_event_type CHECK (
        event_type IN ('enter', 'exit', 'bulk_check_in')
    )
);
```

#### الفهارس للأداء:
```sql
CREATE INDEX idx_geofence_active ON geofences(is_active);
CREATE INDEX idx_geofence_membership_employee ON geofence_membership(employee_id);
CREATE INDEX idx_geofence_events_time ON geofence_events(recorded_at DESC);
CREATE INDEX idx_geofence_events_employee ON geofence_events(employee_id, recorded_at DESC);
```

---

## 💻 التنفيذ المقترح

### 1. Models في Flask

```python
class Geofence(db.Model):
    """دائرة جغرافية"""
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
    notify_on_entry = db.Column(db.Boolean, default=False)
    notify_on_exit = db.Column(db.Boolean, default=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    members = db.relationship('GeofenceMembership', backref='geofence', cascade='all, delete-orphan')
    events = db.relationship('GeofenceEvent', backref='geofence', cascade='all, delete-orphan')
    
    def get_employees_inside(self):
        """جلب جميع الموظفين داخل الدائرة حالياً"""
        from models import Employee, EmployeeLocation
        
        employees_inside = []
        
        # جلب أعضاء الدائرة النشطين
        active_members = GeofenceMembership.query.filter_by(
            geofence_id=self.id
        ).filter(
            (GeofenceMembership.active_to.is_(None)) | 
            (GeofenceMembership.active_to > datetime.utcnow())
        ).all()
        
        for membership in active_members:
            employee = membership.employee
            
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
    
    def calculate_distance(self, lat, lon):
        """حساب المسافة من مركز الدائرة"""
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


class GeofenceMembership(db.Model):
    """عضوية موظف في دائرة"""
    __tablename__ = 'geofence_membership'
    
    id = db.Column(db.Integer, primary_key=True)
    geofence_id = db.Column(db.Integer, db.ForeignKey('geofences.id', ondelete='CASCADE'))
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id', ondelete='CASCADE'))
    active_from = db.Column(db.DateTime, default=datetime.utcnow)
    active_to = db.Column(db.DateTime)
    priority = db.Column(db.Integer, default=1)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    employee = db.relationship('Employee', backref='geofence_memberships')


class GeofenceEvent(db.Model):
    """حدث دخول/خروج"""
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

### 2. Route لتسجيل الحضور الجماعي

```python
@geofences_bp.route('/<int:geofence_id>/bulk-check-in', methods=['POST'])
@login_required
def bulk_check_in(geofence_id):
    """تسجيل حضور جماعي لجميع الموظفين داخل الدائرة"""
    
    geofence = Geofence.query.get_or_404(geofence_id)
    
    # جلب الموظفين داخل الدائرة
    employees_inside = geofence.get_employees_inside()
    
    if not employees_inside:
        return jsonify({
            'success': False,
            'message': 'لا يوجد موظفين داخل الدائرة حالياً'
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
                notes=f'تسجيل جماعي من دائرة: {geofence.name}'
            )
            db.session.add(attendance)
            
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
                notes=f'تسجيل جماعي بواسطة {current_user.username}'
            )
            db.session.add(event)
            
            checked_in.append(employee.name)
            
        except Exception as e:
            errors.append(f'{employee.name}: {str(e)}')
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'checked_in_count': len(checked_in),
        'already_checked_count': len(already_checked),
        'error_count': len(errors),
        'checked_in': checked_in,
        'already_checked': already_checked,
        'errors': errors,
        'message': f'تم تسجيل حضور {len(checked_in)} موظف بنجاح'
    })
```

---

## 🗓️ خطة التنفيذ

### **المرحلة 1: البنية الأساسية** (أسبوع 1)
- [ ] إنشاء الجداول الثلاثة في قاعدة البيانات
- [ ] إنشاء Models في Flask
- [ ] إنشاء Routes الأساسية للدوائر

### **المرحلة 2: المعالجة التلقائية** (أسبوع 2)
- [ ] كشف تلقائي للدخول/الخروج
- [ ] تسجيل الأحداث في الجدول
- [ ] حساب المسافات بكفاءة (Haversine)

### **المرحلة 3: الواجهة والخريطة** (أسبوع 3)
- [ ] صفحة إدارة الدوائر
- [ ] رسم الدوائر على الخريطة (Leaflet.js)
- [ ] عرض الموظفين داخل/خارج الدائرة
- [ ] **زر تسجيل الحضور الجماعي** ⭐
- [ ] عرض صور الموظفين على الخريطة
- [ ] تبديل صورة القمر الصناعي (Mapbox Satellite)

### **المرحلة 4: الميزات الإضافية** (أسبوع 4)
- [ ] روابط المشاركة المؤقتة
- [ ] الإشعارات (اختيارية)
- [ ] التقارير والإحصائيات
- [ ] سجل الدخول والخروج التاريخي

---

## 💡 ملاحظات مهمة

### الفرق الأساسي: تسجيل يدوي بدلاً من تلقائي

#### ❌ **ما لن نفعله:**
- تسجيل حضور تلقائي عند دخول الموظف
- تسجيل انصراف تلقائي عند الخروج

#### ✅ **ما سنفعله:**
- كشف تلقائي لمن هو داخل/خارج الدائرة
- تسجيل أحداث الدخول/الخروج للتتبع فقط
- **زر يدوي** لتسجيل حضور جميع من هم داخل الدائرة
- المدير يضغط الزر متى ما أراد تسجيل الحضور

### الأمان والخصوصية:
- موافقة الموظف على التتبع
- تشفير البيانات
- حذف البيانات القديمة بعد 6 أشهر

### الأداء:
- Cache لمراكز الدوائر
- حساب المسافات فقط عند الحاجة
- تجميع علامات الموظفين على الخريطة

---

**تاريخ التحديث**: 08 نوفمبر 2025  
**الإصدار**: 2.0  
**الحالة**: جاهز للتنفيذ ✅
