from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from models import (
    EmployeeRequest, InvoiceRequest, AdvancePaymentRequest,
    CarWashRequest, CarInspectionRequest, EmployeeLiability,
    RequestNotification, Employee, RequestStatus, RequestType,
    UserRole, Module, Vehicle
)
from datetime import datetime
from sqlalchemy import desc, or_, and_
from utils.employee_requests_drive_uploader import EmployeeRequestsDriveUploader
import os
import logging

logger = logging.getLogger(__name__)

employee_requests = Blueprint('employee_requests', __name__, url_prefix='/employee-requests')


def check_access():
    if current_user.role != UserRole.ADMIN:
        return False
    return True


@employee_requests.route('/')
@login_required
def index():
    if not check_access():
        flash('ليس لديك صلاحية الوصول إلى هذا القسم', 'error')
        return redirect(url_for('dashboard'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    status_filter = request.args.get('status', '')
    type_filter = request.args.get('type', '')
    employee_filter = request.args.get('employee_id', '')
    
    query = EmployeeRequest.query
    
    if status_filter:
        query = query.filter_by(status=RequestStatus[status_filter])
    
    if type_filter:
        query = query.filter_by(request_type=RequestType[type_filter])
    
    if employee_filter:
        query = query.filter_by(employee_id=int(employee_filter))
    
    requests_pagination = query.order_by(desc(EmployeeRequest.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    employees = Employee.query.all()
    
    stats = {
        'total': EmployeeRequest.query.count(),
        'pending': EmployeeRequest.query.filter_by(status=RequestStatus.PENDING).count(),
        'approved': EmployeeRequest.query.filter_by(status=RequestStatus.APPROVED).count(),
        'rejected': EmployeeRequest.query.filter_by(status=RequestStatus.REJECTED).count(),
    }
    
    return render_template('employee_requests/index.html',
                         requests=requests_pagination.items,
                         pagination=requests_pagination,
                         employees=employees,
                         stats=stats,
                         RequestStatus=RequestStatus,
                         RequestType=RequestType)


@employee_requests.route('/<int:request_id>')
@login_required
def view_request(request_id):
    if not check_access():
        flash('ليس لديك صلاحية الوصول إلى هذا القسم', 'error')
        return redirect(url_for('dashboard'))
    
    emp_request = EmployeeRequest.query.get_or_404(request_id)
    
    specific_request = None
    if emp_request.request_type == RequestType.INVOICE:
        specific_request = InvoiceRequest.query.filter_by(request_id=request_id).first()
    elif emp_request.request_type == RequestType.CAR_WASH:
        specific_request = CarWashRequest.query.filter_by(request_id=request_id).first()
    elif emp_request.request_type == RequestType.CAR_INSPECTION:
        specific_request = CarInspectionRequest.query.filter_by(request_id=request_id).first()
    elif emp_request.request_type == RequestType.ADVANCE_PAYMENT:
        specific_request = AdvancePaymentRequest.query.filter_by(request_id=request_id).first()
    
    return render_template('employee_requests/view.html',
                         emp_request=emp_request,
                         specific_request=specific_request,
                         RequestType=RequestType,
                         RequestStatus=RequestStatus)


@employee_requests.route('/<int:request_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_request(request_id):
    if not check_access():
        flash('ليس لديك صلاحية الوصول إلى هذا القسم', 'error')
        return redirect(url_for('dashboard'))
    
    emp_request = EmployeeRequest.query.get_or_404(request_id)
    
    if request.method == 'POST':
        emp_request.title = request.form.get('title')
        emp_request.description = request.form.get('description')
        emp_request.amount = float(request.form.get('amount', 0))
        
        if emp_request.request_type == RequestType.INVOICE:
            invoice = emp_request.invoice_data
            if invoice:
                invoice.vendor_name = request.form.get('vendor_name')
        
        try:
            db.session.commit()
            flash('تم تحديث الطلب بنجاح', 'success')
            return redirect(url_for('employee_requests.view_request', request_id=request_id))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء التحديث: {str(e)}', 'error')
    
    specific_request = None
    if emp_request.request_type == RequestType.INVOICE:
        specific_request = InvoiceRequest.query.filter_by(request_id=request_id).first()
    elif emp_request.request_type == RequestType.CAR_WASH:
        specific_request = CarWashRequest.query.filter_by(request_id=request_id).first()
    elif emp_request.request_type == RequestType.CAR_INSPECTION:
        specific_request = CarInspectionRequest.query.filter_by(request_id=request_id).first()
    elif emp_request.request_type == RequestType.ADVANCE_PAYMENT:
        specific_request = AdvancePaymentRequest.query.filter_by(request_id=request_id).first()
    
    return render_template('employee_requests/edit.html',
                         emp_request=emp_request,
                         specific_request=specific_request,
                         RequestType=RequestType,
                         RequestStatus=RequestStatus)


@employee_requests.route('/<int:request_id>/approve', methods=['POST'])
@login_required
def approve_request(request_id):
    if not check_access():
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية'}), 403
    
    emp_request = EmployeeRequest.query.get_or_404(request_id)
    
    if emp_request.status != RequestStatus.PENDING:
        return jsonify({'success': False, 'message': 'هذا الطلب تمت معالجته مسبقاً'}), 400
    
    emp_request.status = RequestStatus.APPROVED
    emp_request.approved_by_id = current_user.id
    emp_request.approved_at = datetime.utcnow()
    
    admin_notes = request.form.get('admin_notes', '')
    if admin_notes:
        emp_request.admin_notes = admin_notes
    
    type_names = {
        'INVOICE': 'فاتورة',
        'CAR_WASH': 'غسيل سيارة',
        'CAR_INSPECTION': 'فحص وتوثيق',
        'ADVANCE_PAYMENT': 'سلفة مالية'
    }
    
    notification = RequestNotification()
    notification.request_id = request_id
    notification.employee_id = emp_request.employee_id
    notification.title_ar = 'تمت الموافقة على طلبك'
    notification.message_ar = f'تمت الموافقة على طلب {type_names.get(emp_request.request_type.name, emp_request.request_type.name)}'
    notification.notification_type = 'APPROVED'
    db.session.add(notification)
    
    db.session.commit()
    
    flash('تمت الموافقة على الطلب بنجاح', 'success')
    return redirect(url_for('employee_requests.view_request', request_id=request_id))


@employee_requests.route('/<int:request_id>/reject', methods=['POST'])
@login_required
def reject_request(request_id):
    if not check_access():
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية'}), 403
    
    emp_request = EmployeeRequest.query.get_or_404(request_id)
    
    if emp_request.status != RequestStatus.PENDING:
        return jsonify({'success': False, 'message': 'هذا الطلب تمت معالجته مسبقاً'}), 400
    
    rejection_reason = request.form.get('rejection_reason', '')
    if not rejection_reason:
        flash('يجب إدخال سبب الرفض', 'error')
        return redirect(url_for('employee_requests.view_request', request_id=request_id))
    
    emp_request.status = RequestStatus.REJECTED
    emp_request.approved_by_id = current_user.id
    emp_request.approved_at = datetime.utcnow()
    emp_request.rejection_reason = rejection_reason
    
    type_names = {
        'INVOICE': 'فاتورة',
        'CAR_WASH': 'غسيل سيارة',
        'CAR_INSPECTION': 'فحص وتوثيق',
        'ADVANCE_PAYMENT': 'سلفة مالية'
    }
    
    notification = RequestNotification()
    notification.request_id = request_id
    notification.employee_id = emp_request.employee_id
    notification.title_ar = 'تم رفض طلبك'
    notification.message_ar = f'تم رفض طلب {type_names.get(emp_request.request_type.name, emp_request.request_type.name)}: {rejection_reason}'
    notification.notification_type = 'REJECTED'
    db.session.add(notification)
    
    db.session.commit()
    
    flash('تم رفض الطلب', 'warning')
    return redirect(url_for('employee_requests.view_request', request_id=request_id))


@employee_requests.route('/delete/<int:request_id>', methods=['POST'])
@login_required
def delete_request(request_id):
    if not check_access():
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية'}), 403
    
    emp_request = EmployeeRequest.query.get(request_id)
    
    if not emp_request:
        return jsonify({'success': False, 'message': 'الطلب غير موجود'}), 404
    
    try:
        db.session.delete(emp_request)
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'تم حذف الطلب بنجاح'})
        else:
            flash('تم حذف الطلب بنجاح', 'success')
            return redirect(url_for('employee_requests.index'))
    except Exception as e:
        db.session.rollback()
        error_message = f'حدث خطأ أثناء الحذف: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': error_message}), 500
        else:
            flash(error_message, 'error')
            return redirect(url_for('employee_requests.index'))


@employee_requests.route('/advance-payments')
@login_required
def advance_payments():
    if not check_access():
        flash('ليس لديك صلاحية الوصول إلى هذا القسم', 'error')
        return redirect(url_for('dashboard'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    status_filter = request.args.get('status', '')
    
    query = EmployeeRequest.query.filter_by(request_type=RequestType.ADVANCE_PAYMENT)
    
    if status_filter:
        query = query.filter_by(status=RequestStatus[status_filter])
    
    requests_pagination = query.order_by(desc(EmployeeRequest.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    total_pending = EmployeeRequest.query.filter_by(
        request_type=RequestType.ADVANCE_PAYMENT,
        status=RequestStatus.PENDING
    ).count()
    
    total_approved = EmployeeRequest.query.filter_by(
        request_type=RequestType.ADVANCE_PAYMENT,
        status=RequestStatus.APPROVED
    ).count()
    
    return render_template('employee_requests/advance_payments.html',
                         requests=requests_pagination.items,
                         pagination=requests_pagination,
                         total_pending=total_pending,
                         total_approved=total_approved,
                         RequestStatus=RequestStatus)


@employee_requests.route('/liabilities')
@login_required
def liabilities():
    if not check_access():
        flash('ليس لديك صلاحية الوصول إلى هذا القسم', 'error')
        return redirect(url_for('dashboard'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    liability_type = request.args.get('type', '')
    status_filter = request.args.get('status', '')
    
    query = EmployeeLiability.query
    
    if liability_type:
        query = query.filter_by(liability_type=liability_type)
    
    if status_filter:
        if status_filter == 'ACTIVE':
            query = query.filter_by(is_paid=False)
        elif status_filter == 'PAID':
            query = query.filter_by(is_paid=True)
    
    liabilities_pagination = query.order_by(desc(EmployeeLiability.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    total_unpaid = EmployeeLiability.query.filter_by(is_paid=False).count()
    total_amount = db.session.query(db.func.sum(EmployeeLiability.amount)).filter_by(is_paid=False).scalar() or 0
    
    return render_template('employee_requests/liabilities.html',
                         liabilities=liabilities_pagination.items,
                         pagination=liabilities_pagination,
                         total_unpaid=total_unpaid,
                         total_amount=total_amount)


@employee_requests.route('/invoices')
@login_required
def invoices():
    if not check_access():
        flash('ليس لديك صلاحية الوصول إلى هذا القسم', 'error')
        return redirect(url_for('dashboard'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    status_filter = request.args.get('status', '')
    
    query = EmployeeRequest.query.filter_by(request_type=RequestType.INVOICE)
    
    if status_filter:
        query = query.filter_by(status=RequestStatus[status_filter])
    
    requests_pagination = query.order_by(desc(EmployeeRequest.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('employee_requests/invoices.html',
                         requests=requests_pagination.items,
                         pagination=requests_pagination,
                         RequestStatus=RequestStatus)


@employee_requests.route('/<int:request_id>/upload-to-drive', methods=['POST'])
@login_required
def upload_to_drive(request_id):
    """رفع طلب يدوياً إلى Google Drive"""
    if not check_access():
        return jsonify({
            'success': False,
            'message': 'ليس لديك صلاحية لهذا الإجراء'
        }), 403
    
    try:
        # جلب الطلب
        emp_request = EmployeeRequest.query.get_or_404(request_id)
        
        # التحقق من عدم الرفع مسبقاً
        if emp_request.google_drive_folder_id:
            return jsonify({
                'success': False,
                'message': 'هذا الطلب مرفوع بالفعل على Google Drive',
                'folder_url': emp_request.google_drive_folder_url
            }), 400
        
        # تهيئة خدمة Google Drive
        drive_uploader = EmployeeRequestsDriveUploader()
        
        # التحقق من توفر الخدمة
        if not drive_uploader.is_available():
            logger.warning(f"Google Drive غير متاح - الطلب {request_id}")
            return jsonify({
                'success': False,
                'message': 'خدمة Google Drive غير متاحة حالياً. تأكد من إعداد Service Account بشكل صحيح.',
                'error': 'Drive service not configured'
            }), 503
        
        # تحديد نوع الطلب
        request_type_map = {
            RequestType.INVOICE: 'invoice',
            RequestType.CAR_WASH: 'car_wash',
            RequestType.CAR_INSPECTION: 'car_inspection',
            RequestType.ADVANCE_PAYMENT: 'advance_payment'
        }
        
        request_type_str = request_type_map.get(emp_request.request_type, 'other')
        
        # إنشاء مجلد Drive
        employee_name = emp_request.employee.name if emp_request.employee else "موظف غير معروف"
        vehicle_number = None
        
        # للطلبات المتعلقة بالسيارات، جلب رقم السيارة
        if emp_request.request_type in [RequestType.CAR_WASH, RequestType.CAR_INSPECTION]:
            if emp_request.request_type == RequestType.CAR_WASH:
                car_wash = CarWashRequest.query.filter_by(request_id=request_id).first()
                if car_wash and car_wash.vehicle:
                    vehicle_number = str(car_wash.vehicle.plate_number) if car_wash.vehicle.plate_number else None
            elif emp_request.request_type == RequestType.CAR_INSPECTION:
                car_inspection = CarInspectionRequest.query.filter_by(request_id=request_id).first()
                if car_inspection and car_inspection.vehicle:
                    vehicle_number = str(car_inspection.vehicle.plate_number) if car_inspection.vehicle.plate_number else None
        
        folder_result = drive_uploader.create_request_folder(
            request_type=request_type_str,
            request_id=request_id,
            employee_name=employee_name,
            vehicle_number=vehicle_number,
            date=emp_request.created_at
        )
        
        if not folder_result:
            logger.error(f"فشل إنشاء مجلد Drive للطلب {request_id}")
            return jsonify({
                'success': False,
                'message': 'فشل إنشاء المجلد في Google Drive. تحقق من الصلاحيات.',
                'error': 'Failed to create folder'
            }), 500
        
        # حفظ معلومات المجلد في قاعدة البيانات
        emp_request.google_drive_folder_id = folder_result['folder_id']
        emp_request.google_drive_folder_url = folder_result['folder_url']
        
        # رفع الملفات حسب نوع الطلب
        files_uploaded = 0
        
        if emp_request.request_type == RequestType.INVOICE:
            invoice = InvoiceRequest.query.filter_by(request_id=request_id).first()
            if invoice and invoice.local_image_path:
                file_path = os.path.join('static', invoice.local_image_path)
                logger.info(f"📁 فحص ملف الفاتورة: {file_path}")
                
                if os.path.exists(file_path):
                    logger.info(f"✓ الملف موجود - بدء الرفع")
                    upload_result = drive_uploader.upload_invoice_image(
                        file_path=file_path,
                        folder_id=folder_result['folder_id'],
                        custom_name=f"invoice_{request_id}.jpg"
                    )
                    if upload_result:
                        invoice.drive_file_id = upload_result['file_id']
                        files_uploaded += 1
                        logger.info(f"✓ تم رفع الصورة بنجاح")
                    else:
                        logger.error(f"✗ فشل رفع الصورة إلى Drive")
                else:
                    logger.warning(f"✗ الملف غير موجود على القرص: {file_path}")
            else:
                logger.warning(f"⚠ لا توجد فاتورة أو مسار صورة فارغ للطلب {request_id}")
        
        elif emp_request.request_type == RequestType.CAR_WASH:
            car_wash = CarWashRequest.query.filter_by(request_id=request_id).first()
            if car_wash:
                # تحضير الصور للرفع
                images_dict = {}
                photo_mapping = {
                    'photo_plate': 'plate',
                    'photo_front': 'front',
                    'photo_back': 'back',
                    'photo_right_side': 'right',
                    'photo_left_side': 'left'
                }
                
                for field, media_type in photo_mapping.items():
                    photo_path = getattr(car_wash, field, None)
                    if photo_path:
                        full_path = os.path.join('static', photo_path)
                        if os.path.exists(full_path):
                            images_dict[media_type] = full_path
                
                # رفع جميع الصور
                if images_dict:
                    upload_results = drive_uploader.upload_car_wash_images(
                        images_dict=images_dict,
                        folder_id=folder_result['folder_id']
                    )
                    files_uploaded += len([r for r in upload_results.values() if r is not None])
        
        # التحقق من أنه تم رفع ملفات فعلاً
        if files_uploaded == 0:
            # لم يتم رفع أي ملف - فشل العملية
            db.session.rollback()
            logger.warning(f"⚠ فشل رفع الطلب {request_id} - لا توجد ملفات متاحة للرفع")
            return jsonify({
                'success': False,
                'message': 'فشل الرفع: الملفات غير موجودة على الخادم. تأكد من رفع الملفات من التطبيق أولاً.',
                'error': 'No files found to upload',
                'files_uploaded': 0
            }), 400
        
        db.session.commit()
        
        logger.info(f"✅ تم رفع الطلب {request_id} يدوياً إلى Drive - {files_uploaded} ملف")
        
        return jsonify({
            'success': True,
            'message': f'تم الرفع إلى Google Drive بنجاح ({files_uploaded} ملف)',
            'folder_id': folder_result['folder_id'],
            'folder_url': folder_result['folder_url'],
            'files_uploaded': files_uploaded
        }), 200
        
    except Exception as e:
        logger.error(f"خطأ في رفع الطلب {request_id} إلى Drive: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'حدث خطأ أثناء الرفع إلى Google Drive',
            'error': str(e)
        }), 500
