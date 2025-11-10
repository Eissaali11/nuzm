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
        "employee_id": "5216",
        "national_id": "1234567890"
    }
    
    Response:
    {
        "success": true,
        "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "employee": {
            "id": 1,
            "employee_id": "5216",
            "name": "أحمد محمد",
            "email": "ahmad@example.com"
        }
    }
    """
    data = request.get_json()
    
    if not data or not data.get('employee_id') or not data.get('national_id'):
        return jsonify({
            'success': False,
            'message': 'رقم الموظف ورقم الهوية مطلوبان'
        }), 400
    
    from sqlalchemy import text
    
    try:
        result = db.session.execute(text("""
            SELECT id FROM employee 
            WHERE national_id::text = :national_id 
            AND employee_id::text = :employee_id
            AND status = 'active'
            LIMIT 1
        """), {
            'national_id': data['national_id'],
            'employee_id': data['employee_id']
        }).fetchone()
        
        employee = Employee.query.get(result[0]) if result else None
        
    except Exception as e:
        logger.error(f"Database error during login: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء تسجيل الدخول'
        }), 500
    
    if not employee:
        return jsonify({
            'success': False,
            'message': 'بيانات الدخول غير صحيحة أو الحساب غير نشط'
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
            'profile_image': employee.profile_image,
            'mobile': employee.mobile,
            'status': employee.status
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
    
    type_names = {
        'INVOICE': 'فاتورة',
        'CAR_WASH': 'غسيل سيارة',
        'CAR_INSPECTION': 'فحص وتوثيق',
        'ADVANCE_PAYMENT': 'سلفة مالية'
    }
    
    status_names = {
        'PENDING': 'قيد الانتظار',
        'APPROVED': 'موافق عليها',
        'REJECTED': 'مرفوضة'
    }
    
    requests_list = []
    for req in pagination.items:
        request_data = {
            'id': req.id,
            'type': req.request_type.name,
            'type_display': type_names.get(req.request_type.name, req.request_type.name),
            'status': req.status.name,
            'status_display': status_names.get(req.status.name, req.status.name),
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
    
    type_names = {
        'INVOICE': 'فاتورة',
        'CAR_WASH': 'غسيل سيارة',
        'CAR_INSPECTION': 'فحص وتوثيق',
        'ADVANCE_PAYMENT': 'سلفة مالية'
    }
    
    status_names = {
        'PENDING': 'قيد الانتظار',
        'APPROVED': 'موافق عليها',
        'REJECTED': 'مرفوضة'
    }
    
    request_data = {
        'id': emp_request.id,
        'type': emp_request.request_type.name,
        'type_display': type_names.get(emp_request.request_type.name, emp_request.request_type.name),
        'status': emp_request.status.name,
        'status_display': status_names.get(emp_request.status.name, emp_request.status.name),
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
    
    vehicle_number_str = vehicle_number if vehicle_number else ''
    
    folder_result = drive_uploader.create_request_folder(
        request_type=type_map.get(emp_request.request_type, 'other'),
        request_id=emp_request.id,
        employee_name=current_employee.name,
        vehicle_number=vehicle_number_str
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
        temp_path = None
        try:
            file_ext = file.filename.rsplit('.', 1)[1].lower()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as temp_file:
                file.save(temp_file.name)
                temp_path = temp_file.name
            
            result = None
            local_path = None
            
            if emp_request.request_type == RequestType.INVOICE:
                from werkzeug.utils import secure_filename
                import shutil
                
                safe_filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{timestamp}_{safe_filename}"
                local_path = os.path.join('uploads', 'invoices', unique_filename)
                full_path = os.path.join('static', local_path)
                
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                shutil.copy(temp_path, full_path)
                
                result = drive_uploader.upload_invoice_image(
                    file_path=temp_path,
                    folder_id=folder_result['folder_id'],
                    custom_name=file.filename
                )
                
                invoice = emp_request.invoice_data
                if invoice:
                    invoice.local_image_path = local_path
                    if result:
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
            if temp_path and os.path.exists(temp_path):
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
            'request_id': notif.request_id if notif.request_id else None,
            'title': notif.title_ar if notif.title_ar else '',
            'message': notif.message_ar if notif.message_ar else '',
            'type': notif.notification_type if notif.notification_type else '',
            'is_read': notif.is_read if notif.is_read is not None else False,
            'created_at': notif.created_at.isoformat() if notif.created_at else datetime.utcnow().isoformat()
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
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
        
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


@api_employee_requests.route('/requests/create-advance-payment', methods=['POST'])
@token_required
def create_advance_payment_request(current_employee):
    """
    إنشاء طلب سلفة جديد مع validation محسّن
    
    Body:
    {
        "requested_amount": 5000.00,
        "installments": 3,
        "reason": "سبب الطلب (اختياري)"
    }
    
    Response:
    {
        "success": true,
        "message": "تم إنشاء طلب السلفة بنجاح",
        "data": {
            "request_id": 123,
            "type": "advance_payment",
            "status": "pending",
            "requested_amount": 5000.00,
            "installments": 3,
            "monthly_installment": 1666.67
        }
    }
    """
    from services.employee_finance_service import EmployeeFinanceService
    
    data = request.get_json()
    
    if not data or not data.get('requested_amount') or not data.get('installments'):
        return jsonify({
            'success': False,
            'message': 'المبلغ وعدد الأقساط مطلوبان'
        }), 400
    
    requested_amount = float(data.get('requested_amount'))
    installments = int(data.get('installments'))
    reason = data.get('reason', '')
    
    is_valid, message = EmployeeFinanceService.validate_advance_payment_request(
        current_employee.id,
        requested_amount,
        installments
    )
    
    if not is_valid:
        return jsonify({
            'success': False,
            'message': message
        }), 400
    
    try:
        new_request = EmployeeRequest()
        new_request.employee_id = current_employee.id
        new_request.request_type = RequestType.ADVANCE_PAYMENT
        new_request.title = f"طلب سلفة - {requested_amount} ريال"
        new_request.status = RequestStatus.PENDING
        new_request.amount = requested_amount
        
        db.session.add(new_request)
        db.session.flush()
        
        monthly_installment = requested_amount / installments
        
        advance_payment = AdvancePaymentRequest()
        advance_payment.request_id = new_request.id
        advance_payment.employee_name = current_employee.name
        advance_payment.employee_number = current_employee.employee_id
        advance_payment.national_id = current_employee.national_id
        advance_payment.job_title = current_employee.job_title or ''
        advance_payment.department_name = current_employee.department.name if current_employee.department else ''
        advance_payment.requested_amount = requested_amount
        advance_payment.installments = installments
        advance_payment.installment_amount = monthly_installment
        advance_payment.reason = reason
        
        db.session.add(advance_payment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إنشاء طلب السلفة بنجاح',
            'data': {
                'request_id': new_request.id,
                'type': 'advance_payment',
                'status': 'pending',
                'requested_amount': requested_amount,
                'installments': installments,
                'monthly_installment': round(monthly_installment, 2)
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating advance payment request for employee {current_employee.id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء إنشاء الطلب',
            'error': str(e)
        }), 500


@api_employee_requests.route('/requests/create-invoice', methods=['POST'])
@token_required
def create_invoice_request(current_employee):
    """
    رفع فاتورة مع صورة
    
    Form Data:
    - vendor_name: اسم المورد
    - amount: المبلغ
    - invoice_image: ملف الصورة (JPEG/PNG/PDF)
    
    Response:
    {
        "success": true,
        "message": "تم رفع الفاتورة بنجاح",
        "data": {
            "request_id": 124,
            "type": "invoice",
            "status": "pending"
        }
    }
    """
    logger.info(f"📤 Create invoice request - Files: {list(request.files.keys())}, Form: {list(request.form.keys())}")
    
    if not request.files or 'invoice_image' not in request.files:
        logger.warning(f"❌ Invoice image missing - Available files: {list(request.files.keys())}")
        return jsonify({
            'success': False,
            'message': 'صورة الفاتورة مطلوبة',
            'debug': {
                'received_files': list(request.files.keys()),
                'expected': 'invoice_image'
            }
        }), 400
    
    vendor_name = request.form.get('vendor_name')
    amount = request.form.get('amount')
    
    if not vendor_name or not amount:
        logger.warning(f"❌ Missing fields - vendor_name: {vendor_name}, amount: {amount}")
        return jsonify({
            'success': False,
            'message': 'اسم المورد والمبلغ مطلوبان',
            'debug': {
                'vendor_name': vendor_name,
                'amount': amount,
                'received_form_fields': list(request.form.keys())
            }
        }), 400
    
    invoice_image = request.files['invoice_image']
    
    if not allowed_file(invoice_image.filename):
        return jsonify({
            'success': False,
            'message': 'نوع الملف غير مدعوم. استخدم: PNG, JPG, JPEG, PDF'
        }), 400
    
    try:
        new_request = EmployeeRequest()
        new_request.employee_id = current_employee.id
        new_request.request_type = RequestType.INVOICE
        new_request.title = f"فاتورة - {vendor_name}"
        new_request.status = RequestStatus.PENDING
        new_request.amount = float(amount)
        
        db.session.add(new_request)
        db.session.flush()
        
        invoice_request = InvoiceRequest()
        invoice_request.request_id = new_request.id
        invoice_request.vendor_name = vendor_name
        
        db.session.add(invoice_request)
        db.session.flush()
        
        # حفظ الصورة محلياً
        if not invoice_image.filename:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'اسم الملف غير صالح'
            }), 400
        
        filename = secure_filename(invoice_image.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{new_request.id}_{timestamp}_{filename}"
        
        upload_folder = os.path.join('static', 'uploads', 'invoices')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, unique_filename)
        invoice_image.save(file_path)
        
        # حفظ المسار في قاعدة البيانات
        relative_path = os.path.join('uploads', 'invoices', unique_filename)
        invoice_request.local_image_path = relative_path
        
        logger.info(f"✅ Image saved locally: {file_path}")
        logger.info(f"✅ Relative path saved to DB: {relative_path}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم رفع الفاتورة بنجاح',
            'data': {
                'request_id': new_request.id,
                'type': 'invoice',
                'status': 'pending',
                'vendor_name': vendor_name,
                'amount': float(amount),
                'image_saved': True,
                'local_path': relative_path
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating invoice request for employee {current_employee.id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء إنشاء طلب الفاتورة',
            'error': str(e)
        }), 500


@api_employee_requests.route('/requests/create-car-wash', methods=['POST'])
@token_required
def create_car_wash_request(current_employee):
    """
    إنشاء طلب غسيل سيارة مع صور
    
    Form Data:
    - vehicle_id: رقم السيارة
    - service_type: نوع الخدمة (normal, polish, full_clean)
    - requested_date: التاريخ المطلوب (اختياري)
    - photo_plate: صورة اللوحة
    - photo_front: صورة أمامية
    - photo_back: صورة خلفية
    - photo_right_side: صورة جانب أيمن
    - photo_left_side: صورة جانب أيسر
    - notes: ملاحظات (اختياري)
    
    Response:
    {
        "success": true,
        "message": "تم إنشاء طلب الغسيل بنجاح",
        "data": {
            "request_id": 125,
            "type": "car_wash",
            "status": "pending"
        }
    }
    """
    vehicle_id = request.form.get('vehicle_id')
    service_type = request.form.get('service_type')
    
    if not vehicle_id or not service_type:
        return jsonify({
            'success': False,
            'message': 'رقم السيارة ونوع الخدمة مطلوبان'
        }), 400
    
    valid_service_types = ['normal', 'polish', 'full_clean']
    if service_type not in valid_service_types:
        return jsonify({
            'success': False,
            'message': f'نوع الخدمة غير صحيح. الأنواع المتاحة: {", ".join(valid_service_types)}'
        }), 400
    
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        return jsonify({
            'success': False,
            'message': 'السيارة غير موجودة'
        }), 404
    
    try:
        new_request = EmployeeRequest()
        new_request.employee_id = current_employee.id
        new_request.request_type = RequestType.CAR_WASH
        new_request.title = f"طلب غسيل سيارة - {vehicle.plate_number}"
        new_request.status = RequestStatus.PENDING
        
        db.session.add(new_request)
        db.session.flush()
        
        requested_date_str = request.form.get('requested_date')
        requested_date = datetime.strptime(requested_date_str, '%Y-%m-%d').date() if requested_date_str else None
        
        car_wash_request = CarWashRequest()
        car_wash_request.request_id = new_request.id
        car_wash_request.vehicle_id = vehicle_id
        car_wash_request.service_type = service_type
        car_wash_request.scheduled_date = requested_date
        
        db.session.add(car_wash_request)
        
        required_photos = ['photo_plate', 'photo_front', 'photo_back', 'photo_right_side', 'photo_left_side']
        upload_dir = os.path.join('static', 'uploads', 'car_wash')
        os.makedirs(upload_dir, exist_ok=True)
        
        for photo_field in required_photos:
            if photo_field in request.files:
                photo_file = request.files[photo_field]
                if photo_file and photo_file.filename and allowed_file(photo_file.filename):
                    filename = secure_filename(photo_file.filename)
                    file_ext = filename.rsplit('.', 1)[1].lower()
                    unique_filename = f"wash_{new_request.id}_{photo_field}_{uuid.uuid4().hex[:8]}.{file_ext}"
                    file_path = os.path.join(upload_dir, unique_filename)
                    photo_file.save(file_path)
                    
                    media_type_map = {
                        'photo_plate': MediaType.PLATE,
                        'photo_front': MediaType.FRONT,
                        'photo_back': MediaType.BACK,
                        'photo_right_side': MediaType.RIGHT,
                        'photo_left_side': MediaType.LEFT
                    }
                    
                    car_wash_media = CarWashMedia()
                    car_wash_media.wash_request_id = car_wash_request.id
                    car_wash_media.media_type = media_type_map[photo_field]
                    db.session.add(car_wash_media)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إنشاء طلب الغسيل بنجاح',
            'data': {
                'request_id': new_request.id,
                'type': 'car_wash',
                'status': 'pending',
                'vehicle_plate': vehicle.plate_number,
                'service_type': service_type
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating car wash request for employee {current_employee.id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء إنشاء طلب الغسيل',
            'error': str(e)
        }), 500


@api_employee_requests.route('/requests/create-car-inspection', methods=['POST'])
@token_required
def create_car_inspection_request(current_employee):
    """
    إنشاء طلب فحص وتوثيق سيارة
    
    Body:
    {
        "vehicle_id": 456,
        "inspection_type": "delivery",  // 'delivery' or 'receipt'
        "description": "وصف الفحص (اختياري)"
    }
    
    Response:
    {
        "success": true,
        "message": "تم إنشاء طلب الفحص بنجاح",
        "data": {
            "request_id": 126,
            "type": "car_inspection",
            "status": "pending",
            "upload_instructions": {...}
        }
    }
    """
    data = request.get_json()
    
    if not data or not data.get('vehicle_id') or not data.get('inspection_type'):
        return jsonify({
            'success': False,
            'message': 'رقم السيارة ونوع الفحص مطلوبان'
        }), 400
    
    vehicle_id = data.get('vehicle_id')
    inspection_type = data.get('inspection_type')
    
    if inspection_type not in ['delivery', 'receipt']:
        return jsonify({
            'success': False,
            'message': 'نوع الفحص غير صحيح. الأنواع المتاحة: delivery, receipt'
        }), 400
    
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        return jsonify({
            'success': False,
            'message': 'السيارة غير موجودة'
        }), 404
    
    try:
        inspection_type_ar = 'فحص تسليم' if inspection_type == 'delivery' else 'فحص استلام'
        
        new_request = EmployeeRequest()
        new_request.employee_id = current_employee.id
        new_request.request_type = RequestType.CAR_INSPECTION
        new_request.title = f"{inspection_type_ar} - {vehicle.plate_number}"
        new_request.status = RequestStatus.PENDING
        
        db.session.add(new_request)
        db.session.flush()
        
        car_inspection_request = CarInspectionRequest()
        car_inspection_request.request_id = new_request.id
        car_inspection_request.vehicle_id = vehicle_id
        car_inspection_request.inspection_type = inspection_type
        
        db.session.add(car_inspection_request)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إنشاء طلب الفحص بنجاح',
            'data': {
                'request_id': new_request.id,
                'type': 'car_inspection',
                'status': 'pending',
                'inspection_type': inspection_type,
                'inspection_type_ar': inspection_type_ar,
                'vehicle_plate': vehicle.plate_number,
                'upload_instructions': {
                    'max_images': 20,
                    'max_videos': 3,
                    'max_image_size_mb': 10,
                    'max_video_size_mb': 500,
                    'supported_formats': {
                        'images': ['jpg', 'jpeg', 'png', 'heic'],
                        'videos': ['mp4', 'mov']
                    },
                    'upload_endpoint': f'/api/v1/requests/{new_request.id}/upload'
                }
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating car inspection request for employee {current_employee.id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء إنشاء طلب الفحص',
            'error': str(e)
        }), 500


@api_employee_requests.route('/employee/complete-profile', methods=['POST'])
@token_required
def get_employee_complete_profile_jwt(current_employee):
    """
    جلب الملف الشامل للموظف (محمي بـ JWT)
    يتضمن جميع المعلومات: الموظف، السيارات، الحضور، الرواتب، العمليات، الإحصائيات
    
    Headers:
        Authorization: Bearer {jwt_token}
    
    Request Body (Optional):
        {
            "month": "2025-01",  // شهر محدد
            "start_date": "2025-01-01",  // أو تاريخ محدد
            "end_date": "2025-01-31"
        }
    
    Response:
        {
            "success": true,
            "message": "تم جلب البيانات بنجاح",
            "data": {
                "employee": {...},
                "current_car": {...},
                "previous_cars": [...],
                "attendance": [...],
                "salaries": [...],
                "operations": [...],
                "statistics": {...}
            }
        }
    """
    try:
        from routes.api_external import (
            parse_date_filters, get_employee_data, get_vehicle_assignments,
            get_attendance_records, get_salary_records, get_operations_records,
            calculate_statistics
        )
        
        # الحصول على البيانات (اختياري)
        data = request.get_json() or {}
        
        # تحليل فلاتر التواريخ
        try:
            start_date, end_date = parse_date_filters(data)
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': 'طلب غير صحيح',
                'error': str(e)
            }), 400
        
        # جلب معلومات الموظف
        request_origin = request.host_url.rstrip('/')
        employee_data = get_employee_data(current_employee, request_origin)
        
        # جلب السيارات
        current_car, previous_cars = get_vehicle_assignments(current_employee.id)
        
        # جلب الحضور
        attendance = get_attendance_records(current_employee.id, start_date, end_date)
        
        # جلب الرواتب
        salaries = get_salary_records(current_employee.id, start_date, end_date)
        
        # جلب العمليات
        operations = get_operations_records(current_employee.id)
        
        # حساب الإحصائيات
        statistics = calculate_statistics(attendance, salaries, current_car, previous_cars, operations)
        
        # بناء الاستجابة
        response_data = {
            'employee': employee_data,
            'current_car': current_car,
            'previous_cars': previous_cars,
            'attendance': attendance,
            'salaries': salaries,
            'operations': operations,
            'statistics': statistics
        }
        
        logger.info(f"✅ تم جلب الملف الشامل للموظف {current_employee.name} ({current_employee.employee_id}) عبر JWT")
        
        return jsonify({
            'success': True,
            'message': 'تم جلب البيانات بنجاح',
            'data': response_data
        }), 200
        
    except Exception as e:
        logger.error(f"خطأ في جلب الملف الشامل للموظف: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'خطأ في السيرفر',
            'error': str(e)
        }), 500


@api_employee_requests.route('/requests/<int:request_id>', methods=['DELETE'])
@token_required
def delete_request(current_employee, request_id):
    """
    حذف طلب موظف
    
    DELETE /api/v1/requests/{request_id}
    
    Returns:
        200: تم الحذف بنجاح
        403: ليس لديك صلاحية
        404: الطلب غير موجود
    """
    try:
        emp_request = EmployeeRequest.query.get(request_id)
        
        if not emp_request:
            return jsonify({
                'success': False,
                'message': 'الطلب غير موجود'
            }), 404
        
        # التحقق من أن الطلب يخص الموظف الحالي
        if emp_request.employee_id != current_employee.id:
            return jsonify({
                'success': False,
                'message': 'ليس لديك صلاحية لحذف هذا الطلب'
            }), 403
        
        # حذف الطلب
        db.session.delete(emp_request)
        db.session.commit()
        
        logger.info(f"✅ تم حذف الطلب #{request_id} بواسطة {current_employee.name}")
        
        return jsonify({
            'success': True,
            'message': 'تم حذف الطلب بنجاح'
        }), 200
        
    except Exception as e:
        logger.error(f"خطأ في حذف الطلب: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'خطأ في السيرفر',
            'error': str(e)
        }), 500
