import os
import logging
import uuid
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime, date, time
from app import db
from models import (
    Vehicle, VehicleAccident, VehicleAccidentImage,
    Employee, User
)
from utils.storage_helper import upload_image
from PIL import Image
from pillow_heif import register_heif_opener
import jwt

register_heif_opener()

logger = logging.getLogger(__name__)

api_accident_reports = Blueprint('api_accident_reports', __name__, url_prefix='/api/v1/accident-reports')


@api_accident_reports.route('/test-notifications', methods=['GET', 'POST'])
def test_accident_notifications():
    """اختبار إنشاء إشعارات الحوادث لجميع المستخدمين"""
    try:
        from models import User, Vehicle
        
        # الحصول على آخر حادثة
        last_accident = VehicleAccident.query.order_by(VehicleAccident.id.desc()).first()
        
        if not last_accident:
            return jsonify({'success': False, 'message': 'لا توجد حوادث'}), 404
        
        vehicle = Vehicle.query.get(last_accident.vehicle_id)
        all_users = User.query.all()
        
        notification_count = 0
        for user in all_users:
            try:
                create_accident_notification(
                    user_id=user.id,
                    vehicle_plate=vehicle.plate_number if vehicle else 'غير محدد',
                    driver_name=last_accident.driver_name or 'غير محدد',
                    accident_id=last_accident.id,
                    severity=last_accident.severity or 'متوسط'
                )
                notification_count += 1
            except Exception as e:
                logger.error(f'خطأ في إنشاء إشعار للمستخدم {user.id}: {str(e)}')
        
        return jsonify({
            'success': True,
            'message': f'تم إنشاء {notification_count} إشعار للحادثة {last_accident.id}',
            'accident_id': last_accident.id,
            'users_count': len(all_users)
        })
    except Exception as e:
        logger.error(f'خطأ في اختبار الإشعارات: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500

# دالة لإنشاء إشعار الحادثة
def create_accident_notification(user_id, vehicle_plate, driver_name, accident_id, severity='normal'):
    """إشعار حادثة سير جديدة"""
    from models import Notification
    from flask import url_for
    
    severity_labels = {
        'minor': 'بسيطة',
        'moderate': 'متوسطة',
        'severe': 'حادة',
        'critical': 'حرجة',
        'بسيط': 'بسيطة',
        'متوسط': 'متوسطة',
        'حاد': 'حادة',
    }
    
    severity_priority = {
        'minor': 'low',
        'moderate': 'normal',
        'severe': 'high',
        'critical': 'critical',
        'بسيط': 'low',
        'متوسط': 'normal',
        'حاد': 'high',
    }
    
    severity_label = severity_labels.get(severity, severity)
    
    notification = Notification(
        user_id=user_id,
        notification_type='accident',
        title=f'حادثة سير - السيارة {vehicle_plate}',
        description=f'تم تسجيل حادثة سير {severity_label} للسيارة {vehicle_plate} من قبل السائق {driver_name}. يرجى المراجعة والموافقة.',
        related_entity_type='accident',
        related_entity_id=accident_id,
        priority=severity_priority.get(severity, 'normal'),
        action_url=url_for('operations.list_accident_reports')
    )
    db.session.add(notification)
    db.session.commit()
    return notification

SECRET_KEY = os.environ.get('SESSION_SECRET')
if not SECRET_KEY:
    raise RuntimeError("SESSION_SECRET environment variable is required for JWT authentication")

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'heic', 'heif'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'heic', 'heif'}
MAX_FILE_SIZE = 50 * 1024 * 1024


def allowed_file(filename, file_type='image'):
    """
    التحقق من امتداد الملف
    file_type: 'image' للصور فقط، 'document' للصور و PDF
    """
    if not filename or not isinstance(filename, str):
        return False
    
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if file_type == 'document':
        return ext in ALLOWED_DOCUMENT_EXTENSIONS
    else:
        return ext in ALLOWED_IMAGE_EXTENSIONS


def compress_image(filepath, max_size=(1920, 1920), quality=85):
    """ضغط الصورة وتحويلها إلى JPEG"""
    try:
        with Image.open(filepath) as img:
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            img.save(filepath, 'JPEG', quality=quality, optimize=True)
            return True
    except Exception as e:
        logger.error(f"Error compressing image: {str(e)}")
        return False


def token_required(f):
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
                    'message': 'صيغة التوكن غير صحيحة. استخدم: Bearer <token>'
                }), 401
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'التوكن مفقود'
            }), 401
        
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            
            # البحث عن الموظف (تحويل employee_id إلى string لأنه varchar في قاعدة البيانات)
            employee_id_from_token = str(data.get('employee_id')) if data.get('employee_id') else None
            current_employee = Employee.query.filter_by(employee_id=employee_id_from_token).first() if employee_id_from_token else None
            
            if not current_employee and 'id' in data:
                current_employee = Employee.query.get(data.get('id'))
            
            if not current_employee and 'national_id' in data:
                current_employee = Employee.query.filter_by(national_id=data.get('national_id')).first()
            
            if not current_employee and 'user_id' in data:
                user = User.query.get(data.get('user_id'))
                if user:
                    current_employee = Employee.query.filter_by(user_id=user.id).first()
            
            if not current_employee:
                logger.error(f"Employee not found. Token data: {data}")
                return jsonify({
                    'success': False,
                    'message': 'الموظف غير موجود في قاعدة البيانات'
                }), 401
            
        except jwt.ExpiredSignatureError:
            logger.warning("Expired token attempted to access accident reports API")
            return jsonify({
                'success': False,
                'message': 'التوكن منتهي الصلاحية. يرجى تسجيل الدخول مجدداً'
            }), 401
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'التوكن غير صالح'
            }), 401
        
        return f(current_employee, *args, **kwargs)
    
    return decorated


@api_accident_reports.route('/submit', methods=['POST'])
@token_required
def submit_accident_report(current_employee):
    """رفع تقرير حادث من تطبيق Flutter"""
    try:
        # التحقق من البيانات المطلوبة
        vehicle_id = request.form.get('vehicle_id')
        accident_date_str = request.form.get('accident_date')
        accident_time_str = request.form.get('accident_time')
        driver_name = request.form.get('driver_name')
        description = request.form.get('description')
        
        if not all([vehicle_id, accident_date_str, driver_name, description]):
            return jsonify({
                'success': False,
                'message': 'البيانات المطلوبة غير كاملة'
            }), 400
        
        # التحقق من وجود السيارة
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            return jsonify({
                'success': False,
                'message': 'السيارة غير موجودة'
            }), 404
        
        # تحويل التاريخ والوقت
        try:
            accident_date = datetime.strptime(accident_date_str, '%Y-%m-%d').date()
        except:
            return jsonify({
                'success': False,
                'message': 'صيغة التاريخ غير صحيحة. استخدم: YYYY-MM-DD'
            }), 400
        
        accident_time_obj = None
        if accident_time_str:
            try:
                accident_time_obj = datetime.strptime(accident_time_str, '%H:%M').time()
            except:
                logger.warning(f"Invalid time format: {accident_time_str}")
        
        # إنشاء مجلد مؤقت للملفات
        temp_upload_dir = os.path.join('static', 'uploads', 'accidents', 'temp', str(uuid.uuid4().hex[:8]))
        os.makedirs(temp_upload_dir, exist_ok=True)
        
        # معالجة صورة الهوية
        driver_id_image_path = None
        id_image = request.files.get('driver_id_image')
        if id_image and allowed_file(id_image.filename, 'image'):
            filename = f"id_{uuid.uuid4().hex[:8]}.jpg"
            filepath = os.path.join(temp_upload_dir, filename)
            id_image.save(filepath)
            compress_image(filepath)
            driver_id_image_path = filepath.replace('static/', '')
        
        # معالجة صورة الرخصة
        driver_license_image_path = None
        license_image = request.files.get('driver_license_image')
        if license_image and allowed_file(license_image.filename, 'image'):
            filename = f"license_{uuid.uuid4().hex[:8]}.jpg"
            filepath = os.path.join(temp_upload_dir, filename)
            license_image.save(filepath)
            compress_image(filepath)
            driver_license_image_path = filepath.replace('static/', '')
        
        # معالجة تقرير الحادث (PDF أو صورة)
        accident_report_file_path = None
        report_file = request.files.get('accident_report_file')
        if report_file and allowed_file(report_file.filename, 'document'):
            ext = report_file.filename.rsplit('.', 1)[1].lower()
            filename = f"report_{uuid.uuid4().hex[:8]}.{ext}"
            filepath = os.path.join(temp_upload_dir, filename)
            report_file.save(filepath)
            
            # ضغط إذا كانت صورة
            if ext in ALLOWED_IMAGE_EXTENSIONS:
                compress_image(filepath)
            
            accident_report_file_path = filepath.replace('static/', '')
        
        # إنشاء سجل الحادث
        accident = VehicleAccident(
            vehicle_id=vehicle_id,
            accident_date=accident_date,
            accident_time=accident_time_obj,
            driver_name=driver_name,
            driver_phone=request.form.get('driver_phone'),
            driver_id_image=driver_id_image_path,
            driver_license_image=driver_license_image_path,
            accident_report_file=accident_report_file_path,
            reported_by_employee_id=current_employee.id,
            reported_via='mobile_app',
            review_status='pending',
            description=description,
            location=request.form.get('location', ''),
            latitude=request.form.get('latitude'),
            longitude=request.form.get('longitude'),
            severity=request.form.get('severity', 'متوسط'),
            vehicle_condition=request.form.get('vehicle_condition'),
            police_report=request.form.get('police_report', 'false').lower() == 'true',
            police_report_number=request.form.get('police_report_number'),
            notes=request.form.get('notes')
        )
        
        db.session.add(accident)
        db.session.flush()  # للحصول على ID
        
        # نقل المجلد المؤقت إلى المجلد النهائي
        final_upload_dir = os.path.join('static', 'uploads', 'accidents', str(accident.id))
        if os.path.exists(temp_upload_dir):
            import shutil
            shutil.move(temp_upload_dir, final_upload_dir)
            
            # تحديث المسارات في قاعدة البيانات
            if accident.driver_id_image:
                accident.driver_id_image = accident.driver_id_image.replace('temp/' + temp_upload_dir.split('/')[-1], str(accident.id))
            if accident.driver_license_image:
                accident.driver_license_image = accident.driver_license_image.replace('temp/' + temp_upload_dir.split('/')[-1], str(accident.id))
            if accident.accident_report_file:
                accident.accident_report_file = accident.accident_report_file.replace('temp/' + temp_upload_dir.split('/')[-1], str(accident.id))
        
        # معالجة صور الحادث الإضافية
        uploaded_images = []
        # دعم كل من accident_images و accident_images[]
        images = request.files.getlist('accident_images[]') or request.files.getlist('accident_images')
        
        if images:
            logger.info(f"Processing {len(images)} accident images for accident {accident.id}")
            # التأكد من وجود المجلد
            os.makedirs(final_upload_dir, exist_ok=True)
            
            for idx, image_file in enumerate(images):
                if image_file and image_file.filename and allowed_file(image_file.filename, 'image'):
                    # إنشاء اسم ملف آمن وفريد
                    original_filename = secure_filename(image_file.filename)
                    filename_base = os.path.splitext(original_filename)[0] if original_filename else f'photo_{idx}'
                    unique_filename = f"accident_{uuid.uuid4().hex[:8]}_{filename_base}.jpg"
                    filepath = os.path.join(final_upload_dir, unique_filename)
                    
                    # حفظ الصورة
                    image_file.save(filepath)
                    logger.info(f"Saved accident image: {filepath}")
                    
                    # ضغط الصورة
                    compress_image(filepath)
                    
                    # حفظ بيانات الصورة في قاعدة البيانات
                    relative_path = filepath.replace('static/', '')
                    accident_image = VehicleAccidentImage(
                        accident_id=accident.id,
                        image_path=relative_path,
                        image_type=request.form.get(f'image_type_{idx}', 'scene'),
                        caption=request.form.get(f'image_caption_{idx}', f'صورة الحادث {idx + 1}')
                    )
                    db.session.add(accident_image)
                    uploaded_images.append(relative_path)
                    logger.info(f"Added accident image to database: {relative_path}")
        
        db.session.commit()
        
        # إنشاء إشعارات للمسؤولين عند تسجيل حادثة جديدة
        try:
            # الحصول على جميع المستخدمين
            all_users = User.query.all()
            logger.info(f"Found {len(all_users)} users for accident notifications")
            
            severity_val = request.form.get('severity', 'متوسط')
            
            for user in all_users:
                try:
                    # استخدام الدالة المحلية create_accident_notification
                    create_accident_notification(
                        user_id=user.id,
                        vehicle_plate=vehicle.plate_number,
                        driver_name=driver_name,
                        accident_id=accident.id,
                        severity=severity_val
                    )
                    logger.info(f"Created accident notification for user {user.id}")
                except Exception as e:
                    logger.error(f'خطأ في إنشاء إشعار للمستخدم {user.id}: {str(e)}')
        except Exception as e:
            logger.error(f'خطأ في إنشاء إشعارات الحادثة: {str(e)}')
        
        logger.info(f"Accident report {accident.id} submitted by employee {current_employee.employee_id} for vehicle {vehicle.plate_number}")
        
        return jsonify({
            'success': True,
            'message': 'تم رفع تقرير الحادث بنجاح. سيتم مراجعته من قبل إدارة العمليات',
            'data': {
                'accident_id': accident.id,
                'vehicle': {
                    'id': vehicle.id,
                    'plate_number': vehicle.plate_number,
                    'make': vehicle.make,
                    'model': vehicle.model
                },
                'review_status': accident.review_status,
                'uploaded_images_count': len(uploaded_images),
                'created_at': accident.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting accident report: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ أثناء رفع التقرير: {str(e)}'
        }), 500


@api_accident_reports.route('/my-reports', methods=['GET'])
@token_required
def get_my_reports(current_employee):
    """الحصول على تقارير الحوادث الخاصة بالموظف"""
    try:
        accidents = VehicleAccident.query.filter_by(
            reported_by_employee_id=current_employee.id
        ).order_by(VehicleAccident.accident_date.desc()).all()
        
        reports = []
        for accident in accidents:
            reports.append({
                'id': accident.id,
                'vehicle': {
                    'id': accident.vehicle.id,
                    'plate_number': accident.vehicle.plate_number,
                    'make': accident.vehicle.make,
                    'model': accident.vehicle.model
                },
                'accident_date': accident.accident_date.isoformat(),
                'accident_time': accident.accident_time.isoformat() if accident.accident_time else None,
                'driver_name': accident.driver_name,
                'description': accident.description,
                'location': accident.location,
                'severity': accident.severity,
                'review_status': accident.review_status,
                'reviewer_notes': accident.reviewer_notes,
                'images_count': accident.images.count(),
                'created_at': accident.created_at.isoformat(),
                'reviewed_at': accident.reviewed_at.isoformat() if accident.reviewed_at else None
            })
        
        return jsonify({
            'success': True,
            'data': reports,
            'total': len(reports)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching accident reports: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ أثناء جلب التقارير: {str(e)}'
        }), 500


@api_accident_reports.route('/<int:accident_id>', methods=['GET'])
@token_required
def get_accident_details(current_employee, accident_id):
    """الحصول على تفاصيل تقرير حادث معين"""
    try:
        accident = VehicleAccident.query.get_or_404(accident_id)
        
        # التحقق من أن الموظف هو من قام بالإبلاغ أو لديه صلاحيات
        if accident.reported_by_employee_id != current_employee.id:
            # يمكن إضافة تحقق من صلاحيات المشاهدة هنا
            pass
        
        images = []
        for img in accident.images.all():
            images.append({
                'id': img.id,
                'url': f'/static/{img.image_path}',
                'type': img.image_type,
                'caption': img.caption,
                'uploaded_at': img.uploaded_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'data': {
                'id': accident.id,
                'vehicle': {
                    'id': accident.vehicle.id,
                    'plate_number': accident.vehicle.plate_number,
                    'make': accident.vehicle.make,
                    'model': accident.vehicle.model,
                    'year': accident.vehicle.year
                },
                'accident_date': accident.accident_date.isoformat(),
                'accident_time': accident.accident_time.isoformat() if accident.accident_time else None,
                'driver_name': accident.driver_name,
                'description': accident.description,
                'location': accident.location,
                'latitude': accident.latitude,
                'longitude': accident.longitude,
                'severity': accident.severity,
                'vehicle_condition': accident.vehicle_condition,
                'police_report': accident.police_report,
                'police_report_number': accident.police_report_number,
                'insurance_claim': accident.insurance_claim,
                'review_status': accident.review_status,
                'reviewer_notes': accident.reviewer_notes,
                'accident_status': accident.accident_status,
                'images': images,
                'created_at': accident.created_at.isoformat(),
                'reviewed_at': accident.reviewed_at.isoformat() if accident.reviewed_at else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching accident details: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ أثناء جلب تفاصيل التقرير: {str(e)}'
        }), 500
