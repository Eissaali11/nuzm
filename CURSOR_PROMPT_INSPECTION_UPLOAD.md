# 🎯 Cursor AI Prompt: نظام رفع صور الفحص الدوري للسيارات

## 📋 المطلوب

إنشاء نظام كامل لرفع صور الفحص الدوري للسيارات من تطبيق Flutter مع صفحة مراجعة للمسؤول، مشابه تماماً لنظام `/external-safety/share-links` الموجود حالياً.

---

## 🗄️ قاعدة البيانات

### 1. إنشاء الجداول التالية:

```python
# في models.py

class InspectionUploadToken(db.Model):
    """رموز الرفع الفريدة لكل سيارة"""
    __tablename__ = 'inspection_upload_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    
    # معلومات الإنشاء
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # الحالة
    is_active = db.Column(db.Boolean, default=True)
    used_at = db.Column(db.DateTime)
    
    # العلاقات
    vehicle = db.relationship('Vehicle', backref='inspection_tokens')
    created_by_user = db.relationship('User', foreign_keys=[created_by])


class VehicleInspectionRecord(db.Model):
    """سجلات الفحص الدوري"""
    __tablename__ = 'vehicle_inspection_records'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    token_id = db.Column(db.Integer, db.ForeignKey('inspection_upload_tokens.id'))
    
    # بيانات الفحص
    inspection_date = db.Column(db.Date, nullable=False)
    inspection_type = db.Column(db.String(50), default='دوري')
    mileage = db.Column(db.Integer)
    notes = db.Column(db.Text)
    
    # معلومات الرفع
    uploaded_by_name = db.Column(db.String(200))
    uploaded_via = db.Column(db.String(50), default='mobile_app')
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # حالة المراجعة
    review_status = db.Column(db.String(50), default='pending')
    # القيم الممكنة: pending / approved / rejected / needs_review
    
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewed_at = db.Column(db.DateTime)
    reviewer_notes = db.Column(db.Text)
    
    # العلاقات
    vehicle = db.relationship('Vehicle', backref='inspection_records')
    token = db.relationship('InspectionUploadToken', backref='inspections')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    images = db.relationship('VehicleInspectionImage', backref='inspection', 
                            cascade='all, delete-orphan', lazy='dynamic')


class VehicleInspectionImage(db.Model):
    """صور الفحص"""
    __tablename__ = 'vehicle_inspection_images'
    
    id = db.Column(db.Integer, primary_key=True)
    inspection_record_id = db.Column(db.Integer, 
                                    db.ForeignKey('vehicle_inspection_records.id'), 
                                    nullable=False)
    
    image_path = db.Column(db.String(500), nullable=False)
    image_url = db.Column(db.String(500))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_size = db.Column(db.Integer)
    
    # Google Drive (اختياري)
    drive_file_id = db.Column(db.String(200))
    drive_upload_status = db.Column(db.String(50), default='pending')
```

---

## 🔗 API Endpoints المطلوبة

### 1. توليد رابط رفع جديد (للمسؤول)

```python
# في routes/api.py أو routes/vehicles.py

@vehicles_bp.route('/vehicles/<int:vehicle_id>/generate-inspection-link', methods=['POST'])
@login_required
def generate_inspection_link(vehicle_id):
    """
    توليد token ورابط رفع جديد
    
    Response:
    {
        "success": true,
        "upload_url": "http://nuzum.site/inspection-upload/{token}",
        "check_url": "http://nuzum.site/inspection-check/{future_id}",
        "token": "uuid-here",
        "expires_at": "2025-12-17"
    }
    """
    import uuid
    from datetime import timedelta
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    # توليد token فريد
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=30)
    
    # حفظ في قاعدة البيانات
    upload_token = InspectionUploadToken(
        vehicle_id=vehicle_id,
        token=token,
        created_by=current_user.id,
        expires_at=expires_at,
        is_active=True
    )
    db.session.add(upload_token)
    db.session.commit()
    
    # الروابط
    upload_url = f"http://nuzum.site/inspection-upload/{token}"
    
    return jsonify({
        'success': True,
        'upload_url': upload_url,
        'token': token,
        'expires_at': expires_at.strftime('%Y-%m-%d'),
        'vehicle': {
            'id': vehicle.id,
            'plate_number': vehicle.plate_number
        }
    })
```

### 2. صفحة/API رفع الصور (بدون تسجيل دخول)

```python
# إنشاء ملف جديد: routes/inspection_upload.py

from flask import Blueprint, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import uuid

inspection_bp = Blueprint('inspection', __name__)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'heic', 'heif'}
MAX_IMAGES = 30
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@inspection_bp.route('/inspection-upload/<token>', methods=['GET', 'POST'])
def upload_inspection(token):
    """
    GET: عرض صفحة رفع الصور
    POST: استقبال الصور وحفظها
    """
    # التحقق من Token
    upload_token = InspectionUploadToken.query.filter_by(
        token=token,
        is_active=True
    ).first()
    
    if not upload_token:
        return render_template('error.html', 
                             message='رابط غير صحيح أو منتهي الصلاحية'), 404
    
    # التحقق من الصلاحية
    if upload_token.expires_at < datetime.utcnow():
        return render_template('error.html', 
                             message='الرابط منتهي الصلاحية'), 403
    
    vehicle = upload_token.vehicle
    
    if request.method == 'GET':
        # عرض صفحة الرفع
        return render_template('inspection_upload.html', 
                             vehicle=vehicle,
                             token=token)
    
    # POST: حفظ الصور
    try:
        files = request.files.getlist('inspection_images')
        
        # التحقق من عدد الصور
        if len(files) == 0:
            return jsonify({'success': False, 'message': 'يرجى اختيار صور'}), 400
        
        if len(files) > MAX_IMAGES:
            return jsonify({'success': False, 
                          'message': f'الحد الأقصى {MAX_IMAGES} صورة'}), 400
        
        # البيانات
        inspection_date = request.form.get('inspection_date')
        mileage = request.form.get('mileage')
        notes = request.form.get('notes')
        
        if not inspection_date:
            return jsonify({'success': False, 
                          'message': 'تاريخ الفحص مطلوب'}), 400
        
        # إنشاء سجل جديد
        inspection = VehicleInspectionRecord(
            vehicle_id=vehicle.id,
            token_id=upload_token.id,
            inspection_date=datetime.strptime(inspection_date, '%Y-%m-%d').date(),
            mileage=int(mileage) if mileage else None,
            notes=notes,
            uploaded_by_name=vehicle.driver_name or 'غير محدد',
            review_status='pending'
        )
        db.session.add(inspection)
        db.session.flush()
        
        # مجلد الحفظ
        upload_folder = f"static/uploads/inspections/{vehicle.id}"
        os.makedirs(upload_folder, exist_ok=True)
        
        # حفظ الصور
        saved_count = 0
        for file in files:
            if file and allowed_file(file.filename):
                # اسم ملف فريد
                ext = file.filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4()}.{ext}"
                filepath = os.path.join(upload_folder, unique_filename)
                
                # حفظ الملف
                file.save(filepath)
                
                # معلومات الصورة
                file_size = os.path.getsize(filepath)
                image_url = f"http://nuzum.site/{filepath}"
                
                # حفظ في قاعدة البيانات
                image = VehicleInspectionImage(
                    inspection_record_id=inspection.id,
                    image_path=filepath,
                    image_url=image_url,
                    file_size=file_size
                )
                db.session.add(image)
                saved_count += 1
        
        # تحديث Token
        upload_token.used_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'تم رفع {saved_count} صورة بنجاح',
            'inspection_id': inspection.id,
            'images_count': saved_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
```

### 3. API للتحقق من حالة الطلب (للفلاتر)

```python
# في routes/api.py

@api_bp.route('/api/inspection-status/<token>')
def get_inspection_status(token):
    """
    التحقق من حالة الفحص بواسطة token
    
    Response:
    {
        "success": true,
        "inspection": {
            "id": 123,
            "vehicle_plate": "3189-ب س ن",
            "inspection_date": "2025-11-17",
            "uploaded_at": "2025-11-17 14:30:00",
            "images_count": 15,
            "status": "pending",
            "status_arabic": "في الانتظار",
            "approved_at": null,
            "rejected_at": null,
            "rejection_reason": null,
            "reviewer_notes": null
        }
    }
    """
    # البحث عن Token
    upload_token = InspectionUploadToken.query.filter_by(token=token).first()
    
    if not upload_token:
        return jsonify({'success': False, 'message': 'رابط غير صحيح'}), 404
    
    # البحث عن آخر سجل فحص
    inspection = VehicleInspectionRecord.query.filter_by(
        token_id=upload_token.id
    ).order_by(VehicleInspectionRecord.uploaded_at.desc()).first()
    
    if not inspection:
        return jsonify({'success': False, 'message': 'لم يتم رفع صور بعد'}), 404
    
    # ترجمة الحالة
    status_translations = {
        'pending': 'في الانتظار',
        'approved': 'تم الموافقة',
        'rejected': 'مرفوض',
        'needs_review': 'يحتاج مراجعة'
    }
    
    return jsonify({
        'success': True,
        'inspection': {
            'id': inspection.id,
            'vehicle_plate': inspection.vehicle.plate_number,
            'inspection_date': inspection.inspection_date.strftime('%Y-%m-%d'),
            'uploaded_at': inspection.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
            'images_count': inspection.images.count(),
            'status': inspection.review_status,
            'status_arabic': status_translations.get(inspection.review_status, 'غير محدد'),
            'approved_at': inspection.reviewed_at.strftime('%Y-%m-%d %H:%M:%S') if inspection.reviewed_at and inspection.review_status == 'approved' else None,
            'approved_by': inspection.reviewer.username if inspection.reviewer and inspection.review_status == 'approved' else None,
            'rejected_at': inspection.reviewed_at.strftime('%Y-%m-%d %H:%M:%S') if inspection.reviewed_at and inspection.review_status == 'rejected' else None,
            'rejection_reason': inspection.reviewer_notes if inspection.review_status == 'rejected' else None,
            'reviewer_notes': inspection.reviewer_notes if inspection.review_status not in ['rejected'] else None
        }
    })
```

### 4. صفحة التحقق للمسؤول

```python
# في routes/vehicles.py

@vehicles_bp.route('/inspection-check/<int:inspection_id>')
@login_required
def inspection_check(inspection_id):
    """صفحة مراجعة الفحص (مثل external-safety-check)"""
    inspection = VehicleInspectionRecord.query.get_or_404(inspection_id)
    
    # التحقق من الصلاحيات (اختياري)
    # if not current_user.has_permission('review_inspections'):
    #     abort(403)
    
    return render_template('inspection_check.html', 
                          inspection=inspection,
                          vehicle=inspection.vehicle,
                          images=inspection.images.all())
```

### 5. حفظ قرار المسؤول

```python
# في routes/vehicles.py

@vehicles_bp.route('/inspection-check/<int:inspection_id>/review', methods=['POST'])
@login_required
def save_inspection_review(inspection_id):
    """حفظ قرار الموافقة/الرفض"""
    inspection = VehicleInspectionRecord.query.get_or_404(inspection_id)
    
    decision = request.form.get('decision')  # approved / rejected / needs_review
    reviewer_notes = request.form.get('reviewer_notes')
    new_expiry_date = request.form.get('new_expiry_date')
    
    if decision not in ['approved', 'rejected', 'needs_review']:
        flash('قرار غير صحيح', 'error')
        return redirect(url_for('vehicles.inspection_check', inspection_id=inspection_id))
    
    # تحديث السجل
    inspection.review_status = decision
    inspection.reviewed_by = current_user.id
    inspection.reviewed_at = datetime.utcnow()
    inspection.reviewer_notes = reviewer_notes
    
    # إذا كان موافق، تحديث تاريخ انتهاء الفحص
    if decision == 'approved' and new_expiry_date:
        inspection.vehicle.inspection_expiry_date = datetime.strptime(
            new_expiry_date, '%Y-%m-%d'
        ).date()
    
    db.session.commit()
    
    flash('تم حفظ القرار بنجاح', 'success')
    return redirect(url_for('vehicles.vehicle_inspections', 
                           vehicle_id=inspection.vehicle_id))
```

### 6. عرض سجلات الفحص للسيارة

```python
# في routes/vehicles.py

@vehicles_bp.route('/vehicles/<int:vehicle_id>/inspections')
@login_required
def vehicle_inspections(vehicle_id):
    """عرض جميع سجلات الفحص للسيارة"""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    inspections = VehicleInspectionRecord.query.filter_by(
        vehicle_id=vehicle_id
    ).order_by(VehicleInspectionRecord.uploaded_at.desc()).all()
    
    return render_template('vehicle_inspections.html', 
                          vehicle=vehicle,
                          inspections=inspections)
```

---

## 📄 Templates المطلوبة

### 1. صفحة رفع الصور (inspection_upload.html)

```html
{% extends "base.html" %}

{% block content %}
<div class="container mt-5" dir="rtl">
    <div class="card shadow">
        <div class="card-header bg-primary text-white text-center">
            <h2>📸 رفع صور الفحص الدوري</h2>
        </div>
        
        <div class="card-body">
            <!-- معلومات السيارة -->
            <div class="alert alert-info">
                <h4>🚗 معلومات السيارة</h4>
                <p class="mb-1"><strong>رقم اللوحة:</strong> {{ vehicle.plate_number }}</p>
                <p class="mb-0"><strong>الموديل:</strong> {{ vehicle.make }} {{ vehicle.model }} ({{ vehicle.year }})</p>
            </div>
            
            <!-- نموذج الرفع -->
            <form id="uploadForm" method="POST" enctype="multipart/form-data">
                <!-- تاريخ الفحص -->
                <div class="mb-3">
                    <label class="form-label">📅 تاريخ الفحص الدوري *</label>
                    <input type="date" name="inspection_date" class="form-control" required>
                </div>
                
                <!-- القراءة -->
                <div class="mb-3">
                    <label class="form-label">📏 قراءة العداد (كم)</label>
                    <input type="number" name="mileage" class="form-control" 
                           placeholder="مثال: 150000">
                </div>
                
                <!-- الصور -->
                <div class="mb-3">
                    <label class="form-label">📸 صور الفحص (حتى 30 صورة) *</label>
                    <input type="file" name="inspection_images" class="form-control" 
                           accept="image/*" multiple required id="imageInput">
                    <div class="form-text">
                        الصيغ المدعومة: JPG, PNG, HEIC | الحد الأقصى: 30 صورة
                    </div>
                    <div id="imagePreview" class="row mt-3"></div>
                </div>
                
                <!-- الملاحظات -->
                <div class="mb-3">
                    <label class="form-label">📝 ملاحظات (اختياري)</label>
                    <textarea name="notes" class="form-control" rows="3" 
                              placeholder="أي ملاحظات إضافية"></textarea>
                </div>
                
                <!-- زر الرفع -->
                <button type="submit" class="btn btn-primary btn-lg w-100" id="submitBtn">
                    <i class="fas fa-upload"></i> رفع الصور
                </button>
                
                <!-- Progress Bar -->
                <div class="progress mt-3 d-none" id="progressContainer">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" 
                         role="progressbar" style="width: 0%" id="progressBar">0%</div>
                </div>
            </form>
        </div>
    </div>
</div>

<script>
// معاينة الصور
document.getElementById('imageInput').addEventListener('change', function(e) {
    const files = e.target.files;
    const preview = document.getElementById('imagePreview');
    preview.innerHTML = '';
    
    if (files.length > 30) {
        alert('الحد الأقصى 30 صورة');
        this.value = '';
        return;
    }
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const reader = new FileReader();
        
        reader.onload = function(e) {
            const col = document.createElement('div');
            col.className = 'col-md-2 col-4 mb-2';
            col.innerHTML = `
                <img src="${e.target.result}" class="img-fluid rounded" 
                     style="height: 100px; object-fit: cover;">
                <small class="d-block text-center">${i + 1}</small>
            `;
            preview.appendChild(col);
        };
        
        reader.readAsDataURL(file);
    }
});

// رفع النموذج
document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const submitBtn = document.getElementById('submitBtn');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    
    // تعطيل الزر
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جاري الرفع...';
    
    // عرض Progress Bar
    progressContainer.classList.remove('d-none');
    
    const formData = new FormData(this);
    
    try {
        const response = await fetch(window.location.href, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            // نجح الرفع
            progressBar.style.width = '100%';
            progressBar.textContent = '100%';
            
            // عرض رسالة نجاح
            alert('✅ ' + result.message);
            
            // إعادة التوجيه لصفحة النجاح أو الحالة
            window.location.href = '/inspection-success?id=' + result.inspection_id;
        } else {
            alert('❌ ' + result.message);
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-upload"></i> رفع الصور';
            progressContainer.classList.add('d-none');
        }
    } catch (error) {
        alert('حدث خطأ: ' + error.message);
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-upload"></i> رفع الصور';
        progressContainer.classList.add('d-none');
    }
});
</script>
{% endblock %}
```

### 2. صفحة التحقق للمسؤول (inspection_check.html)

```html
{% extends "base.html" %}

{% block content %}
<div class="container mt-4" dir="rtl">
    <div class="card shadow-lg">
        <div class="card-header bg-gradient text-white" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <h3 class="mb-0">
                <i class="fas fa-clipboard-check"></i>
                مراجعة فحص السيارة - {{ vehicle.plate_number }}
            </h3>
        </div>
        
        <div class="card-body">
            <!-- معلومات الفحص -->
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="info-box">
                        <p><strong>📅 تاريخ الفحص:</strong> {{ inspection.inspection_date }}</p>
                        <p><strong>📏 القراءة:</strong> {{ inspection.mileage or 'غير محدد' }} كم</p>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="info-box">
                        <p><strong>👤 رفعت بواسطة:</strong> {{ inspection.uploaded_by_name }}</p>
                        <p><strong>🕐 وقت الرفع:</strong> {{ inspection.uploaded_at.strftime('%Y-%m-%d %H:%M') }}</p>
                    </div>
                </div>
            </div>
            
            <!-- الحالة الحالية -->
            {% if inspection.review_status != 'pending' %}
            <div class="alert {% if inspection.review_status == 'approved' %}alert-success{% elif inspection.review_status == 'rejected' %}alert-danger{% else %}alert-warning{% endif %}">
                <h5>📊 الحالة الحالية: 
                    {% if inspection.review_status == 'approved' %}✅ موافق
                    {% elif inspection.review_status == 'rejected' %}❌ مرفوض
                    {% else %}⚠️ يحتاج مراجعة
                    {% endif %}
                </h5>
                <p class="mb-0"><strong>تم المراجعة:</strong> {{ inspection.reviewed_at.strftime('%Y-%m-%d %H:%M') }}</p>
            </div>
            {% endif %}
            
            <!-- الملاحظات -->
            {% if inspection.notes %}
            <div class="alert alert-info">
                <strong>📝 ملاحظات السائق:</strong> {{ inspection.notes }}
            </div>
            {% endif %}
            
            <!-- الصور -->
            <h4 class="mb-3">
                <i class="fas fa-images"></i>
                الصور المرفوعة ({{ images|length }})
            </h4>
            
            <div class="row">
                {% for image in images %}
                <div class="col-md-3 col-6 mb-3">
                    <a href="{{ image.image_url }}" data-lightbox="inspection-{{ inspection.id }}" 
                       data-title="صورة {{ loop.index }}">
                        <img src="{{ image.image_url }}" class="img-fluid rounded shadow-sm hover-zoom" 
                             style="height: 200px; width: 100%; object-fit: cover;">
                    </a>
                    <small class="d-block text-center mt-1">صورة {{ loop.index }}</small>
                </div>
                {% endfor %}
            </div>
            
            <hr class="my-4">
            
            <!-- نموذج القرار -->
            <form method="POST" action="{{ url_for('vehicles.save_inspection_review', inspection_id=inspection.id) }}">
                <h4 class="mb-3">
                    <i class="fas fa-gavel"></i>
                    قرار المسؤول
                </h4>
                
                <div class="row">
                    <div class="col-md-4">
                        <div class="form-check p-3 border rounded mb-2 hover-highlight">
                            <input type="radio" name="decision" value="approved" 
                                   class="form-check-input" id="approved" required>
                            <label class="form-check-label w-100" for="approved">
                                <i class="fas fa-check-circle text-success"></i>
                                <strong>موافق - الفحص صحيح</strong>
                            </label>
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <div class="form-check p-3 border rounded mb-2 hover-highlight">
                            <input type="radio" name="decision" value="rejected" 
                                   class="form-check-input" id="rejected" required>
                            <label class="form-check-label w-100" for="rejected">
                                <i class="fas fa-times-circle text-danger"></i>
                                <strong>مرفوض - يحتاج إعادة فحص</strong>
                            </label>
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <div class="form-check p-3 border rounded mb-2 hover-highlight">
                            <input type="radio" name="decision" value="needs_review" 
                                   class="form-check-input" id="needs_review" required>
                            <label class="form-check-label w-100" for="needs_review">
                                <i class="fas fa-exclamation-circle text-warning"></i>
                                <strong>يحتاج مراجعة - صور غير واضحة</strong>
                            </label>
                        </div>
                    </div>
                </div>
                
                <!-- تاريخ انتهاء الفحص الجديد -->
                <div class="mb-3 mt-3" id="expiryDateField" style="display: none;">
                    <label class="form-label">
                        <i class="fas fa-calendar-alt"></i>
                        تاريخ انتهاء الفحص الجديد (عند الموافقة):
                    </label>
                    <input type="date" name="new_expiry_date" class="form-control">
                </div>
                
                <!-- ملاحظات المسؤول -->
                <div class="mb-3">
                    <label class="form-label">
                        <i class="fas fa-comment-dots"></i>
                        ملاحظات المسؤول:
                    </label>
                    <textarea name="reviewer_notes" class="form-control" rows="3" 
                              placeholder="أضف ملاحظاتك هنا..."></textarea>
                    <div class="form-text">
                        في حالة الرفض، اشرح السبب بوضوح لكي يتم رفع صور جديدة بشكل صحيح
                    </div>
                </div>
                
                <!-- أزرار الإجراءات -->
                <div class="d-grid gap-2">
                    <button type="submit" class="btn btn-primary btn-lg">
                        <i class="fas fa-save"></i>
                        حفظ القرار
                    </button>
                    <a href="{{ url_for('vehicles.vehicle_inspections', vehicle_id=vehicle.id) }}" 
                       class="btn btn-secondary">
                        <i class="fas fa-arrow-right"></i>
                        رجوع لقائمة الفحوصات
                    </a>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- Lightbox CSS & JS -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/lightbox2/2.11.3/css/lightbox.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/lightbox2/2.11.3/js/lightbox.min.js"></script>

<script>
// إظهار حقل تاريخ الانتهاء عند اختيار "موافق"
document.querySelectorAll('input[name="decision"]').forEach(radio => {
    radio.addEventListener('change', function() {
        const expiryField = document.getElementById('expiryDateField');
        if (this.value === 'approved') {
            expiryField.style.display = 'block';
        } else {
            expiryField.style.display = 'none';
        }
    });
});

// Hover effect
const hoverElements = document.querySelectorAll('.hover-highlight');
hoverElements.forEach(el => {
    el.addEventListener('mouseenter', function() {
        this.style.backgroundColor = '#f8f9fa';
    });
    el.addEventListener('mouseleave', function() {
        this.style.backgroundColor = '';
    });
});
</script>

<style>
.hover-zoom {
    transition: transform 0.3s ease;
    cursor: pointer;
}
.hover-zoom:hover {
    transform: scale(1.05);
}
.info-box p {
    margin-bottom: 8px;
}
</style>
{% endblock %}
```

### 3. قائمة الفحوصات (vehicle_inspections.html)

```html
{% extends "base.html" %}

{% block content %}
<div class="container mt-4" dir="rtl">
    <div class="card">
        <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
            <h3 class="mb-0">
                <i class="fas fa-list"></i>
                سجل الفحوصات - {{ vehicle.plate_number }}
            </h3>
            <button class="btn btn-light" onclick="generateLink()">
                <i class="fas fa-plus"></i>
                إنشاء رابط رفع جديد
            </button>
        </div>
        
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>التاريخ</th>
                            <th>القراءة</th>
                            <th>عدد الصور</th>
                            <th>الحالة</th>
                            <th>المراجع</th>
                            <th>الإجراءات</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for inspection in inspections %}
                        <tr>
                            <td>{{ inspection.inspection_date }}</td>
                            <td>{{ inspection.mileage or '-' }} كم</td>
                            <td>{{ inspection.images.count() }} صورة</td>
                            <td>
                                {% if inspection.review_status == 'pending' %}
                                <span class="badge bg-warning">⏳ في الانتظار</span>
                                {% elif inspection.review_status == 'approved' %}
                                <span class="badge bg-success">✅ موافق</span>
                                {% elif inspection.review_status == 'rejected' %}
                                <span class="badge bg-danger">❌ مرفوض</span>
                                {% else %}
                                <span class="badge bg-info">⚠️ يحتاج مراجعة</span>
                                {% endif %}
                            </td>
                            <td>
                                {{ inspection.reviewer.username if inspection.reviewer else '-' }}
                            </td>
                            <td>
                                <a href="{{ url_for('vehicles.inspection_check', inspection_id=inspection.id) }}" 
                                   class="btn btn-sm btn-info">
                                    <i class="fas fa-eye"></i> عرض
                                </a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<script>
async function generateLink() {
    if (!confirm('هل تريد إنشاء رابط رفع جديد؟')) return;
    
    try {
        const response = await fetch('/vehicles/{{ vehicle.id }}/generate-inspection-link', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            prompt('رابط الرفع (انسخه وأرسله للسائق):', result.upload_url);
        } else {
            alert('فشل إنشاء الرابط');
        }
    } catch (error) {
        alert('حدث خطأ: ' + error.message);
    }
}
</script>
{% endblock %}
```

---

## 🔗 التسجيل في app.py

```python
# في app.py أو main.py

from routes.inspection_upload import inspection_bp

app.register_blueprint(inspection_bp)
```

---

## ✅ متطلبات إضافية

1. **إنشاء مجلد الصور:**
```bash
mkdir -p static/uploads/inspections
```

2. **إضافة دالة مساعدة في routes/api.py:**
```python
def get_full_url(path):
    """إرجاع رابط كامل"""
    if not path:
        return None
    if path.startswith('http'):
        return path
    return f"http://nuzum.site/{path}"
```

3. **CSS إضافي (في static/css/):**
```css
.hover-highlight:hover {
    background-color: #f8f9fa;
    cursor: pointer;
}
```

---

## 🎯 ملخص الخطوات

1. ✅ إنشاء الجداول الثلاثة في `models.py`
2. ✅ إنشاء ملف `routes/inspection_upload.py`
3. ✅ إضافة routes في `routes/vehicles.py` و `routes/api.py`
4. ✅ إنشاء templates الثلاثة
5. ✅ تسجيل blueprint في `app.py`
6. ✅ اختبار النظام بالكامل

---

**ملاحظات:**
- استخدم نفس أسلوب `/external-safety/share-links` الموجود
- تأكد من الروابط تستخدم `http://nuzum.site` وليس localhost
- الحد الأقصى 30 صورة لكل رفع
- إشعارات تلقائية في Flutter عند الموافقة/الرفض
