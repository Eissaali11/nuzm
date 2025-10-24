import pandas as pd
from io import BytesIO
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
from sqlalchemy import func
from datetime import datetime
from app import db
from models import Salary, Employee, Department, SystemAudit, Attendance
from utils.audit_logger import log_activity
from utils.excel import parse_salary_excel, generate_salary_excel, generate_comprehensive_employee_report, generate_employee_salary_simple_excel
# from utils.simple_pdf_generator import create_vehicle_handover_pdf as generate_salary_report_pdf
# from utils.reports import generate_salary_report_pdf
# from utils.salary_pdf_generator import

from utils.ultra_safe_pdf import create_ultra_safe_salary_pdf
from utils.salary_pdf_generator import generate_salary_summary_pdf
from utils.salary_report_pdf import generate_salary_report_pdf

from utils.salary_notification import generate_salary_notification_pdf, generate_batch_salary_notifications
from utils.whatsapp_notification import (
    send_salary_notification_whatsapp, 
    send_salary_deduction_notification_whatsapp,
    send_batch_salary_notifications_whatsapp,
    send_batch_deduction_notifications_whatsapp
)
from utils.salary_calculator import (
    calculate_salary_with_attendance,
    get_attendance_statistics,
    get_attendance_summary_text
)

salaries_bp = Blueprint('salaries', __name__)

@salaries_bp.route('/')
def index():
    """عرض سجلات الرواتب مع خيارات التصفية"""
    # الحصول على الشهر والسنة الحالية
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # الحصول على بيانات التصفية من الطلب
    month = request.args.get('month', None)
    year = request.args.get('year', None)
    employee_id = request.args.get('employee_id', '')
    department_id = request.args.get('department_id', '')
    
    # إذا تم تحديد قيمة خالية للشهر أو السنة، فهذا يعني تصفية كل الشهور أو كل السنوات
    show_all_months = month == ''  # اختار المستخدم "جميع الشهور" بشكل صريح
    show_all_years = year == ''    # اختار المستخدم "جميع السنوات" بشكل صريح
    
    # البحث عن الشهر والسنة التي تحتوي على بيانات إذا لم يتم تحديدها (فقط إذا لم يطلب المستخدم كل الشهور أو كل السنوات)
    if (not month and not show_all_months) or (not year and not show_all_years):
        # محاولة العثور على آخر شهر/سنة يحتوي على بيانات
        latest_salary = Salary.query.order_by(Salary.year.desc(), Salary.month.desc()).first()
        if latest_salary:
            # تحديد قيم افتراضية فقط إذا لم يطلب المستخدم "جميع..." بشكل صريح
            if not month and not show_all_months:
                month = str(latest_salary.month)
            if not year and not show_all_years:
                year = str(latest_salary.year)
        else:
            # إذا لم توجد بيانات، استخدم الشهر والسنة الحالية
            if not month and not show_all_months:
                month = str(current_month)
            if not year and not show_all_years:
                year = str(current_year)
    
    # بناء استعلام قاعدة البيانات
    salaries = []
    employee_records = []
    try:
        # استخدام القيم الافتراضية في حالة عدم وجود قيم في الرابط
        filter_month = int(month) if month and month.isdigit() else current_month
        filter_year = int(year) if year and year.isdigit() else current_year
        filter_employee = int(employee_id) if employee_id and employee_id.isdigit() else None
        filter_department = int(department_id) if department_id and department_id.isdigit() else None
        
        # بناء الاستعلام الأساسي
        query = Salary.query
        
        # إضافة فلتر الشهر (فقط إذا لم يطلب المستخدم كل الشهور)
        if not show_all_months:
            query = query.filter(Salary.month == filter_month)
            
        # إضافة فلتر السنة (فقط إذا لم يطلب المستخدم كل السنوات)
        if not show_all_years:
            query = query.filter(Salary.year == filter_year)
        
        # إضافة تصفية الموظف إذا تم تحديدها
        if filter_employee:
            query = query.filter(Salary.employee_id == filter_employee)
            
        # إضافة تصفية القسم إذا تم تحديدها
        if filter_department:
            # هنا نقوم بعمل join مع جدول الموظفين ثم الأقسام للفلترة
            query = query.join(Employee).join(Employee.departments).filter(Department.id == filter_department)
        
        # تنفيذ الاستعلام
        salaries = query.all()
        
        # **منطق معالجة عرض الموظفين بدون رواتب**
        # نريد أن نعرض موظفين للإدخال في الحالات التالية:
        # 1. عدم وجود رواتب للشهر والسنة المحددين
        # 2. عرض جميع الشهور 
        # 3. تم تحديد قسم معين (لإظهار موظفيه حتى لو لم تكن لديهم رواتب)
        # ولكن ليس إذا تم تحديد موظف معين
        should_show_employees_for_input = (not filter_employee) and (
            not salaries or  # لا توجد رواتب
            show_all_months or  # عرض جميع الشهور
            filter_department  # تم تحديد قسم معين
        )
        
        if should_show_employees_for_input:
            # الحصول على قائمة الموظفين النشطين
            active_employees_query = Employee.query.filter_by(status='active')
            
            # إذا تم تحديد قسم، قم بتصفية الموظفين حسب القسم
            if filter_department:
                active_employees_query = active_employees_query.join(Employee.departments).filter(Department.id == filter_department)
                
            active_employees = active_employees_query.all()
            
            # معالجة حالات الفلترة المختلفة
            if show_all_months and show_all_years:
                # عرض جميع الشهور وجميع السنوات - عرض جميع السجلات وإضافة الموظفين الذين ليس لديهم سجلات
                # في هذه الحالة نعتمد على السجلات المجمعة مما ورد من قاعدة البيانات
                print(f"تم العثور على {len(salaries)} سجل في جميع الشهور وجميع السنوات")
                
                # إضافة الموظفين الذين ليس لديهم سجلات على الإطلاق
                if filter_department:
                    # إذا تم تحديد قسم، أحضر الموظفين الذين ليس لديهم أي سجلات راتب في هذا القسم
                    employee_ids_with_salaries = db.session.query(Salary.employee_id).join(Employee).join(Employee.departments).filter(Department.id == filter_department).distinct().all()
                else:
                    # إذا لم يتم تحديد قسم، أحضر كل الموظفين الذين ليس لديهم سجلات راتب
                    employee_ids_with_salaries = db.session.query(Salary.employee_id).distinct().all()
                employee_ids_with_salaries_set = {id[0] for id in employee_ids_with_salaries}
                employees_without_salaries = [e for e in active_employees if e.id not in employee_ids_with_salaries_set]
                
                for employee in employees_without_salaries:
                    temp_salary = Salary(
                        employee_id=employee.id,
                        employee=employee,
                        month=1,  # شهر افتراضي
                        year=current_year,  # سنة افتراضية (الحالية)
                        basic_salary=0,
                        allowances=0,
                        deductions=0,
                        bonus=0,
                        net_salary=0
                    )
                    employee_records.append(temp_salary)
                
            elif show_all_months and not show_all_years:
                # عرض جميع الشهور لسنة محددة
                # الحصول على قائمة الموظفين الذين لديهم رواتب في السنة المحددة
                salary_query = db.session.query(Salary.employee_id).filter(Salary.year == filter_year)
                if filter_department:
                    salary_query = salary_query.join(Employee).join(Employee.departments).filter(Department.id == filter_department)
                employee_ids_with_salaries = salary_query.distinct().all()
                
                # تحويل القائمة إلى مجموعة (set) للبحث بسرعة
                employee_ids_with_salaries_set = {id[0] for id in employee_ids_with_salaries}
                
                # إنشاء قائمة بالموظفين الذين ليس لديهم رواتب في السنة المحددة
                employees_without_salaries = [e for e in active_employees if e.id not in employee_ids_with_salaries_set]
                
                # إذا كان هناك موظفين بدون رواتب، قم بإنشاء سجلات مؤقتة لهم
                for employee in employees_without_salaries:
                    # إنشاء كائن راتب مؤقت فقط لأغراض العرض (لن يتم حفظه)
                    temp_salary = Salary(
                        employee_id=employee.id,
                        employee=employee,
                        month=1,  # شهر افتراضي
                        year=filter_year,
                        basic_salary=0,
                        allowances=0,
                        deductions=0,
                        bonus=0,
                        net_salary=0
                    )
                    employee_records.append(temp_salary)
                
                print(f"تم العثور على {len(salaries)} سجل راتب للسنة {filter_year} مع {len(employee_records)} موظف بدون رواتب")
                
            elif not show_all_months and show_all_years:
                # عرض شهر محدد لجميع السنوات
                # هنا نبحث عن الموظفين الذين ليس لديهم سجلات في هذا الشهر بغض النظر عن السنة
                employee_ids_with_salaries = db.session.query(Salary.employee_id).filter(
                    Salary.month == filter_month
                ).distinct().all()
                
                employee_ids_with_salaries_set = {id[0] for id in employee_ids_with_salaries}
                employees_without_salaries = [e for e in active_employees if e.id not in employee_ids_with_salaries_set]
                
                for employee in employees_without_salaries:
                    temp_salary = Salary(
                        employee_id=employee.id,
                        employee=employee,
                        month=filter_month,
                        year=current_year,  # سنة افتراضية (الحالية)
                        basic_salary=0,
                        allowances=0,
                        deductions=0,
                        bonus=0,
                        net_salary=0
                    )
                    employee_records.append(temp_salary)
                    
                print(f"تم العثور على {len(salaries)} سجل راتب للشهر {filter_month} في جميع السنوات مع {len(employee_records)} موظف بدون سجلات")
            else:
                # إنشاء كائنات مؤقتة لعرض الموظفين بدون رواتب للشهر المحدد
                # احصل على معرفات الموظفين الذين لديهم رواتب في هذا الشهر والسنة
                employee_ids_with_salaries = {s.employee_id for s in salaries}
                
                for employee in active_employees:
                    # إذا لم يكن لديه راتب في هذا الشهر والسنة، أضف سجل مؤقت
                    if employee.id not in employee_ids_with_salaries:
                        temp_salary = Salary(
                            employee_id=employee.id,
                            employee=employee,
                            month=filter_month,
                            year=filter_year,
                            basic_salary=0,
                            allowances=0,
                            deductions=0,
                            bonus=0,
                            net_salary=0
                        )
                        employee_records.append(temp_salary)
                
                if len(salaries) == 0:
                    print(f"لا توجد سجلات رواتب للشهر {filter_month} والسنة {filter_year}. تم إنشاء {len(employee_records)} سجل مؤقت للموظفين النشطين")
                else:
                    print(f"تم العثور على {len(salaries)} سجل راتب للشهر {filter_month} والسنة {filter_year}. تم إنشاء {len(employee_records)} سجل مؤقت للموظفين الآخرين")
        else:
            if show_all_months and show_all_years:
                print(f"تم العثور على {len(salaries)} سجل في جميع الشهور والسنوات")
            elif show_all_months and not show_all_years:
                print(f"تم العثور على {len(salaries)} سجل في جميع الشهور للسنة {filter_year}")
            elif not show_all_months and show_all_years:
                print(f"تم العثور على {len(salaries)} سجل للشهر {filter_month} في جميع السنوات")
            else:
                print(f"تم العثور على {len(salaries)} سجل للشهر {filter_month} والسنة {filter_year}")
    except Exception as e:
        print(f"خطأ في استرجاع بيانات الرواتب: {str(e)}")
        flash(f'حدث خطأ أثناء استرجاع بيانات الرواتب: {str(e)}', 'danger')
    
    # حساب الإحصائيات
    total_basic = sum(s.basic_salary for s in salaries)
    total_allowances = sum(s.allowances for s in salaries)
    total_deductions = sum(s.deductions for s in salaries)
    total_bonus = sum(s.bonus for s in salaries)
    total_net = sum(s.net_salary for s in salaries)
    
    # Get all employees for filter dropdown
    employees = Employee.query.filter_by(status='active').all()
    
    # Get all departments for filter dropdown
    departments = Department.query.order_by(Department.name).all()
    
    # Get available months and years for dropdown
    # عرض جميع الشهور (1-12) بغض النظر عن وجودها في قاعدة البيانات
    available_months = [(i,) for i in range(1, 13)]
    
    # إضافة عدة سنوات ثابتة (3 سنوات سابقة + السنة الحالية + 2 سنوات قادمة)
    fixed_years = [(current_year + i,) for i in range(-3, 3)]  # مثلا: 2022, 2023, 2024, 2025, 2026, 2027
    
    # الحصول على السنوات المتاحة من قاعدة البيانات
    db_years = db.session.query(Salary.year).distinct().order_by(Salary.year.desc()).all()
    
    # دمج السنوات الثابتة مع السنوات الموجودة في قاعدة البيانات وإزالة التكرار
    all_years = set(fixed_years + db_years)
    
    # ترتيب السنوات تنازليًا
    available_years = sorted(list(all_years), reverse=True)
    
    # معالجة السجلات المؤقتة والفعلية لعرضها
    if show_all_months:
        # في حالة "جميع الشهور"، نعرض السجلات الفعلية مع السجلات المؤقتة للموظفين الذين ليس لهم سجلات
        display_records = list(salaries) + employee_records
    else:
        # في حالة الشهر المحدد، عرض السجلات الفعلية مع السجلات المؤقتة للموظفين الآخرين
        display_records = list(salaries) + employee_records
        
    return render_template('salaries/index.html',
                          salaries=display_records,
                          has_salary_data=(len(salaries) > 0),  # علامة توضح ما إذا كانت هناك بيانات رواتب فعلية
                          employees=employees,
                          departments=departments,
                          available_months=available_months,
                          available_years=available_years,
                          selected_month=month,
                          selected_year=year,
                          selected_employee=employee_id,
                          selected_department=department_id,
                          total_basic=total_basic,
                          total_allowances=total_allowances,
                          total_deductions=total_deductions,
                          total_bonus=total_bonus,
                          total_net=total_net)

@salaries_bp.route('/create', methods=['GET', 'POST'])
def create():
    """Create a new salary record"""
    if request.method == 'POST':
        try:
            employee_id = request.form['employee_id']
            month = int(request.form['month'])
            year = int(request.form['year'])
            basic_salary = float(request.form['basic_salary'])
            allowances = float(request.form.get('allowances', 0))
            deductions = float(request.form.get('deductions', 0))
            bonus = float(request.form.get('bonus', 0))
            
            # Calculate net salary
            net_salary = basic_salary + allowances + bonus - deductions
            
            # Check if salary record already exists for this employee/month/year
            existing = Salary.query.filter_by(
                employee_id=employee_id,
                month=month,
                year=year
            ).first()
            
            if existing:
                flash('يوجد سجل راتب لهذا الموظف في نفس الشهر والسنة', 'danger')
                return redirect(url_for('salaries.create'))
            
            # Create new salary record
            salary = Salary(
                employee_id=employee_id,
                month=month,
                year=year,
                basic_salary=basic_salary,
                allowances=allowances,
                deductions=deductions,
                bonus=bonus,
                net_salary=net_salary,
                notes=request.form.get('notes', '')
            )
            
            db.session.add(salary)
            
            # Log the action
            employee = Employee.query.get(employee_id)
            audit = SystemAudit(
                action='create',
                entity_type='salary',
                entity_id=employee_id,
                details=f'تم إنشاء سجل راتب للموظف: {employee.name} لشهر {month}/{year}'
            )
            db.session.add(audit)
            db.session.commit()
            
            flash('تم إنشاء سجل الراتب بنجاح', 'success')
            return redirect(url_for('salaries.index', month=month, year=year))
        
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'danger')
    
    # Get all active employees for dropdown
    employees = Employee.query.filter_by(status='active').all()
    
    # Default to current month and year
    now = datetime.now()
    
    return render_template('salaries/create.html',
                          employees=employees,
                          current_month=now.month,
                          current_year=now.year)

@salaries_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    """تعديل سجل راتب"""
    # الحصول على سجل الراتب
    salary = Salary.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # تحديث بيانات الراتب
            salary.basic_salary = float(request.form['basic_salary'])
            salary.allowances = float(request.form.get('allowances', 0))
            salary.deductions = float(request.form.get('deductions', 0))
            salary.bonus = float(request.form.get('bonus', 0))
            salary.notes = request.form.get('notes', '')
            
            # تحديث الشهر والسنة
            salary.month = int(request.form.get('month', salary.month))
            salary.year = int(request.form.get('year', salary.year))
            
            # إعادة حساب صافي الراتب
            salary.net_salary = salary.basic_salary + salary.allowances + salary.bonus - salary.deductions
            
            # تسجيل العملية
            audit = SystemAudit(
                action='update',
                entity_type='salary',
                entity_id=salary.id,
                details=f'تم تعديل سجل راتب للموظف: {salary.employee.name} لشهر {salary.month}/{salary.year}'
            )
            db.session.add(audit)
            
            db.session.commit()
            
            flash('تم تعديل سجل الراتب بنجاح', 'success')
            return redirect(url_for('salaries.index', month=salary.month, year=salary.year))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء تعديل سجل الراتب: {str(e)}', 'danger')
    
    # الحصول على قائمة الموظفين للاختيار من القائمة المنسدلة
    employees = Employee.query.order_by(Employee.name).all()
    
    # الحصول على السنة الحالية
    current_year = datetime.now().year
    
    return render_template('salaries/edit.html',
                          salary=salary,
                          employees=employees,
                          current_year=current_year)


@salaries_bp.route('/calculate_from_attendance', methods=['POST'])
def calculate_from_attendance():
    """حساب الراتب من سجلات الحضور (API Endpoint)"""
    try:
        data = request.json
        employee_id = int(data.get('employee_id'))
        month = int(data.get('month'))
        year = int(data.get('year'))
        
        # جلب بيانات الموظف
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({
                'success': False,
                'message': 'الموظف غير موجود'
            }), 404
        
        # الحصول على الراتب الأساسي من بيانات الموظف
        basic_salary = employee.basic_salary if employee.basic_salary else 0
        
        if basic_salary == 0:
            return jsonify({
                'success': False,
                'message': 'الراتب الأساسي للموظف غير محدد. يرجى تحديثه من صفحة الموظف.'
            })
        
        # حساب الراتب بناءً على الحضور
        # عدد أيام العمل في الشهر (26 يوم افتراضياً - استبعاد الجمعة في السعودية)
        working_days_in_month = 26
        
        result = calculate_salary_with_attendance(
            employee_id=employee_id,
            month=month,
            year=year,
            basic_salary=basic_salary,
            allowances=0,  # يمكن تمريره من النموذج لاحقاً
            bonus=0,
            other_deductions=0,
            working_days_in_month=working_days_in_month,
            exclude_leave=employee.exclude_leave_from_deduction,
            exclude_sick=employee.exclude_sick_from_deduction
        )
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'حدث خطأ أثناء حساب الراتب'
            })
        
        # إعداد الرد
        response = {
            'success': True,
            'data': {
                'basic_salary': result['basic_salary'],
                'allowances': result['allowances'],
                'bonus': result['bonus'],
                'attendance_deduction': result['attendance_deduction'],
                'other_deductions': result['other_deductions'],
                'total_deductions': result['total_deductions'],
                'net_salary': result['net_salary']
            },
            'attendance_stats': result.get('attendance_stats'),
            'deductible_days': result.get('deductible_days', 0),
            'summary': get_attendance_summary_text(result.get('attendance_stats')) if result.get('attendance_stats') else 'لا توجد بيانات حضور'
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"خطأ في حساب الراتب من الحضور: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        }), 500


@salaries_bp.route('/bulk_calculate_attendance', methods=['POST'])
def bulk_calculate_attendance():
    """حساب رواتب جميع الموظفين في شهر محدد بناءً على الحضور"""
    try:
        data = request.json
        month = int(data.get('month'))
        year = int(data.get('year'))
        department_id = data.get('department_id')  # اختياري
        working_days_in_month = int(data.get('working_days_in_month', 26))  # القيمة المخصصة أو 26 افتراضياً
        
        if not month or not year:
            return jsonify({
                'success': False,
                'message': 'يرجى تحديد الشهر والسنة'
            }), 400
        
        # التحقق من صحة عدد أيام العمل
        if working_days_in_month < 1 or working_days_in_month > 31:
            return jsonify({
                'success': False,
                'message': 'عدد أيام العمل يجب أن يكون بين 1 و 31'
            }), 400
        
        # حساب الفترة الزمنية للشهر المحدد
        from datetime import datetime
        from calendar import monthrange
        first_day = datetime(year, month, 1).date()
        _, last_day_num = monthrange(year, month)
        last_day = datetime(year, month, last_day_num).date()
        
        # جلب معرفات الموظفين الذين لديهم سجلات حضور في هذا الشهر
        from sqlalchemy import distinct
        employees_with_attendance = db.session.query(distinct(Attendance.employee_id)).filter(
            Attendance.date >= first_day,
            Attendance.date <= last_day
        ).all()
        employee_ids_with_attendance = [emp_id[0] for emp_id in employees_with_attendance]
        
        # جلب الموظفين: النشطين + غير النشطين الذين لديهم حضور في هذا الشهر
        if department_id:
            # موظفين نشطين في القسم أو لديهم حضور في الشهر
            employees = Employee.query.filter(
                Employee.department_id == department_id
            ).filter(
                (Employee.status == 'active') | (Employee.id.in_(employee_ids_with_attendance))
            ).all()
        else:
            # موظفين نشطين أو لديهم حضور في الشهر
            employees = Employee.query.filter(
                (Employee.status == 'active') | (Employee.id.in_(employee_ids_with_attendance))
            ).all()
        
        if not employees:
            return jsonify({
                'success': False,
                'message': 'لا يوجد موظفون للمعالجة'
            }), 404
        
        success_count = 0
        error_count = 0
        errors = []
        
        for employee in employees:
            try:
                # التحقق من الراتب الأساسي - نخطر بدلاً من التجاهل
                if not employee.basic_salary or employee.basic_salary == 0:
                    errors.append(f'{employee.name}: تحذير - الراتب الأساسي = 0 (تم الحساب بقيمة 0)')
                    # نستمر في الحساب بدلاً من continue
                
                # التحقق من وجود سجل راتب مسبق
                existing_salary = Salary.query.filter_by(
                    employee_id=employee.id,
                    month=month,
                    year=year
                ).first()
                
                # حساب الراتب من الحضور
                # استخدام 0 إذا كان الراتب الأساسي غير محدد
                basic_salary_value = employee.basic_salary if employee.basic_salary else 0
                attendance_bonus_value = employee.attendance_bonus if employee.attendance_bonus else 0
                result = calculate_salary_with_attendance(
                    employee_id=employee.id,
                    month=month,
                    year=year,
                    basic_salary=basic_salary_value,
                    allowances=0,
                    bonus=0,
                    other_deductions=0,
                    working_days_in_month=working_days_in_month,
                    exclude_leave=employee.exclude_leave_from_deduction if employee.exclude_leave_from_deduction is not None else True,
                    exclude_sick=employee.exclude_sick_from_deduction if employee.exclude_sick_from_deduction is not None else True,
                    attendance_bonus=attendance_bonus_value
                )
                
                if not result:
                    errors.append(f'{employee.name}: فشل حساب الراتب')
                    error_count += 1
                    continue
                
                # إنشاء أو تحديث سجل الراتب
                if existing_salary:
                    # تحديث السجل الموجود
                    existing_salary.basic_salary = result['basic_salary']
                    existing_salary.attendance_bonus = result.get('attendance_bonus', 0)
                    existing_salary.allowances = result['allowances']
                    existing_salary.bonus = result['bonus']
                    existing_salary.deductions = result['total_deductions']
                    existing_salary.net_salary = result['net_salary']
                    existing_salary.attendance_calculated = True
                    existing_salary.attendance_deduction = result['attendance_deduction']
                    
                    if result.get('attendance_stats'):
                        existing_salary.present_days = result['attendance_stats']['present_days']
                        existing_salary.absent_days = result['attendance_stats']['absent_days']
                        existing_salary.leave_days = result['attendance_stats']['leave_days']
                        existing_salary.sick_days = result['attendance_stats']['sick_days']
                else:
                    # إنشاء سجل جديد
                    new_salary = Salary(
                        employee_id=employee.id,
                        month=month,
                        year=year,
                        basic_salary=result['basic_salary'],
                        attendance_bonus=result.get('attendance_bonus', 0),
                        allowances=result['allowances'],
                        bonus=result['bonus'],
                        deductions=result['total_deductions'],
                        net_salary=result['net_salary'],
                        attendance_calculated=True,
                        attendance_deduction=result['attendance_deduction']
                    )
                    
                    if result.get('attendance_stats'):
                        new_salary.present_days = result['attendance_stats']['present_days']
                        new_salary.absent_days = result['attendance_stats']['absent_days']
                        new_salary.leave_days = result['attendance_stats']['leave_days']
                        new_salary.sick_days = result['attendance_stats']['sick_days']
                    
                    db.session.add(new_salary)
                
                success_count += 1
                
            except Exception as e:
                errors.append(f'{employee.name}: {str(e)}')
                error_count += 1
                continue
        
        # حفظ التغييرات
        db.session.commit()
        
        # تسجيل العملية
        audit = SystemAudit(
            action='bulk_calculate_attendance',
            entity_type='salary',
            entity_id=0,
            details=f'تم حساب رواتب {success_count} موظف لشهر {month}/{year}'
        )
        db.session.add(audit)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'تم حساب رواتب {success_count} موظف بنجاح',
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"خطأ في الحساب الجماعي: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        }), 500


@salaries_bp.route('/<int:id>/confirm-delete')
def confirm_delete(id):
    """صفحة تأكيد حذف سجل راتب"""
    salary = Salary.query.get_or_404(id)
    return render_template('salaries/confirm_delete.html', salary=salary)

@salaries_bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    """Delete a salary record"""
    salary = Salary.query.get_or_404(id)
    employee_name = salary.employee.name
    month = salary.month
    year = salary.year
    
    try:
        db.session.delete(salary)
        
        # Log the action
        audit = SystemAudit(
            action='delete',
            entity_type='salary',
            entity_id=id,
            details=f'تم حذف سجل راتب للموظف: {employee_name} لشهر {month}/{year}'
        )
        db.session.add(audit)
        db.session.commit()
        
        flash('تم حذف سجل الراتب بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف سجل الراتب: {str(e)}', 'danger')
    
    return redirect(url_for('salaries.index', month=month, year=year))

@salaries_bp.route('/save_all_smart', methods=['POST'])
def save_all_smart():
    """حفظ جميع الرواتب المُدخلة دفعة واحدة"""
    try:
        data = request.json
        salaries_data = data.get('salaries', [])
        
        if not salaries_data:
            return {'success': False, 'message': 'لا توجد بيانات للحفظ'}
        
        saved_count = 0
        
        for salary_data in salaries_data:
            employee_id = salary_data.get('employee_id')
            month = int(salary_data.get('month'))
            year = int(salary_data.get('year'))
            
            # التحقق من وجود سجل سابق
            existing_salary = Salary.query.filter_by(
                employee_id=employee_id,
                month=month,
                year=year
            ).first()
            
            if existing_salary:
                continue  # تخطي إذا كان موجود
            
            # معالجة القيم
            def parse_value(value):
                if value and str(value).strip():
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return None
                return None
            
            basic_salary = parse_value(salary_data.get('basic_salary'))
            allowances = parse_value(salary_data.get('allowances'))
            deductions = parse_value(salary_data.get('deductions'))
            bonus = parse_value(salary_data.get('bonus'))
            
            # يجب أن يكون الراتب الأساسي موجود
            if basic_salary is None:
                continue
            
            # حساب صافي الراتب
            net_salary = basic_salary
            if allowances is not None:
                net_salary += allowances
            if bonus is not None:
                net_salary += bonus
            if deductions is not None:
                net_salary -= deductions
            
            # إنشاء سجل الراتب
            new_salary = Salary(
                employee_id=employee_id,
                month=month,
                year=year,
                basic_salary=basic_salary,
                allowances=allowances,
                deductions=deductions,
                bonus=bonus,
                net_salary=net_salary
            )
            
            db.session.add(new_salary)
            saved_count += 1
        
        db.session.commit()
        
        return {'success': True, 'message': f'تم حفظ {saved_count} راتب بنجاح', 'saved_count': saved_count}
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'حدث خطأ: {str(e)}'}

@salaries_bp.route('/save_smart', methods=['POST'])
def save_smart():
    """حفظ ذكي للراتب - يحفظ فقط الحقول التي تم إدخال بيانات فيها"""
    try:
        data = request.json
        employee_id = data.get('employee_id')
        month = int(data.get('month'))
        year = int(data.get('year'))
        
        # التحقق من وجود بيانات أساسية
        if not employee_id or not month or not year:
            return {'success': False, 'message': 'بيانات أساسية مفقودة'}
        
        # فحص الحقول المالية
        basic_salary = data.get('basic_salary')
        allowances = data.get('allowances') 
        deductions = data.get('deductions')
        bonus = data.get('bonus')
        
        # التحقق من أن المستخدم أدخل على الأقل الراتب الأساسي
        if not basic_salary or basic_salary == '' or float(basic_salary) <= 0:
            return {'success': False, 'message': 'يجب إدخال الراتب الأساسي'}
        
        # تحويل القيم الفارغة إلى None بدلاً من 0
        def parse_value(value):
            if value is None or value == '' or value == 'null':
                return None
            try:
                parsed = float(value)
                return parsed if parsed != 0 else None
            except (ValueError, TypeError):
                return None
        
        # معالجة القيم
        basic_salary = float(basic_salary)
        allowances = parse_value(allowances)
        deductions = parse_value(deductions) 
        bonus = parse_value(bonus)
        
        # حساب صافي الراتب
        net_salary = basic_salary
        if allowances:
            net_salary += allowances
        if bonus:
            net_salary += bonus
        if deductions:
            net_salary -= deductions
        
        # التحقق من وجود سجل سابق
        existing = Salary.query.filter_by(
            employee_id=employee_id,
            month=month,
            year=year
        ).first()
        
        if existing:
            return {'success': False, 'message': 'يوجد سجل راتب لهذا الموظف في نفس الشهر والسنة'}
        
        # إنشاء سجل جديد
        salary = Salary(
            employee_id=employee_id,
            month=month,
            year=year,
            basic_salary=basic_salary,
            allowances=allowances,
            deductions=deductions,
            bonus=bonus,
            net_salary=net_salary,
            notes=data.get('notes', '')
        )
        
        db.session.add(salary)
        
        # تسجيل العملية
        employee = Employee.query.get(employee_id)
        audit = SystemAudit(
            action='create',
            entity_type='salary',
            entity_id=employee_id,
            details=f'تم إنشاء سجل راتب ذكي للموظف: {employee.name} لشهر {month}/{year}'
        )
        db.session.add(audit)
        db.session.commit()
        
        # إعداد رسالة النجاح مع تفاصيل الحقول المحفوظة
        saved_fields = ['الراتب الأساسي']
        if allowances:
            saved_fields.append('البدلات')
        if deductions:
            saved_fields.append('الخصومات')
        if bonus:
            saved_fields.append('المكافآت')
        
        return {
            'success': True, 
            'message': f'تم حفظ الراتب بنجاح. الحقول المحفوظة: {", ".join(saved_fields)}',
            'net_salary': net_salary
        }
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'حدث خطأ: {str(e)}'}

@salaries_bp.route('/validate_incomplete', methods=['POST'])
def validate_incomplete():
    """التحقق من الحقول غير المكتملة قبل الحفظ"""
    try:
        data = request.json
        
        empty_fields = []
        filled_fields = []
        
        # فحص الحقول
        basic_salary = data.get('basic_salary')
        allowances = data.get('allowances')
        deductions = data.get('deductions') 
        bonus = data.get('bonus')
        
        if not basic_salary or basic_salary == '' or float(basic_salary) <= 0:
            empty_fields.append('الراتب الأساسي')
        else:
            filled_fields.append('الراتب الأساسي')
            
        if not allowances or allowances == '' or float(allowances) <= 0:
            empty_fields.append('البدلات')
        else:
            filled_fields.append('البدلات')
            
        if not deductions or deductions == '' or float(deductions) <= 0:
            empty_fields.append('الخصومات') 
        else:
            filled_fields.append('الخصومات')
            
        if not bonus or bonus == '' or float(bonus) <= 0:
            empty_fields.append('المكافآت')
        else:
            filled_fields.append('المكافآت')
        
        return {
            'empty_fields': empty_fields,
            'filled_fields': filled_fields,
            'has_basic_salary': 'الراتب الأساسي' in filled_fields
        }
        
    except Exception as e:
        return {'error': str(e)}

@salaries_bp.route('/import', methods=['GET', 'POST'])
def import_excel():
    """Import salary records from Excel file"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('لم يتم اختيار ملف', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('لم يتم اختيار ملف', 'danger')
            return redirect(request.url)
        
        month = int(request.form['month'])
        year = int(request.form['year'])
        
        if file and file.filename.endswith(('.xlsx', '.xls')):
            try:
                # Parse Excel file
                salaries_data = parse_salary_excel(file, month, year)
                success_count = 0
                error_count = 0
                
                for data in salaries_data:
                    try:
                        # تنظيف رقم الموظف المستورد (إزالة الأصفار الزائدة والمسافات)
                        employee_id_str = str(data['employee_id']).strip()
                        
                        # محاولة البحث عن الموظف بأكثر من طريقة
                        # 1. البحث المباشر
                        employee = Employee.query.filter_by(employee_id=employee_id_str).first()
                        
                        # 2. البحث بعد إزالة الأصفار من البداية
                        if not employee:
                            clean_id = employee_id_str.lstrip('0')
                            employee = Employee.query.filter_by(employee_id=clean_id).first()
                            
                        # 3. البحث بإضافة أصفار للبداية (حتى 6 أرقام إجمالاً)
                        if not employee:
                            padded_id = employee_id_str.zfill(6)
                            employee = Employee.query.filter_by(employee_id=padded_id).first()
                            
                        # 4. البحث باستخدام like للعثور على تطابق جزئي
                        if not employee:
                            employee = Employee.query.filter(
                                Employee.employee_id.like(f"%{employee_id_str}%")
                            ).first()
                            
                        if not employee:
                            print(f"لم يتم العثور على موظف برقم: {data['employee_id']} بعد محاولة البحث بعدة طرق")
                            raise ValueError(f"لم يتم العثور على موظف برقم: {data['employee_id']}")
                            
                        # التحقق من وجود سجل راتب لهذا الموظف في نفس الشهر والسنة
                        existing = Salary.query.filter_by(
                            employee_id=employee.id,  # استخدام معرف الموظف في قاعدة البيانات
                            month=month,
                            year=year
                        ).first()
                        
                        # تحضير بيانات الراتب
                        salary_data = {
                            'employee_id': employee.id,  # معرف الموظف في قاعدة البيانات وليس رقم الموظف
                            'month': month,
                            'year': year,
                            'basic_salary': data['basic_salary'],
                            'allowances': data['allowances'],
                            'deductions': data['deductions'],
                            'bonus': data['bonus'],
                            'net_salary': data['net_salary']
                        }
                        
                        if 'notes' in data:
                            salary_data['notes'] = data['notes']
                        
                        if existing:
                            # تحديث السجل الموجود
                            existing.basic_salary = data['basic_salary']
                            existing.allowances = data['allowances']
                            existing.deductions = data['deductions']
                            existing.bonus = data['bonus']
                            existing.net_salary = data['net_salary']
                            if 'notes' in data:
                                existing.notes = data['notes']
                            db.session.commit()
                        else:
                            # إنشاء سجل جديد
                            salary = Salary(**salary_data)
                            db.session.add(salary)
                            db.session.commit()
                        
                        success_count += 1
                    except Exception as e:
                        # طباعة رسالة الخطأ للسجل
                        print(f"Error importing salary: {str(e)}")
                        db.session.rollback()
                        error_count += 1
                
                # Log the import
                audit = SystemAudit(
                    action='import',
                    entity_type='salary',
                    entity_id=0,
                    details=f'تم استيراد {success_count} سجل راتب لشهر {month}/{year} بنجاح و {error_count} فشل'
                )
                db.session.add(audit)
                db.session.commit()
                
                if error_count > 0:
                    flash(f'تم استيراد {success_count} سجل راتب بنجاح و {error_count} فشل', 'warning')
                else:
                    flash(f'تم استيراد {success_count} سجل راتب بنجاح', 'success')
                return redirect(url_for('salaries.index', month=month, year=year))
            except Exception as e:
                flash(f'حدث خطأ أثناء استيراد الملف: {str(e)}', 'danger')
        else:
            flash('الملف يجب أن يكون بصيغة Excel (.xlsx, .xls)', 'danger')
    
    # Default to current month and year
    now = datetime.now()
    
    return render_template('salaries/import.html',
                          current_month=now.month,
                          current_year=now.year)

@salaries_bp.route('/export')
def export_excel():
    """تصدير سجلات الرواتب إلى ملف Excel مع دعم التصفية حسب القسم والشهر والسنة"""
    try:
        # الحصول على معلمات التصفية
        month = request.args.get('month')
        year = request.args.get('year')
        department_id = request.args.get('department_id')
        employee_id = request.args.get('employee_id')
        
        # بناء الاستعلام
        query = Salary.query.join(Employee)
        
        # تطبيق المرشحات
        filename_parts = []
        filter_description = []
        
        # تصفية حسب الشهر
        if month and month.isdigit():
            query = query.filter(Salary.month == int(month))
            filename_parts.append(f"month_{month}")
            
            # قاموس لتحويل رقم الشهر إلى اسمه بالعربية
            arabic_months = {
                1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل", 
                5: "مايو", 6: "يونيو", 7: "يوليو", 8: "أغسطس",
                9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
            }
            month_name = arabic_months.get(int(month), str(month))
            filter_description.append(f"شهر: {month_name}")
        else:
            filename_parts.append("all_months")
            filter_description.append("جميع الشهور")
        
        # تصفية حسب السنة
        if year and year.isdigit():
            query = query.filter(Salary.year == int(year))
            filename_parts.append(f"year_{year}")
            filter_description.append(f"سنة: {year}")
        else:
            filename_parts.append("all_years")
            filter_description.append("جميع السنوات")
        
        # تصفية حسب القسم
        department_name = "جميع الأقسام"
        if department_id and department_id.isdigit():
            # البحث عن اسم القسم لاستخدامه في وصف التصفية
            department = Department.query.get(int(department_id))
            if department:
                department_name = department.name
                query = query.filter(Employee.department_id == int(department_id))
                filename_parts.append(f"dept_{department_id}")
                filter_description.append(f"قسم: {department_name}")
            else:
                filename_parts.append("all_depts")
                filter_description.append("جميع الأقسام")
        else:
            filename_parts.append("all_depts")
            filter_description.append("جميع الأقسام")
        
        # تصفية حسب الموظف
        if employee_id and employee_id.isdigit():
            employee = Employee.query.get(int(employee_id))
            if employee:
                query = query.filter(Salary.employee_id == int(employee_id))
                filename_parts.append(f"emp_{employee_id}")
                filter_description.append(f"موظف: {employee.name}")
            
        # ترتيب النتائج حسب اسم الموظف
        query = query.order_by(Employee.name)
        
        # تنفيذ الاستعلام
        salaries = query.all()
        
        # توليد ملف Excel
        output = generate_salary_excel(salaries, filter_description)
        
        # تسجيل عملية التصدير
        filters_text = " - ".join(filter_description)
        audit = SystemAudit(
            action='export',
            entity_type='salary',
            entity_id=0,
            details=f'تم تصدير {len(salaries)} سجل راتب إلى ملف Excel [{filters_text}]'
        )
        db.session.add(audit)
        db.session.commit()
        
        # إنشاء اسم الملف
        filename = f'رواتب_{"_".join(filename_parts)}.xlsx'
        
        return send_file(
            BytesIO(output.getvalue()),
            download_name=filename,
            as_attachment=True,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        flash(f'حدث خطأ أثناء تصدير البيانات: {str(e)}', 'danger')
        return redirect(url_for('salaries.index'))

@salaries_bp.route('/report')
def report():
    """Generate a salary report for a specific month and year"""
    # Get filter parameters
    month = request.args.get('month', str(datetime.now().month))
    year = request.args.get('year', str(datetime.now().year))
    
    # Validate parameters
    if not month.isdigit() or not year.isdigit():
        flash('يرجى اختيار شهر وسنة صالحين', 'danger')
        return redirect(url_for('salaries.index'))
    
    month = int(month)
    year = int(year)
    
    # Get salary records for the selected month and year
    salaries = Salary.query.filter_by(month=month, year=year).all()
    
    if not salaries:
        flash('لا توجد سجلات رواتب للشهر والسنة المحددين', 'warning')
        return redirect(url_for('salaries.index'))
    
    # Get summary statistics
    total_basic = sum(s.basic_salary for s in salaries)
    total_allowances = sum(s.allowances for s in salaries)
    total_deductions = sum(s.deductions for s in salaries)
    total_bonus = sum(s.bonus for s in salaries)
    total_net = sum(s.net_salary for s in salaries)
    
    return render_template('salaries/report.html',
                          salaries=salaries,
                          month=month,
                          year=year,
                          total_basic=total_basic,
                          total_allowances=total_allowances,
                          total_deductions=total_deductions,
                          total_bonus=total_bonus,
                          total_net=total_net)

@salaries_bp.route('/report/pdf')
def report_pdf():
    """Generate a PDF salary report for a specific month and year"""
    try:
        # Get filter parameters
        month = request.args.get('month')
        year = request.args.get('year')
        department_id = request.args.get('department_id')

        if not month or not month.isdigit() or not year or not year.isdigit():
            flash('يرجى اختيار شهر وسنة صالحين', 'danger')
            return redirect(url_for('salaries.index'))
        
        month = int(month)
        year = int(year)
        
  

        # Get salary records for the selected month and year
        salaries = Salary.query.filter_by(month=month, year=year).all()

        if not salaries:
            flash('لا توجد سجلات رواتب للشهر والسنة المحددين', 'warning')
            return redirect(url_for('salaries.index'))
        # Generate PDF report
        # pdf_bytes = generate_salary_report_pdf(salaries, month, year)

        pdf_bytes = generate_salary_summary_pdf(salaries, month, year)
        # Log the export
        audit = SystemAudit(
            action='export_pdf',
            entity_type='salary',
            entity_id=0,
            details=f'تم تصدير تقرير رواتب لشهر {month}/{year} بصيغة PDF'
        )
        db.session.add(audit)
        db.session.commit()
        
        return send_file(
            BytesIO(pdf_bytes),
            download_name=f'salary_report_{month}_{year}.pdf',
            as_attachment=True,
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f'حدث خطأ أثناء إنشاء تقرير PDF: {str(e)}', 'danger')
        return redirect(url_for('salaries.index'))


@salaries_bp.route('/notification/<int:id>/pdf')
def salary_notification_pdf(id):
    """إنشاء إشعار راتب لموظف بصيغة PDF"""
    try:
        # الحصول على سجل الراتب
        salary = Salary.query.get_or_404(id)
        
        # إنشاء ملف PDF
        pdf_bytes = generate_salary_notification_pdf(salary)
        
        # تسجيل العملية - بدون تحديد user_id
        audit = SystemAudit(
            action='generate_notification',
            entity_type='salary',
            entity_id=salary.id,
            details=f'تم إنشاء إشعار راتب للموظف: {salary.employee.name} لشهر {salary.month}/{salary.year}',
            user_id=None  # تحديد القيمة بشكل واضح كقيمة فارغة
        )
        db.session.add(audit)
        db.session.commit()
        
        return send_file(
            BytesIO(pdf_bytes),
            download_name=f'salary_notification_{salary.employee.employee_id}_{salary.month}_{salary.year}.pdf',
            as_attachment=True,
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f'حدث خطأ أثناء إنشاء إشعار الراتب: {str(e)}', 'danger')
        return redirect(url_for('salaries.index'))

@salaries_bp.route('/notification/<int:id>/share_whatsapp')
def share_salary_via_whatsapp(id):
    """مشاركة إشعار راتب عبر الواتس اب باستخدام رابط المشاركة المباشر"""
    try:
        # الحصول على سجل الراتب
        salary = Salary.query.get_or_404(id)
        employee = salary.employee
        
        # الحصول على اسم الشهر بالعربية
        month_names = {
            1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
            5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
            9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
        }
        month_name = month_names.get(salary.month, str(salary.month))
        
        # إنشاء رابط لتحميل ملف PDF
        pdf_url = url_for('salaries.salary_notification_pdf', id=salary.id, _external=True)
        
        # إعداد نص الرسالة مع رابط التحميل
        message_text = f"""
        *إشعار راتب - نُظم*

        السلام عليكم ورحمة الله وبركاته،

        تحية طيبة،

        نود إشعاركم بإيداع راتب شهر {month_name} {salary.year}.

        الموظف: {employee.name}
        الشهر: {month_name} {salary.year}

        صافي الراتب: *{salary.net_salary:.2f}*

        للاطلاع على تفاصيل الراتب، يمكنكم تحميل نسخة الإشعار من الرابط التالي:
        {pdf_url}

        مع تحيات إدارة الموارد البشرية
        نُظم - نظام إدارة متكامل
        """
        
        # تسجيل العملية
        audit = SystemAudit(
            action='share_whatsapp_link',
            entity_type='salary',
            entity_id=salary.id,
            details=f'تم مشاركة إشعار راتب عبر رابط واتس اب للموظف: {employee.name} لشهر {salary.month}/{salary.year}',
            user_id=None
        )
        db.session.add(audit)
        db.session.commit()
        
        # إنشاء رابط الواتس اب مع نص الرسالة
        from urllib.parse import quote
        
        # التحقق مما إذا كان رقم الهاتف متوفر للموظف
        if employee.mobile:
            # تنسيق رقم الهاتف (إضافة رمز الدولة +966 إذا لم يكن موجودًا)
            to_phone = employee.mobile
            if not to_phone.startswith('+'):
                # إذا كان الرقم يبدأ بـ 0، نحذفه ونضيف رمز الدولة
                if to_phone.startswith('0'):
                    to_phone = "+966" + to_phone[1:]
                else:
                    to_phone = "+966" + to_phone
            
            # إنشاء رابط مباشر للموظف
            whatsapp_url = f"https://wa.me/{to_phone}?text={quote(message_text)}"
        else:
            # إذا لم يكن هناك رقم هاتف، استخدم الطريقة العادية
            whatsapp_url = f"https://wa.me/?text={quote(message_text)}"
        
        # إعادة توجيه المستخدم إلى رابط الواتس اب
        return redirect(whatsapp_url)
        
    except Exception as e:
        flash(f'حدث خطأ أثناء مشاركة إشعار الراتب عبر الواتس اب: {str(e)}', 'danger')
        return redirect(url_for('salaries.index'))


@salaries_bp.route('/notification/<int:id>/share_deduction_whatsapp')
def share_deduction_via_whatsapp(id):
    """مشاركة إشعار خصم راتب عبر الواتس اب باستخدام رابط المشاركة المباشر"""
    try:
        # الحصول على سجل الراتب
        salary = Salary.query.get_or_404(id)
        employee = salary.employee
        
        # التحقق من وجود خصم على الراتب
        if salary.deductions <= 0:
            flash('لا يوجد خصم على هذا الراتب', 'warning')
            return redirect(url_for('salaries.index'))
        
        # الحصول على اسم الشهر بالعربية
        month_names = {
            1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
            5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
            9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
        }
        month_name = month_names.get(salary.month, str(salary.month))
        
        # إنشاء رابط لتحميل ملف PDF
        pdf_url = url_for('salaries.salary_notification_pdf', id=salary.id, _external=True)
        
        # إعداد نص الرسالة مع رابط التحميل
        message_text = f"""
        *إشعار خصم على الراتب - نُظم*

        السلام عليكم ورحمة الله وبركاته،

        تحية طيبة،

        نود إبلاغكم عن وجود خصم على راتب شهر {month_name} {salary.year}.

        الموظف: {employee.name}
        الشهر: {month_name} {salary.year}     

        مبلغ الخصم: *{salary.deductions:.2f}*

        الراتب بعد الخصم: {salary.net_salary:.2f}

        للاطلاع على تفاصيل الراتب والخصم، يمكنكم تحميل نسخة الإشعار من الرابط التالي:
        {pdf_url}  

        مع تحيات إدارة الموارد البشرية
        نُظم - نظام إدارة متكامل
        """
        
        # تسجيل العملية
        audit = SystemAudit(
            action='share_deduction_whatsapp_link',
            entity_type='salary',
            entity_id=salary.id,
            details=f'تم مشاركة إشعار خصم عبر رابط واتس اب للموظف: {employee.name} لشهر {salary.month}/{salary.year}',
            user_id=None
        )
        db.session.add(audit)
        db.session.commit()
        
        # إنشاء رابط الواتس اب مع نص الرسالة
        from urllib.parse import quote
        
        # التحقق مما إذا كان رقم الهاتف متوفر للموظف
        if employee.mobile:
            # تنسيق رقم الهاتف (إضافة رمز الدولة +966 إذا لم يكن موجودًا)
            to_phone = employee.mobile
            if not to_phone.startswith('+'):
                # إذا كان الرقم يبدأ بـ 0، نحذفه ونضيف رمز الدولة
                if to_phone.startswith('0'):
                    to_phone = "+966" + to_phone[1:]
                else:
                    to_phone = "+966" + to_phone
            
            # إنشاء رابط مباشر للموظف
            whatsapp_url = f"https://wa.me/{to_phone}?text={quote(message_text)}"
        else:
            # إذا لم يكن هناك رقم هاتف، استخدم الطريقة العادية
            whatsapp_url = f"https://wa.me/?text={quote(message_text)}"
        
        # إعادة توجيه المستخدم إلى رابط الواتس اب
        return redirect(whatsapp_url)
        
    except Exception as e:
        flash(f'حدث خطأ أثناء مشاركة إشعار الخصم عبر الواتس اب: {str(e)}', 'danger')
        return redirect(url_for('salaries.index'))


@salaries_bp.route('/notification/<int:id>/whatsapp', methods=['GET'])
def salary_notification_whatsapp(id):
    """إرسال إشعار راتب لموظف عبر WhatsApp"""
    try:
        # الحصول على سجل الراتب
        salary = Salary.query.get_or_404(id)
        employee = salary.employee
        
        # إرسال الإشعار عبر WhatsApp
        success, message = send_salary_notification_whatsapp(employee, salary)
        
        if success:
            # تسجيل العملية
            audit = SystemAudit(
                action='send_whatsapp_notification',
                entity_type='salary',
                entity_id=salary.id,
                details=f'تم إرسال إشعار راتب عبر WhatsApp للموظف: {employee.name} لشهر {salary.month}/{salary.year}',
                user_id=None
            )
            db.session.add(audit)
            db.session.commit()
            
            flash(f'تم إرسال إشعار الراتب عبر WhatsApp بنجاح للموظف {employee.name}', 'success')
        else:
            flash(f'فشل إرسال إشعار الراتب عبر WhatsApp: {message}', 'danger')
        
        return redirect(url_for('salaries.index'))
    except Exception as e:
        flash(f'حدث خطأ أثناء إرسال إشعار الراتب عبر WhatsApp: {str(e)}', 'danger')
        return redirect(url_for('salaries.index'))


@salaries_bp.route('/notification/<int:id>/deduction/whatsapp', methods=['GET'])
def salary_deduction_notification_whatsapp(id):
    """إرسال إشعار خصم على الراتب لموظف عبر WhatsApp"""
    try:
        # الحصول على سجل الراتب
        salary = Salary.query.get_or_404(id)
        employee = salary.employee
        
        # التحقق من وجود خصم على الراتب
        if salary.deductions <= 0:
            flash('لا يوجد خصم على هذا الراتب', 'warning')
            return redirect(url_for('salaries.index'))
        
        # إرسال الإشعار عبر WhatsApp
        success, message = send_salary_deduction_notification_whatsapp(employee, salary)
        
        if success:
            # تسجيل العملية
            audit = SystemAudit(
                action='send_whatsapp_deduction_notification',
                entity_type='salary',
                entity_id=salary.id,
                details=f'تم إرسال إشعار خصم على الراتب عبر WhatsApp للموظف: {employee.name} لشهر {salary.month}/{salary.year}',
                user_id=None
            )
            db.session.add(audit)
            db.session.commit()
            
            flash(f'تم إرسال إشعار الخصم عبر WhatsApp بنجاح للموظف {employee.name}', 'success')
        else:
            flash(f'فشل إرسال إشعار الخصم عبر WhatsApp: {message}', 'danger')
        
        return redirect(url_for('salaries.index'))
    except Exception as e:
        flash(f'حدث خطأ أثناء إرسال إشعار الخصم عبر WhatsApp: {str(e)}', 'danger')
        return redirect(url_for('salaries.index'))


@salaries_bp.route('/comprehensive_report', methods=['GET', 'POST'])
def comprehensive_report():
    """تقرير شامل للموظفين مع كامل تفاصيل الرواتب"""
    # الحصول على قائمة الأقسام للاختيار
    departments = Department.query.order_by(Department.name).all()
    
    # الحصول على الشهر والسنة الحالية
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    if request.method == 'POST':
        try:
            # الحصول على معلمات التصفية
            department_id = request.form.get('department_id')
            if department_id == '':
                department_id = None
            elif department_id:
                department_id = int(department_id)
            
            employee_id = request.form.get('employee_id')
            if employee_id == '':
                employee_id = None
            elif employee_id:
                employee_id = int(employee_id)
            
            month = request.form.get('month')
            if month:
                month = int(month)
            
            year = request.form.get('year')
            if year:
                year = int(year)
            
            # إنشاء التقرير الشامل
            report_excel = generate_comprehensive_employee_report(
                db.session, department_id, employee_id, month, year
            )
            
            # تسجيل العملية
            filter_description = []
            if department_id:
                dept = Department.query.get(department_id)
                filter_description.append(f"القسم: {dept.name}")
            if employee_id:
                emp = Employee.query.get(employee_id)
                filter_description.append(f"الموظف: {emp.name}")
            if month:
                filter_description.append(f"الشهر: {month}")
            if year:
                filter_description.append(f"السنة: {year}")
            
            filter_str = " | ".join(filter_description) if filter_description else "كافة البيانات"
            
            audit = SystemAudit(
                action='comprehensive_report',
                entity_type='employee',
                entity_id=0,
                details=f'تم إنشاء تقرير شامل للموظفين مع تفاصيل الرواتب ({filter_str})',
                user_id=None
            )
            db.session.add(audit)
            db.session.commit()
            
            # إرسال الملف كتنزيل
            return send_file(
                report_excel,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'تقرير_شامل_الموظفين_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            flash(f'حدث خطأ أثناء إنشاء التقرير الشامل: {str(e)}', 'danger')
            return redirect(url_for('salaries.index'))
    
    # في حالة طلب GET، عرض صفحة اختيار الفلاتر
    return render_template('salaries/comprehensive_report.html',
                          departments=departments,
                          current_month=current_month,
                          current_year=current_year)

@salaries_bp.route('/export/simple_employees_salary')
def export_simple_employees_salary():
    """تصدير بيانات الموظفين مع تفاصيل الرواتب بتنسيق بسيط"""
    # الحصول على معلمات التصفية
    month = request.args.get('month')
    if month:
        month = int(month)
    
    year = request.args.get('year')
    if year:
        year = int(year)
    
    department_id = request.args.get('department_id')
    if department_id:
        department_id = int(department_id)
    
    try:
        # إنشاء ملف Excel بسيط ومرتب للموظفين والرواتب
        output = generate_employee_salary_simple_excel(db.session, month, year, department_id)
        
        # إعداد وصف الفلاتر للسجل
        filter_description = []
        if month:
            filter_description.append(f"الشهر: {month}")
        if year:
            filter_description.append(f"السنة: {year}")
        if department_id:
            department = Department.query.get(department_id)
            if department:
                filter_description.append(f"القسم: {department.name}")
        
        filter_str = " | ".join(filter_description) if filter_description else "كافة البيانات"
        
        # تسجيل العملية
        audit = SystemAudit(
            action='export_simple_employees_salary',
            entity_type='employee_salary',
            entity_id=0,
            details=f'تم تصدير بيانات الموظفين مع تفاصيل الرواتب بتنسيق بسيط ({filter_str})',
            user_id=None
        )
        db.session.add(audit)
        db.session.commit()
        
        # إعداد اسم الملف
        today = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"الموظفين_والرواتب_{today}.xlsx"
        
        # إرسال الملف
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        flash(f'حدث خطأ أثناء تصدير بيانات الموظفين والرواتب: {str(e)}', 'danger')
        return redirect(url_for('salaries.index'))


@salaries_bp.route('/notifications/deduction/batch', methods=['GET', 'POST'])
def batch_deduction_notifications():
    """إرسال إشعارات خصومات مجمعة للموظفين عبر WhatsApp"""
    # الحصول على الأقسام للاختيار
    departments = Department.query.all()
    
    if request.method == 'POST':
        try:
            # الحصول على المعلمات
            department_id = request.form.get('department_id')
            month = request.form.get('month')
            year = request.form.get('year')
            
            if not month or not month.isdigit() or not year or not year.isdigit():
                flash('يرجى اختيار شهر وسنة صالحين', 'danger')
                return redirect(url_for('salaries.batch_deduction_notifications'))
                
            month = int(month)
            year = int(year)
            
            # إذا تم تحديد قسم
            if department_id and department_id != 'all':
                department_id = int(department_id)
                department = Department.query.get(department_id)
                department_name = department.name if department else "غير معروف"
                
                # إرسال إشعارات الخصم عبر WhatsApp
                success_count, failure_count, error_messages = send_batch_deduction_notifications_whatsapp(department_id, month, year)
                
                if success_count > 0:
                    # تسجيل العملية
                    audit = SystemAudit(
                        action='batch_whatsapp_deduction_notifications',
                        entity_type='salary',
                        entity_id=0,
                        details=f'تم إرسال {success_count} إشعار خصم عبر WhatsApp لموظفي قسم {department_name} لشهر {month}/{year}',
                        user_id=None
                    )
                    db.session.add(audit)
                    db.session.commit()
                    
                    # عرض رسالة نجاح مع تفاصيل النجاح/الفشل
                    if failure_count > 0:
                        flash(f'تم إرسال {success_count} إشعار خصم بنجاح و {failure_count} فشل', 'warning')
                        for error in error_messages[:5]:  # عرض أول 5 أخطاء فقط
                            flash(error, 'danger')
                        if len(error_messages) > 5:
                            flash(f'... و {len(error_messages) - 5} أخطاء أخرى', 'danger')
                    else:
                        flash(f'تم إرسال {success_count} إشعار خصم عبر WhatsApp بنجاح', 'success')
                else:
                    flash(f'لم يتم إرسال أي إشعارات خصم. {error_messages[0] if error_messages else "لا توجد خصومات مسجلة لموظفي قسم " + department_name + " في شهر " + str(month) + "/" + str(year)}', 'warning')
            else:
                # إرسال إشعارات الخصم لجميع الموظفين
                success_count, failure_count, error_messages = send_batch_deduction_notifications_whatsapp(None, month, year)
                
                if success_count > 0:
                    # تسجيل العملية
                    audit = SystemAudit(
                        action='batch_whatsapp_deduction_notifications',
                        entity_type='salary',
                        entity_id=0,
                        details=f'تم إرسال {success_count} إشعار خصم عبر WhatsApp لجميع الموظفين لشهر {month}/{year}',
                        user_id=None
                    )
                    db.session.add(audit)
                    db.session.commit()
                    
                    # عرض رسالة نجاح مع تفاصيل النجاح/الفشل
                    if failure_count > 0:
                        flash(f'تم إرسال {success_count} إشعار خصم بنجاح و {failure_count} فشل', 'warning')
                        for error in error_messages[:5]:  # عرض أول 5 أخطاء فقط
                            flash(error, 'danger')
                        if len(error_messages) > 5:
                            flash(f'... و {len(error_messages) - 5} أخطاء أخرى', 'danger')
                    else:
                        flash(f'تم إرسال {success_count} إشعار خصم عبر WhatsApp بنجاح', 'success')
                else:
                    flash(f'لم يتم إرسال أي إشعارات خصم. {error_messages[0] if error_messages else "لا توجد خصومات مسجلة لشهر " + str(month) + "/" + str(year)}', 'warning')
                
            return redirect(url_for('salaries.index', month=month, year=year))
                
        except Exception as e:
            flash(f'حدث خطأ أثناء إرسال إشعارات الخصم: {str(e)}', 'danger')
    
    # Default to current month and year
    now = datetime.now()
    
    return render_template('salaries/batch_deduction_notifications.html',
                          departments=departments,
                          current_month=now.month,
                          current_year=now.year)

@salaries_bp.route('/notifications/batch', methods=['GET', 'POST'])
def batch_salary_notifications():
    """إنشاء إشعارات رواتب مجمعة للموظفين حسب القسم"""
    # الحصول على الأقسام للاختيار
    departments = Department.query.all()
    
    if request.method == 'POST':
        try:
            # الحصول على المعلمات
            department_id = request.form.get('department_id')
            month = request.form.get('month')
            year = request.form.get('year')
            notification_type = request.form.get('notification_type', 'pdf')  # نوع الإشعار (pdf أو whatsapp)
            
            if not month or not month.isdigit() or not year or not year.isdigit():
                flash('يرجى اختيار شهر وسنة صالحين', 'danger')
                return redirect(url_for('salaries.batch_salary_notifications'))
                
            month = int(month)
            year = int(year)
            
            # إذا تم تحديد قسم
            if department_id and department_id != 'all':
                department_id = int(department_id)
                department = Department.query.get(department_id)
                department_name = department.name if department else "غير معروف"
                
                if notification_type == 'whatsapp':
                    # إرسال الإشعارات عبر WhatsApp
                    success_count, failure_count, error_messages = send_batch_salary_notifications_whatsapp(department_id, month, year)
                    
                    if success_count > 0:
                        # تسجيل العملية
                        audit = SystemAudit(
                            action='batch_whatsapp_notifications',
                            entity_type='salary',
                            entity_id=0,
                            details=f'تم إرسال {success_count} إشعار راتب عبر WhatsApp لموظفي قسم {department_name} لشهر {month}/{year}',
                            user_id=None
                        )
                        db.session.add(audit)
                        db.session.commit()
                        
                        # عرض رسالة نجاح مع تفاصيل النجاح/الفشل
                        if failure_count > 0:
                            flash(f'تم إرسال {success_count} إشعار راتب بنجاح و {failure_count} فشل', 'warning')
                            for error in error_messages[:5]:  # عرض أول 5 أخطاء فقط
                                flash(error, 'danger')
                            if len(error_messages) > 5:
                                flash(f'... و {len(error_messages) - 5} أخطاء أخرى', 'danger')
                        else:
                            flash(f'تم إرسال {success_count} إشعار راتب عبر WhatsApp بنجاح', 'success')
                    else:
                        flash(f'لم يتم إرسال أي إشعارات. {error_messages[0] if error_messages else "لا توجد رواتب مسجلة لموظفي قسم " + department_name + " في شهر " + str(month) + "/" + str(year)}', 'warning')
                else:
                    # إنشاء ملفات PDF (السلوك الافتراضي)
                    processed_employees = generate_batch_salary_notifications(department_id, month, year)
                    
                    if processed_employees:
                        # تسجيل العملية
                        audit = SystemAudit(
                            action='batch_notifications',
                            entity_type='salary',
                            entity_id=0,
                            details=f'تم إنشاء {len(processed_employees)} إشعار راتب لموظفي قسم {department_name} لشهر {month}/{year}',
                            user_id=None
                        )
                        db.session.add(audit)
                        db.session.commit()
                        
                        flash(f'تم إنشاء {len(processed_employees)} إشعار راتب لموظفي قسم {department_name}', 'success')
                    else:
                        flash(f'لا توجد رواتب مسجلة لموظفي قسم {department_name} في شهر {month}/{year}', 'warning')
            else:
                # معالجة الإشعارات لجميع الموظفين
                if notification_type == 'whatsapp':
                    # إرسال الإشعارات عبر WhatsApp
                    success_count, failure_count, error_messages = send_batch_salary_notifications_whatsapp(None, month, year)
                    
                    if success_count > 0:
                        # تسجيل العملية
                        audit = SystemAudit(
                            action='batch_whatsapp_notifications',
                            entity_type='salary',
                            entity_id=0,
                            details=f'تم إرسال {success_count} إشعار راتب عبر WhatsApp لجميع الموظفين لشهر {month}/{year}',
                            user_id=None
                        )
                        db.session.add(audit)
                        db.session.commit()
                        
                        # عرض رسالة نجاح مع تفاصيل النجاح/الفشل
                        if failure_count > 0:
                            flash(f'تم إرسال {success_count} إشعار راتب بنجاح و {failure_count} فشل', 'warning')
                            for error in error_messages[:5]:  # عرض أول 5 أخطاء فقط
                                flash(error, 'danger')
                            if len(error_messages) > 5:
                                flash(f'... و {len(error_messages) - 5} أخطاء أخرى', 'danger')
                        else:
                            flash(f'تم إرسال {success_count} إشعار راتب عبر WhatsApp بنجاح', 'success')
                    else:
                        flash(f'لم يتم إرسال أي إشعارات. {error_messages[0] if error_messages else "لا توجد رواتب مسجلة لشهر " + str(month) + "/" + str(year)}', 'warning')
                else:
                    # إنشاء ملفات PDF (السلوك الافتراضي)
                    processed_employees = generate_batch_salary_notifications(None, month, year)
                    
                    if processed_employees:
                        # تسجيل العملية
                        audit = SystemAudit(
                            action='batch_notifications',
                            entity_type='salary',
                            entity_id=0,
                            details=f'تم إنشاء {len(processed_employees)} إشعار راتب لجميع الموظفين لشهر {month}/{year}',
                            user_id=None
                        )
                        db.session.add(audit)
                        db.session.commit()
                        
                        flash(f'تم إنشاء {len(processed_employees)} إشعار راتب لجميع الموظفين', 'success')
                    else:
                        flash(f'لا توجد رواتب مسجلة لشهر {month}/{year}', 'warning')
                    
            return redirect(url_for('salaries.index', month=month, year=year))
                
        except Exception as e:
            flash(f'حدث خطأ أثناء إنشاء إشعارات الرواتب: {str(e)}', 'danger')
    
    # Default to current month and year
    now = datetime.now()
    
    return render_template('salaries/batch_notifications.html',
                          departments=departments,
                          current_month=now.month,
                          current_year=now.year)
