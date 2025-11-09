import os
import jwt
from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user
from werkzeug.security import check_password_hash
from functools import wraps
from datetime import datetime, timedelta
from app import db
from models import (
    User, Employee, EmployeeRequest, InvoiceRequest, AdvancePaymentRequest,
    CarWashRequest, CarInspectionRequest, CarWashMedia, CarInspectionMedia,
    RequestNotification, RequestStatus, RequestType, Vehicle, MediaType, FileType
)
from utils.employee_requests_drive_uploader import EmployeeRequestsDriveUploader
from werkzeug.utils import secure_filename
import uuid

api_employee_requests = Blueprint('api_employee_requests', __name__, url_prefix='/api/v1')

SECRET_KEY = os.environ.get('SESSION_SECRET', 'your-secret-key-here')
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
        "uploaded_files": [
            {
                "filename": "image1.jpg",
                "drive_url": "https://drive.google.com/..."
            }
        ],
        "message": "تم رفع 3 ملفات بنجاح"
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
    
    uploaded_files = []
    drive_uploader = EmployeeRequestsDriveUploader()
    
    for file in files:
        if not file.filename or file.filename == '':
            continue
        
        if not allowed_file(file.filename):
            continue
        
        if '.' not in file.filename:
            continue
        
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        file_type = 'image' if file_ext in ['png', 'jpg', 'jpeg', 'heic'] else 'video' if file_ext in ['mp4', 'mov', 'avi'] else 'document'
        
        try:
            if emp_request.request_type == RequestType.INVOICE:
                result = drive_uploader.upload_invoice_file(
                    emp_request,
                    file,
                    current_employee.name
                )
                
                if result['success']:
                    invoice = emp_request.invoice_data
                    if invoice:
                        invoice.drive_file_id = result['file_id']
                        invoice.drive_view_url = result['view_url']
                        invoice.drive_download_url = result['download_url']
                        invoice.file_size = len(file.read())
                        file.seek(0)
                        
                        uploaded_files.append({
                            'filename': file.filename,
                            'drive_url': result['view_url']
                        })
            
            elif emp_request.request_type == RequestType.CAR_WASH:
                media_types_order = [MediaType.PLATE, MediaType.FRONT, MediaType.BACK, MediaType.RIGHT, MediaType.LEFT]
                existing_count = len(emp_request.car_wash_data.media_files)
                
                if existing_count < 5:
                    media_type = media_types_order[existing_count]
                    
                    result = drive_uploader.upload_car_wash_media(
                        emp_request.car_wash_data,
                        file,
                        media_type.value,
                        current_employee.name
                    )
                    
                    if result['success']:
                        media = CarWashMedia()
                        media.wash_request_id = emp_request.car_wash_data.id
                        media.media_type = media_type
                        media.drive_file_id = result['file_id']
                        media.drive_view_url = result['view_url']
                        db.session.add(media)
                        
                        uploaded_files.append({
                            'filename': file.filename,
                            'drive_url': result['view_url']
                        })
            
            elif emp_request.request_type == RequestType.CAR_INSPECTION:
                inspection_file_type = FileType.IMAGE if file_ext in ['png', 'jpg', 'jpeg', 'heic'] else FileType.VIDEO
                
                result = drive_uploader.upload_inspection_media(
                    emp_request.inspection_data,
                    file,
                    inspection_file_type.value,
                    current_employee.name
                )
                
                if result['success']:
                    media = CarInspectionMedia()
                    media.inspection_request_id = emp_request.inspection_data.id
                    media.file_type = inspection_file_type
                    media.drive_file_id = result['file_id']
                    media.drive_view_url = result['view_url']
                    media.drive_download_url = result.get('download_url')
                    media.original_filename = file.filename
                    db.session.add(media)
                    
                    uploaded_files.append({
                        'filename': file.filename,
                        'drive_url': result['view_url']
                    })
        
        except Exception as e:
            print(f"Error uploading file {file.filename}: {str(e)}")
            continue
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'uploaded_files': uploaded_files,
        'message': f'تم رفع {len(uploaded_files)} ملف بنجاح'
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
