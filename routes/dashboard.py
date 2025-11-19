from flask import Blueprint, render_template, jsonify, redirect, url_for, flash
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from flask_login import login_required, current_user
from models import Employee, Department, Attendance, Document, Salary, Module, UserRole
from app import db
from utils.decorators import module_access_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
@module_access_required(Module.DASHBOARD)
def index():
    """Main dashboard with overview of system statistics"""
    # Get basic statistics - count only active employees
    total_active_employees = Employee.query.filter_by(status='active').count()
    total_all_employees = Employee.query.count()
    total_departments = Department.query.count()
    
    # Get current date and time for calculations
    now = datetime.now()
    today = now.date()
    
    # Get attendance for today
    today_attendance = Attendance.query.filter_by(date=today).count()
    
    # Get documents statistics using single aggregation query with CASE
    expiry_threshold = today + timedelta(days=30)
    
    from sqlalchemy import case
    doc_stats_result = db.session.query(
        func.count().label('total'),
        func.sum(case((Document.expiry_date < today, 1), else_=0)).label('expired'),
        func.sum(case(((Document.expiry_date >= today) & (Document.expiry_date <= expiry_threshold), 1), else_=0)).label('expiring'),
        func.sum(case((Document.expiry_date > expiry_threshold, 1), else_=0)).label('valid'),
        func.sum(case((Document.expiry_date.is_(None), 1), else_=0)).label('no_expiry')
    ).one()
    
    total_documents = doc_stats_result.total or 0
    expired_documents = doc_stats_result.expired or 0
    expiring_documents = doc_stats_result.expiring or 0
    valid_documents = doc_stats_result.valid or 0
    no_expiry_documents = doc_stats_result.no_expiry or 0
    
    # Document statistics for template
    document_stats = {
        'total': total_documents,
        'valid': valid_documents,
        'expired': expired_documents,
        'expiring': expiring_documents,
        'no_expiry': no_expiry_documents
    }
    
    # Get department statistics - only count active employees using many-to-many relationship
    from models import employee_departments
    
    departments = db.session.query(
        Department.name,
        func.count(Employee.id).label('employee_count')
    ).outerjoin(
        employee_departments, Department.id == employee_departments.c.department_id
    ).outerjoin(
        Employee, (employee_departments.c.employee_id == Employee.id) & (Employee.status == 'active')
    ).group_by(Department.id, Department.name).all()
    
    # Get recent activity
    recent_employees = Employee.query.order_by(Employee.created_at.desc()).limit(5).all()
    
    # Get monthly salary totals for the current year
    current_year = now.year
    monthly_salaries = db.session.query(
        Salary.month,
        func.sum(Salary.net_salary).label('total')
    ).filter(
        Salary.year == current_year
    ).group_by(Salary.month).all()
    
    # Format data for charts
    dept_labels = [dept.name for dept in departments]
    dept_data = [count for _, count in departments]
    
    # If no departments, add default data to avoid empty chart error
    if not dept_labels:
        dept_labels = ["لا يوجد أقسام"]
        dept_data = [0]
    
    salary_labels = [f"شهر {month}" for month, _ in monthly_salaries]
    salary_data = [float(total) for _, total in monthly_salaries]
    
    # If no salary data, add default data to avoid empty chart error
    if not salary_labels:
        salary_labels = ["لا يوجد بيانات"]
        salary_data = [0]
    
    # إحصائيات الموظفين حسب الحالة
    status_stats = db.session.query(
        Employee.status,
        func.count(Employee.id).label('count')
    ).group_by(Employee.status).all()
    
    # ترجمة حالات الموظفين
    status_map = {
        'active': 'نشط',
        'inactive': 'غير نشط',
        'on_leave': 'في إجازة',
        'terminated': 'متوقف عن العمل'
    }
    
    status_data = [
        {'status': status_map.get(stat.status, stat.status), 'count': stat.count}
        for stat in status_stats
    ]
    
    return render_template('dashboard.html',
                          now=now,
                          total_employees=total_active_employees,
                          total_all_employees=total_all_employees,
                          total_departments=total_departments,
                          today_attendance=today_attendance,
                          document_stats=document_stats,
                          expiring_documents=expiring_documents,
                          recent_employees=recent_employees,
                          dept_labels=dept_labels,
                          dept_data=dept_data,
                          salary_labels=salary_labels,
                          salary_data=salary_data,
                          status_data=status_data)

@dashboard_bp.route('/employee-stats')
@login_required
@module_access_required(Module.DASHBOARD)
def employee_stats():
    """عرض إحصائيات الموظفين حسب القسم والحالة مع فلترة حسب قسم المستخدم"""
    # فلترة الإحصائيات حسب القسم المحدد للمستخدم الحالي
    from models import employee_departments
    
    if current_user.assigned_department_id:
        # إذا كان المستخدم مرتبط بقسم محدد، عرض إحصائيات ذلك القسم فقط
        department_stats = db.session.query(
            Department.id,
            Department.name,
            func.count(func.distinct(Employee.id)).label('employee_count')
        ).outerjoin(
            employee_departments, Department.id == employee_departments.c.department_id
        ).outerjoin(
            Employee, employee_departments.c.employee_id == Employee.id
        ).filter(
            Department.id == current_user.assigned_department_id
        ).group_by(Department.id, Department.name).all()
    else:
        # إذا لم يكن المستخدم مرتبط بقسم، عرض جميع الأقسام (للمديرين العامين)
        department_stats = db.session.query(
            Department.id,
            Department.name,
            func.count(func.distinct(Employee.id)).label('employee_count')
        ).outerjoin(
            employee_departments, Department.id == employee_departments.c.department_id
        ).outerjoin(
            Employee, employee_departments.c.employee_id == Employee.id
        ).group_by(Department.id, Department.name).order_by(func.count(func.distinct(Employee.id)).desc()).all()
    
    # إحصائيات الموظفين حسب الحالة
    status_stats = db.session.query(
        Employee.status,
        func.count(Employee.id).label('count')
    ).group_by(Employee.status).all()
    
    # ترجمة حالات الموظفين
    status_map = {
        'active': 'نشط',
        'inactive': 'غير نشط',
        'on_leave': 'في إجازة',
        'terminated': 'متوقف عن العمل'
    }
    
    status_data = [
        {'status': status_map.get(stat.status, stat.status), 'count': stat.count}
        for stat in status_stats
    ]
    
    # إحصائيات الموظفين حسب القسم والحالة مع فلترة القسم
    detailed_stats = []
    
    if current_user.assigned_department_id:
        # عرض إحصائيات القسم المحدد فقط
        dept = Department.query.get(current_user.assigned_department_id)
        if dept:
            # حساب عدد الموظفين في القسم حسب الحالة
            active_count = db.session.query(Employee.id).join(
                employee_departments, Employee.id == employee_departments.c.employee_id
            ).filter(
                employee_departments.c.department_id == dept.id,
                Employee.status == 'active'
            ).count()
            
            inactive_count = db.session.query(Employee.id).join(
                employee_departments, Employee.id == employee_departments.c.employee_id
            ).filter(
                employee_departments.c.department_id == dept.id,
                Employee.status == 'inactive'
            ).count()
            
            on_leave_count = db.session.query(Employee.id).join(
                employee_departments, Employee.id == employee_departments.c.employee_id
            ).filter(
                employee_departments.c.department_id == dept.id,
                Employee.status == 'on_leave'
            ).count()
            
            terminated_count = db.session.query(Employee.id).join(
                employee_departments, Employee.id == employee_departments.c.employee_id
            ).filter(
                employee_departments.c.department_id == dept.id,
                Employee.status == 'terminated'
            ).count()
            
            total_count = db.session.query(Employee.id).join(
                employee_departments, Employee.id == employee_departments.c.employee_id
            ).filter(
                employee_departments.c.department_id == dept.id
            ).count()
            
            dept_stats = {
                'department_id': dept.id,
                'department_name': dept.name,
                'active': active_count,
                'inactive': inactive_count,
                'on_leave': on_leave_count,
                'terminated': terminated_count,
                'total': total_count,
                'total_active': active_count,
            }
            detailed_stats.append(dept_stats)
    else:
        # عرض جميع الأقسام (للمديرين العامين)
        for dept in Department.query.all():
            active_count = db.session.query(Employee.id).join(
                employee_departments, Employee.id == employee_departments.c.employee_id
            ).filter(
                employee_departments.c.department_id == dept.id,
                Employee.status == 'active'
            ).count()
            
            inactive_count = db.session.query(Employee.id).join(
                employee_departments, Employee.id == employee_departments.c.employee_id
            ).filter(
                employee_departments.c.department_id == dept.id,
                Employee.status == 'inactive'
            ).count()
            
            on_leave_count = db.session.query(Employee.id).join(
                employee_departments, Employee.id == employee_departments.c.employee_id
            ).filter(
                employee_departments.c.department_id == dept.id,
                Employee.status == 'on_leave'
            ).count()
            
            terminated_count = db.session.query(Employee.id).join(
                employee_departments, Employee.id == employee_departments.c.employee_id
            ).filter(
                employee_departments.c.department_id == dept.id,
                Employee.status == 'terminated'
            ).count()
            
            total_count = db.session.query(Employee.id).join(
                employee_departments, Employee.id == employee_departments.c.employee_id
            ).filter(
                employee_departments.c.department_id == dept.id
            ).count()
            
            dept_stats = {
                'department_id': dept.id,
                'department_name': dept.name,
                'active': active_count,
                'inactive': inactive_count,
                'on_leave': on_leave_count,
                'terminated': terminated_count,
                'total': total_count,
                'total_active': active_count,
            }
            detailed_stats.append(dept_stats)
    
    # ترتيب الإحصائيات حسب العدد الإجمالي للموظفين
    detailed_stats.sort(key=lambda x: x['total'], reverse=True)
    
    # تحضير بيانات المخطط للموظفين النشطين فقط
    chart_labels = []
    chart_data = []
    chart_dept_ids = []
    chart_percentages = []
    
    # الحصول على بيانات الموظفين النشطين فقط لكل قسم
    active_dept_stats = db.session.query(
        Department.id,
        Department.name,
        func.count(func.distinct(Employee.id)).label('employee_count')
    ).outerjoin(
        employee_departments, Department.id == employee_departments.c.department_id
    ).outerjoin(
        Employee, (employee_departments.c.employee_id == Employee.id) & (Employee.status == 'active')
    ).group_by(Department.id, Department.name).order_by(func.count(func.distinct(Employee.id)).desc()).all()
    
    total_active = sum(stat.employee_count for stat in active_dept_stats)
    
    for stat in active_dept_stats:
        chart_labels.append(stat.name)
        chart_data.append(stat.employee_count)
        chart_dept_ids.append(stat.id)
        percentage = round((stat.employee_count / total_active * 100), 1) if total_active > 0 else 0
        chart_percentages.append(percentage)
    
    # قائمة بالألوان للمخطط
    chart_colors = [
        'rgba(24, 144, 255, 0.85)', 'rgba(47, 194, 91, 0.85)', 'rgba(250, 173, 20, 0.85)',
        'rgba(245, 34, 45, 0.85)', 'rgba(114, 46, 209, 0.85)', 'rgba(19, 194, 194, 0.85)',
        'rgba(82, 196, 26, 0.85)', 'rgba(144, 19, 254, 0.85)', 'rgba(240, 72, 68, 0.85)',
        'rgba(250, 140, 22, 0.85)'
    ]
    
    return render_template('employee_stats.html',
                           department_stats=department_stats,
                           status_stats=status_data,
                           detailed_stats=detailed_stats,
                           chart_labels=chart_labels,
                           chart_data=chart_data,
                           chart_dept_ids=chart_dept_ids,
                           chart_percentages=chart_percentages,
                           chart_colors=chart_colors,
                           total_active_employees=total_active)

@dashboard_bp.route('/api/department-employee-stats')
@login_required
def department_employee_stats_api():
    """واجهة برمجة لإحصائيات الموظفين حسب القسم للرسوم البيانية"""
    try:
        from models import employee_departments
        
        # إحصائيات الموظفين حسب القسم (فقط الموظفون النشطون) باستخدام علاقة many-to-many
        department_stats = db.session.query(
            Department.id,
            Department.name,
            func.count(func.distinct(Employee.id)).label('employee_count')
        ).outerjoin(
            employee_departments, Department.id == employee_departments.c.department_id
        ).outerjoin(
            Employee, (employee_departments.c.employee_id == Employee.id) & (Employee.status == 'active')
        ).group_by(Department.id, Department.name).order_by(func.count(func.distinct(Employee.id)).desc()).all()
    except Exception as e:
        import traceback
        print(f"Error in department_employee_stats_api: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'labels': [],
            'data': [],
            'backgroundColor': [],
            'hoverBackgroundColor': [],
            'departmentIds': [],
            'percentages': [],
            'total': 0,
            'error': str(e)
        }), 200
    
    # قائمة بالألوان الجميلة المتناسقة للمخطط
    gradient_colors = [
        ['rgba(24, 144, 255, 0.85)', 'rgba(24, 144, 255, 0.4)'],    # أزرق
        ['rgba(47, 194, 91, 0.85)', 'rgba(47, 194, 91, 0.4)'],      # أخضر
        ['rgba(250, 173, 20, 0.85)', 'rgba(250, 173, 20, 0.4)'],    # برتقالي
        ['rgba(245, 34, 45, 0.85)', 'rgba(245, 34, 45, 0.4)'],      # أحمر
        ['rgba(114, 46, 209, 0.85)', 'rgba(114, 46, 209, 0.4)'],    # بنفسجي
        ['rgba(19, 194, 194, 0.85)', 'rgba(19, 194, 194, 0.4)'],    # فيروزي
        ['rgba(82, 196, 26, 0.85)', 'rgba(82, 196, 26, 0.4)'],      # أخضر فاتح
        ['rgba(144, 19, 254, 0.85)', 'rgba(144, 19, 254, 0.4)'],    # أرجواني
        ['rgba(240, 72, 68, 0.85)', 'rgba(240, 72, 68, 0.4)'],      # أحمر فاتح
        ['rgba(250, 140, 22, 0.85)', 'rgba(250, 140, 22, 0.4)'],    # برتقالي داكن
    ]
    
    # تحضير البيانات للرسم البياني مع معلومات إضافية
    labels = []
    data = []
    background_colors = []
    hover_colors = []
    department_ids = []
    
    # إذا لم تكن هناك أقسام
    if not department_stats:
        return jsonify({
            'labels': ['لا توجد أقسام'],
            'data': [0],
            'backgroundColor': ['rgba(200, 200, 200, 0.6)'],
            'hoverBackgroundColor': ['rgba(200, 200, 200, 0.8)'],
            'departmentIds': [0],
            'percentages': [100],
            'total': 0
        })
    
    total_employees = sum(stat.employee_count for stat in department_stats)
    percentages = []
    
    for idx, stat in enumerate(department_stats):
        labels.append(stat.name)
        data.append(stat.employee_count)
        color_idx = idx % len(gradient_colors)
        background_colors.append(gradient_colors[color_idx][1])
        hover_colors.append(gradient_colors[color_idx][0])
        department_ids.append(stat.id)
        
        # حساب النسبة المئوية
        percentage = round((stat.employee_count / total_employees * 100), 1) if total_employees > 0 else 0
        percentages.append(percentage)
    
    # تنسيق البيانات للرسم البياني
    dept_data = {
        'labels': labels,
        'data': data,
        'backgroundColor': background_colors,
        'hoverBackgroundColor': hover_colors,
        'departmentIds': department_ids,
        'percentages': percentages,
        'total': total_employees
    }
    
    return jsonify(dept_data)
