# 📍 خطة تطوير ميزة الدوائر الجغرافية (Geofencing)

> مستوحاة من تطبيق Life360 - نظام تتبع ذكي للموظفين داخل مناطق محددة

---

## 🎯 الفكرة الأساسية

### ما هي الدوائر الجغرافية؟

الدوائر الجغرافية (Geofencing) هي مناطق افتراضية يتم رسمها على الخريطة. عندما يدخل أو يخرج الموظف من هذه المنطقة، يتم تسجيل ذلك تلقائياً وإرسال إشعارات.

### مثال عملي:
- **دائرة المشروع الأول**: نطاق 500 متر حول موقع المشروع
- **دائرة المكتب الرئيسي**: نطاق 200 متر حول المكتب
- **دائرة المستودع**: نطاق 300 متر حول المستودع

---

## 🏗️ البنية المقترحة

### 1. قاعدة البيانات

#### جدول الدوائر الجغرافية
```sql
CREATE TABLE geofences (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,                    -- اسم الدائرة (مثل: "مشروع برج المملكة")
    description TEXT,                               -- وصف الدائرة
    center_latitude NUMERIC(10, 8) NOT NULL,       -- خط العرض للمركز
    center_longitude NUMERIC(11, 8) NOT NULL,      -- خط الطول للمركز
    radius_meters INTEGER NOT NULL,                -- نصف القطر بالأمتار
    color VARCHAR(20) DEFAULT '#667eea',           -- لون الدائرة على الخريطة
    is_active BOOLEAN DEFAULT TRUE,                -- هل الدائرة نشطة؟
    notify_on_entry BOOLEAN DEFAULT TRUE,          -- إرسال إشعار عند الدخول؟
    notify_on_exit BOOLEAN DEFAULT TRUE,           -- إرسال إشعار عند الخروج؟
    created_by INTEGER REFERENCES users(id),       -- من أنشأ الدائرة
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- علاقات
    department_id INTEGER REFERENCES department(id),  -- ربط بقسم معين (اختياري)
    project_id INTEGER,                               -- ربط بمشروع (اختياري)
    
    CONSTRAINT valid_radius CHECK (radius_meters > 0 AND radius_meters <= 10000)
);

-- جدول ربط الموظفين بالدوائر
CREATE TABLE geofence_employees (
    id SERIAL PRIMARY KEY,
    geofence_id INTEGER REFERENCES geofences(id) ON DELETE CASCADE,
    employee_id INTEGER REFERENCES employee(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by INTEGER REFERENCES users(id),
    
    UNIQUE(geofence_id, employee_id)
);

-- جدول تتبع الدخول والخروج
CREATE TABLE geofence_events (
    id SERIAL PRIMARY KEY,
    geofence_id INTEGER REFERENCES geofences(id) ON DELETE CASCADE,
    employee_id INTEGER REFERENCES employee(id) ON DELETE CASCADE,
    event_type VARCHAR(20) NOT NULL,               -- 'enter' أو 'exit'
    location_latitude NUMERIC(10, 8) NOT NULL,
    location_longitude NUMERIC(11, 8) NOT NULL,
    distance_from_center INTEGER,                   -- المسافة من المركز بالأمتار
    event_time TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    
    CONSTRAINT valid_event_type CHECK (event_type IN ('enter', 'exit'))
);

-- فهارس للأداء
CREATE INDEX idx_geofence_active ON geofences(is_active);
CREATE INDEX idx_geofence_events_employee ON geofence_events(employee_id, event_time DESC);
CREATE INDEX idx_geofence_events_geofence ON geofence_events(geofence_id, event_time DESC);
```

---

## 🎨 واجهة المستخدم

### 1. صفحة إدارة الدوائر (`/employees/geofences`)

#### المكونات:
- **خريطة تفاعلية**: لرسم وتحرير الدوائر
- **قائمة الدوائر**: عرض جميع الدوائر المُنشأة
- **نموذج إضافة/تعديل**: لإنشاء دوائر جديدة

#### الميزات:
```
┌─────────────────────────────────────────────────────────┐
│  إدارة الدوائر الجغرافية                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [خريطة تفاعلية - 70%]        [قائمة الدوائر - 30%]  │
│  • رسم دائرة جديدة             • مشروع برج المملكة    │
│  • تحرير الدوائر               • المكتب الرئيسي       │
│  • معاينة الموظفين داخلها      • مستودع الشمال       │
│                                                         │
│  [+ إضافة دائرة جديدة]                                │
└─────────────────────────────────────────────────────────┘
```

### 2. صفحة التتبع المُحسّنة

#### إضافات جديدة:
- **عرض الدوائر على الخريطة**: كدوائر شفافة ملونة
- **حالة الموظف داخل الدائرة**: 
  - ✅ داخل الدائرة (أخضر)
  - ⚠️ خارج الدائرة (أصفر)
  - ❌ بعيد جداً (أحمر)

---

## 💻 الكود المقترح

### 1. نموذج البيانات (Models)

```python
# في models.py

class Geofence(db.Model):
    """دائرة جغرافية لتتبع الموظفين"""
    __tablename__ = 'geofences'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    center_latitude = db.Column(db.Numeric(10, 8), nullable=False)
    center_longitude = db.Column(db.Numeric(11, 8), nullable=False)
    radius_meters = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(20), default='#667eea')
    is_active = db.Column(db.Boolean, default=True)
    notify_on_entry = db.Column(db.Boolean, default=True)
    notify_on_exit = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    
    # العلاقات
    employees = db.relationship('Employee', secondary='geofence_employees', backref='geofences')
    events = db.relationship('GeofenceEvent', backref='geofence', cascade='all, delete-orphan')
    
    def is_location_inside(self, latitude, longitude):
        """التحقق من وجود نقطة داخل الدائرة"""
        from math import radians, sin, cos, sqrt, atan2
        
        # حساب المسافة باستخدام Haversine formula
        R = 6371000  # نصف قطر الأرض بالأمتار
        
        lat1 = radians(float(self.center_latitude))
        lat2 = radians(latitude)
        delta_lat = radians(latitude - float(self.center_latitude))
        delta_lon = radians(longitude - float(self.center_longitude))
        
        a = sin(delta_lat/2)**2 + cos(lat1) * cos(lat2) * sin(delta_lon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        
        return distance <= self.radius_meters
    
    def get_distance(self, latitude, longitude):
        """حساب المسافة من المركز"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000
        lat1 = radians(float(self.center_latitude))
        lat2 = radians(latitude)
        delta_lat = radians(latitude - float(self.center_latitude))
        delta_lon = radians(longitude - float(self.center_longitude))
        
        a = sin(delta_lat/2)**2 + cos(lat1) * cos(lat2) * sin(delta_lon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c


class GeofenceEvent(db.Model):
    """سجل دخول وخروج الموظفين من الدوائر"""
    __tablename__ = 'geofence_events'
    
    id = db.Column(db.Integer, primary_key=True)
    geofence_id = db.Column(db.Integer, db.ForeignKey('geofences.id', ondelete='CASCADE'))
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id', ondelete='CASCADE'))
    event_type = db.Column(db.String(20), nullable=False)  # 'enter' or 'exit'
    location_latitude = db.Column(db.Numeric(10, 8), nullable=False)
    location_longitude = db.Column(db.Numeric(11, 8), nullable=False)
    distance_from_center = db.Column(db.Integer)
    event_time = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    # العلاقات
    employee = db.relationship('Employee', backref='geofence_events')


# جدول ربط
geofence_employees = db.Table('geofence_employees',
    db.Column('id', db.Integer, primary_key=True),
    db.Column('geofence_id', db.Integer, db.ForeignKey('geofences.id', ondelete='CASCADE')),
    db.Column('employee_id', db.Integer, db.ForeignKey('employee.id', ondelete='CASCADE')),
    db.Column('assigned_at', db.DateTime, default=datetime.utcnow),
    db.Column('assigned_by', db.Integer, db.ForeignKey('users.id'))
)
```

### 2. معالجة المواقع الواردة

```python
# في routes/api_external.py

def process_geofence_events(employee, latitude, longitude):
    """
    معالجة أحداث الدوائر الجغرافية عند استلام موقع جديد
    """
    # جلب جميع الدوائر النشطة المرتبطة بالموظف
    active_geofences = Geofence.query.filter(
        Geofence.is_active == True,
        Geofence.employees.contains(employee)
    ).all()
    
    for geofence in active_geofences:
        is_inside = geofence.is_location_inside(latitude, longitude)
        distance = geofence.get_distance(latitude, longitude)
        
        # جلب آخر حدث للموظف في هذه الدائرة
        last_event = GeofenceEvent.query.filter_by(
            geofence_id=geofence.id,
            employee_id=employee.id
        ).order_by(GeofenceEvent.event_time.desc()).first()
        
        # تحديد نوع الحدث
        event_type = None
        
        if is_inside:
            # داخل الدائرة
            if not last_event or last_event.event_type == 'exit':
                # دخول جديد
                event_type = 'enter'
        else:
            # خارج الدائرة
            if last_event and last_event.event_type == 'enter':
                # خروج جديد
                event_type = 'exit'
        
        # تسجيل الحدث
        if event_type:
            event = GeofenceEvent(
                geofence_id=geofence.id,
                employee_id=employee.id,
                event_type=event_type,
                location_latitude=latitude,
                location_longitude=longitude,
                distance_from_center=int(distance),
                notes=f'تم الكشف تلقائياً'
            )
            db.session.add(event)
            
            # إرسال إشعار (اختياري)
            if (event_type == 'enter' and geofence.notify_on_entry) or \
               (event_type == 'exit' and geofence.notify_on_exit):
                send_geofence_notification(employee, geofence, event_type)
    
    db.session.commit()


def send_geofence_notification(employee, geofence, event_type):
    """
    إرسال إشعار عند دخول أو خروج من دائرة
    """
    # يمكن استخدام SendGrid أو Twilio لإرسال الإشعارات
    message = f"الموظف {employee.name} "
    if event_type == 'enter':
        message += f"دخل إلى {geofence.name}"
    else:
        message += f"خرج من {geofence.name}"
    
    # TODO: تنفيذ إرسال الإشعار
    logger.info(f"إشعار: {message}")
```

### 3. Routes للدوائر

```python
# في routes/geofences.py (ملف جديد)

from flask import Blueprint, render_template, request, jsonify
from models import Geofence, GeofenceEvent, Employee, db
from flask_login import login_required, current_user

geofences_bp = Blueprint('geofences', __name__)

@geofences_bp.route('/')
@login_required
def index():
    """صفحة إدارة الدوائر الجغرافية"""
    if current_user.role != 'admin':
        flash('هذه الصفحة متاحة للمديرين فقط', 'danger')
        return redirect(url_for('dashboard.index'))
    
    geofences = Geofence.query.all()
    return render_template('geofences/index.html', geofences=geofences)


@geofences_bp.route('/create', methods=['POST'])
@login_required
def create():
    """إنشاء دائرة جديدة"""
    data = request.get_json()
    
    geofence = Geofence(
        name=data['name'],
        description=data.get('description'),
        center_latitude=data['latitude'],
        center_longitude=data['longitude'],
        radius_meters=data['radius'],
        color=data.get('color', '#667eea'),
        created_by=current_user.id
    )
    
    db.session.add(geofence)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'geofence_id': geofence.id,
        'message': 'تم إنشاء الدائرة بنجاح'
    })


@geofences_bp.route('/<int:id>/employees', methods=['POST'])
@login_required
def assign_employees(id):
    """ربط موظفين بدائرة"""
    geofence = Geofence.query.get_or_404(id)
    employee_ids = request.get_json().get('employee_ids', [])
    
    employees = Employee.query.filter(Employee.id.in_(employee_ids)).all()
    geofence.employees = employees
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'تم ربط {len(employees)} موظف بالدائرة'
    })


@geofences_bp.route('/<int:id>/events')
@login_required
def get_events(id):
    """جلب أحداث دائرة معينة"""
    geofence = Geofence.query.get_or_404(id)
    
    events = GeofenceEvent.query.filter_by(
        geofence_id=id
    ).order_by(GeofenceEvent.event_time.desc()).limit(100).all()
    
    return jsonify({
        'success': True,
        'events': [{
            'employee_name': event.employee.name,
            'event_type': event.event_type,
            'event_time': event.event_time.isoformat(),
            'distance': event.distance_from_center
        } for event in events]
    })
```

---

## 📊 الميزات المتقدمة

### 1. الإحصائيات والتقارير
- كم ساعة قضى الموظف داخل الدائرة؟
- متى دخل ومتى خرج؟
- كم مرة زار الموقع في الشهر؟

### 2. الإشعارات الذكية
- إشعار فوري عند دخول/خروج موظف
- تقرير يومي عن الحضور في المواقع
- تنبيه إذا لم يصل موظف للموقع في الوقت المحدد

### 3. التكامل مع الحضور
- ربط دخول الدائرة بتسجيل الحضور تلقائياً
- ربط خروج الدائرة بتسجيل الانصراف

---

## 🎯 خطة التنفيذ

### المرحلة 1: البنية الأساسية (أسبوع 1)
- [x] إنشاء جداول قاعدة البيانات
- [ ] إنشاء Models في Flask
- [ ] إنشاء Routes الأساسية

### المرحلة 2: الواجهة (أسبوع 2)
- [ ] صفحة إدارة الدوائر
- [ ] رسم الدوائر على الخريطة
- [ ] تحديث صفحة التتبع لعرض الدوائر

### المرحلة 3: المعالجة التلقائية (أسبوع 3)
- [ ] كشف الدخول/الخروج تلقائياً
- [ ] تسجيل الأحداث
- [ ] إرسال الإشعارات

### المرحلة 4: التحسينات (أسبوع 4)
- [ ] التقارير والإحصائيات
- [ ] التكامل مع نظام الحضور
- [ ] الإشعارات المتقدمة

---

## 💡 ملاحظات مهمة

### الأداء:
- استخدام حساب المسافة فقط للموظفين المرتبطين بالدائرة
- تخزين الأحداث في cache لتقليل الاستعلامات

### الخصوصية:
- التأكد من موافقة الموظف على التتبع
- حفظ البيانات بشكل آمن ومشفر
- إمكانية حذف البيانات القديمة

### الدقة:
- الأخذ بعين الاعتبار دقة GPS (accuracy)
- تجاهل المواقع ذات الدقة المنخفضة
- إضافة هامش خطأ للدوائر

---

## 📞 الأسئلة الشائعة

### س: كم دائرة يمكن إنشاؤها؟
ج: لا يوجد حد أقصى، لكن يُنصح بعدم تجاوز 50 دائرة نشطة لكل موظف للحفاظ على الأداء.

### س: هل يمكن تداخل الدوائر؟
ج: نعم، يمكن للموظف أن يكون داخل عدة دوائر في نفس الوقت.

### س: ماذا لو كان GPS غير دقيق؟
ج: يتم تجاهل المواقع ذات دقة أقل من 50 متر تلقائياً.

---

**تاريخ الإنشاء**: 07 نوفمبر 2025  
**الإصدار**: 1.0  
**الحالة**: مقترح - في انتظار الموافقة
