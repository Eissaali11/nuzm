from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import (
    db, VehicleWorkshop, VehicleHandover, VehicleExternalSafetyCheck,
    EmployeeRequest, Vehicle, Employee, Department, InvoiceRequest
)
from datetime import datetime, timedelta
from sqlalchemy import or_, and_, func, case
import json

drive_browser_bp = Blueprint('drive_browser', __name__)


def get_drive_statistics():
    """حساب الإحصائيات الإجمالية لملفات Google Drive"""
    stats = {
        'total_operations': 0,
        'successful_uploads': 0,
        'failed_uploads': 0,
        'pending_uploads': 0,
        'last_upload': None,
        'vehicles_count': 0,
        'requests_count': 0
    }
    
    workshop_stats = db.session.query(
        func.count(VehicleWorkshop.id).label('total'),
        func.sum(case((VehicleWorkshop.drive_upload_status == 'success', 1), else_=0)).label('success'),
        func.sum(case((VehicleWorkshop.drive_upload_status == 'failed', 1), else_=0)).label('failed'),
        func.sum(case((VehicleWorkshop.drive_upload_status == 'pending', 1), else_=0)).label('pending'),
        func.max(VehicleWorkshop.drive_uploaded_at).label('last_upload')
    ).filter(VehicleWorkshop.drive_folder_id.isnot(None)).first()
    
    handover_stats = db.session.query(
        func.count(VehicleHandover.id).label('total'),
        func.sum(case((VehicleHandover.drive_upload_status == 'success', 1), else_=0)).label('success'),
        func.sum(case((VehicleHandover.drive_upload_status == 'failed', 1), else_=0)).label('failed'),
        func.sum(case((VehicleHandover.drive_upload_status == 'pending', 1), else_=0)).label('pending'),
        func.max(VehicleHandover.drive_uploaded_at).label('last_upload')
    ).filter(VehicleHandover.drive_folder_id.isnot(None)).first()
    
    safety_stats = db.session.query(
        func.count(VehicleExternalSafetyCheck.id).label('total'),
        func.sum(case((VehicleExternalSafetyCheck.drive_upload_status == 'success', 1), else_=0)).label('success'),
        func.sum(case((VehicleExternalSafetyCheck.drive_upload_status == 'failed', 1), else_=0)).label('failed'),
        func.sum(case((VehicleExternalSafetyCheck.drive_upload_status == 'pending', 1), else_=0)).label('pending'),
        func.max(VehicleExternalSafetyCheck.drive_uploaded_at).label('last_upload')
    ).filter(VehicleExternalSafetyCheck.drive_folder_id.isnot(None)).first()
    
    request_stats = db.session.query(
        func.count(EmployeeRequest.id).label('total'),
        func.max(EmployeeRequest.created_at).label('last_upload')
    ).filter(EmployeeRequest.google_drive_folder_id.isnot(None)).first()
    
    stats['vehicles_count'] = (workshop_stats.total or 0) + (handover_stats.total or 0) + (safety_stats.total or 0)
    stats['requests_count'] = request_stats.total or 0
    stats['total_operations'] = stats['vehicles_count'] + stats['requests_count']
    
    stats['successful_uploads'] = (workshop_stats.success or 0) + (handover_stats.success or 0) + (safety_stats.success or 0)
    stats['failed_uploads'] = (workshop_stats.failed or 0) + (handover_stats.failed or 0) + (safety_stats.failed or 0)
    stats['pending_uploads'] = (workshop_stats.pending or 0) + (handover_stats.pending or 0) + (safety_stats.pending or 0)
    
    last_uploads = [
        workshop_stats.last_upload,
        handover_stats.last_upload,
        safety_stats.last_upload,
        request_stats.last_upload
    ]
    last_uploads = [d for d in last_uploads if d is not None]
    if last_uploads:
        stats['last_upload'] = max(last_uploads)
    
    return stats


def build_unified_records(filters=None, page=1, per_page=50):
    """بناء قائمة موحدة من جميع السجلات المرفوعة على Google Drive"""
    records = []
    
    workshop_query = db.session.query(
        VehicleWorkshop.id,
        VehicleWorkshop.drive_folder_id,
        VehicleWorkshop.drive_pdf_link,
        VehicleWorkshop.drive_images_links,
        VehicleWorkshop.drive_upload_status,
        VehicleWorkshop.drive_uploaded_at,
        VehicleWorkshop.entry_date,
        Vehicle.plate_number,
        Vehicle.make,
        Vehicle.model,
        Department.name.label('department_name')
    ).join(Vehicle, VehicleWorkshop.vehicle_id == Vehicle.id
    ).outerjoin(Department, Vehicle.department_id == Department.id
    ).filter(VehicleWorkshop.drive_folder_id.isnot(None))
    
    if filters:
        if filters.get('department_id'):
            workshop_query = workshop_query.filter(Vehicle.department_id == filters['department_id'])
        if filters.get('plate_number'):
            workshop_query = workshop_query.filter(Vehicle.plate_number.like(f"%{filters['plate_number']}%"))
        if filters.get('date_from'):
            workshop_query = workshop_query.filter(VehicleWorkshop.entry_date >= filters['date_from'])
        if filters.get('date_to'):
            workshop_query = workshop_query.filter(VehicleWorkshop.entry_date <= filters['date_to'])
        if filters.get('status'):
            workshop_query = workshop_query.filter(VehicleWorkshop.drive_upload_status == filters['status'])
    
    for row in workshop_query.all():
        images_count = 0
        if row.drive_images_links:
            try:
                images_count = len(json.loads(row.drive_images_links))
            except:
                pass
        
        records.append({
            'id': row.id,
            'type': 'vehicle_workshop',
            'type_ar': 'سجل ورشة',
            'entity_name': f"{row.plate_number} - {row.make} {row.model}",
            'department': row.department_name or 'غير محدد',
            'date': row.entry_date,
            'folder_id': row.drive_folder_id,
            'folder_url': f"https://drive.google.com/drive/folders/{row.drive_folder_id}",
            'pdf_link': row.drive_pdf_link,
            'has_pdf': bool(row.drive_pdf_link),
            'images_count': images_count,
            'status': row.drive_upload_status or 'pending',
            'uploaded_at': row.drive_uploaded_at
        })
    
    handover_query = db.session.query(
        VehicleHandover.id,
        VehicleHandover.drive_folder_id,
        VehicleHandover.drive_pdf_link,
        VehicleHandover.drive_images_links,
        VehicleHandover.drive_upload_status,
        VehicleHandover.drive_uploaded_at,
        VehicleHandover.handover_date,
        VehicleHandover.handover_type,
        VehicleHandover.vehicle_plate_number,
        Department.name.label('department_name'),
        Employee.name.label('employee_name')
    ).outerjoin(Employee, VehicleHandover.employee_id == Employee.id
    ).outerjoin(Department, Employee.department_id == Department.id
    ).filter(VehicleHandover.drive_folder_id.isnot(None))
    
    if filters:
        if filters.get('department_id'):
            handover_query = handover_query.filter(Employee.department_id == filters['department_id'])
        if filters.get('plate_number'):
            handover_query = handover_query.filter(VehicleHandover.vehicle_plate_number.like(f"%{filters['plate_number']}%"))
        if filters.get('employee_name'):
            handover_query = handover_query.filter(Employee.name.ilike(f"%{filters['employee_name']}%"))
        if filters.get('date_from'):
            handover_query = handover_query.filter(VehicleHandover.handover_date >= filters['date_from'])
        if filters.get('date_to'):
            handover_query = handover_query.filter(VehicleHandover.handover_date <= filters['date_to'])
        if filters.get('status'):
            handover_query = handover_query.filter(VehicleHandover.drive_upload_status == filters['status'])
    
    for row in handover_query.all():
        images_count = 0
        if row.drive_images_links:
            try:
                images_count = len(json.loads(row.drive_images_links))
            except:
                pass
        
        type_ar = 'عملية تسليم' if row.handover_type == 'delivery' else 'عملية استلام'
        
        records.append({
            'id': row.id,
            'type': 'vehicle_handover',
            'type_ar': type_ar,
            'entity_name': row.vehicle_plate_number or 'غير محدد',
            'department': row.department_name or 'غير محدد',
            'date': row.handover_date,
            'folder_id': row.drive_folder_id,
            'folder_url': f"https://drive.google.com/drive/folders/{row.drive_folder_id}",
            'pdf_link': row.drive_pdf_link,
            'has_pdf': bool(row.drive_pdf_link),
            'images_count': images_count,
            'status': row.drive_upload_status or 'pending',
            'uploaded_at': row.drive_uploaded_at
        })
    
    safety_query = db.session.query(
        VehicleExternalSafetyCheck.id,
        VehicleExternalSafetyCheck.drive_folder_id,
        VehicleExternalSafetyCheck.drive_pdf_link,
        VehicleExternalSafetyCheck.drive_images_links,
        VehicleExternalSafetyCheck.drive_upload_status,
        VehicleExternalSafetyCheck.drive_uploaded_at,
        VehicleExternalSafetyCheck.inspection_date,
        VehicleExternalSafetyCheck.vehicle_plate_number,
        VehicleExternalSafetyCheck.driver_department,
        VehicleExternalSafetyCheck.driver_name
    ).filter(VehicleExternalSafetyCheck.drive_folder_id.isnot(None))
    
    if filters:
        if filters.get('department_id'):
            dept = Department.query.get(filters['department_id'])
            if dept:
                safety_query = safety_query.filter(VehicleExternalSafetyCheck.driver_department.ilike(f"%{dept.name}%"))
        if filters.get('plate_number'):
            safety_query = safety_query.filter(VehicleExternalSafetyCheck.vehicle_plate_number.like(f"%{filters['plate_number']}%"))
        if filters.get('employee_name'):
            safety_query = safety_query.filter(VehicleExternalSafetyCheck.driver_name.ilike(f"%{filters['employee_name']}%"))
        if filters.get('date_from'):
            safety_query = safety_query.filter(VehicleExternalSafetyCheck.inspection_date >= filters['date_from'])
        if filters.get('date_to'):
            safety_query = safety_query.filter(VehicleExternalSafetyCheck.inspection_date <= filters['date_to'])
        if filters.get('status'):
            safety_query = safety_query.filter(VehicleExternalSafetyCheck.drive_upload_status == filters['status'])
    
    for row in safety_query.all():
        images_count = 0
        if row.drive_images_links:
            try:
                images_count = len(json.loads(row.drive_images_links))
            except:
                pass
        
        records.append({
            'id': row.id,
            'type': 'vehicle_safety',
            'type_ar': 'فحص سلامة',
            'entity_name': f"{row.vehicle_plate_number} - {row.driver_name}" if row.driver_name else row.vehicle_plate_number or 'غير محدد',
            'department': row.driver_department or 'غير محدد',
            'date': row.inspection_date,
            'folder_id': row.drive_folder_id,
            'folder_url': f"https://drive.google.com/drive/folders/{row.drive_folder_id}",
            'pdf_link': row.drive_pdf_link,
            'has_pdf': bool(row.drive_pdf_link),
            'images_count': images_count,
            'status': row.drive_upload_status or 'pending',
            'uploaded_at': row.drive_uploaded_at
        })
    
    request_query = db.session.query(
        EmployeeRequest.id,
        EmployeeRequest.google_drive_folder_id,
        EmployeeRequest.google_drive_folder_url,
        EmployeeRequest.request_type,
        EmployeeRequest.status,
        EmployeeRequest.created_at,
        Employee.name.label('employee_name'),
        Employee.employee_id.label('employee_number'),
        Department.name.label('department_name'),
        InvoiceRequest.local_image_path.label('invoice_local_path')
    ).join(Employee, EmployeeRequest.employee_id == Employee.id
    ).outerjoin(Department, Employee.department_id == Department.id
    ).outerjoin(InvoiceRequest, InvoiceRequest.request_id == EmployeeRequest.id)
    
    if filters:
        if filters.get('department_id'):
            request_query = request_query.filter(Employee.department_id == filters['department_id'])
        if filters.get('employee_name'):
            request_query = request_query.filter(Employee.name.like(f"%{filters['employee_name']}%"))
        if filters.get('date_from'):
            request_query = request_query.filter(EmployeeRequest.created_at >= filters['date_from'])
        if filters.get('date_to'):
            request_query = request_query.filter(EmployeeRequest.created_at <= filters['date_to'])
        if filters.get('request_type'):
            request_query = request_query.filter(EmployeeRequest.request_type == filters['request_type'])
    
    request_type_names = {
        'INVOICE': 'فاتورة',
        'invoice': 'فاتورة',
        'CAR_WASH': 'غسيل سيارة',
        'car_wash': 'غسيل سيارة',
        'CAR_INSPECTION': 'فحص وتوثيق',
        'car_inspection': 'فحص وتوثيق',
        'ADVANCE_PAYMENT': 'سلفة',
        'advance_payment': 'سلفة'
    }
    
    request_status_names = {
        'PENDING': 'قيد الانتظار',
        'pending': 'قيد الانتظار',
        'APPROVED': 'موافق عليها',
        'approved': 'موافق عليها',
        'REJECTED': 'مرفوضة',
        'rejected': 'مرفوضة'
    }
    
    for row in request_query.all():
        has_drive = bool(row.google_drive_folder_id)
        drive_status = 'success' if has_drive else 'local_only'
        
        local_file_path = row.invoice_local_path if hasattr(row, 'invoice_local_path') else None
        
        folder_url = None
        if row.google_drive_folder_url:
            folder_url = row.google_drive_folder_url
        elif row.google_drive_folder_id:
            folder_url = f"https://drive.google.com/drive/folders/{row.google_drive_folder_id}"
        
        request_type_str = row.request_type if isinstance(row.request_type, str) else row.request_type.name
        status_str = row.status if isinstance(row.status, str) else row.status.name
        
        records.append({
            'id': row.id,
            'type': 'employee_request',
            'type_ar': request_type_names.get(request_type_str, request_type_str),
            'entity_name': f"{row.employee_name} ({row.employee_number})",
            'department': row.department_name or 'غير محدد',
            'date': row.created_at,
            'folder_id': row.google_drive_folder_id,
            'folder_url': folder_url,
            'pdf_link': None,
            'has_pdf': False,
            'images_count': 1 if local_file_path else 0,
            'status': drive_status,
            'uploaded_at': row.created_at,
            'local_file_path': local_file_path,
            'request_status': request_status_names.get(status_str, status_str)
        })
    
    records.sort(key=lambda x: x['date'] if x['date'] else datetime.min, reverse=True)
    
    total = len(records)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_records = records[start:end]
    
    return paginated_records, total


@drive_browser_bp.route('/browser')
@login_required
def browser():
    """الصفحة الرئيسية لمستعرض ملفات Google Drive"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    filters = {}
    if request.args.get('department_id'):
        filters['department_id'] = int(request.args.get('department_id'))
    if request.args.get('plate_number'):
        filters['plate_number'] = request.args.get('plate_number')
    if request.args.get('employee_name'):
        filters['employee_name'] = request.args.get('employee_name')
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('request_type'):
        filters['request_type'] = request.args.get('request_type')
    if request.args.get('date_from'):
        try:
            filters['date_from'] = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d')
        except:
            pass
    if request.args.get('date_to'):
        try:
            filters['date_to'] = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d')
        except:
            pass
    
    stats = get_drive_statistics()
    
    records, total = build_unified_records(filters, page, per_page)
    
    total_pages = (total + per_page - 1) // per_page
    
    departments = Department.query.order_by(Department.name).all()
    
    return render_template(
        'drive_browser/index.html',
        stats=stats,
        records=records,
        departments=departments,
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        filters=filters
    )


@drive_browser_bp.route('/retry-upload/<record_type>/<int:record_id>')
@login_required
def retry_upload(record_type, record_id):
    """إعادة محاولة رفع ملف فشل رفعه"""
    from utils.vehicle_drive_uploader import VehicleDriveUploader
    
    try:
        if record_type == 'vehicle_workshop':
            record = VehicleWorkshop.query.get_or_404(record_id)
            VehicleDriveUploader.upload_workshop_record(record)
            db.session.commit()
            flash('تم إعادة محاولة رفع سجل الورشة بنجاح', 'success')
            
        elif record_type == 'vehicle_handover':
            record = VehicleHandover.query.get_or_404(record_id)
            VehicleDriveUploader.upload_handover_record(record)
            db.session.commit()
            flash('تم إعادة محاولة رفع عملية التسليم/الاستلام بنجاح', 'success')
            
        elif record_type == 'vehicle_safety':
            record = VehicleExternalSafetyCheck.query.get_or_404(record_id)
            VehicleDriveUploader.upload_safety_check(record)
            db.session.commit()
            flash('تم إعادة محاولة رفع فحص السلامة بنجاح', 'success')
        else:
            flash('نوع السجل غير صحيح', 'error')
            
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'error')
    
    return redirect(url_for('drive_browser.browser'))
