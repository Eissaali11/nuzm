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
import os
from openai import OpenAI

powerbi_bp = Blueprint('powerbi', __name__, url_prefix='/powerbi')

# Initialize OpenAI client
client = OpenAI(
    api_key=os.environ.get('AI_INTEGRATIONS_OPENAI_API_KEY'),
    base_url=os.environ.get('AI_INTEGRATIONS_OPENAI_BASE_URL')
)

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
            
            # Calculate expected days (employees × days in period)
            num_days = (date_to - date_from).days + 1
            expected_days = len(employees) * num_days
            
            # Correct attendance rate: present / expected
            attendance_rate = round((present / expected_days) * 100, 1) if expected_days > 0 else 0
            
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
                'expected_days': expected_days,
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

@powerbi_bp.route('/api/ai-analysis')
@login_required
@require_module_access(Module.ATTENDANCE, Permission.VIEW)
def ai_analysis():
    """تحليل ذكي بـ AI للبيانات"""
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
            total = len(attendance_records)
            attendance_rate = round((present / total) * 100, 1) if total > 0 else 0
            
            departments_data.append({
                'name': dept.name,
                'employees': len(employees),
                'present': present,
                'absent': absent,
                'rate': attendance_rate
            })
        
        departments_data.sort(key=lambda x: x['rate'], reverse=True)
        
        # Get AI analysis
        prompt = f"""أنت محلل بيانات متخصص. حلل البيانات وقدم تقرير قصير (3-4 فقرات):
1. تقييم إجمالي
2. أفضل 3 أقسام
3. التوصيات الرئيسية

البيانات (آخر 30 يوم):
{json.dumps(departments_data, ensure_ascii=False)}

الرجاء الإجابة باللغة العربية فقط."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=600
        )
        
        analysis = response.choices[0].message.content
        
        return jsonify({
            'success': True,
            'data': {
                'analysis': analysis,
                'date_range': {
                    'from': date_from.strftime('%Y-%m-%d'),
                    'to': date_to.strftime('%Y-%m-%d')
                }
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
            
            completion_rate = round((available / total_employees) * 100, 1) if total_employees > 0 else 0
            
            documents_summary.append({
                'type': doc_type,
                'priority': doc_info['priority'],
                'available': available,
                'missing': missing,
                'valid': valid,
                'expiring_soon': expiring_soon,
                'expired': expired,
                'completion_rate': completion_rate
            })
        
        valid_count = sum(d['valid'] for d in documents_summary)
        expiring_count = sum(d['expiring_soon'] for d in documents_summary)
        expired_count = sum(d['expired'] for d in documents_summary)
        
        return jsonify({
            'success': True,
            'data': documents_summary,
            'total_employees': total_employees,
            'summary': {
                'valid': valid_count,
                'expiring_soon': expiring_count,
                'expired': expired_count
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@powerbi_bp.route('/api/vehicles-summary')
@login_required
@require_module_access(Module.VEHICLES, Permission.VIEW)
def vehicles_summary():
    """ملخص حالة السيارات"""
    try:
        total = Vehicle.query.count()
        
        statuses = {
            'in_project': Vehicle.query.filter_by(status='in_project').count(),
            'in_workshop': Vehicle.query.filter_by(status='in_workshop').count(),
            'out_of_service': Vehicle.query.filter_by(status='out_of_service').count(),
            'accident': Vehicle.query.filter_by(status='accident').count()
        }
        
        by_status = [
            {'status': 'في المشروع', 'count': statuses.get('in_project', 0), 'value': 'in_project'},
            {'status': 'في الورشة', 'count': statuses.get('in_workshop', 0), 'value': 'in_workshop'},
            {'status': 'خارج الخدمة', 'count': statuses.get('out_of_service', 0), 'value': 'out_of_service'},
            {'status': 'حادثة', 'count': statuses.get('accident', 0), 'value': 'accident'}
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'total_vehicles': total,
                'in_project': statuses.get('in_project', 0),
                'in_workshop': statuses.get('in_workshop', 0),
                'out_of_service': statuses.get('out_of_service', 0),
                'accident': statuses.get('accident', 0),
                'by_status': by_status
            }
        })
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
        
        working_vehicles = Vehicle.query.filter_by(status='in_project').count()
        
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
