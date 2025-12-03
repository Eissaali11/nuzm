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
    """الصفحة الرئيسية للوحة معلومات Power BI الاحترافية"""
    departments = Department.query.all()
    return render_template('powerbi/dashboard.html', departments=departments)

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
        absent = sum(1 for a in attendance_records if a.status == 'absent')
        late = sum(1 for a in attendance_records if a.status == 'late')
        excused = sum(1 for a in attendance_records if a.status == 'excused')
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
                'late': late,
                'excused': excused,
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
            absent = sum(1 for a in attendance_records if a.status == 'absent')
            late = sum(1 for a in attendance_records if a.status == 'late')
            excused = sum(1 for a in attendance_records if a.status == 'excused')
            total = len(attendance_records)
            
            attendance_rate = round((present / total) * 100, 1) if total > 0 else 0
            
            performance = 'excellent' if attendance_rate >= 90 else 'good' if attendance_rate >= 75 else 'average' if attendance_rate >= 60 else 'poor'
            
            departments_data.append({
                'department': dept.name,
                'department_id': dept.id,
                'employee_count': len(employees),
                'present': present,
                'absent': absent,
                'late': late,
                'excused': excused,
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
            'working': 'نشط',
            'maintenance': 'صيانة',
            'inactive': 'غير نشط',
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
        working = statuses.get('working', 0)
        maintenance = statuses.get('maintenance', 0)
        inactive = statuses.get('inactive', 0)
        
        fleet_health = 'excellent' if working >= total * 0.8 else 'good' if working >= total * 0.6 else 'average' if working >= total * 0.4 else 'poor'
        
        return jsonify({
            'success': True,
            'data': {
                'by_status': vehicles_by_status,
                'by_brand': vehicles_by_brand[:5],
                'total_vehicles': total,
                'working': working,
                'maintenance': maintenance,
                'inactive': inactive,
                'utilization_rate': round((working / total) * 100, 1) if total > 0 else 0,
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
        maintenance = sum(1 for v in vehicles if v.status == 'maintenance')
        active = sum(1 for v in vehicles if v.status == 'working')
        inactive = sum(1 for v in vehicles if v.status == 'inactive')
        
        operations_data = [
            {'type': 'نشط', 'count': active, 'color': '#38ef7d'},
            {'type': 'مستلمة', 'count': handovers, 'color': '#667eea'},
            {'type': 'صيانة', 'count': maintenance, 'color': '#fbbf24'},
            {'type': 'غير نشط', 'count': inactive, 'color': '#ef4444'}
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'by_type': operations_data,
                'total_vehicles': len(vehicles),
                'summary': {
                    'active_percentage': round((active / len(vehicles)) * 100, 1) if vehicles else 0,
                    'handover_percentage': round((handovers / len(vehicles)) * 100, 1) if vehicles else 0
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@powerbi_bp.route('/api/export-data')
@login_required
def export_data():
    """تصدير البيانات بصيغة Excel احترافية"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
    from openpyxl.utils import get_column_letter
    from openpyxl.chart import BarChart, PieChart, DoughnutChart, Reference
    from openpyxl.chart.series import DataPoint
    from openpyxl.chart.label import DataLabelList
    from sqlalchemy.orm import joinedload
    from sqlalchemy import func
    
    data_type = request.args.get('type', 'all')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    try:
        wb = Workbook()
        
        header_fill = PatternFill(start_color="1a1a2e", end_color="1a1a2e", fill_type="solid")
        header_font = Font(bold=True, color="F2C811", size=12)
        title_font = Font(bold=True, color="1a1a2e", size=16)
        subtitle_font = Font(bold=True, color="667eea", size=11)
        chart_title_font = Font(bold=True, size=14)
        gold_fill = PatternFill(start_color="F2C811", end_color="F2C811", fill_type="solid")
        
        thin_border = Border(
            left=Side(style='thin', color='CCCCCC'),
            right=Side(style='thin', color='CCCCCC'),
            top=Side(style='thin', color='CCCCCC'),
            bottom=Side(style='thin', color='CCCCCC')
        )
        
        success_fill = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")
        warning_fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")
        danger_fill = PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid")
        info_fill = PatternFill(start_color="D1ECF1", end_color="D1ECF1", fill_type="solid")
        alt_row_fill = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid")
        
        chart_colors = ['38EF7D', 'EF4444', 'FFA500', '667EEA', 'F2C811']
        
        ws_charts = wb.active
        ws_charts.title = "لوحة الرسوم البيانية"
        ws_charts.sheet_view.rightToLeft = True
        
        ws_charts.merge_cells('A1:N1')
        ws_charts['A1'] = "📊 لوحة التحليلات الاحترافية - نُظم"
        ws_charts['A1'].font = Font(bold=True, color="1a1a2e", size=18)
        ws_charts['A1'].alignment = Alignment(horizontal='center', vertical='center')
        ws_charts.row_dimensions[1].height = 40
        
        ws_charts['A2'] = f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ws_charts['A2'].font = Font(italic=True, size=10)
        
        total_employees = Employee.query.count()
        total_vehicles = Vehicle.query.count()
        working_vehicles = Vehicle.query.filter_by(status='working').count()
        maintenance_vehicles = Vehicle.query.filter_by(status='maintenance').count()
        inactive_vehicles = Vehicle.query.filter_by(status='inactive').count()
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
        
        att_data = {'present': 0, 'absent': 0, 'late': 0, 'excused': 0}
        for status, count in attendance_stats:
            if status in att_data:
                att_data[status] = count
        
        ws_charts['A4'] = "حالة الحضور"
        ws_charts['B4'] = "العدد"
        ws_charts['A4'].font = header_font
        ws_charts['A4'].fill = header_fill
        ws_charts['B4'].font = header_font
        ws_charts['B4'].fill = header_fill
        
        att_labels = [('حاضر', att_data['present']), ('غائب', att_data['absent']), 
                      ('متأخر', att_data['late']), ('معذور', att_data['excused'])]
        for i, (label, value) in enumerate(att_labels, start=5):
            ws_charts[f'A{i}'] = label
            ws_charts[f'B{i}'] = value
            ws_charts[f'A{i}'].border = thin_border
            ws_charts[f'B{i}'].border = thin_border
        
        pie1 = PieChart()
        pie1.title = "توزيع حالات الحضور"
        labels1 = Reference(ws_charts, min_col=1, min_row=5, max_row=8)
        data1 = Reference(ws_charts, min_col=2, min_row=4, max_row=8)
        pie1.add_data(data1, titles_from_data=True)
        pie1.set_categories(labels1)
        pie1.width = 12
        pie1.height = 10
        pie1.dataLabels = DataLabelList()
        pie1.dataLabels.showPercent = True
        pie1.dataLabels.showVal = True
        ws_charts.add_chart(pie1, "D4")
        
        ws_charts['A11'] = "حالة السيارات"
        ws_charts['B11'] = "العدد"
        ws_charts['A11'].font = header_font
        ws_charts['A11'].fill = header_fill
        ws_charts['B11'].font = header_font
        ws_charts['B11'].fill = header_fill
        
        veh_data = [('نشط', working_vehicles), ('صيانة', maintenance_vehicles), ('غير نشط', inactive_vehicles)]
        for i, (label, value) in enumerate(veh_data, start=12):
            ws_charts[f'A{i}'] = label
            ws_charts[f'B{i}'] = value
            ws_charts[f'A{i}'].border = thin_border
            ws_charts[f'B{i}'].border = thin_border
        
        pie2 = DoughnutChart()
        pie2.title = "حالة أسطول السيارات"
        labels2 = Reference(ws_charts, min_col=1, min_row=12, max_row=14)
        data2 = Reference(ws_charts, min_col=2, min_row=11, max_row=14)
        pie2.add_data(data2, titles_from_data=True)
        pie2.set_categories(labels2)
        pie2.width = 12
        pie2.height = 10
        pie2.dataLabels = DataLabelList()
        pie2.dataLabels.showPercent = True
        pie2.dataLabels.showVal = True
        ws_charts.add_chart(pie2, "D11")
        
        departments = Department.query.all()
        all_employees = Employee.query.all()
        dept_emp_map = {}
        for e in all_employees:
            if e.department_id:
                if e.department_id not in dept_emp_map:
                    dept_emp_map[e.department_id] = []
                dept_emp_map[e.department_id].append(e.id)
        
        ws_charts['A17'] = "القسم"
        ws_charts['B17'] = "عدد الموظفين"
        ws_charts['C17'] = "نسبة الحضور"
        for col in ['A', 'B', 'C']:
            ws_charts[f'{col}17'].font = header_font
            ws_charts[f'{col}17'].fill = header_fill
        
        dept_row = 18
        for dept in departments[:8]:
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
            
            ws_charts[f'A{dept_row}'] = dept.name
            ws_charts[f'B{dept_row}'] = len(emp_ids)
            ws_charts[f'C{dept_row}'] = rate
            for col in ['A', 'B', 'C']:
                ws_charts[f'{col}{dept_row}'].border = thin_border
            dept_row += 1
        
        if dept_row > 18:
            bar1 = BarChart()
            bar1.type = "col"
            bar1.title = "نسبة الحضور حسب القسم"
            bar1.y_axis.title = "النسبة %"
            bar1.x_axis.title = "القسم"
            
            data_bar = Reference(ws_charts, min_col=3, min_row=17, max_row=dept_row-1)
            cats_bar = Reference(ws_charts, min_col=1, min_row=18, max_row=dept_row-1)
            bar1.add_data(data_bar, titles_from_data=True)
            bar1.set_categories(cats_bar)
            bar1.shape = 4
            bar1.width = 14
            bar1.height = 10
            bar1.dataLabels = DataLabelList()
            bar1.dataLabels.showVal = True
            ws_charts.add_chart(bar1, "E17")
        
        doc_counts = db.session.query(
            Document.employee_id,
            func.count(Document.id)
        ).group_by(Document.employee_id).all()
        
        complete_docs = sum(1 for _, cnt in doc_counts if cnt >= 4)
        incomplete_docs = total_employees - complete_docs
        
        ws_charts[f'A{dept_row + 2}'] = "حالة الوثائق"
        ws_charts[f'B{dept_row + 2}'] = "العدد"
        ws_charts[f'A{dept_row + 2}'].font = header_font
        ws_charts[f'A{dept_row + 2}'].fill = header_fill
        ws_charts[f'B{dept_row + 2}'].font = header_font
        ws_charts[f'B{dept_row + 2}'].fill = header_fill
        
        ws_charts[f'A{dept_row + 3}'] = "مكتمل"
        ws_charts[f'B{dept_row + 3}'] = complete_docs
        ws_charts[f'A{dept_row + 4}'] = "ناقص"
        ws_charts[f'B{dept_row + 4}'] = incomplete_docs
        
        pie3 = PieChart()
        pie3.title = "حالة اكتمال الوثائق"
        labels3 = Reference(ws_charts, min_col=1, min_row=dept_row+3, max_row=dept_row+4)
        data3 = Reference(ws_charts, min_col=2, min_row=dept_row+2, max_row=dept_row+4)
        pie3.add_data(data3, titles_from_data=True)
        pie3.set_categories(labels3)
        pie3.width = 12
        pie3.height = 10
        pie3.dataLabels = DataLabelList()
        pie3.dataLabels.showPercent = True
        pie3.dataLabels.showVal = True
        ws_charts.add_chart(pie3, f"D{dept_row + 2}")
        
        for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N']:
            ws_charts.column_dimensions[col].width = 15
        
        ws_summary = wb.create_sheet("ملخص تنفيذي")
        ws_summary.sheet_view.rightToLeft = True
        
        ws_summary.merge_cells('A1:F1')
        ws_summary['A1'] = "📊 الملخص التنفيذي - نُظم"
        ws_summary['A1'].font = title_font
        ws_summary['A1'].alignment = Alignment(horizontal='center', vertical='center')
        ws_summary.row_dimensions[1].height = 35
        
        ws_summary['A3'] = "تاريخ التقرير:"
        ws_summary['B3'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        ws_summary['A4'] = "الفترة من:"
        ws_summary['B4'] = date_from or "آخر 30 يوم"
        ws_summary['A5'] = "الفترة إلى:"
        ws_summary['B5'] = date_to or datetime.now().strftime('%Y-%m-%d')
        
        ws_summary['A7'] = "📈 الإحصائيات الرئيسية"
        ws_summary['A7'].font = subtitle_font
        ws_summary.merge_cells('A7:C7')
        
        stats = [
            ("إجمالي الموظفين", total_employees),
            ("إجمالي السيارات", total_vehicles),
            ("السيارات النشطة", working_vehicles),
            ("إجمالي الوثائق", total_documents),
            ("إجمالي الأقسام", total_departments),
            ("نسبة تشغيل الأسطول", f"{round((working_vehicles/total_vehicles)*100, 1) if total_vehicles > 0 else 0}%")
        ]
        
        for idx, (label, value) in enumerate(stats, start=8):
            ws_summary[f'A{idx}'] = label
            ws_summary[f'B{idx}'] = value
            ws_summary[f'A{idx}'].border = thin_border
            ws_summary[f'B{idx}'].border = thin_border
            if idx % 2 == 0:
                ws_summary[f'A{idx}'].fill = alt_row_fill
                ws_summary[f'B{idx}'].fill = alt_row_fill
        
        for col in ['A', 'B', 'C', 'D', 'E', 'F']:
            ws_summary.column_dimensions[col].width = 20
        
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
            
            query = Attendance.query.options(
                joinedload(Attendance.employee).joinedload(Employee.department)
            ).order_by(Attendance.date.desc())
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
                emp = record.employee
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
            
            employees = Employee.query.options(joinedload(Employee.department)).all()
            
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
