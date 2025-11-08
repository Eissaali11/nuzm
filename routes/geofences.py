from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Geofence, GeofenceEvent, Employee, Department, Attendance, EmployeeLocation, db, employee_departments
from datetime import datetime

geofences_bp = Blueprint('geofences', __name__, url_prefix='/employees/geofences')


@geofences_bp.route('/')
@login_required
def index():
    """صفحة إدارة الدوائر الجغرافية"""
    geofences = Geofence.query.filter_by(is_active=True).all()
    departments = Department.query.all()
    
    geofences_data = []
    for geofence in geofences:
        employees_inside = geofence.get_department_employees_inside()
        geofences_data.append({
            'geofence': geofence,
            'employees_count': len(employees_inside),
            'employees_inside': employees_inside
        })
    
    return render_template(
        'geofences/index.html',
        geofences_data=geofences_data,
        departments=departments
    )


@geofences_bp.route('/create', methods=['POST'])
@login_required
def create():
    """إنشاء دائرة جديدة"""
    try:
        data = request.get_json()
        
        geofence = Geofence(
            name=data['name'],
            type=data.get('type', 'project'),
            description=data.get('description'),
            center_latitude=data['latitude'],
            center_longitude=data['longitude'],
            radius_meters=data['radius'],
            color=data.get('color', '#667eea'),
            department_id=data['department_id'],
            notify_on_entry=data.get('notify_on_entry', False),
            notify_on_exit=data.get('notify_on_exit', False),
            created_by=current_user.id
        )
        
        db.session.add(geofence)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'geofence_id': geofence.id,
            'message': 'تم إنشاء الدائرة بنجاح'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في إنشاء الدائرة: {str(e)}'
        }), 400


@geofences_bp.route('/<int:geofence_id>')
@login_required
def view(geofence_id):
    """عرض تفاصيل دائرة معينة"""
    geofence = Geofence.query.get_or_404(geofence_id)
    
    employees_inside = geofence.get_department_employees_inside()
    all_employees = geofence.get_all_employees_inside()
    
    recent_events = GeofenceEvent.query.filter_by(
        geofence_id=geofence_id
    ).order_by(GeofenceEvent.recorded_at.desc()).limit(50).all()
    
    return render_template(
        'geofences/view.html',
        geofence=geofence,
        employees_inside=employees_inside,
        all_employees=all_employees,
        recent_events=recent_events
    )


@geofences_bp.route('/<int:geofence_id>/bulk-check-in', methods=['POST'])
@login_required
def bulk_check_in(geofence_id):
    """تسجيل حضور جماعي فقط لموظفي القسم المرتبط بالدائرة"""
    try:
        geofence = Geofence.query.get_or_404(geofence_id)
        
        employees_inside = geofence.get_department_employees_inside()
        
        if not employees_inside:
            return jsonify({
                'success': False,
                'message': f'لا يوجد موظفين من قسم "{geofence.department.name}" داخل الدائرة حالياً'
            })
        
        checked_in = []
        already_checked = []
        errors = []
        
        for emp_data in employees_inside:
            employee = emp_data['employee']
            location = emp_data['location']
            
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            existing_attendance = Attendance.query.filter(
                Attendance.employee_id == employee.id,
                Attendance.check_in_time >= today_start
            ).first()
            
            if existing_attendance:
                already_checked.append(employee.name)
                continue
            
            try:
                attendance = Attendance(
                    employee_id=employee.id,
                    check_in_time=datetime.utcnow(),
                    status='present',
                    notes=f'تسجيل جماعي من دائرة: {geofence.name} (قسم: {geofence.department.name})'
                )
                db.session.add(attendance)
                db.session.flush()
                
                event = GeofenceEvent(
                    geofence_id=geofence.id,
                    employee_id=employee.id,
                    event_type='bulk_check_in',
                    location_latitude=location.latitude,
                    location_longitude=location.longitude,
                    distance_from_center=int(emp_data['distance']),
                    source='bulk',
                    attendance_id=attendance.id,
                    notes=f'تسجيل جماعي بواسطة {current_user.username} - قسم: {geofence.department.name}'
                )
                db.session.add(event)
                
                checked_in.append(employee.name)
                
            except Exception as e:
                errors.append(f'{employee.name}: {str(e)}')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'department_name': geofence.department.name,
            'checked_in_count': len(checked_in),
            'already_checked_count': len(already_checked),
            'error_count': len(errors),
            'checked_in': checked_in,
            'already_checked': already_checked,
            'errors': errors,
            'message': f'تم تسجيل حضور {len(checked_in)} موظف من قسم "{geofence.department.name}" بنجاح'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تسجيل الحضور: {str(e)}'
        }), 400


@geofences_bp.route('/<int:geofence_id>/employees')
@login_required
def get_employees(geofence_id):
    """جلب الموظفين داخل الدائرة (API)"""
    try:
        geofence = Geofence.query.get_or_404(geofence_id)
        
        employees_inside = geofence.get_department_employees_inside()
        all_employees = geofence.get_all_employees_inside()
        
        return jsonify({
            'success': True,
            'department_employees': [{
                'id': emp['employee'].id,
                'name': emp['employee'].name,
                'employee_id': emp['employee'].employee_id,
                'distance': round(emp['distance'], 2),
                'latitude': float(emp['location'].latitude),
                'longitude': float(emp['location'].longitude),
                'profile_image': emp['employee'].profile_image
            } for emp in employees_inside],
            'other_employees': [{
                'id': emp['employee'].id,
                'name': emp['employee'].name,
                'employee_id': emp['employee'].employee_id,
                'distance': round(emp['distance'], 2),
                'latitude': float(emp['location'].latitude),
                'longitude': float(emp['location'].longitude),
                'is_eligible': emp['is_eligible'],
                'profile_image': emp['employee'].profile_image
            } for emp in all_employees if not emp['is_eligible']]
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }), 400


@geofences_bp.route('/<int:geofence_id>/events')
@login_required
def get_events(geofence_id):
    """جلب أحداث دائرة معينة"""
    try:
        geofence = Geofence.query.get_or_404(geofence_id)
        
        events = GeofenceEvent.query.filter_by(
            geofence_id=geofence_id
        ).order_by(GeofenceEvent.recorded_at.desc()).limit(100).all()
        
        return jsonify({
            'success': True,
            'events': [{
                'id': event.id,
                'employee_name': event.employee.name,
                'event_type': event.event_type,
                'event_time': event.recorded_at.isoformat(),
                'distance': event.distance_from_center,
                'notes': event.notes
            } for event in events]
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }), 400


@geofences_bp.route('/api/list')
@login_required
def api_list():
    """API: جلب قائمة جميع الدوائر النشطة"""
    try:
        geofences = Geofence.query.filter_by(is_active=True).all()
        
        return jsonify({
            'success': True,
            'geofences': [{
                'id': g.id,
                'name': g.name,
                'type': g.type,
                'center_lat': float(g.center_latitude),
                'center_lng': float(g.center_longitude),
                'radius': g.radius_meters,
                'color': g.color,
                'department_id': g.department_id,
                'department_name': g.department.name
            } for g in geofences]
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ: {str(e)}'
        }), 400


@geofences_bp.route('/<int:geofence_id>/update', methods=['PUT'])
@login_required
def update(geofence_id):
    """تحديث دائرة"""
    try:
        geofence = Geofence.query.get_or_404(geofence_id)
        data = request.get_json()
        
        if 'name' in data:
            geofence.name = data['name']
        if 'description' in data:
            geofence.description = data['description']
        if 'radius' in data:
            geofence.radius_meters = data['radius']
        if 'color' in data:
            geofence.color = data['color']
        if 'notify_on_entry' in data:
            geofence.notify_on_entry = data['notify_on_entry']
        if 'notify_on_exit' in data:
            geofence.notify_on_exit = data['notify_on_exit']
        
        geofence.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث الدائرة بنجاح'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في التحديث: {str(e)}'
        }), 400


@geofences_bp.route('/<int:geofence_id>/delete', methods=['DELETE'])
@login_required
def delete(geofence_id):
    """حذف دائرة"""
    try:
        geofence = Geofence.query.get_or_404(geofence_id)
        
        db.session.delete(geofence)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم حذف الدائرة بنجاح'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في الحذف: {str(e)}'
        }), 400
