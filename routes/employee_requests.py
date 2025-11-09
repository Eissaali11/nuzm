from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from models import (
    EmployeeRequest, InvoiceRequest, AdvancePaymentRequest,
    CarWashRequest, CarInspectionRequest, EmployeeLiability,
    RequestNotification, Employee, RequestStatus, RequestType,
    UserRole, Module
)
from datetime import datetime
from sqlalchemy import desc, or_, and_

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


@employee_requests.route('/<int:request_id>/delete', methods=['POST'])
@login_required
def delete_request(request_id):
    if not check_access():
        return jsonify({'success': False, 'message': 'ليس لديك صلاحية'}), 403
    
    emp_request = EmployeeRequest.query.get_or_404(request_id)
    
    try:
        db.session.delete(emp_request)
        db.session.commit()
        
        flash('تم حذف الطلب بنجاح', 'success')
        return redirect(url_for('employee_requests.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف الطلب: {str(e)}', 'error')
        return redirect(url_for('employee_requests.view_request', request_id=request_id))


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
