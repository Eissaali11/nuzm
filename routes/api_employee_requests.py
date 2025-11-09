import os
import jwt
import logging
from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user
from werkzeug.security import check_password_hash
from functools import wraps
from datetime import datetime, timedelta
from app import db

logger = logging.getLogger(__name__)
from models import (
    User, Employee, EmployeeRequest, InvoiceRequest, AdvancePaymentRequest,
    CarWashRequest, CarInspectionRequest, CarWashMedia, CarInspectionMedia,
    RequestNotification, RequestStatus, RequestType, Vehicle, MediaType, FileType
)
from utils.employee_requests_drive_uploader import EmployeeRequestsDriveUploader
from werkzeug.utils import secure_filename
import uuid

api_employee_requests = Blueprint('api_employee_requests', __name__, url_prefix='/api/v1')

SECRET_KEY = os.environ.get('SESSION_SECRET')
if not SECRET_KEY:
    raise RuntimeError("SESSION_SECRET environment variable is required for JWT authentication")

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'heic', 'mp4', 'mov', 'avi', 'pdf'}
MAX_FILE_SIZE = 500 * 1024 * 1024


def allowed_file(filename):
    if not filename or not isinstance(filename, str):
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
            current_employee = Employee.query.filter_by(employee_id=data['employee_id']).first()
            
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


@api_employee_requests.route('/auth/login', methods=['POST'])
def login():
    """
    تسجيل الدخول والحصول على JWT Token
    
    Body:
    {
        "employee_id": "EMP001",
        "password": "password123"
    }
    
    Response:
    {
        "success": true,
        "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "employee": {
            "id": 1,
            "employee_id": "EMP001",
            "name": "أحمد محمد",
            "email": "ahmad@example.com"
        }
    }
    """
    data = request.get_json()
    
    if not data or not data.get('employee_id') or not data.get('password'):
        return jsonify({
            'success': False,
            'message': 'معرف الموظف وكلمة المرور مطلوبان'
        }), 400
    
    employee = Employee.query.filter_by(employee_id=data['employee_id']).first()
    
    if not employee:
        return jsonify({
            'success': False,
            'message': 'بيانات الدخول غير صحيحة'
        }), 401
    
    if not employee.password_hash or not check_password_hash(employee.password_hash, data['password']):
        return jsonify({
            'success': False,
            'message': 'بيانات الدخول غير صحيحة'
        }), 401
    
    token = jwt.encode({
        'employee_id': employee.employee_id,
        'exp': datetime.utcnow() + timedelta(days=30)
    }, SECRET_KEY, algorithm='HS256')
    
    return jsonify({
        'success': True,
        'token': token,
        'employee': {
            'id': employee.id,
            'employee_id': employee.employee_id,
            'name': employee.name,
            'email': employee.email,
            'job_title': employee.job_title,
            'department': employee.department.name if employee.department else None,
            'profile_image': employee.profile_image
        }
    }), 200


@api_employee_requests.route('/requests', methods=['GET'])
@token_required
def get_requests(current_employee):
    """
    الحصول على قائمة طلبات الموظف
    
    Query Parameters:
    - page: رقم الصفحة (default: 1)
    - per_page: عدد العناصر في الصفحة (default: 20)
    - status: فلترة حسب الحالة (PENDING, APPROVED, REJECTED, IN_REVIEW, CANCELLED)
    - type: فلترة حسب النوع (INVOICE, CAR_WASH, CAR_INSPECTION, ADVANCE_PAYMENT)
    
    Response:
    {
        "success": true,
        "requests": [...],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total": 45,
            "pages": 3
        }
    }
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status_filter = request.args.get('status', '')
    type_filter = request.args.get('type', '')
    
    query = EmployeeRequest.query.filter_by(employee_id=current_employee.id)
    
    if status_filter:
        try:
            query = query.filter_by(status=RequestStatus[status_filter])
        except KeyError:
            return jsonify({
                'success': False,
                'message': f'حالة غير صحيحة: {status_filter}'
            }), 400
    
    if type_filter:
        try:
            query = query.filter_by(request_type=RequestType[type_filter])
        except KeyError:
            return jsonify({
                'success': False,
                'message': f'نوع غير صحيح: {type_filter}'
            }), 400
    
    pagination = query.order_by(EmployeeRequest.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    requests_list = []
    for req in pagination.items:
        request_data = {
            'id': req.id,
            'type': req.request_type.name,
            'type_display': req.get_type_display(),
            'status': req.status.name,
            'status_display': req.get_status_display(),
            'title': req.title,
            'description': req.description,
            'amount': float(req.amount) if req.amount else None,
            'created_at': req.created_at.isoformat(),
            'updated_at': req.updated_at.isoformat() if req.updated_at else None,
            'reviewed_at': req.reviewed_at.isoformat() if req.reviewed_at else None,
            'admin_notes': req.admin_notes,
            'google_drive_folder_url': req.google_drive_folder_url
        }
        requests_list.append(request_data)
    
    return jsonify({
        'success': True,
        'requests': requests_list,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    }), 200


@api_employee_requests.route('/requests/<int:request_id>', methods=['GET'])
@token_required
def get_request_details(current_employee, request_id):
    """
    الحصول على تفاصيل طلب معين
    
    Response:
    {
        "success": true,
        "request": {
            "id": 1,
            "type": "INVOICE",
            "status": "PENDING",
            ...
            "details": {...}  // تفاصيل خاصة بنوع الطلب
        }
    }
    """
    emp_request = EmployeeRequest.query.filter_by(
        id=request_id,
        employee_id=current_employee.id
    ).first()
    
    if not emp_request:
        return jsonify({
            'success': False,
            'message': 'الطلب غير موجود'
        }), 404
    
    request_data = {
        'id': emp_request.id,
        'type': emp_request.request_type.name,
        'type_display': emp_request.get_type_display(),
        'status': emp_request.status.name,
        'status_display': emp_request.get_status_display(),
        'title': emp_request.title,
        'description': emp_request.description,
        'amount': float(emp_request.amount) if emp_request.amount else None,
        'created_at': emp_request.created_at.isoformat(),
        'updated_at': emp_request.updated_at.isoformat() if emp_request.updated_at else None,
        'reviewed_at': emp_request.reviewed_at.isoformat() if emp_request.reviewed_at else None,
        'admin_notes': emp_request.admin_notes,
        'google_drive_folder_url': emp_request.google_drive_folder_url
    }
    
    if emp_request.request_type == RequestType.INVOICE and emp_request.invoice_data:
        invoice = emp_request.invoice_data
        request_data['details'] = {
            'vendor_name': invoice.vendor_name,
            'invoice_date': invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            'drive_view_url': invoice.drive_view_url,
            'file_size': invoice.file_size
        }
    
    elif emp_request.request_type == RequestType.ADVANCE_PAYMENT and emp_request.advance_payment_data:
        advance = emp_request.advance_payment_data
        request_data['details'] = {
            'requested_amount': float(advance.requested_amount),
            'reason': advance.reason,
            'installments': advance.installments,
            'installment_amount': float(advance.installment_amount) if advance.installment_amount else None
        }
    
    elif emp_request.request_type == RequestType.CAR_WASH and emp_request.car_wash_data:
        wash = emp_request.car_wash_data
        media_files = []
        for media in wash.media_files:
            media_files.append({
                'id': media.id,
                'file_type': media.file_type,
                'drive_file_id': media.drive_file_id,
                'drive_view_url': media.drive_view_url,
                'uploaded_at': media.uploaded_at.isoformat()
            })
        
        request_data['details'] = {
            'service_type': wash.service_type,
            'scheduled_date': wash.scheduled_date.isoformat() if wash.scheduled_date else None,
            'vehicle': {
                'id': wash.vehicle.id,
                'plate_number': wash.vehicle.plate_number,
                'make': wash.vehicle.make,
                'model': wash.vehicle.model
            } if wash.vehicle else None,
            'media_files': media_files
        }
    
    elif emp_request.request_type == RequestType.CAR_INSPECTION and emp_request.inspection_data:
        inspection = emp_request.inspection_data
        media_files = []
        for media in inspection.media_files:
            media_files.append({
                'id': media.id,
                'file_type': media.file_type,
                'drive_file_id': media.drive_file_id,
                'drive_view_url': media.drive_view_url,
                'file_size': media.file_size,
                'uploaded_at': media.uploaded_at.isoformat()
            })
        
        request_data['details'] = {
            'inspection_type': inspection.inspection_type,
            'inspection_date': inspection.inspection_date.isoformat() if inspection.inspection_date else None,
            'vehicle': {
                'id': inspection.vehicle.id,
                'plate_number': inspection.vehicle.plate_number,
                'make': inspection.vehicle.make,
                'model': inspection.vehicle.model
            } if inspection.vehicle else None,
            'media_files': media_files
        }
    
    return jsonify({
        'success': True,
        'request': request_data
    }), 200


@api_employee_requests.route('/requests', methods=['POST'])
@token_required
def create_request(current_employee):
    """
    إنشاء طلب جديد
    
    Body:
    {
        "type": "INVOICE",  // INVOICE, CAR_WASH, CAR_INSPECTION, ADVANCE_PAYMENT
        "title": "عنوان الطلب",
        "description": "وصف الطلب",
        "amount": 1500.00,
        "details": {
            // تفاصيل خاصة بنوع الطلب
        }
    }
    
    Response:
    {
        "success": true,
        "request_id": 123,
        "message": "تم إنشاء الطلب بنجاح"
    }
    """
    data = request.get_json()
    
    if not data or not data.get('type') or not data.get('title'):
        return jsonify({
            'success': False,
            'message': 'النوع والعنوان مطلوبان'
        }), 400
    
    try:
        request_type = RequestType[data['type']]
    except KeyError:
        return jsonify({
            'success': False,
            'message': f'نوع طلب غير صحيح: {data["type"]}'
        }), 400
    
    new_request = EmployeeRequest()
    new_request.employee_id = current_employee.id
    new_request.request_type = request_type
    new_request.title = data['title']
    new_request.description = data.get('description')
    new_request.amount = data.get('amount')
    new_request.status = RequestStatus.PENDING
    
    db.session.add(new_request)
    db.session.flush()
    
    details = data.get('details', {})
    
    if request_type == RequestType.INVOICE:
        invoice = InvoiceRequest()
        invoice.request_id = new_request.id
        invoice.vendor_name = details.get('vendor_name', '')
        invoice.invoice_date = datetime.strptime(details['invoice_date'], '%Y-%m-%d').date() if details.get('invoice_date') else None
        db.session.add(invoice)
    
    elif request_type == RequestType.ADVANCE_PAYMENT:
        advance = AdvancePaymentRequest()
        advance.request_id = new_request.id
        advance.employee_name = current_employee.name
        advance.employee_number = current_employee.employee_id
        advance.national_id = current_employee.national_id or ''
        advance.job_title = current_employee.job_title or ''
        advance.department_name = current_employee.department.name if current_employee.department else ''
        advance.requested_amount = details.get('requested_amount', 0)
        advance.reason = details.get('reason')
        advance.installments = details.get('installments')
        advance.installment_amount = details.get('installment_amount')
        db.session.add(advance)
    
    elif request_type == RequestType.CAR_WASH:
        wash = CarWashRequest()
        wash.request_id = new_request.id
        wash.vehicle_id = details.get('vehicle_id')
        wash.service_type = details.get('service_type', 'غسيل عادي')
        wash.scheduled_date = datetime.strptime(details['scheduled_date'], '%Y-%m-%d').date() if details.get('scheduled_date') else None
        db.session.add(wash)
    
    elif request_type == RequestType.CAR_INSPECTION:
        inspection = CarInspectionRequest()
        inspection.request_id = new_request.id
        inspection.vehicle_id = details.get('vehicle_id')
        inspection.inspection_type = details.get('inspection_type', 'فحص دوري')
        inspection.inspection_date = datetime.strptime(details['inspection_date'], '%Y-%m-%d').date() if details.get('inspection_date') else datetime.now().date()
        db.session.add(inspection)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'request_id': new_request.id,
        'message': 'تم إنشاء الطلب بنجاح'
    }), 201


@api_employee_requests.route('/requests/<int:request_id>/upload', methods=['POST'])
@token_required
def upload_files(current_employee, request_id):
    """
    رفع ملفات (صور أو فيديوهات) لطلب معين
    
    Files:
    - files[]: ملفات متعددة (حتى 500MB لكل ملف)
    
    Response:
    {
        "success": true,
        "uploaded_files": [...],
        "google_drive_folder_url": "https://drive.google.com/...",
        "message": "تم رفع 3 ملفات بنجاح"
    }
    """
    import tempfile
    
    emp_request = EmployeeRequest.query.filter_by(
        id=request_id,
        employee_id=current_employee.id
    ).first()
    
    if not emp_request:
        return jsonify({
            'success': False,
            'message': 'الطلب غير موجود'
        }), 404
    
    if 'files' not in request.files:
        return jsonify({
            'success': False,
            'message': 'لا يوجد ملفات مرفقة'
        }), 400
    
    files = request.files.getlist('files')
    
    if not files:
        return jsonify({
            'success': False,
            'message': 'لا يوجد ملفات مرفقة'
        }), 400
    
    drive_uploader = EmployeeRequestsDriveUploader()
    
    if not drive_uploader.is_available():
        return jsonify({
            'success': False,
            'message': 'خدمة Google Drive غير متاحة حالياً'
        }), 503
    
    type_map = {
        RequestType.INVOICE: 'invoice',
        RequestType.CAR_WASH: 'car_wash',
        RequestType.CAR_INSPECTION: 'car_inspection',
        RequestType.ADVANCE_PAYMENT: 'advance_payment'
    }
    
    vehicle_number = None
    if emp_request.request_type in [RequestType.CAR_WASH, RequestType.CAR_INSPECTION]:
        if emp_request.request_type == RequestType.CAR_WASH and emp_request.car_wash_data and emp_request.car_wash_data.vehicle:
            vehicle_number = emp_request.car_wash_data.vehicle.plate_number
        elif emp_request.request_type == RequestType.CAR_INSPECTION and emp_request.inspection_data and emp_request.inspection_data.vehicle:
            vehicle_number = emp_request.inspection_data.vehicle.plate_number
    
    folder_result = drive_uploader.create_request_folder(
        request_type=type_map.get(emp_request.request_type, 'other'),
        request_id=emp_request.id,
        employee_name=current_employee.name,
        vehicle_number=vehicle_number
    )
    
    if not folder_result:
        return jsonify({
            'success': False,
            'message': 'فشل إنشاء مجلد على Google Drive'
        }), 500
    
    emp_request.google_drive_folder_id = folder_result['folder_id']
    emp_request.google_drive_folder_url = folder_result['folder_url']
    db.session.commit()
    
    uploaded_files = []
    
    for file in files:
        if not file.filename or file.filename == '':
            continue
        
        if not allowed_file(file.filename):
            continue
        
        if '.' not in file.filename:
            continue
        
        temp_file = None
        try:
            file_ext = file.filename.rsplit('.', 1)[1].lower()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as temp_file:
                file.save(temp_file.name)
                temp_path = temp_file.name
            
            result = None
            
            if emp_request.request_type == RequestType.INVOICE:
                result = drive_uploader.upload_invoice_image(
                    file_path=temp_path,
                    folder_id=folder_result['folder_id'],
                    custom_name=file.filename
                )
                
                if result:
                    invoice = emp_request.invoice_data
                    if invoice:
                        invoice.drive_file_id = result['file_id']
                        invoice.drive_view_url = result['view_url']
                        invoice.drive_download_url = result.get('download_url')
                        invoice.file_size = result.get('file_size')
            
            elif emp_request.request_type == RequestType.CAR_WASH:
                existing_count = len(emp_request.car_wash_data.media_files) if emp_request.car_wash_data else 0
                media_types_order = [MediaType.PLATE, MediaType.FRONT, MediaType.BACK, MediaType.RIGHT, MediaType.LEFT]
                
                if existing_count < 5:
                    media_type = media_types_order[existing_count]
                    images_dict = {media_type.value: temp_path}
                    
                    results = drive_uploader.upload_car_wash_images(
                        images_dict=images_dict,
                        folder_id=folder_result['folder_id']
                    )
                    
                    result = results.get(media_type.value)
                    
                    if result:
                        media = CarWashMedia()
                        media.wash_request_id = emp_request.car_wash_data.id
                        media.media_type = media_type
                        media.drive_file_id = result['file_id']
                        media.drive_view_url = result['view_url']
                        media.file_size = result.get('file_size')
                        db.session.add(media)
            
            elif emp_request.request_type == RequestType.CAR_INSPECTION:
                is_video = file_ext in ['mp4', 'mov', 'avi']
                inspection_file_type = FileType.VIDEO if is_video else FileType.IMAGE
                
                if is_video:
                    result = drive_uploader.upload_large_video_resumable(
                        file_path=temp_path,
                        folder_id=folder_result['folder_id'],
                        filename=file.filename
                    )
                else:
                    results = drive_uploader.upload_inspection_images_batch(
                        images_list=[temp_path],
                        folder_id=folder_result['folder_id']
                    )
                    result = results[0] if results else None
                
                if result:
                    media = CarInspectionMedia()
                    media.inspection_request_id = emp_request.inspection_data.id
                    media.file_type = inspection_file_type
                    media.drive_file_id = result['file_id']
                    media.drive_view_url = result['view_url']
                    media.drive_download_url = result.get('download_url')
                    media.original_filename = file.filename
                    media.file_size = result.get('file_size')
                    media.upload_status = 'completed'
                    media.upload_progress = 100
                    db.session.add(media)
            
            if result:
                uploaded_files.append({
                    'filename': file.filename,
                    'drive_url': result['view_url'],
                    'file_id': result['file_id']
                })
        
        except Exception as e:
            logger.error(f"Error uploading file {file.filename}: {str(e)}")
            continue
        finally:
            if temp_file and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'uploaded_files': uploaded_files,
        'google_drive_folder_url': folder_result['folder_url'],
        'message': f'تم رفع {len(uploaded_files)} ملف بنجاح إلى Google Drive'
    }), 200


@api_employee_requests.route('/requests/statistics', methods=['GET'])
@token_required
def get_statistics(current_employee):
    """
    الحصول على إحصائيات طلبات الموظف
    
    Response:
    {
        "success": true,
        "statistics": {
            "total": 45,
            "pending": 5,
            "approved": 35,
            "rejected": 3,
            "in_review": 2,
            "by_type": {...}
        }
    }
    """
    total = EmployeeRequest.query.filter_by(employee_id=current_employee.id).count()
    pending = EmployeeRequest.query.filter_by(employee_id=current_employee.id, status=RequestStatus.PENDING).count()
    approved = EmployeeRequest.query.filter_by(employee_id=current_employee.id, status=RequestStatus.APPROVED).count()
    rejected = EmployeeRequest.query.filter_by(employee_id=current_employee.id, status=RequestStatus.REJECTED).count()
    completed = EmployeeRequest.query.filter_by(employee_id=current_employee.id, status=RequestStatus.COMPLETED).count()
    closed = EmployeeRequest.query.filter_by(employee_id=current_employee.id, status=RequestStatus.CLOSED).count()
    
    by_type = {}
    for req_type in RequestType:
        count = EmployeeRequest.query.filter_by(
            employee_id=current_employee.id,
            request_type=req_type
        ).count()
        by_type[req_type.name] = count
    
    return jsonify({
        'success': True,
        'statistics': {
            'total': total,
            'pending': pending,
            'approved': approved,
            'rejected': rejected,
            'completed': completed,
            'closed': closed,
            'by_type': by_type
        }
    }), 200


@api_employee_requests.route('/requests/types', methods=['GET'])
def get_request_types():
    """
    الحصول على أنواع الطلبات المتاحة
    
    Response:
    {
        "success": true,
        "types": [
            {"value": "INVOICE", "label_ar": "فاتورة"},
            {"value": "CAR_WASH", "label_ar": "غسيل سيارة"},
            ...
        ]
    }
    """
    types = []
    type_labels = {
        'INVOICE': 'فاتورة',
        'CAR_WASH': 'غسيل سيارة',
        'CAR_INSPECTION': 'فحص وتوثيق سيارة',
        'ADVANCE_PAYMENT': 'سلفة مالية'
    }
    
    for req_type in RequestType:
        types.append({
            'value': req_type.name,
            'label_ar': type_labels.get(req_type.name, req_type.name)
        })
    
    return jsonify({
        'success': True,
        'types': types
    }), 200


@api_employee_requests.route('/vehicles', methods=['GET'])
@token_required
def get_vehicles(current_employee):
    """
    الحصول على قائمة السيارات المتاحة
    
    Response:
    {
        "success": true,
        "vehicles": [...]
    }
    """
    vehicles = Vehicle.query.filter_by(status='active').all()
    
    vehicles_list = []
    for vehicle in vehicles:
        vehicles_list.append({
            'id': vehicle.id,
            'plate_number': vehicle.plate_number,
            'make': vehicle.make,
            'model': vehicle.model,
            'year': vehicle.year,
            'color': vehicle.color
        })
    
    return jsonify({
        'success': True,
        'vehicles': vehicles_list
    }), 200


@api_employee_requests.route('/notifications', methods=['GET'])
@token_required
def get_notifications(current_employee):
    """
    الحصول على إشعارات الموظف
    
    Query Parameters:
    - unread_only: true/false (default: false)
    - page: رقم الصفحة (default: 1)
    - per_page: عدد العناصر (default: 20)
    
    Response:
    {
        "success": true,
        "notifications": [...],
        "unread_count": 5
    }
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    query = RequestNotification.query.filter_by(employee_id=current_employee.id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    pagination = query.order_by(RequestNotification.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    notifications_list = []
    for notif in pagination.items:
        notifications_list.append({
            'id': notif.id,
            'request_id': notif.request_id,
            'title': notif.title_ar,
            'message': notif.message_ar,
            'type': notif.notification_type,
            'is_read': notif.is_read,
            'created_at': notif.created_at.isoformat()
        })
    
    unread_count = RequestNotification.query.filter_by(
        employee_id=current_employee.id,
        is_read=False
    ).count()
    
    return jsonify({
        'success': True,
        'notifications': notifications_list,
        'unread_count': unread_count,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    }), 200


@api_employee_requests.route('/notifications/<int:notification_id>/read', methods=['PUT'])
@token_required
def mark_notification_read(current_employee, notification_id):
    """
    تعليم إشعار كمقروء
    
    Response:
    {
        "success": true,
        "message": "تم تعليم الإشعار كمقروء"
    }
    """
    notification = RequestNotification.query.filter_by(
        id=notification_id,
        employee_id=current_employee.id
    ).first()
    
    if not notification:
        return jsonify({
            'success': False,
            'message': 'الإشعار غير موجود'
        }), 404
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'تم تعليم الإشعار كمقروء'
    }), 200


@api_employee_requests.route('/employee/liabilities', methods=['GET'])
@token_required
def get_employee_liabilities(current_employee):
    """
    جلب الالتزامات المالية للموظف (سلف، ديون، تلفيات)
    
    Query Parameters:
    - status: 'active', 'paid', 'all'
    - type: 'advance_repayment', 'damage', 'debt', 'other'
    
    Response:
    {
        "success": true,
        "data": {
            "total_liabilities": 15000.00,
            "active_liabilities": 10000.00,
            "paid_liabilities": 5000.00,
            "liabilities": [...]
        }
    }
    """
    from services.employee_finance_service import EmployeeFinanceService
    
    status_filter = request.args.get('status', 'all')
    type_filter = request.args.get('type')
    
    try:
        liabilities_data = EmployeeFinanceService.get_employee_liabilities(
            current_employee.id,
            status_filter=status_filter,
            liability_type_filter=type_filter
        )
        
        return jsonify({
            'success': True,
            'data': liabilities_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching liabilities for employee {current_employee.id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء جلب الالتزامات المالية',
            'error': str(e)
        }), 500


@api_employee_requests.route('/employee/financial-summary', methods=['GET'])
@token_required
def get_employee_financial_summary(current_employee):
    """
    جلب الملخص المالي الشامل للموظف
    
    Response:
    {
        "success": true,
        "data": {
            "current_balance": 5000.00,
            "total_earnings": 50000.00,
            "total_deductions": 45000.00,
            "active_liabilities": 10000.00,
            "pending_requests": 3,
            "last_salary": {...},
            "upcoming_installment": {...},
            "monthly_summary": {...}
        }
    }
    """
    from services.employee_finance_service import EmployeeFinanceService
    
    try:
        summary = EmployeeFinanceService.get_financial_summary(current_employee.id)
        
        if not summary:
            return jsonify({
                'success': False,
                'message': 'الموظف غير موجود'
            }), 404
        
        return jsonify({
            'success': True,
            'data': summary
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching financial summary for employee {current_employee.id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء جلب الملخص المالي',
            'error': str(e)
        }), 500


@api_employee_requests.route('/notifications/mark-all-read', methods=['PUT'])
@token_required
def mark_all_notifications_read(current_employee):
    """
    تحديد جميع الإشعارات كمقروءة
    
    Response:
    {
        "success": true,
        "message": "تم تحديد جميع الإشعارات كمقروءة",
        "data": {
            "updated_count": 15
        }
    }
    """
    try:
        unread_notifications = RequestNotification.query.filter_by(
            employee_id=current_employee.id,
            is_read=False
        ).all()
        
        updated_count = len(unread_notifications)
        
        for notification in unread_notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديد جميع الإشعارات كمقروءة',
            'data': {
                'updated_count': updated_count,
                'unread_count': 0
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read for employee {current_employee.id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء تحديث الإشعارات',
            'error': str(e)
        }), 500
