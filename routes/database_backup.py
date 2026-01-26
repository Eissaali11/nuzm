from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from sqlalchemy import inspect
from datetime import datetime
from decimal import Decimal
from models import (
    Employee, Vehicle, Department, User, Salary, Attendance, 
    MobileDevice, VehicleHandover, VehicleWorkshop, Document,
    VehicleAccident, EmployeeRequest, RentalProperty, PropertyPayment, 
    PropertyImage, PropertyFurnishing, Geofence, GeofenceSession, 
    SimCard, VoiceHubCall, VehicleExternalSafetyCheck, VehicleSafetyImage, db, UserRole
)
import json
import io
import logging

logger = logging.getLogger(__name__)

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

TABLE_ORDER = [
    'departments', 'users', 'employees', 'vehicles', 'geofences',
    'rental_properties', 'sim_cards', 'mobile_devices',
    'documents', 'salaries', 'attendance', 'vehicle_handovers',
    'vehicle_workshops', 'vehicle_accidents', 'employee_requests',
    'property_payments', 'property_images', 'property_furnishings',
    'geofence_sessions', 'voicehub_calls', 'external_safety_checks', 'safety_images'
]

def serialize_model(obj):
    """تحويل كائن SQLAlchemy إلى قاموس JSON بدقة احترافية"""
    result = {}
    try:
        mapper = inspect(obj.__class__)
        for column in mapper.columns:
            value = getattr(obj, column.name)
            
            if value is None:
                result[column.name] = None
            elif isinstance(value, datetime):
                result[column.name] = value.isoformat()
            elif hasattr(value, 'isoformat'):
                result[column.name] = value.isoformat()
            elif isinstance(value, bytes):
                result[column.name] = None
            elif isinstance(value, Decimal):
                result[column.name] = float(value)
            elif isinstance(value, (int, float, str, bool)):
                result[column.name] = value
            else:
                try:
                    json.dumps(value)
                    result[column.name] = value
                except (TypeError, ValueError):
                    result[column.name] = str(value)
    except Exception as e:
        logger.error(f"Error serializing {obj}: {e}")
    return result

def parse_date_value(value):
    """تحويل قيمة التاريخ من نص إلى كائن datetime مع الحفاظ على المنطقة الزمنية"""
    if not value or not isinstance(value, str):
        return value
    try:
        if 'T' in value:
            cleaned = value.replace('Z', '+00:00')
            try:
                return datetime.fromisoformat(cleaned)
            except:
                return datetime.fromisoformat(cleaned.split('+')[0])
        elif '-' in value and len(value) == 10:
            return datetime.strptime(value, '%Y-%m-%d')
        return value
    except:
        return None

def get_model_columns(model):
    """الحصول على أسماء الأعمدة وأنواعها للنموذج"""
    mapper = inspect(model)
    columns = {}
    for column in mapper.columns:
        col_type = str(column.type).upper()
        columns[column.name] = {
            'type': col_type,
            'is_date': any(t in col_type for t in ['DATE', 'TIME', 'TIMESTAMP'])
        }
    return columns

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
        except Exception:
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
                'version': '2.0',
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
    """استيراد البيانات من ملف JSON مع تحسين الأداء"""
    if current_user.role != UserRole.ADMIN:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        if 'backup_file' not in request.files:
            flash('لم يتم اختيار ملف', 'error')
            return redirect(url_for('database_backup.backup_page'))
        
        file = request.files['backup_file']
        if not file or file.filename == '':
            flash('لم يتم اختيار ملف', 'error')
            return redirect(url_for('database_backup.backup_page'))
        
        content = file.read().decode('utf-8')
        try:
            backup_data = json.loads(content)
        except json.JSONDecodeError:
            flash('ملف JSON غير صالح', 'error')
            return redirect(url_for('database_backup.backup_page'))
        
        if not isinstance(backup_data, dict):
            flash('ملف النسخة الاحتياطية غير صالح', 'error')
            return redirect(url_for('database_backup.backup_page'))

        if 'data' not in backup_data:
            if all(isinstance(v, list) for v in backup_data.values() if isinstance(v, list)):
                backup_data = {'data': backup_data}
            elif 'metadata' in backup_data and 'table_name' in backup_data.get('metadata', {}):
                table_name = backup_data['metadata']['table_name']
                backup_data = {'data': {table_name: backup_data.get('data', [])}}
            else:
                flash('تنسيق ملف النسخة الاحتياطية غير مدعوم', 'error')
                return redirect(url_for('database_backup.backup_page'))

        if not isinstance(backup_data.get('data'), dict):
            flash('بيانات الجداول يجب أن تكون بتنسيق صحيح', 'error')
            return redirect(url_for('database_backup.backup_page'))
        
        import_mode = request.form.get('import_mode', 'add')
        imported_counts = {}
        errors = []
        
        ordered_tables = []
        for t in TABLE_ORDER:
            if t in backup_data['data']:
                ordered_tables.append(t)
        for t in backup_data['data'].keys():
            if t not in ordered_tables and t in BACKUP_TABLES:
                ordered_tables.append(t)

        for table_name in ordered_tables:
            records = backup_data['data'].get(table_name, [])
            
            if not isinstance(records, list):
                continue
            
            if table_name not in BACKUP_TABLES:
                continue
            
            model = BACKUP_TABLES[table_name]
            columns_info = get_model_columns(model)
            valid_columns = set(columns_info.keys())
            
            try:
                if import_mode == 'replace':
                    db.session.query(model).delete()
                    db.session.commit()
                
                count = 0
                batch_size = 100
                batch_records = []
                
                for record in records:
                    if not isinstance(record, dict):
                        continue
                    
                    filtered_record = {}
                    for k, v in record.items():
                        if k not in valid_columns:
                            continue
                        
                        if columns_info[k]['is_date'] and v:
                            filtered_record[k] = parse_date_value(v)
                        else:
                            filtered_record[k] = v
                    
                    batch_records.append(filtered_record)
                    
                    if len(batch_records) >= batch_size:
                        for rec in batch_records:
                            try:
                                db.session.merge(model(**rec))
                                count += 1
                            except Exception as e:
                                logger.error(f"Record error in {table_name}: {e}")
                        try:
                            db.session.commit()
                        except Exception as e:
                            db.session.rollback()
                            logger.error(f"Batch commit error in {table_name}: {e}")
                        batch_records = []
                
                for rec in batch_records:
                    try:
                        db.session.merge(model(**rec))
                        count += 1
                    except Exception as e:
                        logger.error(f"Record error in {table_name}: {e}")
                
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Final commit error in {table_name}: {e}")
                
                imported_counts[table_name] = count
                
            except Exception as e:
                db.session.rollback()
                errors.append(f"{table_name}: {str(e)}")
                logger.error(f"Table import error {table_name}: {e}")
        
        total_imported = sum(imported_counts.values())
        
        if errors:
            flash(f'تم استيراد {total_imported} سجل مع بعض الأخطاء: {", ".join(errors[:3])}', 'warning')
        else:
            flash(f'تم استيراد {total_imported} سجل بنجاح', 'success')
        
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
