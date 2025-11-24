from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
from models import (
    Employee, Vehicle, Department, User, Salary, Attendance, 
    MobileDevice, VehicleHandover, db
)
import json

admin_dashboard_bp = Blueprint('admin_dashboard', __name__)

def admin_required(f):
    """ديكوريتر للتحقق من صلاحيات المدير"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('غير مسموح لك بالوصول لهذه الصفحة', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_dashboard_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """الصفحة الرئيسية للوحة التحكم"""
    
    # إحصائيات عامة
    stats = {
        'employees': Employee.query.count(),
        'vehicles': Vehicle.query.count(),
        'departments': Department.query.count(),
        'users': User.query.count(),
        'mobile_devices': MobileDevice.query.count(),
        'active_handovers': VehicleHandover.query.filter_by(return_date=None).count(),
        'pending_documents': Employee.query.filter(
            Employee.id_expiry < datetime.now() + timedelta(days=30)
        ).count()
    }
    
    # إحصائيات شهرية
    current_month = datetime.now().replace(day=1)
    monthly_stats = {
        'new_employees': Employee.query.filter(
            Employee.date_joined >= current_month
        ).count(),
        'new_vehicles': Vehicle.query.filter(
            Vehicle.registration_date >= current_month
        ).count(),
        'salary_records': Salary.query.filter(
            and_(
                Salary.month == datetime.now().month,
                Salary.year == datetime.now().year
            )
        ).count()
    }
    
    # أحدث العمليات
    recent_employees = Employee.query.order_by(desc(Employee.date_joined)).limit(5).all()
    recent_vehicles = Vehicle.query.order_by(desc(Vehicle.registration_date)).limit(5).all()
    recent_handovers = VehicleHandover.query.order_by(desc(VehicleHandover.handover_date)).limit(5).all()
    
    # المستندات منتهية الصلاحية
    expiring_docs = Employee.query.filter(
        Employee.id_expiry <= datetime.now() + timedelta(days=30)
    ).order_by(Employee.id_expiry).limit(10).all()
    
    return render_template('admin_dashboard/dashboard.html', 
                         stats=stats,
                         monthly_stats=monthly_stats,
                         recent_employees=recent_employees,
                         recent_vehicles=recent_vehicles,
                         recent_handovers=recent_handovers,
                         expiring_docs=expiring_docs)

@admin_dashboard_bp.route('/employees')
@login_required  
@admin_required
def employees():
    """إدارة الموظفين"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    department_id = request.args.get('department_id', type=int)
    
    query = Employee.query
    
    if search:
        query = query.filter(
            (Employee.name.contains(search)) |
            (Employee.employee_id.contains(search)) |
            (Employee.phone.contains(search))
        )
    
    if department_id:
        query = query.filter(Employee.department_id == department_id)
        
    employees = query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    departments = Department.query.all()
    
    return render_template('admin_dashboard/employees.html',
                         employees=employees,
                         departments=departments,
                         search=search,
                         department_id=department_id)

@admin_dashboard_bp.route('/vehicles')
@login_required
@admin_required 
def vehicles():
    """إدارة المركبات"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    status = request.args.get('status', '', type=str)
    
    query = Vehicle.query
    
    if search:
        query = query.filter(
            (Vehicle.license_plate.contains(search)) |
            (Vehicle.model.contains(search)) |
            (Vehicle.chassis_number.contains(search))
        )
    
    if status:
        query = query.filter(Vehicle.status == status)
        
    vehicles = query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin_dashboard/vehicles.html',
                         vehicles=vehicles,
                         search=search,
                         status=status)

@admin_dashboard_bp.route('/departments')
@login_required
@admin_required
def departments():
    """إدارة الأقسام"""
    departments = Department.query.all()
    return render_template('admin_dashboard/departments.html',
                         departments=departments)

@admin_dashboard_bp.route('/users')
@login_required
@admin_required
def users():
    """إدارة المستخدمين"""
    users = User.query.all()
    return render_template('admin_dashboard/users.html',
                         users=users)

@admin_dashboard_bp.route('/mobile-devices')
@login_required
@admin_required
def mobile_devices():
    """إدارة الأجهزة المحمولة"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = MobileDevice.query
    
    if search:
        query = query.filter(
            (MobileDevice.device_id.contains(search)) |
            (MobileDevice.imei.contains(search)) |
            (MobileDevice.phone_number.contains(search))
        )
        
    devices = query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin_dashboard/mobile_devices.html',
                         devices=devices,
                         search=search)

# API Endpoints للعمليات CRUD

@admin_dashboard_bp.route('/api/employee/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_employee(id):
    """حذف موظف"""
    from models import EmployeeRequest
    employee = Employee.query.get_or_404(id)
    try:
        # التحقق من وجود طلبات معلقة للموظف
        pending_requests = EmployeeRequest.query.filter_by(
            employee_id=id,
            status='PENDING'
        ).count()
        
        if pending_requests > 0:
            return jsonify({
                'success': False, 
                'message': f'لا يمكن حذف الموظف لديه {pending_requests} طلب(ات) معلقة. يرجى حذف الطلبات أولاً'
            }), 400
        
        # حذف جميع الطلبات المرتبطة بالموظف
        EmployeeRequest.query.filter_by(employee_id=id).delete()
        
        db.session.delete(employee)
        db.session.commit()
        return jsonify({'success': True, 'message': 'تم حذف الموظف بنجاح'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ في حذف الموظف: {str(e)}'}), 500

@admin_dashboard_bp.route('/api/vehicle/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_vehicle(id):
    """حذف مركبة"""
    vehicle = Vehicle.query.get_or_404(id)
    try:
        db.session.delete(vehicle)
        db.session.commit()
        return jsonify({'success': True, 'message': 'تم حذف المركبة بنجاح'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'حدث خطأ في حذف المركبة'}), 500

@admin_dashboard_bp.route('/api/department/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_department(id):
    """حذف قسم"""
    department = Department.query.get_or_404(id)
    try:
        db.session.delete(department)
        db.session.commit()
        return jsonify({'success': True, 'message': 'تم حذف القسم بنجاح'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'حدث خطأ في حذف القسم'}), 500

@admin_dashboard_bp.route('/api/user/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(id):
    """حذف مستخدم"""
    if id == current_user.id:
        return jsonify({'success': False, 'message': 'لا يمكن حذف حسابك الخاص'}), 400
        
    user = User.query.get_or_404(id)
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True, 'message': 'تم حذف المستخدم بنجاح'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'حدث خطأ في حذف المستخدم'}), 500

@admin_dashboard_bp.route('/api/mobile-device/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_mobile_device(id):
    """حذف جهاز محمول"""
    device = MobileDevice.query.get_or_404(id)
    try:
        db.session.delete(device)
        db.session.commit()
        return jsonify({'success': True, 'message': 'تم حذف الجهاز بنجاح'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'حدث خطأ في حذف الجهاز'}), 500

@admin_dashboard_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    """API للحصول على الإحصائيات المحدثة"""
    stats = {
        'employees': Employee.query.count(),
        'vehicles': Vehicle.query.count(),
        'departments': Department.query.count(),
        'users': User.query.count(),
        'mobile_devices': MobileDevice.query.count(),
        'active_handovers': VehicleHandover.query.filter_by(return_date=None).count()
    }
    return jsonify(stats)

@admin_dashboard_bp.route('/bulk-actions', methods=['POST'])
@login_required
@admin_required
def bulk_actions():
    """العمليات المجمعة"""
    data = request.get_json()
    action = data.get('action')
    ids = data.get('ids', [])
    table = data.get('table')
    
    if not action or not ids or not table:
        return jsonify({'success': False, 'message': 'بيانات غير مكتملة'}), 400
    
    try:
        if action == 'delete':
            if table == 'employees':
                Employee.query.filter(Employee.id.in_(ids)).delete(synchronize_session=False)
            elif table == 'vehicles':
                Vehicle.query.filter(Vehicle.id.in_(ids)).delete(synchronize_session=False)
            elif table == 'departments':
                Department.query.filter(Department.id.in_(ids)).delete(synchronize_session=False)
            elif table == 'users':
                # تجنب حذف المستخدم الحالي
                ids = [id for id in ids if id != current_user.id]
                User.query.filter(User.id.in_(ids)).delete(synchronize_session=False)
            elif table == 'mobile_devices':
                MobileDevice.query.filter(MobileDevice.id.in_(ids)).delete(synchronize_session=False)
            
            db.session.commit()
            return jsonify({'success': True, 'message': f'تم حذف {len(ids)} عنصر بنجاح'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'حدث خطأ في العملية'}), 500
    
    return jsonify({'success': False, 'message': 'عملية غير مدعومة'}), 400