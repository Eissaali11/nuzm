"""
لوحة معلومات Power BI احترافية - نُظم
تحليلات متقدمة للحضور والوثائق والسيارات
تصدير Excel بتصميم احترافي
"""
from flask import Blueprint, render_template, request, jsonify, Response, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from models import Employee, Attendance, Document, Vehicle, Department
from sqlalchemy import func, or_, and_, case
from utils.user_helpers import require_module_access
from models import Module, Permission
import csv
from io import StringIO, BytesIO
import json

powerbi_bp = Blueprint('powerbi', __name__, url_prefix='/powerbi')

@powerbi_bp.route('/')
@login_required
def dashboard():
    """الصفحة الرئيسية للوحة معلومات Power BI الاحترافية - بيانات حقيقية"""
    from datetime import datetime, timedelta
    
    # البيانات الأساسية
    departments = Department.query.all()
    total_vehicles = Vehicle.query.count()
    total_documents = Document.query.count()
    
    # فلاتر التاريخ
    date_from_str = request.args.get('date_from')
    date_to_str = request.args.get('date_to')
    department_id = request.args.get('department_id')
    
    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except:
            date_from = datetime.now().date() - timedelta(days=30)
    else:
        date_from = datetime.now().date() - timedelta(days=30)
    
    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except:
            date_to = datetime.now().date()
    else:
        date_to = datetime.now().date()
    
    # جلب الموظفين النشطين فقط الذين لهم حضور في الفترة المحددة
    active_employee_ids_with_attendance = db.session.query(Attendance.employee_id).filter(
        Attendance.date >= date_from,
        Attendance.date <= date_to
    ).distinct().all()
    active_employee_ids_with_attendance = [e[0] for e in active_employee_ids_with_attendance]
    
    # عدد الموظفين النشطين الذين لهم حضور
    active_employees_count = Employee.query.filter(
        Employee.status == 'active',
        Employee.id.in_(active_employee_ids_with_attendance)
    ).count()
    
    total_employees = active_employees_count
    
    # سجلات الحضور للموظفين النشطين فقط
    active_emp_ids = [e.id for e in Employee.query.filter(Employee.status == 'active').all()]
    
    attendance_records = Attendance.query.filter(
        Attendance.date >= date_from,
        Attendance.date <= date_to,
        Attendance.employee_id.in_(active_emp_ids)
    ).all()
    
    attendance_stats = {
        'present': sum(1 for a in attendance_records if a.status == 'present'),
        'absent': sum(1 for a in attendance_records if a.status in ['absent', 'غائب']),
        'leave': sum(1 for a in attendance_records if a.status == 'leave'),
        'sick': sum(1 for a in attendance_records if a.status == 'sick'),
        'total': len(attendance_records)
    }
    attendance_stats['rate'] = round((attendance_stats['present'] / attendance_stats['total']) * 100, 1) if attendance_stats['total'] > 0 else 0
    
    # إحصائيات السيارات
    vehicles = Vehicle.query.all()
    vehicle_stats = {}
    for v in vehicles:
        status = v.status or 'unknown'
        vehicle_stats[status] = vehicle_stats.get(status, 0) + 1
    
    # الحضور حسب القسم - الموظفين النشطين فقط الذين لهم حضور
    dept_attendance = []
    for dept in departments:
        # جلب موظفي القسم النشطين فقط
        emp_ids = db.session.query(Employee.id).join(
            Employee.departments
        ).filter(
            Department.id == dept.id,
            Employee.status == 'active'
        ).all()
        emp_ids = [e[0] for e in emp_ids]
        
        if not emp_ids:
            continue
        
        # الموظفين الذين لهم حضور فعلي في الفترة
        emp_ids_with_attendance = db.session.query(Attendance.employee_id).filter(
            Attendance.date >= date_from,
            Attendance.date <= date_to,
            Attendance.employee_id.in_(emp_ids)
        ).distinct().all()
        emp_ids_with_attendance = [e[0] for e in emp_ids_with_attendance]
        
        if not emp_ids_with_attendance:
            continue
            
        # حساب الحضور
        dept_records = Attendance.query.filter(
            Attendance.date >= date_from,
            Attendance.date <= date_to,
            Attendance.employee_id.in_(emp_ids_with_attendance)
        ).all()
        
        present = sum(1 for a in dept_records if a.status == 'present')
        total = len(dept_records)
        rate = round((present / total) * 100, 1) if total > 0 else 0
        
        dept_attendance.append({
            'name': dept.name,
            'employee_count': len(emp_ids_with_attendance),
            'present': present,
            'total': total,
            'rate': rate
        })
    
    # ترتيب حسب نسبة الحضور
    dept_attendance.sort(key=lambda x: x['rate'], reverse=True)
    
    # إحصائيات الوثائق
    today = datetime.now().date()
    thirty_days = today + timedelta(days=30)
    
    docs = Document.query.all()
    doc_stats = {
        'valid': 0,
        'expiring': 0,
        'expired': 0,
        'total': len(docs)
    }
    
    for doc in docs:
        if hasattr(doc, 'expiry_date') and doc.expiry_date:
            if doc.expiry_date < today:
                doc_stats['expired'] += 1
            elif doc.expiry_date <= thirty_days:
                doc_stats['expiring'] += 1
            else:
                doc_stats['valid'] += 1
        else:
            doc_stats['valid'] += 1
    
    return render_template('powerbi/dashboard.html',
        departments=departments,
        total_employees=total_employees,
        total_vehicles=total_vehicles,
        total_documents=total_documents,
        attendance_stats=attendance_stats,
        vehicle_stats=vehicle_stats,
        dept_attendance=dept_attendance,
        doc_stats=doc_stats,
        date_from=date_from,
        date_to=date_to
    )

@powerbi_bp.route('/api/attendance-summary')
@login_required
@require_module_access(Module.ATTENDANCE, Permission.VIEW)
def attendance_summary():
    """ملخص الحضور مع تحليلات متقدمة"""
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    department_id = request.args.get('department_id')
    
    try:
        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        else:
            date_from = datetime.now().date() - timedelta(days=30)
        
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        else:
            date_to = datetime.now().date()
        
        query = Attendance.query.filter(
            Attendance.date >= date_from,
            Attendance.date <= date_to
        )
        
        if department_id:
            employee_ids = [e.id for e in Employee.query.filter_by(department_id=department_id).all()]
            query = query.filter(Attendance.employee_id.in_(employee_ids))
        
        attendance_records = query.all()
        
        present = sum(1 for a in attendance_records if a.status == 'present')
        absent = sum(1 for a in attendance_records if a.status in ['absent', 'غائب'])
        leave = sum(1 for a in attendance_records if a.status == 'leave')
        sick = sum(1 for a in attendance_records if a.status == 'sick')
        total = len(attendance_records)
        
        attendance_rate = round((present / total) * 100, 1) if total > 0 else 0
        absence_rate = round((absent / total) * 100, 1) if total > 0 else 0
        
        prev_date_from = date_from - timedelta(days=30)
        prev_query = Attendance.query.filter(
            Attendance.date >= prev_date_from,
            Attendance.date < date_from
        )
        if department_id:
            prev_query = prev_query.filter(Attendance.employee_id.in_(employee_ids))
        
        prev_records = prev_query.all()
        prev_present = sum(1 for a in prev_records if a.status == 'present')
        prev_total = len(prev_records)
        prev_rate = round((prev_present / prev_total) * 100, 1) if prev_total > 0 else 0
        
        trend = round(attendance_rate - prev_rate, 1)
        trend_direction = 'up' if trend > 0 else 'down' if trend < 0 else 'stable'
        
        return jsonify({
            'success': True,
            'data': {
                'present': present,
                'absent': absent,
                'leave': leave,
                'sick': sick,
                'total': total,
                'attendance_rate': attendance_rate,
                'absence_rate': absence_rate,
                'trend': {
                    'value': abs(trend),
                    'direction': trend_direction,
                    'previous_rate': prev_rate
                },
                'date_range': {
                    'from': date_from.strftime('%Y-%m-%d'),
                    'to': date_to.strftime('%Y-%m-%d')
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@powerbi_bp.route('/api/attendance-by-department')
@login_required
@require_module_access(Module.ATTENDANCE, Permission.VIEW)
def attendance_by_department():
    """الحضور حسب القسم مع تحليل مفصل"""
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    try:
        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        else:
            date_from = datetime.now().date() - timedelta(days=30)
        
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        else:
            date_to = datetime.now().date()
        
        departments_data = []
        departments = Department.query.all()
        
        for dept in departments:
            employees = Employee.query.filter_by(department_id=dept.id).all()
            employee_ids = [e.id for e in employees]
            
            if not employee_ids:
                continue
            
            attendance_records = Attendance.query.filter(
                Attendance.date >= date_from,
                Attendance.date <= date_to,
                Attendance.employee_id.in_(employee_ids)
            ).all()
            
            present = sum(1 for a in attendance_records if a.status == 'present')
            absent = sum(1 for a in attendance_records if a.status in ['absent', 'غائب'])
            leave = sum(1 for a in attendance_records if a.status == 'leave')
            sick = sum(1 for a in attendance_records if a.status == 'sick')
            total = len(attendance_records)
            
            attendance_rate = round((present / total) * 100, 1) if total > 0 else 0
            
            performance = 'excellent' if attendance_rate >= 90 else 'good' if attendance_rate >= 75 else 'average' if attendance_rate >= 60 else 'poor'
            
            departments_data.append({
                'department': dept.name,
                'department_id': dept.id,
                'employee_count': len(employees),
                'present': present,
                'absent': absent,
                'leave': leave,
                'sick': sick,
                'total': total,
                'attendance_rate': attendance_rate,
                'performance': performance
            })
        
        departments_data.sort(key=lambda x: x['attendance_rate'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': departments_data,
            'summary': {
                'total_departments': len(departments_data),
                'avg_attendance_rate': round(sum(d['attendance_rate'] for d in departments_data) / len(departments_data), 1) if departments_data else 0,
                'best_department': departments_data[0]['department'] if departments_data else None,
                'worst_department': departments_data[-1]['department'] if departments_data else None
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@powerbi_bp.route('/api/documents-status')
@login_required
@require_module_access(Module.EMPLOYEES, Permission.VIEW)
def documents_status():
    """حالة الوثائق المطلوبة مع تحليل شامل"""
    try:
        required_docs = [
            {'type': 'الهوية الوطنية', 'priority': 'high'},
            {'type': 'جواز السفر', 'priority': 'high'},
            {'type': 'رخصة القيادة', 'priority': 'medium'},
            {'type': 'وثيقة التأمين', 'priority': 'medium'}
        ]
        
        total_employees = Employee.query.count()
        documents_summary = []
        
        today = datetime.now().date()
        thirty_days_later = today + timedelta(days=30)
        
        for doc_info in required_docs:
            doc_type = doc_info['type']
            
            docs = Document.query.filter(
                Document.document_type.ilike(f'%{doc_type}%')
            ).all()
            
            available = len(docs)
            missing = total_employees - available
            
            expiring_soon = 0
            expired = 0
            valid = 0
            
            for doc in docs:
                if hasattr(doc, 'expiry_date') and doc.expiry_date:
                    if doc.expiry_date < today:
                        expired += 1
                    elif doc.expiry_date <= thirty_days_later:
                        expiring_soon += 1
                    else:
                        valid += 1
                else:
                    valid += 1
            
            documents_summary.append({
                'type': doc_type,
                'priority': doc_info['priority'],
                'available': available,
                'missing': missing,
                'valid': valid,
                'expiring_soon': expiring_soon,
                'expired': expired,
                'completion_rate': round((available / total_employees * 100), 1) if total_employees > 0 else 0,
                'health_score': round(((valid) / available * 100), 1) if available > 0 else 0
            })
        
        total_available = sum(d['available'] for d in documents_summary)
        total_required = total_employees * len(required_docs)
        overall_completion = round((total_available / total_required * 100), 1) if total_required > 0 else 0
        
        return jsonify({
            'success': True,
            'data': documents_summary,
            'total_employees': total_employees,
            'overall_completion': overall_completion,
            'total_expiring_soon': sum(d['expiring_soon'] for d in documents_summary),
            'total_expired': sum(d['expired'] for d in documents_summary),
            'total_missing': sum(d['missing'] for d in documents_summary)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@powerbi_bp.route('/api/employee-documents')
@login_required
@require_module_access(Module.EMPLOYEES, Permission.VIEW)
def employee_documents():
    """قائمة الموظفين والوثائق الناقصة مع تفاصيل"""
    department_id = request.args.get('department_id')
    limit = request.args.get('limit', 50, type=int)
    
    try:
        query = Employee.query
        
        if department_id:
            query = query.filter_by(department_id=department_id)
        
        employees = query.limit(limit).all()
        
        required_docs = ['الهوية الوطنية', 'جواز السفر', 'رخصة القيادة', 'وثيقة التأمين']
        employees_data = []
        
        for emp in employees:
            docs = Document.query.filter_by(employee_id=emp.id).all()
            doc_types = [d.document_type for d in docs]
            
            missing_docs = []
            for req_doc in required_docs:
                if not any(req_doc in dt for dt in doc_types):
                    missing_docs.append(req_doc)
            
            completion_rate = round(((len(required_docs) - len(missing_docs)) / len(required_docs)) * 100, 0)
            
            employees_data.append({
                'id': emp.id,
                'name': emp.name,
                'employee_id': emp.employee_id or '-',
                'department': emp.department.name if emp.department else 'بدون قسم',
                'total_docs': len(docs),
                'missing_docs': missing_docs,
                'missing_count': len(missing_docs),
                'documents_complete': len(missing_docs) == 0,
                'completion_rate': completion_rate
            })
        
        employees_data.sort(key=lambda x: x['missing_count'], reverse=True)
        
        complete_count = sum(1 for e in employees_data if e['documents_complete'])
        incomplete_count = len(employees_data) - complete_count
        
        return jsonify({
            'success': True,
            'data': employees_data,
            'summary': {
                'total': len(employees_data),
                'complete': complete_count,
                'incomplete': incomplete_count,
                'completion_rate': round((complete_count / len(employees_data)) * 100, 1) if employees_data else 0
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@powerbi_bp.route('/api/vehicles-summary')
@login_required
@require_module_access(Module.VEHICLES, Permission.VIEW)
def vehicles_summary():
    """ملخص حالة السيارات مع تحليل الأسطول"""
    try:
        vehicles = Vehicle.query.all()
        
        statuses = {}
        brands = {}
        years = {}
        
        for vehicle in vehicles:
            status = vehicle.status or 'unknown'
            statuses[status] = statuses.get(status, 0) + 1
            
            if hasattr(vehicle, 'make') and vehicle.make:
                brands[vehicle.make] = brands.get(vehicle.make, 0) + 1
            
            if hasattr(vehicle, 'year') and vehicle.year:
                years[str(vehicle.year)] = years.get(str(vehicle.year), 0) + 1
        
        vehicles_by_status = []
        status_labels = {
            'in_project': 'في المشروع',
            'in_workshop': 'في الورشة',
            'out_of_service': 'خارج الخدمة',
            'accident': 'حادث',
            'unknown': 'غير محدد'
        }
        
        for status, count in statuses.items():
            vehicles_by_status.append({
                'status': status_labels.get(status, status),
                'status_key': status,
                'count': count,
                'percentage': round((count / len(vehicles) * 100), 1) if vehicles else 0
            })
        
        vehicles_by_brand = [{'brand': b, 'count': c} for b, c in sorted(brands.items(), key=lambda x: x[1], reverse=True)]
        
        total = len(vehicles)
        in_project = statuses.get('in_project', 0)
        in_workshop = statuses.get('in_workshop', 0)
        out_of_service = statuses.get('out_of_service', 0)
        accident = statuses.get('accident', 0)
        
        fleet_health = 'excellent' if in_project >= total * 0.8 else 'good' if in_project >= total * 0.6 else 'average' if in_project >= total * 0.4 else 'poor'
        
        return jsonify({
            'success': True,
            'data': {
                'by_status': vehicles_by_status,
                'by_brand': vehicles_by_brand[:5],
                'total_vehicles': total,
                'in_project': in_project,
                'in_workshop': in_workshop,
                'out_of_service': out_of_service,
                'accident': accident,
                'utilization_rate': round((in_project / total) * 100, 1) if total > 0 else 0,
                'fleet_health': fleet_health
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@powerbi_bp.route('/api/vehicle-operations-summary')
@login_required
@require_module_access(Module.VEHICLES, Permission.VIEW)
def vehicle_operations_summary():
    """ملخص عمليات السيارات"""
    try:
        vehicles = Vehicle.query.all()
        
        handovers = sum(1 for v in vehicles if v.handover_records)
        in_workshop = sum(1 for v in vehicles if v.status == 'in_workshop')
        in_project = sum(1 for v in vehicles if v.status == 'in_project')
        out_of_service = sum(1 for v in vehicles if v.status == 'out_of_service')
        accident = sum(1 for v in vehicles if v.status == 'accident')
        
        operations_data = [
            {'type': 'في المشروع', 'count': in_project, 'color': '#38ef7d'},
            {'type': 'مستلمة', 'count': handovers, 'color': '#667eea'},
            {'type': 'في الورشة', 'count': in_workshop, 'color': '#fbbf24'},
            {'type': 'خارج الخدمة', 'count': out_of_service, 'color': '#ef4444'},
            {'type': 'حادث', 'count': accident, 'color': '#ff6b6b'}
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'by_type': operations_data,
                'total_vehicles': len(vehicles),
                'summary': {
                    'active_percentage': round((in_project / len(vehicles)) * 100, 1) if vehicles else 0,
                    'handover_percentage': round((handovers / len(vehicles)) * 100, 1) if vehicles else 0
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@powerbi_bp.route('/api/export-data')
@login_required
def export_data():
    """تصدير البيانات بصيغة Excel احترافية بتصميم Power BI"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Border, Side, Alignment, GradientFill
    from openpyxl.utils import get_column_letter
    from openpyxl.chart import BarChart, PieChart, DoughnutChart, Reference
    from openpyxl.chart.label import DataLabelList
    from openpyxl.chart.series import DataPoint
    from openpyxl.drawing.fill import PatternFillProperties, ColorChoice
    from sqlalchemy import func
    
    data_type = request.args.get('type', 'all')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    try:
        wb = Workbook()
        
        dark_fill = PatternFill(start_color="1E1E2E", end_color="1E1E2E", fill_type="solid")
        dark_header = PatternFill(start_color="2D2D44", end_color="2D2D44", fill_type="solid")
        gold_fill = PatternFill(start_color="F2C811", end_color="F2C811", fill_type="solid")
        card_fill = PatternFill(start_color="252538", end_color="252538", fill_type="solid")
        
        gold_font = Font(bold=True, color="F2C811", size=12)
        white_font = Font(bold=True, color="FFFFFF", size=11)
        title_font = Font(bold=True, color="F2C811", size=22)
        subtitle_font = Font(bold=True, color="AAAAAA", size=10)
        kpi_value_font = Font(bold=True, color="FFFFFF", size=28)
        kpi_label_font = Font(color="AAAAAA", size=10)
        
        green_fill = PatternFill(start_color="38EF7D", end_color="38EF7D", fill_type="solid")
        red_fill = PatternFill(start_color="EF4444", end_color="EF4444", fill_type="solid")
        orange_fill = PatternFill(start_color="FFA500", end_color="FFA500", fill_type="solid")
        blue_fill = PatternFill(start_color="667EEA", end_color="667EEA", fill_type="solid")
        
        success_fill = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")
        warning_fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")
        danger_fill = PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid")
        info_fill = PatternFill(start_color="D1ECF1", end_color="D1ECF1", fill_type="solid")
        alt_row_fill = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid")
        
        gold_border = Border(
            left=Side(style='medium', color='F2C811'),
            right=Side(style='medium', color='F2C811'),
            top=Side(style='medium', color='F2C811'),
            bottom=Side(style='medium', color='F2C811')
        )
        thin_border = Border(
            left=Side(style='thin', color='444444'),
            right=Side(style='thin', color='444444'),
            top=Side(style='thin', color='444444'),
            bottom=Side(style='thin', color='444444')
        )
        
        total_employees = Employee.query.count()
        total_vehicles = Vehicle.query.count()
        in_project_vehicles = Vehicle.query.filter_by(status='in_project').count()
        in_workshop_vehicles = Vehicle.query.filter_by(status='in_workshop').count()
        out_of_service_vehicles = Vehicle.query.filter_by(status='out_of_service').count()
        accident_vehicles = Vehicle.query.filter_by(status='accident').count()
        total_documents = Document.query.count()
        total_departments = Department.query.count()
        
        d_from = datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else (datetime.now().date() - timedelta(days=30))
        d_to = datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else datetime.now().date()
        
        attendance_stats = db.session.query(
            Attendance.status,
            func.count(Attendance.id)
        ).filter(
            Attendance.date >= d_from,
            Attendance.date <= d_to
        ).group_by(Attendance.status).all()
        
        att_data = {'present': 0, 'absent': 0, 'leave': 0, 'sick': 0}
        for status, count in attendance_stats:
            if status == 'present':
                att_data['present'] = count
            elif status in ['absent', 'غائب']:
                att_data['absent'] += count
            elif status == 'leave':
                att_data['leave'] = count
            elif status == 'sick':
                att_data['sick'] = count
        total_attendance = sum(att_data.values())
        
        ws = wb.active
        ws.title = "Power BI Dashboard"
        ws.sheet_view.rightToLeft = True
        
        for row in range(1, 60):
            for col in range(1, 20):
                ws.cell(row=row, column=col).fill = dark_fill
        
        for col in range(1, 20):
            ws.column_dimensions[get_column_letter(col)].width = 12
        
        ws.merge_cells('A1:S1')
        ws['A1'] = "نُـظـم | لوحة التحليلات الاحترافية"
        ws['A1'].font = title_font
        ws['A1'].fill = dark_fill
        ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[1].height = 50
        
        ws.merge_cells('A2:S2')
        ws['A2'] = f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')} | الفترة: {d_from} إلى {d_to}"
        ws['A2'].font = subtitle_font
        ws['A2'].fill = dark_fill
        ws['A2'].alignment = Alignment(horizontal='center', vertical='center')
        
        kpi_data = [
            ("إجمالي الموظفين", total_employees, "👥", "A"),
            ("إجمالي السيارات", total_vehicles, "🚗", "E"),
            ("في المشاريع", in_project_vehicles, "✅", "I"),
            ("إجمالي الأقسام", total_departments, "🏢", "M"),
        ]
        
        for label, value, icon, start_col in kpi_data:
            col_idx = ord(start_col) - ord('A') + 1
            end_col = get_column_letter(col_idx + 2)
            
            ws.merge_cells(f'{start_col}4:{end_col}4')
            ws[f'{start_col}4'] = f"{icon} {label}"
            ws[f'{start_col}4'].font = kpi_label_font
            ws[f'{start_col}4'].fill = card_fill
            ws[f'{start_col}4'].alignment = Alignment(horizontal='center', vertical='center')
            ws[f'{start_col}4'].border = gold_border
            
            ws.merge_cells(f'{start_col}5:{end_col}5')
            ws[f'{start_col}5'] = value
            ws[f'{start_col}5'].font = kpi_value_font
            ws[f'{start_col}5'].fill = card_fill
            ws[f'{start_col}5'].alignment = Alignment(horizontal='center', vertical='center')
            ws[f'{start_col}5'].border = gold_border
            
            ws.row_dimensions[4].height = 25
            ws.row_dimensions[5].height = 40
        
        ws.merge_cells('A7:H7')
        ws['A7'] = "📊 توزيع حالات الحضور"
        ws['A7'].font = gold_font
        ws['A7'].fill = dark_header
        ws['A7'].alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[7].height = 30
        
        att_headers = ['الحالة', 'العدد', 'النسبة', 'الرسم']
        for i, h in enumerate(att_headers):
            cell = ws.cell(row=8, column=i+1)
            cell.value = h
            cell.font = gold_font
            cell.fill = dark_header
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = thin_border
        
        att_rows = [
            ('حاضر ✅', att_data['present'], green_fill),
            ('غائب ❌', att_data['absent'], red_fill),
            ('إجازة 📋', att_data['leave'], blue_fill),
            ('مريض 🏥', att_data['sick'], orange_fill)
        ]
        
        for idx, (label, count, fill) in enumerate(att_rows, start=9):
            pct = round((count / total_attendance * 100), 1) if total_attendance > 0 else 0
            
            ws.cell(row=idx, column=1).value = label
            ws.cell(row=idx, column=1).font = white_font
            ws.cell(row=idx, column=1).fill = card_fill
            ws.cell(row=idx, column=1).alignment = Alignment(horizontal='center')
            ws.cell(row=idx, column=1).border = thin_border
            
            ws.cell(row=idx, column=2).value = count
            ws.cell(row=idx, column=2).font = white_font
            ws.cell(row=idx, column=2).fill = card_fill
            ws.cell(row=idx, column=2).alignment = Alignment(horizontal='center')
            ws.cell(row=idx, column=2).border = thin_border
            
            ws.cell(row=idx, column=3).value = f"{pct}%"
            ws.cell(row=idx, column=3).font = white_font
            ws.cell(row=idx, column=3).fill = card_fill
            ws.cell(row=idx, column=3).alignment = Alignment(horizontal='center')
            ws.cell(row=idx, column=3).border = thin_border
            
            bar_width = int(pct / 5) if pct > 0 else 1
            ws.cell(row=idx, column=4).value = "█" * bar_width
            ws.cell(row=idx, column=4).font = Font(color=fill.fgColor.rgb[2:] if fill.fgColor else "FFFFFF", size=10)
            ws.cell(row=idx, column=4).fill = card_fill
            ws.cell(row=idx, column=4).border = thin_border
        
        pie1 = PieChart()
        pie1.title = "توزيع الحضور"
        labels1 = Reference(ws, min_col=1, min_row=9, max_row=12)
        data1 = Reference(ws, min_col=2, min_row=8, max_row=12)
        pie1.add_data(data1, titles_from_data=True)
        pie1.set_categories(labels1)
        pie1.width = 10
        pie1.height = 8
        pie1.dataLabels = DataLabelList()
        pie1.dataLabels.showPercent = True
        pie1.dataLabels.showCatName = True
        ws.add_chart(pie1, "E8")
        
        ws.merge_cells('A15:H15')
        ws['A15'] = "🚗 حالة أسطول السيارات"
        ws['A15'].font = gold_font
        ws['A15'].fill = dark_header
        ws['A15'].alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[15].height = 30
        
        veh_headers = ['الحالة', 'العدد', 'النسبة', 'الرسم']
        for i, h in enumerate(veh_headers):
            cell = ws.cell(row=16, column=i+1)
            cell.value = h
            cell.font = gold_font
            cell.fill = dark_header
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = thin_border
        
        veh_rows = [
            ('في المشروع 🟢', in_project_vehicles, green_fill),
            ('في الورشة 🟡', in_workshop_vehicles, orange_fill),
            ('خارج الخدمة 🔴', out_of_service_vehicles, red_fill),
            ('حادث ⚠️', accident_vehicles, blue_fill)
        ]
        
        for idx, (label, count, fill) in enumerate(veh_rows, start=17):
            pct = round((count / total_vehicles * 100), 1) if total_vehicles > 0 else 0
            
            ws.cell(row=idx, column=1).value = label
            ws.cell(row=idx, column=1).font = white_font
            ws.cell(row=idx, column=1).fill = card_fill
            ws.cell(row=idx, column=1).alignment = Alignment(horizontal='center')
            ws.cell(row=idx, column=1).border = thin_border
            
            ws.cell(row=idx, column=2).value = count
            ws.cell(row=idx, column=2).font = white_font
            ws.cell(row=idx, column=2).fill = card_fill
            ws.cell(row=idx, column=2).alignment = Alignment(horizontal='center')
            ws.cell(row=idx, column=2).border = thin_border
            
            ws.cell(row=idx, column=3).value = f"{pct}%"
            ws.cell(row=idx, column=3).font = white_font
            ws.cell(row=idx, column=3).fill = card_fill
            ws.cell(row=idx, column=3).alignment = Alignment(horizontal='center')
            ws.cell(row=idx, column=3).border = thin_border
            
            bar_width = int(pct / 5) if pct > 0 else 1
            ws.cell(row=idx, column=4).value = "█" * bar_width
            ws.cell(row=idx, column=4).font = Font(color=fill.fgColor.rgb[2:] if fill.fgColor else "FFFFFF", size=10)
            ws.cell(row=idx, column=4).fill = card_fill
            ws.cell(row=idx, column=4).border = thin_border
        
        doughnut1 = DoughnutChart()
        doughnut1.title = "حالة الأسطول"
        labels2 = Reference(ws, min_col=1, min_row=17, max_row=20)
        data2 = Reference(ws, min_col=2, min_row=16, max_row=20)
        doughnut1.add_data(data2, titles_from_data=True)
        doughnut1.set_categories(labels2)
        doughnut1.width = 10
        doughnut1.height = 8
        doughnut1.dataLabels = DataLabelList()
        doughnut1.dataLabels.showPercent = True
        ws.add_chart(doughnut1, "E15")
        
        departments = Department.query.all()
        all_employees_list = Employee.query.all()
        dept_emp_map = {}
        for e in all_employees_list:
            if e.department_id:
                if e.department_id not in dept_emp_map:
                    dept_emp_map[e.department_id] = []
                dept_emp_map[e.department_id].append(e.id)
        
        ws.merge_cells('A23:H23')
        ws['A23'] = "🏢 نسبة الحضور حسب القسم"
        ws['A23'].font = gold_font
        ws['A23'].fill = dark_header
        ws['A23'].alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[23].height = 30
        
        dept_headers = ['القسم', 'الموظفين', 'الحضور', 'النسبة', 'التقييم']
        for i, h in enumerate(dept_headers):
            cell = ws.cell(row=24, column=i+1)
            cell.value = h
            cell.font = gold_font
            cell.fill = dark_header
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = thin_border
        
        dept_row = 25
        for dept in departments[:10]:
            emp_ids = dept_emp_map.get(dept.id, [])
            if not emp_ids:
                continue
            
            dept_attendance = Attendance.query.filter(
                Attendance.date >= d_from,
                Attendance.date <= d_to,
                Attendance.employee_id.in_(emp_ids)
            ).all()
            
            present = sum(1 for a in dept_attendance if a.status == 'present')
            total = len(dept_attendance)
            rate = round((present / total) * 100) if total > 0 else 0
            
            if rate >= 90:
                rating = "ممتاز ⭐"
                rating_fill = green_fill
            elif rate >= 75:
                rating = "جيد 👍"
                rating_fill = blue_fill
            elif rate >= 60:
                rating = "متوسط ⚡"
                rating_fill = orange_fill
            else:
                rating = "يحتاج تحسين ⚠️"
                rating_fill = red_fill
            
            ws.cell(row=dept_row, column=1).value = dept.name
            ws.cell(row=dept_row, column=1).font = white_font
            ws.cell(row=dept_row, column=1).fill = card_fill
            ws.cell(row=dept_row, column=1).border = thin_border
            
            ws.cell(row=dept_row, column=2).value = len(emp_ids)
            ws.cell(row=dept_row, column=2).font = white_font
            ws.cell(row=dept_row, column=2).fill = card_fill
            ws.cell(row=dept_row, column=2).alignment = Alignment(horizontal='center')
            ws.cell(row=dept_row, column=2).border = thin_border
            
            ws.cell(row=dept_row, column=3).value = present
            ws.cell(row=dept_row, column=3).font = white_font
            ws.cell(row=dept_row, column=3).fill = card_fill
            ws.cell(row=dept_row, column=3).alignment = Alignment(horizontal='center')
            ws.cell(row=dept_row, column=3).border = thin_border
            
            ws.cell(row=dept_row, column=4).value = f"{rate}%"
            ws.cell(row=dept_row, column=4).font = white_font
            ws.cell(row=dept_row, column=4).fill = card_fill
            ws.cell(row=dept_row, column=4).alignment = Alignment(horizontal='center')
            ws.cell(row=dept_row, column=4).border = thin_border
            
            ws.cell(row=dept_row, column=5).value = rating
            ws.cell(row=dept_row, column=5).font = Font(bold=True, color="FFFFFF", size=10)
            ws.cell(row=dept_row, column=5).fill = rating_fill
            ws.cell(row=dept_row, column=5).alignment = Alignment(horizontal='center')
            ws.cell(row=dept_row, column=5).border = thin_border
            
            dept_row += 1
        
        if dept_row > 25:
            bar1 = BarChart()
            bar1.type = "col"
            bar1.style = 12
            bar1.title = "نسبة الحضور بالأقسام"
            bar1.y_axis.title = "النسبة %"
            
            data_bar = Reference(ws, min_col=4, min_row=24, max_row=dept_row-1)
            cats_bar = Reference(ws, min_col=1, min_row=25, max_row=dept_row-1)
            bar1.add_data(data_bar, titles_from_data=True)
            bar1.set_categories(cats_bar)
            bar1.width = 14
            bar1.height = 10
            bar1.dataLabels = DataLabelList()
            bar1.dataLabels.showVal = True
            ws.add_chart(bar1, "G23")
        
        doc_counts = db.session.query(
            Document.employee_id,
            func.count(Document.id)
        ).group_by(Document.employee_id).all()
        
        complete_docs = sum(1 for _, cnt in doc_counts if cnt >= 4)
        incomplete_docs = total_employees - complete_docs
        
        doc_start = dept_row + 2
        ws.merge_cells(f'A{doc_start}:H{doc_start}')
        ws[f'A{doc_start}'] = "📄 حالة اكتمال الوثائق"
        ws[f'A{doc_start}'].font = gold_font
        ws[f'A{doc_start}'].fill = dark_header
        ws[f'A{doc_start}'].alignment = Alignment(horizontal='center', vertical='center')
        
        ws.cell(row=doc_start+1, column=1).value = "الحالة"
        ws.cell(row=doc_start+1, column=2).value = "العدد"
        ws.cell(row=doc_start+1, column=3).value = "النسبة"
        for i in range(1, 4):
            ws.cell(row=doc_start+1, column=i).font = gold_font
            ws.cell(row=doc_start+1, column=i).fill = dark_header
            ws.cell(row=doc_start+1, column=i).border = thin_border
        
        complete_pct = round((complete_docs / total_employees * 100), 1) if total_employees > 0 else 0
        incomplete_pct = round((incomplete_docs / total_employees * 100), 1) if total_employees > 0 else 0
        
        ws.cell(row=doc_start+2, column=1).value = "مكتمل ✅"
        ws.cell(row=doc_start+2, column=2).value = complete_docs
        ws.cell(row=doc_start+2, column=3).value = f"{complete_pct}%"
        for i in range(1, 4):
            ws.cell(row=doc_start+2, column=i).font = white_font
            ws.cell(row=doc_start+2, column=i).fill = card_fill
            ws.cell(row=doc_start+2, column=i).border = thin_border
        
        ws.cell(row=doc_start+3, column=1).value = "ناقص ⚠️"
        ws.cell(row=doc_start+3, column=2).value = incomplete_docs
        ws.cell(row=doc_start+3, column=3).value = f"{incomplete_pct}%"
        for i in range(1, 4):
            ws.cell(row=doc_start+3, column=i).font = white_font
            ws.cell(row=doc_start+3, column=i).fill = card_fill
            ws.cell(row=doc_start+3, column=i).border = thin_border
        
        pie3 = PieChart()
        pie3.title = "اكتمال الوثائق"
        labels3 = Reference(ws, min_col=1, min_row=doc_start+2, max_row=doc_start+3)
        data3 = Reference(ws, min_col=2, min_row=doc_start+1, max_row=doc_start+3)
        pie3.add_data(data3, titles_from_data=True)
        pie3.set_categories(labels3)
        pie3.width = 10
        pie3.height = 8
        pie3.dataLabels = DataLabelList()
        pie3.dataLabels.showPercent = True
        ws.add_chart(pie3, f"E{doc_start}")
        
        header_fill = PatternFill(start_color="1a1a2e", end_color="1a1a2e", fill_type="solid")
        header_font = Font(bold=True, color="F2C811", size=12)
        
        if data_type in ['attendance', 'all']:
            ws_att = wb.create_sheet("تقرير الحضور")
            ws_att.sheet_view.rightToLeft = True
            
            ws_att.merge_cells('A1:G1')
            ws_att['A1'] = "📋 تقرير الحضور التفصيلي"
            ws_att['A1'].font = title_font
            ws_att['A1'].alignment = Alignment(horizontal='center', vertical='center')
            ws_att.row_dimensions[1].height = 30
            
            headers = ['التاريخ', 'اسم الموظف', 'الرقم الوظيفي', 'القسم', 'الحالة', 'وقت الحضور', 'وقت الانصراف']
            for col, header in enumerate(headers, start=1):
                cell = ws_att.cell(row=3, column=col)
                cell.value = header
                cell.font = header_font
                cell.fill = header_fill
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center', vertical='center')
            ws_att.row_dimensions[3].height = 25
            
            query = Attendance.query.order_by(Attendance.date.desc())
            if date_from and date_to:
                d_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                d_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(Attendance.date >= d_from, Attendance.date <= d_to)
            
            status_translations = {
                'present': 'حاضر',
                'absent': 'غائب',
                'late': 'متأخر',
                'excused': 'معذور'
            }
            
            attendance_records = query.limit(500).all()
            for row_idx, record in enumerate(attendance_records, start=4):
                emp = Employee.query.get(record.employee_id) if record.employee_id else None
                status = record.status or 'unknown'
                
                data_row = [
                    record.date.strftime('%Y-%m-%d') if record.date else '',
                    emp.name if emp else 'غير معروف',
                    emp.employee_id if emp else '',
                    emp.department.name if emp and emp.department else '',
                    status_translations.get(status, status),
                    record.time.strftime('%H:%M') if hasattr(record, 'time') and record.time else '',
                    record.checkout_time.strftime('%H:%M') if hasattr(record, 'checkout_time') and record.checkout_time else ''
                ]
                
                for col, value in enumerate(data_row, start=1):
                    cell = ws_att.cell(row=row_idx, column=col)
                    cell.value = value
                    cell.border = thin_border
                    cell.alignment = Alignment(horizontal='center')
                    
                    if col == 5:
                        if status == 'present':
                            cell.fill = success_fill
                        elif status == 'absent':
                            cell.fill = danger_fill
                        elif status == 'late':
                            cell.fill = warning_fill
                        elif status == 'excused':
                            cell.fill = info_fill
                    elif row_idx % 2 == 0:
                        cell.fill = alt_row_fill
            
            for col in range(1, 8):
                ws_att.column_dimensions[get_column_letter(col)].width = 18
        
        if data_type in ['employees', 'all']:
            ws_emp = wb.create_sheet("تقرير الموظفين")
            ws_emp.sheet_view.rightToLeft = True
            
            ws_emp.merge_cells('A1:F1')
            ws_emp['A1'] = "👥 تقرير الموظفين والوثائق"
            ws_emp['A1'].font = title_font
            ws_emp['A1'].alignment = Alignment(horizontal='center', vertical='center')
            ws_emp.row_dimensions[1].height = 30
            
            headers = ['الرقم', 'اسم الموظف', 'الرقم الوظيفي', 'القسم', 'عدد الوثائق', 'حالة الوثائق']
            for col, header in enumerate(headers, start=1):
                cell = ws_emp.cell(row=3, column=col)
                cell.value = header
                cell.font = header_font
                cell.fill = header_fill
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center', vertical='center')
            ws_emp.row_dimensions[3].height = 25
            
            employees = Employee.query.all()
            
            doc_counts = db.session.query(
                Document.employee_id,
                func.count(Document.id).label('count')
            ).group_by(Document.employee_id).all()
            doc_count_map = {e_id: cnt for e_id, cnt in doc_counts}
            
            for row_idx, emp in enumerate(employees, start=4):
                docs_count = doc_count_map.get(emp.id, 0)
                status = 'مكتمل ✅' if docs_count >= 4 else 'ناقص ⚠️'
                
                data_row = [
                    emp.id,
                    emp.name,
                    emp.employee_id or '-',
                    emp.department.name if emp.department else 'بدون قسم',
                    docs_count,
                    status
                ]
                
                for col, value in enumerate(data_row, start=1):
                    cell = ws_emp.cell(row=row_idx, column=col)
                    cell.value = value
                    cell.border = thin_border
                    cell.alignment = Alignment(horizontal='center')
                    
                    if col == 6:
                        cell.fill = success_fill if docs_count >= 4 else warning_fill
                    elif row_idx % 2 == 0:
                        cell.fill = alt_row_fill
            
            for col in range(1, 7):
                ws_emp.column_dimensions[get_column_letter(col)].width = 18
        
        if data_type in ['vehicles', 'all']:
            ws_veh = wb.create_sheet("تقرير السيارات")
            ws_veh.sheet_view.rightToLeft = True
            
            ws_veh.merge_cells('A1:F1')
            ws_veh['A1'] = "🚗 تقرير أسطول السيارات"
            ws_veh['A1'].font = title_font
            ws_veh['A1'].alignment = Alignment(horizontal='center', vertical='center')
            ws_veh.row_dimensions[1].height = 30
            
            headers = ['رقم اللوحة', 'الماركة', 'الموديل', 'السنة', 'الحالة', 'حالة التسليم']
            for col, header in enumerate(headers, start=1):
                cell = ws_veh.cell(row=3, column=col)
                cell.value = header
                cell.font = header_font
                cell.fill = header_fill
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center', vertical='center')
            ws_veh.row_dimensions[3].height = 25
            
            status_translations = {
                'working': 'نشط',
                'maintenance': 'صيانة',
                'inactive': 'غير نشط'
            }
            
            vehicles = Vehicle.query.all()
            for row_idx, v in enumerate(vehicles, start=4):
                status = v.status or 'unknown'
                
                data_row = [
                    v.plate_number if hasattr(v, 'plate_number') else '',
                    v.make if hasattr(v, 'make') else '',
                    v.model if hasattr(v, 'model') else '',
                    v.year if hasattr(v, 'year') else '',
                    status_translations.get(status, status),
                    'مستلمة ✅' if v.handover_records else 'غير مستلمة'
                ]
                
                for col, value in enumerate(data_row, start=1):
                    cell = ws_veh.cell(row=row_idx, column=col)
                    cell.value = value
                    cell.border = thin_border
                    cell.alignment = Alignment(horizontal='center')
                    
                    if col == 5:
                        if status == 'working':
                            cell.fill = success_fill
                        elif status == 'maintenance':
                            cell.fill = warning_fill
                        elif status == 'inactive':
                            cell.fill = danger_fill
                    elif row_idx % 2 == 0:
                        cell.fill = alt_row_fill
            
            for col in range(1, 7):
                ws_veh.column_dimensions[get_column_letter(col)].width = 16
        
        if data_type == 'all':
            ws_dept = wb.create_sheet("تحليل الأقسام")
            ws_dept.sheet_view.rightToLeft = True
            
            ws_dept.merge_cells('A1:G1')
            ws_dept['A1'] = "🏢 تحليل الحضور حسب الأقسام"
            ws_dept['A1'].font = title_font
            ws_dept['A1'].alignment = Alignment(horizontal='center', vertical='center')
            ws_dept.row_dimensions[1].height = 30
            
            headers = ['القسم', 'عدد الموظفين', 'حاضر', 'غائب', 'متأخر', 'نسبة الحضور', 'التقييم']
            for col, header in enumerate(headers, start=1):
                cell = ws_dept.cell(row=3, column=col)
                cell.value = header
                cell.font = header_font
                cell.fill = header_fill
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center', vertical='center')
            ws_dept.row_dimensions[3].height = 25
            
            if date_from:
                d_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            else:
                d_from = datetime.now().date() - timedelta(days=30)
            
            if date_to:
                d_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            else:
                d_to = datetime.now().date()
            
            departments = Department.query.all()
            
            all_employees = Employee.query.all()
            dept_employees = {}
            for e in all_employees:
                if e.department_id:
                    if e.department_id not in dept_employees:
                        dept_employees[e.department_id] = []
                    dept_employees[e.department_id].append(e.id)
            
            all_attendance = Attendance.query.filter(
                Attendance.date >= d_from,
                Attendance.date <= d_to
            ).all()
            
            dept_attendance = {}
            for a in all_attendance:
                for d_id, emp_ids in dept_employees.items():
                    if a.employee_id in emp_ids:
                        if d_id not in dept_attendance:
                            dept_attendance[d_id] = {'present': 0, 'absent': 0, 'late': 0, 'total': 0}
                        dept_attendance[d_id]['total'] += 1
                        if a.status == 'present':
                            dept_attendance[d_id]['present'] += 1
                        elif a.status == 'absent':
                            dept_attendance[d_id]['absent'] += 1
                        elif a.status == 'late':
                            dept_attendance[d_id]['late'] += 1
                        break
            
            actual_row = 4
            for dept in departments:
                emp_count = len(dept_employees.get(dept.id, []))
                if emp_count == 0:
                    continue
                
                stats = dept_attendance.get(dept.id, {'present': 0, 'absent': 0, 'late': 0, 'total': 0})
                present = stats['present']
                absent = stats['absent']
                late = stats['late']
                total = stats['total']
                rate = round((present / total) * 100, 1) if total > 0 else 0
                
                if rate >= 90:
                    performance = 'ممتاز ⭐'
                    perf_fill = success_fill
                elif rate >= 75:
                    performance = 'جيد 👍'
                    perf_fill = info_fill
                elif rate >= 60:
                    performance = 'متوسط ⚡'
                    perf_fill = warning_fill
                else:
                    performance = 'يحتاج تحسين ⚠️'
                    perf_fill = danger_fill
                
                data_row = [dept.name, len(employees), present, absent, late, f'{rate}%', performance]
                
                for col, value in enumerate(data_row, start=1):
                    cell = ws_dept.cell(row=row_idx, column=col)
                    cell.value = value
                    cell.border = thin_border
                    cell.alignment = Alignment(horizontal='center')
                    
                    if col == 7:
                        cell.fill = perf_fill
                    elif row_idx % 2 == 0:
                        cell.fill = alt_row_fill
            
            for col in range(1, 8):
                ws_dept.column_dimensions[get_column_letter(col)].width = 16
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        filename = f"powerbi_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@powerbi_bp.route('/api/dashboard-stats')
@login_required
def dashboard_stats():
    """إحصائيات شاملة للوحة المعلومات"""
    try:
        total_employees = Employee.query.count()
        total_vehicles = Vehicle.query.count()
        total_documents = Document.query.count()
        total_departments = Department.query.count()
        
        today = datetime.now().date()
        today_attendance = Attendance.query.filter(Attendance.date == today).all()
        today_present = sum(1 for a in today_attendance if a.status == 'present')
        
        working_vehicles = Vehicle.query.filter_by(status='working').count()
        
        return jsonify({
            'success': True,
            'data': {
                'employees': {
                    'total': total_employees,
                    'present_today': today_present
                },
                'vehicles': {
                    'total': total_vehicles,
                    'working': working_vehicles
                },
                'documents': {
                    'total': total_documents
                },
                'departments': {
                    'total': total_departments
                },
                'last_updated': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
