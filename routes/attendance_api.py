"""
API endpoints للحضور مع التحقق من الوجه والموقع
Attendance API with Face Recognition and Location Verification
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, date, time, timezone, timedelta
from sqlalchemy import func, and_, or_
from decimal import Decimal
from functools import wraps
import json
import os
import jwt
import hashlib
import logging
from math import radians, sin, cos, sqrt, atan2

from app import db
from models import Employee, Attendance, EmployeeLocation, Geofence, GeofenceSession

logger = logging.getLogger(__name__)

# إنشاء Blueprint
attendance_api_bp = Blueprint('attendance_api', __name__, url_prefix='/api/v1/attendance')

# إعدادات الأمان
SECRET_KEY = os.environ.get('SESSION_SECRET')
if not SECRET_KEY:
    raise RuntimeError("SESSION_SECRET environment variable is required for JWT authentication")

# إعدادات Geofencing
GEOFENCE_REQUIRED = True  # إلزامية التحقق من الموقع
MIN_GPS_ACCURACY = 100  # الحد الأدنى للدقة بالأمتار
MAX_GPS_ACCURACY = 500  # الحد الأقصى للدقة بالأمتار

# إعدادات التحقق البيومتري
MIN_CONFIDENCE_SCORE = 0.75  # الحد الأدنى لدرجة الثقة
MIN_LIVENESS_SCORE = 0.70  # الحد الأدنى لدرجة الحياة

# Rate Limiting (بسيط - يمكن تحسينه باستخدام Redis)
check_in_attempts = {}  # {employee_id: [(timestamp, success), ...]}
MAX_ATTEMPTS_PER_HOUR = 5

# ============================================
# Security & Authentication
# ============================================

def token_required(f):
    """Decorator للتحقق من JWT Token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({
                    'success': False,
                    'error': 'صيغة التوكن غير صحيحة',
                    'code': 'INVALID_TOKEN_FORMAT'
                }), 401
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'التوكن مفقود - يجب تسجيل الدخول',
                'code': 'MISSING_TOKEN'
            }), 401
        
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_employee = Employee.query.filter_by(
                employee_id=data['employee_id'],
                status='active'
            ).first()
            
            if not current_employee:
                return jsonify({
                    'success': False,
                    'error': 'الموظف غير موجود أو غير نشط',
                    'code': 'EMPLOYEE_NOT_FOUND'
                }), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'error': 'التوكن منتهي الصلاحية - يجب تسجيل الدخول مرة أخرى',
                'code': 'TOKEN_EXPIRED'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'error': 'التوكن غير صالح',
                'code': 'INVALID_TOKEN'
            }), 401
        
        return f(current_employee, *args, **kwargs)
    
    return decorated


def check_rate_limit(employee_id):
    """التحقق من rate limiting"""
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)
    
    # تنظيف المحاولات القديمة
    if employee_id in check_in_attempts:
        check_in_attempts[employee_id] = [
            (ts, success) for ts, success in check_in_attempts[employee_id]
            if ts > one_hour_ago
        ]
    else:
        check_in_attempts[employee_id] = []
    
    # التحقق من عدد المحاولات
    recent_attempts = len(check_in_attempts[employee_id])
    
    if recent_attempts >= MAX_ATTEMPTS_PER_HOUR:
        return False, f"تم تجاوز الحد الأقصى للمحاولات ({MAX_ATTEMPTS_PER_HOUR} محاولات في الساعة)"
    
    return True, None


def record_attempt(employee_id, success=True):
    """تسجيل محاولة حضور"""
    now = datetime.now(timezone.utc)
    if employee_id not in check_in_attempts:
        check_in_attempts[employee_id] = []
    check_in_attempts[employee_id].append((now, success))


def validate_gps_data(latitude, longitude, accuracy):
    """التحقق من صحة بيانات GPS"""
    try:
        lat = float(latitude)
        lon = float(longitude)
        acc = float(accuracy)
        
        # التحقق من النطاقات
        if not (-90 <= lat <= 90):
            return False, "خط العرض غير صحيح"
        if not (-180 <= lon <= 180):
            return False, "خط الطول غير صحيح"
        if acc < 0 or acc > MAX_GPS_ACCURACY:
            return False, f"دقة الموقع غير مقبولة (يجب أن تكون أقل من {MAX_GPS_ACCURACY}م)"
        
        return True, None
        
    except (ValueError, TypeError):
        return False, "بيانات الموقع غير صحيحة"


def validate_biometric_scores(confidence, liveness_score, require_biometric=False):
    """
    التحقق من درجات التحقق البيومتري
    
    Args:
        confidence: درجة الثقة (0-1)
        liveness_score: درجة الحياة (0-1)
        require_biometric: إلزامية التحقق البيومتري
    
    Returns:
        (valid: bool, error_msg: str|None)
    """
    errors = []
    
    # معالجة confidence
    if confidence is not None and str(confidence).strip() != '':
        try:
            conf = float(confidence)
            if conf <= 0:
                errors.append("مستوى الثقة يجب أن يكون أكبر من 0")
            elif conf < MIN_CONFIDENCE_SCORE:
                errors.append(f"مستوى الثقة منخفض جداً ({conf:.2f} < {MIN_CONFIDENCE_SCORE})")
            elif conf > 1.0:
                errors.append("مستوى الثقة غير صحيح (أكبر من 1.0)")
        except (ValueError, TypeError):
            errors.append("مستوى الثقة غير صحيح - يجب أن يكون رقم بين 0 و 1")
    elif require_biometric:
        errors.append("مستوى الثقة مطلوب")
    
    # معالجة liveness_score
    if liveness_score is not None and str(liveness_score).strip() != '':
        try:
            liveness = float(liveness_score)
            if liveness <= 0:
                errors.append("درجة الحياة يجب أن تكون أكبر من 0")
            elif liveness < MIN_LIVENESS_SCORE:
                errors.append(f"فحص الحياة فشل ({liveness:.2f} < {MIN_LIVENESS_SCORE})")
            elif liveness > 1.0:
                errors.append("درجة الحياة غير صحيحة (أكبر من 1.0)")
        except (ValueError, TypeError):
            errors.append("درجة الحياة غير صحيحة - يجب أن تكون رقم بين 0 و 1")
    elif require_biometric:
        errors.append("درجة الحياة مطلوبة")
    
    if errors:
        return False, " | ".join(errors)
    return True, None


# ============================================
# Helper Functions
# ============================================

def calculate_distance(lat1, lon1, lat2, lon2):
    """حساب المسافة بين نقطتين باستخدام Haversine formula"""
    try:
        R = 6371000  # نصف قطر الأرض بالأمتار
        
        lat1_rad = radians(float(lat1))
        lat2_rad = radians(float(lat2))
        delta_lat = radians(float(lat2) - float(lat1))
        delta_lon = radians(float(lon2) - float(lon1))
        
        a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    except Exception as e:
        logger.error(f"Error calculating distance: {e}")
        return None


def verify_geofence(employee, latitude, longitude, strict=True):
    """
    التحقق من أن الموظف داخل منطقة العمل
    
    Args:
        employee: كائن الموظف
        latitude: خط العرض
        longitude: خط الطول
        strict: إذا كان True، يُطلب وجود geofence محدد
    
    Returns:
        (success: bool, geofence: Geofence|None, message: str)
    """
    try:
        # البحث عن geofences المرتبطة بالموظف أو القسم
        geofences = Geofence.query.filter(
            or_(
                Geofence.employees.contains(employee),
                Geofence.department_id == employee.department_id
            ),
            Geofence.is_active == True
        ).all()
        
        if not geofences:
            if GEOFENCE_REQUIRED or strict:
                # إلزامية وجود geofence
                return False, None, "لم يتم تعيين منطقة عمل لهذا الموظف - اتصل بالإدارة"
            else:
                # السماح بدون geofence (للتطوير فقط)
                logger.warning(f"No geofence assigned for employee {employee.employee_id}")
                return True, None, "⚠️ لا توجد منطقة محددة (تحذير)"
        
        # التحقق من وجود الموظف داخل أي geofence
        closest_distance = None
        closest_geofence = None
        
        for geofence in geofences:
            distance = calculate_distance(
                float(geofence.latitude),
                float(geofence.longitude),
                float(latitude),
                float(longitude)
            )
            
            if distance is None:
                continue
                
            # حفظ أقرب منطقة
            if closest_distance is None or distance < closest_distance:
                closest_distance = distance
                closest_geofence = geofence
            
            # التحقق من الدخول
            if distance <= float(geofence.radius):
                logger.info(f"✓ Employee {employee.employee_id} inside geofence '{geofence.name}' (distance: {distance:.1f}m)")
                return True, geofence, f"✓ داخل منطقة {geofence.name}"
        
        # الموظف خارج جميع المناطق
        if closest_geofence and closest_distance:
            logger.warning(
                f"✗ Employee {employee.employee_id} outside geofence. "
                f"Closest: '{closest_geofence.name}' at {closest_distance:.1f}m "
                f"(max: {closest_geofence.radius}m)"
            )
            return False, closest_geofence, (
                f"✗ خارج منطقة العمل - أنت على بُعد {closest_distance:.0f}م من '{closest_geofence.name}' "
                f"(المسموح: {closest_geofence.radius}م)"
            )
        else:
            return False, None, "✗ خارج جميع مناطق العمل المحددة"
        
    except Exception as e:
        logger.error(f"Error verifying geofence for {employee.employee_id}: {e}")
        return False, None, f"خطأ في التحقق من الموقع: {str(e)}"


def save_face_image(face_image, employee_id, check_type='check_in'):
    """حفظ صورة الوجه"""
    try:
        if not face_image:
            return None
        
        # إنشاء مجلد التخزين
        upload_folder = 'static/uploads/attendance'
        os.makedirs(upload_folder, exist_ok=True)
        
        # توليد اسم فريد للملف
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{check_type}_{employee_id}_{timestamp}.jpg'
        filepath = os.path.join(upload_folder, filename)
        
        # حفظ الصورة
        face_image.save(filepath)
        
        # إرجاع المسار النسبي
        return f'uploads/attendance/{filename}'
        
    except Exception as e:
        logger.error(f"Error saving face image: {e}")
        return None


# ============================================
# API Endpoints
# ============================================

@attendance_api_bp.route('/check-in', methods=['POST'])
@token_required
def attendance_check_in(current_employee):
    """
    تسجيل الحضور مع التحقق من الوجه والموقع (محمي بـ JWT)
    
    Headers:
    - Authorization: Bearer <JWT_TOKEN>
    
    Request (multipart/form-data):
    - latitude: خط العرض (مطلوب)
    - longitude: خط الطول (مطلوب)
    - accuracy: دقة الموقع بالأمتار (مطلوب)
    - confidence: مستوى الثقة في التعرف (0-1، اختياري)
    - liveness_score: درجة الحياة (0-1، اختياري)
    - device_fingerprint: JSON معلومات الجهاز (اختياري)
    - timestamp: وقت التحضير ISO 8601 (اختياري)
    - face_image: صورة الوجه (اختياري)
    
    Response:
    - success: true/false
    - message: رسالة النتيجة
    - data: بيانات الحضور
    """
    try:
        # 1. التحقق من Rate Limiting
        can_proceed, rate_limit_msg = check_rate_limit(current_employee.employee_id)
        if not can_proceed:
            record_attempt(current_employee.employee_id, success=False)
            return jsonify({
                'success': False,
                'error': rate_limit_msg,
                'code': 'RATE_LIMIT_EXCEEDED'
            }), 429
        
        # 2. استقبال و التحقق من بيانات الموقع
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        accuracy = request.form.get('accuracy')
        
        if not all([latitude, longitude, accuracy]):
            return jsonify({
                'success': False,
                'error': 'بيانات الموقع مطلوبة (latitude, longitude, accuracy)',
                'code': 'MISSING_LOCATION_DATA'
            }), 400
        
        # التحقق من صحة بيانات GPS
        gps_valid, gps_error = validate_gps_data(latitude, longitude, accuracy)
        if not gps_valid:
            record_attempt(current_employee.employee_id, success=False)
            return jsonify({
                'success': False,
                'error': gps_error,
                'code': 'INVALID_GPS_DATA'
            }), 400
        
        latitude = float(latitude)
        longitude = float(longitude)
        accuracy = float(accuracy)
        
        # 3. استقبال بيانات التحقق البيومتري (اختياري)
        confidence_raw = request.form.get('confidence', '')
        liveness_score_raw = request.form.get('liveness_score', '')
        
        # التحقق من صحة البيانات البيومترية
        biometric_valid, biometric_error = validate_biometric_scores(confidence_raw, liveness_score_raw)
        if not biometric_valid:
            record_attempt(current_employee.employee_id, success=False)
            return jsonify({
                'success': False,
                'error': biometric_error,
                'code': 'BIOMETRIC_VALIDATION_FAILED'
            }), 400
        
        # تحويل إلى أرقام بعد التحقق
        try:
            confidence = float(confidence_raw) if confidence_raw and str(confidence_raw).strip() else None
            liveness_score = float(liveness_score_raw) if liveness_score_raw and str(liveness_score_raw).strip() else None
        except (ValueError, TypeError):
            confidence = None
            liveness_score = None
        
        try:
            device_fingerprint = json.loads(request.form.get('device_fingerprint', '{}'))
        except json.JSONDecodeError:
            device_fingerprint = {}
        
        # 4. استقبال الصورة
        face_image = request.files.get('face_image')
        
        # 5. التحقق من التاريخ
        timestamp_str = request.form.get('timestamp')
        try:
            check_in_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            check_in_timestamp = datetime.now(timezone.utc)
        
        # 6. التحقق من الموقع (Geofencing) - MANDATORY
        geofence_ok, geofence, geofence_msg = verify_geofence(current_employee, latitude, longitude, strict=True)
        
        if not geofence_ok:
            record_attempt(current_employee.employee_id, success=False)
            logger.warning(f"Geofence check failed for {current_employee.employee_id}: {geofence_msg}")
            return jsonify({
                'success': False,
                'error': geofence_msg,
                'code': 'GEOFENCE_VIOLATION',
                'details': {
                    'your_location': {'lat': latitude, 'lon': longitude},
                    'geofence': geofence.name if geofence else None
                }
            }), 403
        
        # 7. التحقق من عدم التحضير المتكرر
        today = date.today()
        existing_attendance = Attendance.query.filter(
            Attendance.employee_id == current_employee.id,
            Attendance.date == today
        ).first()
        
        if existing_attendance and existing_attendance.check_in:
            return jsonify({
                'success': False,
                'error': 'تم تسجيل الحضور مسبقاً اليوم',
                'code': 'ALREADY_CHECKED_IN',
                'data': {
                    'check_in_time': existing_attendance.check_in.strftime('%H:%M:%S'),
                    'date': today.strftime('%Y-%m-%d')
                }
            }), 400
        
        # 8. حفظ صورة الوجه
        face_image_path = save_face_image(face_image, current_employee.employee_id, 'check_in')
        
        # 9. إنشاء أو تحديث سجل الحضور
        verification_id = f'ver_{int(datetime.now().timestamp() * 1000)}'
        check_in_time = check_in_timestamp.time()
        
        if existing_attendance:
            # تحديث السجل الموجود
            existing_attendance.check_in = check_in_time
            existing_attendance.status = 'present'
            existing_attendance.check_in_latitude = Decimal(str(latitude))
            existing_attendance.check_in_longitude = Decimal(str(longitude))
            existing_attendance.check_in_accuracy = Decimal(str(accuracy))
            existing_attendance.check_in_face_image = face_image_path
            existing_attendance.check_in_confidence = Decimal(str(confidence)) if confidence else None
            existing_attendance.check_in_liveness_score = Decimal(str(liveness_score)) if liveness_score else None
            existing_attendance.check_in_device_info = device_fingerprint
            existing_attendance.check_in_verification_id = verification_id
            attendance_record = existing_attendance
        else:
            # إنشاء سجل جديد
            attendance_record = Attendance(
                employee_id=current_employee.id,
                date=today,
                check_in=check_in_time,
                status='present',
                check_in_latitude=Decimal(str(latitude)),
                check_in_longitude=Decimal(str(longitude)),
                check_in_accuracy=Decimal(str(accuracy)),
                check_in_face_image=face_image_path,
                check_in_confidence=Decimal(str(confidence)) if confidence else None,
                check_in_liveness_score=Decimal(str(liveness_score)) if liveness_score else None,
                check_in_device_info=device_fingerprint,
                check_in_verification_id=verification_id
            )
            db.session.add(attendance_record)
        
        # 10. حفظ موقع الموظف
        location_record = EmployeeLocation(
            employee_id=current_employee.id,
            latitude=Decimal(str(latitude)),
            longitude=Decimal(str(longitude)),
            accuracy_m=Decimal(str(accuracy)),
            source='attendance_check_in',
            recorded_at=check_in_timestamp,
            notes=f'تسجيل حضور - {geofence_msg}'
        )
        db.session.add(location_record)
        
        db.session.commit()
        
        # 11. تسجيل المحاولة الناجحة
        record_attempt(current_employee.employee_id, success=True)
        
        # 12. إرجاع الاستجابة
        response_data = {
            'verification_id': verification_id,
            'server_timestamp': datetime.now(timezone.utc).isoformat(),
            'attendance_id': attendance_record.id,
            'employee_id': current_employee.employee_id,
            'employee_name': current_employee.name,
            'check_in_time': check_in_time.strftime('%H:%M:%S'),
            'date': today.strftime('%Y-%m-%d'),
            'location': {
                'latitude': float(latitude),
                'longitude': float(longitude),
                'accuracy': float(accuracy),
                'geofence_status': geofence_msg
            },
            'confidence': float(confidence) if confidence else None,
            'liveness_score': float(liveness_score) if liveness_score else None,
            'geofence_verified': geofence_ok
        }
        
        logger.info(f"✅ تسجيل حضور ناجح: {current_employee.name} - {verification_id}")
        
        return jsonify({
            'success': True,
            'message': f'تم تسجيل الحضور بنجاح - {geofence_msg}',
            'data': response_data
        }), 201
        
    except Exception as e:
        logger.error(f"❌ خطأ في تسجيل الحضور: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'حدث خطأ في تسجيل الحضور',
            'code': 'SERVER_ERROR',
            'message': str(e)
        }), 500


@attendance_api_bp.route('/check-out', methods=['POST'])
@token_required
def attendance_check_out(current_employee):
    """تسجيل الانصراف (محمي بـ JWT)"""
    try:
        # 1. استقبال بيانات الموقع
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        accuracy = request.form.get('accuracy')
        
        if not all([latitude, longitude, accuracy]):
            return jsonify({
                'success': False,
                'error': 'بيانات الموقع مطلوبة',
                'code': 'MISSING_LOCATION_DATA'
            }), 400
        
        # التحقق من صحة GPS
        gps_valid, gps_error = validate_gps_data(latitude, longitude, accuracy)
        if not gps_valid:
            return jsonify({
                'success': False,
                'error': gps_error,
                'code': 'INVALID_GPS_DATA'
            }), 400
        
        latitude = float(latitude)
        longitude = float(longitude)
        accuracy = float(accuracy)
        
        # 2. استقبال الصورة (اختياري)
        face_image = request.files.get('face_image')
        
        # 3. البحث عن سجل الحضور لليوم
        today = date.today()
        attendance_record = Attendance.query.filter(
            Attendance.employee_id == current_employee.id,
            Attendance.date == today
        ).first()
        
        if not attendance_record or not attendance_record.check_in:
            return jsonify({
                'success': False,
                'error': 'لم يتم تسجيل الحضور اليوم. يجب تسجيل الحضور أولاً.',
                'code': 'NO_CHECK_IN'
            }), 400
        
        if attendance_record.check_out:
            return jsonify({
                'success': False,
                'error': 'تم تسجيل الانصراف مسبقاً',
                'code': 'ALREADY_CHECKED_OUT',
                'data': {
                    'check_out_time': attendance_record.check_out.strftime('%H:%M:%S')
                }
            }), 400
        
        # 4. حفظ صورة الوجه
        face_image_path = save_face_image(face_image, current_employee.employee_id, 'check_out')
        
        # 5. تحديث سجل الحضور
        check_out_time = datetime.now().time()
        attendance_record.check_out = check_out_time
        attendance_record.check_out_latitude = Decimal(str(latitude))
        attendance_record.check_out_longitude = Decimal(str(longitude))
        attendance_record.check_out_accuracy = Decimal(str(accuracy))
        attendance_record.check_out_face_image = face_image_path
        
        # 6. حفظ موقع الموظف
        location_record = EmployeeLocation(
            employee_id=current_employee.id,
            latitude=Decimal(str(latitude)),
            longitude=Decimal(str(longitude)),
            accuracy_m=Decimal(str(accuracy)),
            source='attendance_check_out',
            recorded_at=datetime.now(timezone.utc),
            notes='تسجيل انصراف'
        )
        db.session.add(location_record)
        
        db.session.commit()
        
        # 7. حساب ساعات العمل
        check_in_datetime = datetime.combine(today, attendance_record.check_in)
        check_out_datetime = datetime.combine(today, check_out_time)
        work_duration = (check_out_datetime - check_in_datetime).total_seconds() / 3600  # بالساعات
        
        logger.info(f"✅ تسجيل انصراف ناجح: {current_employee.name}")
        
        return jsonify({
            'success': True,
            'message': 'تم تسجيل الانصراف بنجاح',
            'data': {
                'employee_id': current_employee.employee_id,
                'employee_name': current_employee.name,
                'check_in_time': attendance_record.check_in.strftime('%H:%M:%S'),
                'check_out_time': check_out_time.strftime('%H:%M:%S'),
                'work_duration_hours': round(work_duration, 2),
                'date': today.strftime('%Y-%m-%d')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ خطأ في تسجيل الانصراف: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'حدث خطأ في تسجيل الانصراف',
            'message': str(e)
        }), 500


@attendance_api_bp.route('/records', methods=['GET'])
@token_required
def get_attendance_records(current_employee):
    """جلب سجلات الحضور للموظف المُسجل (محمي بـ JWT)"""
    try:
        # معاملات الاستعلام
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        
        # بناء الاستعلام - سجلات الموظف الحالي فقط
        query = Attendance.query.filter(Attendance.employee_id == current_employee.id)
        
        if date_from:
            query = query.filter(Attendance.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        
        if date_to:
            query = query.filter(Attendance.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        
        # ترتيب وتصفح
        query = query.order_by(Attendance.date.desc(), Attendance.check_in.desc())
        pagination = query.paginate(page=page, per_page=limit, error_out=False)
        
        # بناء البيانات
        records = []
        for att in pagination.items:
            record = {
                'id': att.id,
                'employee_id': att.employee.employee_id,
                'employee_name': att.employee.name,
                'date': att.date.strftime('%Y-%m-%d'),
                'check_in': att.check_in.strftime('%H:%M:%S') if att.check_in else None,
                'check_out': att.check_out.strftime('%H:%M:%S') if att.check_out else None,
                'status': att.status,
                'location': {
                    'check_in': {
                        'latitude': float(att.check_in_latitude) if att.check_in_latitude else None,
                        'longitude': float(att.check_in_longitude) if att.check_in_longitude else None,
                        'accuracy': float(att.check_in_accuracy) if att.check_in_accuracy else None
                    },
                    'check_out': {
                        'latitude': float(att.check_out_latitude) if att.check_out_latitude else None,
                        'longitude': float(att.check_out_longitude) if att.check_out_longitude else None,
                        'accuracy': float(att.check_out_accuracy) if att.check_out_accuracy else None
                    }
                },
                'verification': {
                    'confidence': float(att.check_in_confidence) if att.check_in_confidence else None,
                    'liveness_score': float(att.check_in_liveness_score) if att.check_in_liveness_score else None,
                    'face_image': att.check_in_face_image
                },
                'created_at': att.created_at.isoformat() if att.created_at else None
            }
            records.append(record)
        
        return jsonify({
            'success': True,
            'data': {
                'records': records,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': pagination.total,
                    'total_pages': pagination.pages
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ خطأ في جلب سجلات الحضور: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'حدث خطأ في جلب السجلات',
            'message': str(e)
        }), 500


@attendance_api_bp.route('/today', methods=['GET'])
@token_required
def get_today_attendance(current_employee):
    """جلب حضور اليوم للموظف المُسجل (محمي بـ JWT)"""
    try:
        today = date.today()
        attendance = Attendance.query.filter(
            Attendance.employee_id == current_employee.id,
            Attendance.date == today
        ).first()
        
        if not attendance:
            return jsonify({
                'success': True,
                'message': 'لم يتم تسجيل الحضور اليوم',
                'data': {
                    'has_checked_in': False,
                    'has_checked_out': False
                }
            }), 200
        
        return jsonify({
            'success': True,
            'data': {
                'has_checked_in': attendance.check_in is not None,
                'has_checked_out': attendance.check_out is not None,
                'check_in': attendance.check_in.strftime('%H:%M:%S') if attendance.check_in else None,
                'check_out': attendance.check_out.strftime('%H:%M:%S') if attendance.check_out else None,
                'date': today.strftime('%Y-%m-%d')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ خطأ في جلب حضور اليوم: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'حدث خطأ',
            'message': str(e)
        }), 500
