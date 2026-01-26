from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file, Response
from flask_login import login_required, current_user
from sqlalchemy import inspect
from datetime import datetime
from models import (
    Employee, Vehicle, Department, User, Salary, Attendance, 
    MobileDevice, VehicleHandover, VehicleWorkshop, Document,
    VehicleAccident, EmployeeRequest, RentalProperty, PropertyPayment, 
    PropertyImage, PropertyFurnishing, Geofence, GeofenceSession, 
    SimCard, VoiceHubCall, VehicleExternalSafetyCheck, VehicleSafetyImage, db, UserRole
)
import json
import io
import os
from functools import wraps

database_backup_bp = Blueprint('database_backup', __name__)

BACKUP_TABLES = {
    'employees': Employee,
    'vehicles': Vehicle,
    'departments': Department,
    'users': User,
    'salaries': Salary,
    'attendance': Attendance,
    'mobile_devices': MobileDevice,
    'vehicle_handovers': VehicleHandover,
    'vehicle_workshops': VehicleWorkshop,
    'documents': Document,
    'vehicle_accidents': VehicleAccident,
    'employee_requests': EmployeeRequest,
    'rental_properties': RentalProperty,
    'property_payments': PropertyPayment,
    'property_images': PropertyImage,
    'property_furnishings': PropertyFurnishing,
    'geofences': Geofence,
    'geofence_sessions': GeofenceSession,
    'sim_cards': SimCard,
    'voicehub_calls': VoiceHubCall,
    'external_safety_checks': VehicleExternalSafetyCheck,
    'safety_images': VehicleSafetyImage,
}

def serialize_model(obj):
    """تحويل كائن SQLAlchemy إلى قاموس"""
    result = {}
    try:
        for column in inspect(obj.__class__).columns:
            value = getattr(obj, column.name)
            if value is None:
                result[column.name] = None
            elif isinstance(value, datetime):
                result[column.name] = value.isoformat()
            elif hasattr(value, 'isoformat'):
                result[column.name] = value.isoformat()
            elif isinstance(value, bytes):
                result[column.name] = None
            else:
                try:
                    json.dumps(value)
                    result[column.name] = value
                except (TypeError, ValueError):
                    result[column.name] = str(value)
    except Exception as e:
        print(f"Error serializing {obj}: {e}")
    return result

@database_backup_bp.route('/')
@login_required
def backup_page():
    """صفحة النسخ الاحتياطي"""
    if current_user.role != UserRole.ADMIN:
        flash('غير مصرح لك بالدخول لهذه الصفحة', 'error')
        return redirect(url_for('admin_dashboard.index'))
    table_stats = {}
    for table_name, model in BACKUP_TABLES.items():
        try:
            count = model.query.count()
            table_stats[table_name] = count
        except Exception as e:
            table_stats[table_name] = 0
    
    return render_template('backup/index.html', 
                         table_stats=table_stats,
                         total_records=sum(table_stats.values()))

@database_backup_bp.route('/export', methods=['POST'])
@login_required
def export_backup():
    """تصدير جميع البيانات كملف JSON"""
    if current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        selected_tables = request.form.getlist('tables')
        if not selected_tables:
            selected_tables = list(BACKUP_TABLES.keys())
        
        backup_data = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'created_by': current_user.username if current_user.is_authenticated else 'System',
                'version': '1.0',
                'total_tables': len(selected_tables)
            },
            'data': {}
        }
        
        for table_name in selected_tables:
            if table_name in BACKUP_TABLES:
                model = BACKUP_TABLES[table_name]
                try:
                    records = model.query.all()
                    backup_data['data'][table_name] = [serialize_model(r) for r in records]
                except Exception as e:
                    backup_data['data'][table_name] = {'error': str(e)}
        
        json_str = json.dumps(backup_data, ensure_ascii=False, indent=2)
        
        buffer = io.BytesIO()
        buffer.write(json_str.encode('utf-8'))
        buffer.seek(0)
        
        filename = f"nuzum_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return send_file(
            buffer,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'حدث خطأ أثناء إنشاء النسخة الاحتياطية: {str(e)}', 'error')
        return redirect(url_for('database_backup.backup_page'))

@database_backup_bp.route('/import', methods=['POST'])
@login_required
def import_backup():
    """استيراد البيانات من ملف JSON"""
    if current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        if 'backup_file' not in request.files:
            flash('لم يتم اختيار ملف', 'error')
            return redirect(url_for('database_backup.backup_page'))
        
        file = request.files['backup_file']
        if file.filename == '':
            flash('لم يتم اختيار ملف', 'error')
            return redirect(url_for('database_backup.backup_page'))
        
        if not file.filename.endswith('.json'):
            flash('يجب أن يكون الملف بصيغة JSON', 'error')
            return redirect(url_for('database_backup.backup_page'))
        
        content = file.read().decode('utf-8')
        try:
            backup_data = json.loads(content)
        except json.JSONDecodeError:
            flash('ملف JSON غير صالح أو فارغ', 'error')
            return redirect(url_for('database_backup.backup_page'))
        
        # Ensure we have a dictionary and handle different possible structures
        if not isinstance(backup_data, dict):
            flash('ملف النسخة الاحتياطية غير صالح (يجب أن يكون بتنسيق JSON Object)', 'error')
            return redirect(url_for('database_backup.backup_page'))

        if 'data' not in backup_data or not isinstance(backup_data['data'], dict):
            # If it's a list, it might be a single table export
            if isinstance(backup_data, list):
                # We need to know which table this list belongs to. 
                # Check metadata if available, otherwise we can't be sure.
                flash('ملف النسخة الاحتياطية غير صالح (تنسيق القائمة غير مدعوم بدون معلومات الجدول)', 'error')
                return redirect(url_for('database_backup.backup_page'))
            
            # If the JSON is just the records directly without the 'data' key (alternate format)
            if isinstance(backup_data, dict):
                # Check if it has a 'table_name' in metadata (single table export)
                if 'metadata' in backup_data and 'table_name' in backup_data['metadata'] and isinstance(backup_data.get('data'), list):
                    table_name = backup_data['metadata']['table_name']
                    backup_data = {'data': {table_name: backup_data['data']}, 'metadata': backup_data.get('metadata', {})}
                elif all(isinstance(v, list) for v in backup_data.values() if v is not None):
                    backup_data = {'data': backup_data, 'metadata': {}}
                else:
                    flash('ملف النسخة الاحتياطية غير صالح (تنسيق غير مدعوم)', 'error')
                    return redirect(url_for('database_backup.backup_page'))
        
        # Final check to ensure backup_data['data'] is a dict before calling .items()
        if not isinstance(backup_data.get('data'), dict):
            flash('ملف النسخة الاحتياطية غير صالح (بيانات الجدول يجب أن تكون قاموساً)', 'error')
            return redirect(url_for('database_backup.backup_page'))
        
        import_mode = request.form.get('import_mode', 'add')
        imported_counts = {}
        errors = []
        
        for table_name, records in backup_data['data'].items():
            if table_name not in BACKUP_TABLES:
                continue
            
            if isinstance(records, dict) and 'error' in records:
                continue
            
            model = BACKUP_TABLES[table_name]
            imported_count = 0
            
            try:
                # Get columns for this model to handle potential extra data
                mapper = inspect(model)
                valid_columns = {c.key for c in mapper.attrs if hasattr(c, 'columns')}
                
                if import_mode == 'replace':
                    db.session.query(model).delete()
                    db.session.commit()
                
                for record in records:
                    try:
                        # Filter record to only include valid columns for this model
                        filtered_record = {k: v for k, v in record.items() if k in valid_columns}
                        
                        if import_mode == 'add':
                            # Try to get existing record by primary key if possible
                            try:
                                pk_values = [filtered_record.get(c.name) for c in mapper.primary_key]
                                if all(v is not None for v in pk_values):
                                    existing = db.session.get(model, pk_values[0] if len(pk_values) == 1 else tuple(pk_values))
                                    if existing:
                                        # Update existing record instead of skipping (prevents duplicates while keeping data fresh)
                                        for k, v in filtered_record.items():
                                            setattr(existing, k, v)
                                        imported_count += 1
                                        continue
                            except Exception as e:
                                print(f"Duplicate check error: {e}")
                                pass
                        
                        for date_field in ['created_at', 'updated_at', 'date_joined', 'handover_date', 
                                          'return_date', 'id_expiry', 'license_expiry', 'passport_expiry',
                                          'contract_start', 'contract_end', 'registration_date']:
                            if date_field in filtered_record and filtered_record[date_field]:
                                try:
                                    if isinstance(filtered_record[date_field], str):
                                        if 'T' in filtered_record[date_field]:
                                            filtered_record[date_field] = datetime.fromisoformat(filtered_record[date_field].replace('Z', '+00:00'))
                                        else:
                                            filtered_record[date_field] = datetime.strptime(filtered_record[date_field], '%Y-%m-%d')
                                except:
                                    filtered_record[date_field] = None
                        
                        new_obj = model(**filtered_record)
                        db.session.merge(new_obj)
                        imported_count += 1
                        
                    except Exception as e:
                        errors.append(f"{table_name} record error: {str(e)}")
                        continue
                
                db.session.commit()
                imported_counts[table_name] = imported_count
                
            except Exception as e:
                db.session.rollback()
                errors.append(f"{table_name}: {str(e)}")
        
        total_imported = sum(imported_counts.values())
        
        if errors:
            flash(f'تم استيراد {total_imported} سجل مع بعض الأخطاء', 'warning')
        else:
            flash(f'تم استيراد {total_imported} سجل بنجاح', 'success')
        
        return redirect(url_for('database_backup.backup_page'))
        
    except json.JSONDecodeError:
        flash('ملف JSON غير صالح', 'error')
        return redirect(url_for('database_backup.backup_page'))
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء الاستيراد: {str(e)}', 'error')
        return redirect(url_for('database_backup.backup_page'))

@database_backup_bp.route('/export/<table_name>')
@login_required
def export_single_table(table_name):
    """تصدير جدول واحد كملف JSON"""
    if current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Unauthorized'}), 403
    if table_name not in BACKUP_TABLES:
        flash('الجدول غير موجود', 'error')
        return redirect(url_for('database_backup.backup_page'))
    
    try:
        model = BACKUP_TABLES[table_name]
        records = model.query.all()
        
        backup_data = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'table_name': table_name,
                'record_count': len(records)
            },
            'data': [serialize_model(r) for r in records]
        }
        
        json_str = json.dumps(backup_data, ensure_ascii=False, indent=2)
        
        buffer = io.BytesIO()
        buffer.write(json_str.encode('utf-8'))
        buffer.seek(0)
        
        filename = f"nuzum_{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return send_file(
            buffer,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('database_backup.backup_page'))
