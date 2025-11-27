"""
وحدة تقارير محسنة تستخدم وظائف PDF المحسنة مع دعم كامل للغة العربية
"""
from flask import Blueprint, render_template, request, jsonify, make_response, send_file
from sqlalchemy import func
from datetime import datetime, date, timedelta
from io import BytesIO
from app import db
from models import Department, Employee, Attendance, Salary, Document, SystemAudit
from utils.date_converter import parse_date, format_date_hijri, format_date_gregorian, get_month_name_ar
from utils.excel import generate_employee_excel, generate_salary_excel
# استخدام مولد PDF البسيط الذي يتجنب مشاكل الترميز
# from utils.simple_pdf_generator import generate_salary_report_pdf
# استيراد الدوال المتبقية من الملفات المناسبة
from utils.simple_pdf_generator import create_vehicle_handover_pdf as generate_vehicle_handover_pdf
from utils.salary_notification import generate_salary_notification_pdf

# إنشاء موجه المسارات
enhanced_reports_bp = Blueprint('enhanced_reports', __name__)

@enhanced_reports_bp.route('/')
def index():
    """
    الصفحة الرئيسية للتقارير المحسنة
    """
    from datetime import datetime
    # الحصول على الشهر والسنة الحالية
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # الحصول على قائمة الأقسام والموظفين
    departments = Department.query.all()
    employees = Employee.query.all()
    
    return render_template('reports/enhanced.html', 
                         departments=departments,
                         employees=employees,
                         current_year=current_year,
                         current_month=current_month,
                         get_month_name_ar=get_month_name_ar)

@enhanced_reports_bp.route('/salaries/pdf')
def salaries_pdf():
    """
    تصدير تقرير الرواتب إلى PDF باستخدام النسخة المحسنة
    """
    # الحصول على معلمات الفلتر
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    month = int(request.args.get('month', current_month))
    year = int(request.args.get('year', current_year))
    department_id = request.args.get('department_id', '')
    
    # استعلام الرواتب
    salaries_query = Salary.query.filter_by(
        month=month,
        year=year
    )
    
    # تطبيق فلتر القسم إذا كان محدداً
    if department_id:
        # الحصول على معرفات الموظفين في القسم المحدد
        dept_employee_ids = [e.id for e in Employee.query.filter_by(department_id=department_id).all()]
        salaries_query = salaries_query.filter(Salary.employee_id.in_(dept_employee_ids))
        department = Department.query.get(department_id)
        department_name = department.name if department else ""
    else:
        department_name = "جميع الأقسام"
    
    # الحصول على بيانات الرواتب مع تفاصيل الموظفين
    salaries_data = []
    for salary in salaries_query.all():
        employee = Employee.query.get(salary.employee_id)
        if employee:
            salaries_data.append({
                'employee_name': employee.name,
                'employee_id': employee.employee_id,
                'basic_salary': float(salary.basic_salary),
                'allowances': float(salary.allowances),
                'deductions': float(salary.deductions),
                'bonus': float(salary.bonus),
                'net_salary': float(salary.net_salary)
            })
    
    try:
        # الحصول على اسم الشهر العربي
        month_name = get_month_name_ar(month)
        
        # إنشاء تقرير باستخدام الدالة المتاحة  
        if salaries_data:
            title = f"تقرير رواتب {month_name} {year}"
            pdf_data = generate_salary_notification_pdf([{'title': title, 'data': salaries_data}], title)
        else:
            # إنشاء PDF فارغ للتقرير
            pdf_data = b"PDF Report Not Available"
        
        # إرجاع البيانات كملف تنزيل
        if isinstance(pdf_data, str):
            pdf_bytes = pdf_data.encode('latin-1')
        else:
            pdf_bytes = pdf_data
            
        return send_file(
            BytesIO(pdf_bytes),
            as_attachment=True,
            download_name=f"salaries_report_{year}_{month}.pdf",
            mimetype='application/pdf'
        )
    
    except Exception as e:
        # في حالة حدوث خطأ، نسجله ونعرض رسالة خطأ للمستخدم
        print(f"حدث خطأ أثناء إنشاء تقرير الرواتب: {str(e)}")
        return jsonify({"error": "حدث خطأ أثناء إنشاء تقرير الرواتب"}), 500

@enhanced_reports_bp.route('/salaries/excel')
def salaries_excel():
    """
    تصدير تقرير الرواتب إلى ملف Excel
    """
    # الحصول على معلمات الفلتر
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    month = int(request.args.get('month', current_month))
    year = int(request.args.get('year', current_year))
    department_id = request.args.get('department_id', '')
    
    # استعلام الرواتب
    salaries_query = Salary.query.filter_by(
        month=month,
        year=year
    )
    
    # تطبيق فلتر القسم إذا كان محدداً
    if department_id:
        # الحصول على معرفات الموظفين في القسم المحدد
        dept_employee_ids = [e.id for e in Employee.query.filter_by(department_id=department_id).all()]
        salaries_query = salaries_query.filter(Salary.employee_id.in_(dept_employee_ids))
        department = Department.query.get(department_id)
        department_name = department.name if department else ""
    else:
        department_name = "جميع الأقسام"
    
    # الحصول على بيانات الرواتب كقائمة كائنات
    salaries = salaries_query.all()
    
    try:
        # استدعاء دالة إنشاء ملف Excel
        excel_data = generate_salary_excel(salaries)
        
        # إرجاع البيانات كملف تنزيل
        return send_file(
            excel_data,
            as_attachment=True,
            download_name=f"salaries_report_{year}_{month}.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    except Exception as e:
        # في حالة حدوث خطأ، نسجله ونعرض رسالة خطأ للمستخدم
        print(f"حدث خطأ أثناء إنشاء تقرير الرواتب Excel: {str(e)}")
        return jsonify({"error": "حدث خطأ أثناء إنشاء تقرير الرواتب Excel"}), 500

@enhanced_reports_bp.route('/salary_notification/<int:salary_id>/pdf')
def salary_notification_pdf(salary_id):
    """
    إنشاء إشعار راتب فردي كملف PDF
    """
    # الحصول على الراتب
    salary = Salary.query.get_or_404(salary_id)
    
    # الحصول على معلومات الموظف
    employee = Employee.query.get_or_404(salary.employee_id)
    
    # الحصول على القسم إذا وجد
    department = Department.query.get(employee.department_id) if employee.department_id else None
    
    # إعداد البيانات لإنشاء PDF
    notification_data = {
        'employee_name': employee.name,
        'employee_id': employee.employee_id,
        'job_title': employee.job_title,
        'department_name': department.name if department else "",
        'month_name': get_month_name_ar(salary.month),
        'year': salary.year,
        'basic_salary': salary.basic_salary,
        'allowances': salary.allowances,
        'deductions': salary.deductions,
        'bonus': salary.bonus,
        'net_salary': salary.net_salary,
        'notes': salary.notes,
        'current_date': datetime.now().strftime('%Y-%m-%d')
    }
    
    try:
        # استدعاء الدالة المحسنة لإنشاء إشعار الراتب
        pdf_data = generate_salary_notification_pdf(notification_data)
        
        # إرجاع البيانات كملف تنزيل
        return send_file(
            BytesIO(pdf_data),
            as_attachment=True,
            download_name=f"salary_notification_{employee.employee_id}_{salary.month}_{salary.year}.pdf",
            mimetype='application/pdf'
        )
    
    except Exception as e:
        # في حالة حدوث خطأ، نسجله ونعرض رسالة خطأ للمستخدم
        print(f"حدث خطأ أثناء إنشاء إشعار الراتب: {str(e)}")
        return jsonify({"error": "حدث خطأ أثناء إنشاء إشعار الراتب"}), 500

@enhanced_reports_bp.route('/vehicle_handover/<int:handover_id>/pdf')
def vehicle_handover_pdf(handover_id):
    """
    إنشاء نموذج تسليم/استلام سيارة كملف PDF
    """
    from models import VehicleHandover, Vehicle
    from utils.enhanced_arabic_handover_pdf import create_vehicle_handover_pdf
    
    # الحصول على بيانات التسليم/الاستلام الحقيقية
    handover = VehicleHandover.query.get_or_404(handover_id)
    
    try:
        # إنشاء رابط النموذج الإلكتروني الكامل
        from flask import url_for, request
        form_url = url_for('vehicles.view_handover', id=handover_id, _external=True)
        
        # إضافة رابط النموذج الإلكتروني إلى بيانات التسليم
        handover.form_link = form_url
        
        # استدعاء الدالة المحسنة لإنشاء نموذج تسليم/استلام السيارة
        pdf_buffer = create_vehicle_handover_pdf(handover)
        
        if pdf_buffer is None:
            return jsonify({"error": "فشل في إنشاء ملف PDF"}), 500
        
        # تحديد اسم الملف
        vehicle_plate = handover.vehicle_rel.plate_number if handover.vehicle_rel else "unknown"
        filename = f"vehicle_handover_{handover_id}_{vehicle_plate}.pdf"
        
        # إرجاع البيانات كملف تنزيل
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    
    except Exception as e:
        # في حالة حدوث خطأ، نسجله ونعرض رسالة خطأ للمستخدم
        print(f"حدث خطأ أثناء إنشاء نموذج تسليم/استلام السيارة: {str(e)}")
        return jsonify({"error": "حدث خطأ أثناء إنشاء نموذج تسليم/استلام السيارة"}), 500