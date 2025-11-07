"""
API Endpoints الخارجية - بدون مصادقة
تستخدم للتطبيقات الخارجية مثل تطبيق الأندرويد لتتبع المواقع
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from models import Employee, EmployeeLocation, db
import os
import logging

# إنشاء Blueprint
api_external_bp = Blueprint('api_external', __name__, url_prefix='/api/external')

# مفتاح API الثابت (محفوظ في متغير بيئة)
LOCATION_API_KEY = os.environ.get('LOCATION_API_KEY', 'test_location_key_2025')

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@api_external_bp.route('/employee-location', methods=['POST'])
def receive_employee_location():
    """
    استقبال موقع الموظف من تطبيق الأندرويد
    
    مثال على البيانات المُرسلة:
    {
        "api_key": "test_location_key_2025",
        "job_number": "EMP12345",
        "latitude": 24.7136,
        "longitude": 46.6753,
        "accuracy": 10.5,
        "recorded_at": "2025-11-07T10:30:00Z"
    }
    """
    try:
        # الحصول على البيانات
        data = request.get_json()
        
        if not data:
            logger.warning(f"طلب فارغ من {request.remote_addr}")
            return jsonify({
                'success': False,
                'error': 'لا توجد بيانات في الطلب'
            }), 400
        
        # التحقق من مفتاح API
        api_key = data.get('api_key')
        if not api_key or api_key != LOCATION_API_KEY:
            logger.warning(f"محاولة وصول بمفتاح خاطئ من {request.remote_addr}")
            return jsonify({
                'success': False,
                'error': 'مفتاح API غير صحيح'
            }), 401
        
        # التحقق من البيانات المطلوبة
        job_number = data.get('job_number')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not job_number:
            return jsonify({
                'success': False,
                'error': 'الرقم الوظيفي مطلوب'
            }), 400
        
        if latitude is None or longitude is None:
            return jsonify({
                'success': False,
                'error': 'الإحداثيات (latitude, longitude) مطلوبة'
            }), 400
        
        # التحقق من صحة الإحداثيات
        try:
            lat = float(latitude)
            lng = float(longitude)
            
            # التحقق من النطاق المعقول للإحداثيات
            if not (-90 <= lat <= 90):
                return jsonify({
                    'success': False,
                    'error': 'latitude يجب أن يكون بين -90 و 90'
                }), 400
            
            if not (-180 <= lng <= 180):
                return jsonify({
                    'success': False,
                    'error': 'longitude يجب أن يكون بين -180 و 180'
                }), 400
                
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'الإحداثيات يجب أن تكون أرقام صحيحة'
            }), 400
        
        # البحث عن الموظف باستخدام job_number
        employee = Employee.query.filter_by(employee_id=job_number).first()
        
        if not employee:
            logger.warning(f"موظف غير موجود: {job_number} من {request.remote_addr}")
            return jsonify({
                'success': False,
                'error': f'لم يتم العثور على موظف بالرقم الوظيفي: {job_number}'
            }), 404
        
        # البيانات الاختيارية
        accuracy = data.get('accuracy')
        recorded_at_str = data.get('recorded_at')
        notes = data.get('notes', '')
        
        # تحليل وقت التسجيل
        if recorded_at_str:
            try:
                recorded_at = datetime.fromisoformat(recorded_at_str.replace('Z', '+00:00'))
            except:
                recorded_at = datetime.utcnow()
        else:
            recorded_at = datetime.utcnow()
        
        # إنشاء سجل الموقع الجديد
        location = EmployeeLocation(
            employee_id=employee.id,
            latitude=lat,
            longitude=lng,
            accuracy_m=float(accuracy) if accuracy else None,
            source='android_app',
            recorded_at=recorded_at,
            received_at=datetime.utcnow(),
            notes=notes
        )
        
        # حفظ في قاعدة البيانات
        db.session.add(location)
        db.session.commit()
        
        # تسجيل النجاح
        logger.info(f"✅ تم حفظ موقع الموظف {employee.name} ({job_number}) من {request.remote_addr}")
        
        return jsonify({
            'success': True,
            'message': 'تم حفظ الموقع بنجاح',
            'data': {
                'employee_name': employee.name,
                'location_id': location.id,
                'recorded_at': location.recorded_at.isoformat(),
                'received_at': location.received_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"خطأ في حفظ الموقع: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'حدث خطأ في الخادم'
        }), 500


@api_external_bp.route('/test', methods=['GET'])
def test_api():
    """نقطة اختبار بسيطة للتأكد من عمل API"""
    return jsonify({
        'success': True,
        'message': 'External API is working!',
        'endpoints': {
            'employee_location': '/api/external/employee-location [POST]'
        }
    }), 200
