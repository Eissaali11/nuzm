"""
لوحة معلومات Power BI مدمجة في نُظم
تقارير تفاعلية للحضور والهويات والسيارات
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from datetime import datetime, timedelta
from app import db
from models import Employee, Attendance, Document, Vehicle, Department
from sqlalchemy import func, or_
from utils.user_helpers import require_module_access
from models import Module, Permission

powerbi_bp = Blueprint('powerbi', __name__, url_prefix='/powerbi')

@powerbi_bp.route('/')
@login_required
def dashboard():
    """الصفحة الرئيسية للوحة معلومات Power BI"""
    departments = Department.query.all()
    return render_template('powerbi/dashboard.html', departments=departments)

# ============ APIs للحضور ============

@powerbi_bp.route('/api/attendance-summary')
@login_required
@require_module_access(Module.ATTENDANCE, Permission.VIEW)
def attendance_summary():
    """ملخص الحضور اليومي"""
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    department_id = request.args.get('department_id')
    
    try:
        # تحويل التواريخ
        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        else:
            date_from = datetime.now().date() - timedelta(days=30)
        
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        else:
            date_to = datetime.now().date()
        
        # استعلام الحضور
        query = Attendance.query.filter(
            Attendance.date >= date_from,
            Attendance.date <= date_to
        )
        
        # تطبيق فلتر القسم
        if department_id:
            employee_ids = [e.id for e in Employee.query.filter_by(department_id=department_id).all()]
            query = query.filter(Attendance.employee_id.in_(employee_ids))
        
        attendance_records = query.all()
        
        # جمع الإحصائيات
        present = sum(1 for a in attendance_records if a.status == 'present')
        absent = sum(1 for a in attendance_records if a.status == 'absent')
        late = sum(1 for a in attendance_records if a.status == 'late')
        excused = sum(1 for a in attendance_records if a.status == 'excused')
        
        return jsonify({
            'success': True,
            'data': {
                'present': present,
                'absent': absent,
                'late': late,
                'excused': excused,
                'total': len(attendance_records),
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
    """الحضور حسب القسم"""
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
        
        # جمع بيانات الحضور حسب القسم
        departments_data = []
        departments = Department.query.all()
        
        for dept in departments:
            employee_ids = [e.id for e in Employee.query.filter_by(department_id=dept.id).all()]
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
            total = len(attendance_records)
            
            if total > 0:
                departments_data.append({
                    'department': dept.name,
                    'present': present,
                    'absent': absent,
                    'late': late,
                    'total': total,
                    'attendance_rate': round((present / total) * 100, 2)
                })
        
        return jsonify({
            'success': True,
            'data': departments_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ============ APIs الهويات ============

@powerbi_bp.route('/api/documents-status')
@login_required
@require_module_access(Module.EMPLOYEES, Permission.VIEW)
def documents_status():
    """حالة الوثائق المطلوبة"""
    try:
        # أنواع الوثائق المطلوبة
        required_docs = ['وثيقة التأمين', 'جواز السفر', 'البطاقة الوطنية', 'رخصة القيادة']
        
        documents_summary = []
        for doc_type in required_docs:
            total_employees = Employee.query.count()
            docs_available = Document.query.filter(
                Document.document_type.ilike(f'%{doc_type}%')
            ).count()
            
            documents_summary.append({
                'type': doc_type,
                'available': docs_available,
                'missing': total_employees - docs_available,
                'completion_rate': round((docs_available / total_employees * 100), 2) if total_employees > 0 else 0
            })
        
        return jsonify({
            'success': True,
            'data': documents_summary,
            'total_employees': total_employees
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@powerbi_bp.route('/api/employee-documents')
@login_required
@require_module_access(Module.EMPLOYEES, Permission.VIEW)
def employee_documents():
    """قائمة الموظفين والوثائق الناقصة"""
    department_id = request.args.get('department_id')
    
    try:
        query = Employee.query
        
        if department_id:
            query = query.filter_by(department_id=department_id)
        
        employees = query.all()
        
        employees_data = []
        for emp in employees:
            docs = Document.query.filter_by(employee_id=emp.id).all()
            doc_types = [d.document_type for d in docs]
            
            required_docs = ['وثيقة التأمين', 'جواز السفر', 'البطاقة الوطنية', 'رخصة القيادة']
            missing_docs = [d for d in required_docs if d not in doc_types]
            
            employees_data.append({
                'id': emp.id,
                'name': emp.name,
                'employee_id': emp.employee_id,
                'department': emp.department.name if emp.department else 'بدون قسم',
                'total_docs': len(docs),
                'missing_docs': missing_docs,
                'documents_complete': len(missing_docs) == 0
            })
        
        return jsonify({
            'success': True,
            'data': employees_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# ============ APIs السيارات ============

@powerbi_bp.route('/api/vehicles-summary')
@login_required
@require_module_access(Module.VEHICLES, Permission.VIEW)
def vehicles_summary():
    """ملخص حالة السيارات"""
    try:
        vehicles = Vehicle.query.all()
        
        statuses = {}
        for vehicle in vehicles:
            status = vehicle.status or 'unknown'
            statuses[status] = statuses.get(status, 0) + 1
        
        vehicles_data = []
        for status, count in statuses.items():
            vehicles_data.append({
                'status': status,
                'count': count,
                'percentage': round((count / len(vehicles) * 100), 2) if vehicles else 0
            })
        
        return jsonify({
            'success': True,
            'data': {
                'by_status': vehicles_data,
                'total_vehicles': len(vehicles),
                'working': statuses.get('working', 0),
                'maintenance': statuses.get('maintenance', 0),
                'inactive': statuses.get('inactive', 0)
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
        # إحصائيات بسيطة حول السيارات
        vehicles = Vehicle.query.all()
        
        handovers = sum(1 for v in vehicles if v.handover_status)
        maintenance = sum(1 for v in vehicles if v.status == 'maintenance')
        active = sum(1 for v in vehicles if v.status == 'working')
        
        operations_data = [
            {'type': 'نقل', 'count': handovers},
            {'type': 'صيانة', 'count': maintenance},
            {'type': 'نشط', 'count': active}
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'by_type': operations_data,
                'total_vehicles': len(vehicles)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@powerbi_bp.route('/api/export-data')
@login_required
def export_data():
    """تصدير البيانات لـ Power BI"""
    import csv
    from io import StringIO
    
    data_type = request.args.get('type', 'attendance')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    try:
        output = StringIO()
        
        if data_type == 'attendance':
            writer = csv.writer(output)
            writer.writerow(['التاريخ', 'اسم الموظف', 'الحالة', 'الوقت'])
            
            query = Attendance.query
            if date_from and date_to:
                d_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                d_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(
                    Attendance.date >= d_from,
                    Attendance.date <= d_to
                )
            
            for record in query.all():
                emp = Employee.query.get(record.employee_id)
                writer.writerow([
                    record.date.strftime('%Y-%m-%d'),
                    emp.name if emp else 'unknown',
                    record.status,
                    record.time.strftime('%H:%M') if record.time else ''
                ])
        
        response_text = output.getvalue()
        return response_text, 200, {
            'Content-Disposition': f'attachment; filename="data_{data_type}.csv"',
            'Content-Type': 'text/csv; charset=utf-8-sig'
        }
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
