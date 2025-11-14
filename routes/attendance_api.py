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
import json
import os
import hashlib
import logging
from math import radians, sin, cos, sqrt, atan2

from app import db
from models import Employee, Attendance, EmployeeLocation, Geofence, GeofenceSession

logger = logging.getLogger(__name__)

# إنشاء Blueprint
attendance_api_bp = Blueprint('attendance_api', __name__, url_prefix='/api/v1/attendance')

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


def verify_geofence(employee, latitude, longitude):
    """التحقق من أن الموظف داخل منطقة العمل"""
    try:
        # البحث عن geofences المرتبطة بالموظف
        geofences = Geofence.query.filter(
            Geofence.employees.contains(employee)
        ).all()
        
        if not geofences:
            # لا توجد geofences محددة - السماح بالحضور
            return True, None, "لا توجد منطقة محددة"
        
        # التحقق من وجود الموظف داخل أي geofence
        for geofence in geofences:
            distance = calculate_distance(
                float(geofence.latitude),
                float(geofence.longitude),
                float(latitude),
                float(longitude)
            )
            
            if distance is not None and distance <= float(geofence.radius):
                return True, geofence, f"داخل منطقة {geofence.name}"
        
        # الموظف خارج جميع المناطق
        return False, None, "خارج منطقة العمل"
        
    except Exception as e:
        logger.error(f"Error verifying geofence: {e}")
        return False, None, f"خطأ في التحقق: {str(e)}"


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
def attendance_check_in():
    """
    تسجيل الحضور مع التحقق من الوجه والموقع
    
    Request (multipart/form-data):
    - employee_id: معرف الموظف
    - latitude: خط العرض
    - longitude: خط الطول  
    - accuracy: دقة الموقع
    - confidence: مستوى الثقة في التعرف (0-1)
    - liveness_score: درجة الحياة (0-1)
    - liveness_checks: JSON تفاصيل فحوصات الحياة
    - device_fingerprint: JSON معلومات الجهاز
    - timestamp: وقت التحضير ISO 8601
    - face_image: صورة الوجه (اختياري)
    
    Response:
    - success: true/false
    - message: رسالة النتيجة
    - data: بيانات الحضور
    """
    try:
        # 1. استقبال البيانات
        employee_id = request.form.get('employee_id')
        if not employee_id:
            return jsonify({
                'success': False,
                'error': 'employee_id مطلوب',
                'code': 'MISSING_EMPLOYEE_ID'
            }), 400
        
        # 2. التحقق من وجود الموظف
        employee = Employee.query.filter_by(employee_id=employee_id, status='active').first()
        if not employee:
            return jsonify({
                'success': False,
                'error': 'الموظف غير موجود أو غير نشط',
                'code': 'EMPLOYEE_NOT_FOUND'
            }), 404
        
        # 3. استقبال بيانات الموقع
        try:
            latitude = float(request.form.get('latitude', 0))
            longitude = float(request.form.get('longitude', 0))
            accuracy = float(request.form.get('accuracy', 0))
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'بيانات الموقع غير صحيحة',
                'code': 'INVALID_LOCATION'
            }), 400
        
        # 4. استقبال بيانات التحقق
        confidence = float(request.form.get('confidence', 0))
        liveness_score = float(request.form.get('liveness_score', 0))
        
        try:
            liveness_checks = json.loads(request.form.get('liveness_checks', '{}'))
            device_fingerprint = json.loads(request.form.get('device_fingerprint', '{}'))
        except json.JSONDecodeError:
            liveness_checks = {}
            device_fingerprint = {}
        
        # 5. استقبال الصورة
        face_image = request.files.get('face_image')
        
        # 6. التحقق من التاريخ
        timestamp_str = request.form.get('timestamp')
        try:
            check_in_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            check_in_timestamp = datetime.now(timezone.utc)
        
        # 7. التحقق من الموقع (Geofencing)
        geofence_ok, geofence, geofence_msg = verify_geofence(employee, latitude, longitude)
        
        # 8. التحقق من Liveness (إذا كانت مطلوبة)
        if liveness_score > 0 and liveness_score < 0.7:
            return jsonify({
                'success': False,
                'error': 'فحص الحياة فشل. الرجاء التأكد من أنك شخص حقيقي.',
                'code': 'LIVENESS_FAILED',
                'details': {'liveness_score': liveness_score}
            }), 400
        
        # 9. التحقق من Confidence (إذا كانت مطلوبة)
        if confidence > 0 and confidence < 0.75:
            return jsonify({
                'success': False,
                'error': 'مستوى الثقة منخفض. الرجاء التأكد من الإضاءة الجيدة.',
                'code': 'LOW_CONFIDENCE',
                'details': {'confidence': confidence}
            }), 400
        
        # 10. التحقق من عدم التحضير المتكرر
        today = date.today()
        existing_attendance = Attendance.query.filter(
            Attendance.employee_id == employee.id,
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
        
        # 11. حفظ صورة الوجه
        face_image_path = save_face_image(face_image, employee_id, 'check_in')
        
        # 12. إنشاء أو تحديث سجل الحضور
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
                employee_id=employee.id,
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
        
        # 13. حفظ موقع الموظف
        location_record = EmployeeLocation(
            employee_id=employee.id,
            latitude=Decimal(str(latitude)),
            longitude=Decimal(str(longitude)),
            accuracy_m=Decimal(str(accuracy)),
            source='attendance_check_in',
            recorded_at=check_in_timestamp,
            notes=f'تسجيل حضور - {geofence_msg}'
        )
        db.session.add(location_record)
        
        db.session.commit()
        
        # 14. إرجاع الاستجابة
        response_data = {
            'verification_id': verification_id,
            'server_timestamp': datetime.now(timezone.utc).isoformat(),
            'attendance_id': attendance_record.id,
            'employee_id': employee.employee_id,
            'employee_name': employee.name,
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
        
        logger.info(f"✅ تسجيل حضور ناجح: {employee.name} - {verification_id}")
        
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
def attendance_check_out():
    """تسجيل الانصراف"""
    try:
        # 1. استقبال البيانات
        employee_id = request.form.get('employee_id')
        if not employee_id:
            return jsonify({
                'success': False,
                'error': 'employee_id مطلوب'
            }), 400
        
        # 2. التحقق من وجود الموظف
        employee = Employee.query.filter_by(employee_id=employee_id).first()
        if not employee:
            return jsonify({
                'success': False,
                'error': 'الموظف غير موجود'
            }), 404
        
        # 3. استقبال بيانات الموقع
        latitude = float(request.form.get('latitude', 0))
        longitude = float(request.form.get('longitude', 0))
        accuracy = float(request.form.get('accuracy', 0))
        
        # 4. استقبال الصورة (اختياري)
        face_image = request.files.get('face_image')
        
        # 5. البحث عن سجل الحضور لليوم
        today = date.today()
        attendance_record = Attendance.query.filter(
            Attendance.employee_id == employee.id,
            Attendance.date == today
        ).first()
        
        if not attendance_record or not attendance_record.check_in:
            return jsonify({
                'success': False,
                'error': 'لم يتم تسجيل الحضور اليوم. يجب تسجيل الحضور أولاً.'
            }), 400
        
        if attendance_record.check_out:
            return jsonify({
                'success': False,
                'error': 'تم تسجيل الانصراف مسبقاً',
                'data': {
                    'check_out_time': attendance_record.check_out.strftime('%H:%M:%S')
                }
            }), 400
        
        # 6. حفظ صورة الوجه
        face_image_path = save_face_image(face_image, employee_id, 'check_out')
        
        # 7. تحديث سجل الحضور
        check_out_time = datetime.now().time()
        attendance_record.check_out = check_out_time
        attendance_record.check_out_latitude = Decimal(str(latitude))
        attendance_record.check_out_longitude = Decimal(str(longitude))
        attendance_record.check_out_accuracy = Decimal(str(accuracy))
        attendance_record.check_out_face_image = face_image_path
        
        # 8. حفظ موقع الموظف
        location_record = EmployeeLocation(
            employee_id=employee.id,
            latitude=Decimal(str(latitude)),
            longitude=Decimal(str(longitude)),
            accuracy_m=Decimal(str(accuracy)),
            source='attendance_check_out',
            recorded_at=datetime.now(timezone.utc),
            notes='تسجيل انصراف'
        )
        db.session.add(location_record)
        
        db.session.commit()
        
        # 9. حساب ساعات العمل
        check_in_datetime = datetime.combine(today, attendance_record.check_in)
        check_out_datetime = datetime.combine(today, check_out_time)
        work_duration = (check_out_datetime - check_in_datetime).total_seconds() / 3600  # بالساعات
        
        logger.info(f"✅ تسجيل انصراف ناجح: {employee.name}")
        
        return jsonify({
            'success': True,
            'message': 'تم تسجيل الانصراف بنجاح',
            'data': {
                'employee_id': employee.employee_id,
                'employee_name': employee.name,
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
def get_attendance_records():
    """جلب سجلات الحضور"""
    try:
        # معاملات الاستعلام
        employee_id = request.args.get('employee_id')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        
        # بناء الاستعلام
        query = Attendance.query
        
        if employee_id:
            employee = Employee.query.filter_by(employee_id=employee_id).first()
            if employee:
                query = query.filter(Attendance.employee_id == employee.id)
        
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
def get_today_attendance():
    """جلب حضور اليوم لموظف معين"""
    try:
        employee_id = request.args.get('employee_id')
        if not employee_id:
            return jsonify({
                'success': False,
                'error': 'employee_id مطلوب'
            }), 400
        
        employee = Employee.query.filter_by(employee_id=employee_id).first()
        if not employee:
            return jsonify({
                'success': False,
                'error': 'الموظف غير موجود'
            }), 404
        
        today = date.today()
        attendance = Attendance.query.filter(
            Attendance.employee_id == employee.id,
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
