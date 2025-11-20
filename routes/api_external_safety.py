import os
import jwt
import logging
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
from app import db
from models import (
    Vehicle, VehicleExternalSafetyCheck, VehicleSafetyImage, 
    Employee, User
)
from utils.storage_helper import upload_image
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

logger = logging.getLogger(__name__)

api_external_safety = Blueprint('api_external_safety', __name__, url_prefix='/api/v1/external-safety')

SECRET_KEY = os.environ.get('SESSION_SECRET')
if not SECRET_KEY:
    raise RuntimeError("SESSION_SECRET environment variable is required for JWT authentication")

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'heic', 'heif'}
MAX_FILE_SIZE = 50 * 1024 * 1024


def allowed_file(filename):
    if not filename or not isinstance(filename, str):
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
            current_employee = Employee.query.get(data['employee_id'])
            
            if not current_employee:
                return jsonify({
                    'success': False,
                    'message': 'الموظف غير موجود'
                }), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'message': 'التوكن منتهي الصلاحية'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'message': 'التوكن غير صالح'
            }), 401
        
        return f(current_employee, *args, **kwargs)
    
    return decorated


@api_external_safety.route('/checks', methods=['POST'])
@token_required
def create_safety_check(current_employee):
    """
    إنشاء فحص سلامة خارجي جديد من تطبيق Flutter
    
    JSON Body:
    {
        "vehicle_id": 123,
        "driver_name": "محمد أحمد",
        "driver_national_id": "1234567890",
        "driver_department": "المشاريع",
        "driver_city": "الرياض",
        "current_delegate": "أحمد علي",
        "notes": "ملاحظات إضافية"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'لا توجد بيانات'
            }), 400
        
        vehicle_id = data.get('vehicle_id')
        if not vehicle_id:
            return jsonify({
                'success': False,
                'message': 'رقم السيارة مطلوب'
            }), 400
        
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            return jsonify({
                'success': False,
                'message': 'السيارة غير موجودة'
            }), 404
        
        driver_name = data.get('driver_name') or current_employee.name
        driver_national_id = data.get('driver_national_id') or current_employee.national_id
        driver_department = data.get('driver_department') or current_employee.department.name if current_employee.department else 'غير محدد'
        driver_city = data.get('driver_city', 'الرياض')
        
        if not all([driver_name, driver_national_id, driver_department, driver_city]):
            return jsonify({
                'success': False,
                'message': 'يرجى تعبئة جميع البيانات المطلوبة'
            }), 400
        
        safety_check = VehicleExternalSafetyCheck()
        safety_check.vehicle_id = vehicle.id
        safety_check.driver_name = driver_name
        safety_check.driver_national_id = driver_national_id
        safety_check.driver_department = driver_department
        safety_check.driver_city = driver_city
        safety_check.vehicle_plate_number = vehicle.plate_number
        safety_check.vehicle_make_model = f"{vehicle.make} {vehicle.model}"
        safety_check.current_delegate = data.get('current_delegate', '')
        safety_check.notes = data.get('notes', '')
        safety_check.inspection_date = datetime.now()
        safety_check.approval_status = 'pending'
        
        db.session.add(safety_check)
        db.session.commit()
        
        logger.info(f"Safety check created: ID={safety_check.id}, Vehicle={vehicle.plate_number}, Employee={current_employee.name}")
        
        return jsonify({
            'success': True,
            'data': {
                'check_id': safety_check.id,
                'vehicle_plate_number': safety_check.vehicle_plate_number,
                'inspection_date': safety_check.inspection_date.isoformat(),
                'approval_status': safety_check.approval_status
            },
            'message': 'تم إنشاء فحص السلامة بنجاح'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating safety check: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء إنشاء الفحص',
            'error': str(e)
        }), 500


@api_external_safety.route('/checks/<int:check_id>/upload-image', methods=['POST'])
@token_required
def upload_safety_check_image(current_employee, check_id):
    """
    رفع صورة لفحص السلامة (متوافق مع Flutter)
    يحفظ الصورة في Object Storage مباشرة
    
    Form Field:
    - image: صورة واحدة
    - description: وصف الصورة (اختياري)
    """
    try:
        safety_check = VehicleExternalSafetyCheck.query.get(check_id)
        
        if not safety_check:
            return jsonify({
                'success': False,
                'message': 'فحص السلامة غير موجود'
            }), 404
        
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'message': 'لا توجد صورة مرفقة'
            }), 400
        
        file = request.files['image']
        description = request.form.get('description', '')
        
        if not file or not file.filename or file.filename == '':
            return jsonify({
                'success': False,
                'message': 'الصورة فارغة'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': 'نوع الملف غير مدعوم. الأنواع المدعومة: jpg, jpeg, png, heic'
            }), 400
        
        safe_filename_str = secure_filename(file.filename)
        file_ext = safe_filename_str.rsplit('.', 1)[1].lower() if '.' in safe_filename_str else 'jpg'
        filename = f"{uuid.uuid4()}.{file_ext}"
        
        file_data = file.read()
        temp_path = f"/tmp/{filename}"
        
        with open(temp_path, 'wb') as f:
            f.write(file_data)
        
        compress_image(temp_path)
        
        with open(temp_path, 'rb') as f:
            compressed_data = f.read()
        
        object_key = upload_image(compressed_data, 'safety_checks', filename)
        
        os.remove(temp_path)
        
        file_size = len(compressed_data)
        
        safety_image = VehicleSafetyImage()
        safety_image.safety_check_id = safety_check.id
        safety_image.image_path = object_key
        safety_image.image_description = description if description else f"رفع من تطبيق الموبايل - {current_employee.name}"
        
        db.session.add(safety_image)
        db.session.commit()
        
        image_url = f"https://nuzum.site/storage/safety_checks/{filename}"
        
        logger.info(f"Safety check image uploaded: CheckID={check_id}, ImageID={safety_image.id}, Employee={current_employee.name}")
        
        return jsonify({
            'success': True,
            'data': {
                'image_id': safety_image.id,
                'image_url': image_url,
                'object_key': object_key,
                'file_size': file_size,
                'description': safety_image.image_description
            },
            'message': 'تم رفع الصورة بنجاح'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error uploading safety check image: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء رفع الصورة',
            'error': str(e)
        }), 500


@api_external_safety.route('/checks/<int:check_id>', methods=['GET'])
@token_required
def get_safety_check(current_employee, check_id):
    """الحصول على تفاصيل فحص السلامة"""
    try:
        safety_check = VehicleExternalSafetyCheck.query.get(check_id)
        
        if not safety_check:
            return jsonify({
                'success': False,
                'message': 'فحص السلامة غير موجود'
            }), 404
        
        images = []
        for img in safety_check.safety_images:
            filename = img.image_path.split('/')[-1] if '/' in img.image_path else img.image_path
            images.append({
                'id': img.id,
                'url': f"https://nuzum.site/storage/safety_checks/{filename}",
                'description': img.image_description,
                'uploaded_at': img.uploaded_at.isoformat() if img.uploaded_at else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'id': safety_check.id,
                'vehicle_plate_number': safety_check.vehicle_plate_number,
                'vehicle_make_model': safety_check.vehicle_make_model,
                'driver_name': safety_check.driver_name,
                'driver_national_id': safety_check.driver_national_id,
                'driver_department': safety_check.driver_department,
                'driver_city': safety_check.driver_city,
                'current_delegate': safety_check.current_delegate,
                'notes': safety_check.notes,
                'inspection_date': safety_check.inspection_date.isoformat(),
                'approval_status': safety_check.approval_status,
                'approved_at': safety_check.approved_at.isoformat() if safety_check.approved_at else None,
                'rejection_reason': safety_check.rejection_reason,
                'images': images,
                'images_count': len(images)
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting safety check: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء جلب البيانات',
            'error': str(e)
        }), 500


@api_external_safety.route('/vehicles', methods=['GET'])
@token_required
def get_vehicles(current_employee):
    """الحصول على قائمة السيارات"""
    try:
        vehicles = Vehicle.query.filter_by(status='active').all()
        
        vehicles_list = []
        for vehicle in vehicles:
            vehicles_list.append({
                'id': vehicle.id,
                'plate_number': vehicle.plate_number,
                'make': vehicle.make,
                'model': vehicle.model,
                'year': vehicle.year,
                'make_model': f"{vehicle.make} {vehicle.model}"
            })
        
        return jsonify({
            'success': True,
            'data': vehicles_list,
            'count': len(vehicles_list)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting vehicles: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء جلب البيانات',
            'error': str(e)
        }), 500
