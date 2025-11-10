"""
API Endpoints الخارجية - بدون مصادقة
تستخدم للتطبيقات الخارجية مثل تطبيق الأندرويد لتتبع المواقع
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from models import Employee, EmployeeLocation, Geofence, GeofenceEvent, employee_departments, VehicleHandover, db
import os
import logging

# إنشاء Blueprint
api_external_bp = Blueprint('api_external', __name__, url_prefix='/api/external')

# مفتاح API الثابت (محفوظ في متغير بيئة)
LOCATION_API_KEY = os.environ.get('LOCATION_API_KEY', 'test_location_key_2025')

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_geofence_events(employee, latitude, longitude):
    """
    معالجة أحداث الدوائر الجغرافية عند استلام موقع جديد
    يكتشف تلقائياً دخول/خروج الموظف من جميع الدوائر (بغض النظر عن القسم)
    """
    try:
        # جلب جميع الدوائر النشطة (بدون تصفية حسب القسم)
        # هذا يضمن تسجيل جميع الدخولات والخروجات للأمان والمراقبة
        active_geofences = Geofence.query.filter(
            Geofence.is_active == True
        ).all()
        
        for geofence in active_geofences:
            # حساب المسافة من مركز الدائرة
            distance = geofence.calculate_distance(latitude, longitude)
            is_inside = distance <= geofence.radius_meters
            
            # جلب آخر حدث للموظف في هذه الدائرة
            last_event = GeofenceEvent.query.filter_by(
                geofence_id=geofence.id,
                employee_id=employee.id
            ).order_by(GeofenceEvent.recorded_at.desc()).first()
            
            # تحديد نوع الحدث
            event_type = None
            
            if is_inside:
                # داخل الدائرة
                if not last_event or last_event.event_type == 'exit':
                    # دخول جديد
                    event_type = 'enter'
                    logger.info(f"🟢 دخول: {employee.name} دخل دائرة {geofence.name}")
            else:
                # خارج الدائرة
                if last_event and last_event.event_type == 'enter':
                    # خروج جديد
                    event_type = 'exit'
                    logger.info(f"🔴 خروج: {employee.name} خرج من دائرة {geofence.name}")
            
            # تسجيل الحدث
            if event_type:
                event = GeofenceEvent(
                    geofence_id=geofence.id,
                    employee_id=employee.id,
                    event_type=event_type,
                    location_latitude=latitude,
                    location_longitude=longitude,
                    distance_from_center=int(distance),
                    source='auto',
                    notes=f'كشف تلقائي من نظام تتبع المواقع'
                )
                db.session.add(event)
                
                # إرسال إشعار (اختياري) - يمكن تفعيله لاحقاً
                if (event_type == 'enter' and geofence.notify_on_entry) or \
                   (event_type == 'exit' and geofence.notify_on_exit):
                    # TODO: إضافة إشعارات (SendGrid أو Twilio)
                    logger.info(f"📧 يجب إرسال إشعار لـ {event_type} في {geofence.name}")
        
        db.session.commit()
        
    except Exception as e:
        logger.error(f"خطأ في معالجة أحداث الدوائر الجغرافية: {str(e)}")
        db.session.rollback()


@api_external_bp.route('/employee-location', methods=['POST'])
def receive_employee_location():
    """
    استقبال موقع الموظف من تطبيق الأندرويد
    
    مثال على البيانات المُرسلة:
    {
        "api_key": "test_location_key_2025",
        "job_number": "EMP12345",
        "latitude": 24.7136,
        "longitude": 46.6753,
        "accuracy": 10.5,
        "recorded_at": "2025-11-07T10:30:00Z"
    }
    """
    try:
        # الحصول على البيانات
        data = request.get_json()
        
        if not data:
            logger.warning(f"طلب فارغ من {request.remote_addr}")
            return jsonify({
                'success': False,
                'error': 'لا توجد بيانات في الطلب'
            }), 400
        
        # التحقق من مفتاح API
        api_key = data.get('api_key')
        if not api_key or api_key != LOCATION_API_KEY:
            logger.warning(f"محاولة وصول بمفتاح خاطئ من {request.remote_addr}")
            return jsonify({
                'success': False,
                'error': 'مفتاح API غير صحيح'
            }), 401
        
        # التحقق من البيانات المطلوبة
        job_number = data.get('job_number')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not job_number:
            return jsonify({
                'success': False,
                'error': 'الرقم الوظيفي مطلوب'
            }), 400
        
        if latitude is None or longitude is None:
            return jsonify({
                'success': False,
                'error': 'الإحداثيات (latitude, longitude) مطلوبة'
            }), 400
        
        # التحقق من صحة الإحداثيات
        try:
            lat = float(latitude)
            lng = float(longitude)
            
            # التحقق من النطاق المعقول للإحداثيات
            if not (-90 <= lat <= 90):
                return jsonify({
                    'success': False,
                    'error': 'latitude يجب أن يكون بين -90 و 90'
                }), 400
            
            if not (-180 <= lng <= 180):
                return jsonify({
                    'success': False,
                    'error': 'longitude يجب أن يكون بين -180 و 180'
                }), 400
                
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'الإحداثيات يجب أن تكون أرقام صحيحة'
            }), 400
        
        # البحث عن الموظف باستخدام job_number
        employee = Employee.query.filter_by(employee_id=job_number).first()
        
        if not employee:
            logger.warning(f"موظف غير موجود: {job_number} من {request.remote_addr}")
            return jsonify({
                'success': False,
                'error': f'لم يتم العثور على موظف بالرقم الوظيفي: {job_number}'
            }), 404
        
        # البيانات الاختيارية
        accuracy = data.get('accuracy')
        recorded_at_str = data.get('recorded_at')
        notes = data.get('notes', '')
        
        # تحليل وقت التسجيل
        if recorded_at_str:
            try:
                recorded_at = datetime.fromisoformat(recorded_at_str.replace('Z', '+00:00'))
            except:
                recorded_at = datetime.utcnow()
        else:
            recorded_at = datetime.utcnow()
        
        # إنشاء سجل الموقع الجديد
        location = EmployeeLocation(
            employee_id=employee.id,
            latitude=lat,
            longitude=lng,
            accuracy_m=float(accuracy) if accuracy else None,
            source='android_app',
            recorded_at=recorded_at,
            received_at=datetime.utcnow(),
            notes=notes
        )
        
        # حفظ في قاعدة البيانات
        db.session.add(location)
        db.session.commit()
        
        # معالجة الدوائر الجغرافية (كشف تلقائي للدخول/الخروج)
        process_geofence_events(employee, lat, lng)
        
        # تسجيل النجاح
        logger.info(f"✅ تم حفظ موقع الموظف {employee.name} ({job_number}) من {request.remote_addr}")
        
        return jsonify({
            'success': True,
            'message': 'تم حفظ الموقع بنجاح',
            'data': {
                'employee_name': employee.name,
                'location_id': location.id,
                'recorded_at': location.recorded_at.isoformat(),
                'received_at': location.received_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"خطأ في حفظ الموقع: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'حدث خطأ في الخادم'
        }), 500


@api_external_bp.route('/test', methods=['GET'])
def test_api():
    """نقطة اختبار بسيطة للتأكد من عمل API"""
    return jsonify({
        'success': True,
        'message': 'External API is working!',
        'endpoints': {
            'employee_location': '/api/external/employee-location [POST]',
            'employee_complete_profile': '/api/external/employee-complete-profile [POST]'
        }
    }), 200


def parse_date_filters(data):
    """تحليل فلاتر التاريخ من الطلب"""
    from datetime import datetime
    
    month = data.get('month')  # YYYY-MM format
    start_date = data.get('start_date')  # YYYY-MM-DD
    end_date = data.get('end_date')  # YYYY-MM-DD
    
    # إذا تم إرسال month، استخدمه وتجاهل start/end
    if month:
        try:
            year, month_num = map(int, month.split('-'))
            # أول يوم في الشهر
            start = datetime(year, month_num, 1).date()
            # آخر يوم في الشهر
            import calendar
            last_day = calendar.monthrange(year, month_num)[1]
            end = datetime(year, month_num, last_day).date()
            return start, end
        except (ValueError, AttributeError):
            raise ValueError("تنسيق month غير صحيح. يجب أن يكون YYYY-MM")
    
    # إذا تم إرسال start_date أو end_date
    if start_date or end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
            return start, end
        except ValueError:
            raise ValueError("تنسيق التاريخ غير صحيح. يجب أن يكون YYYY-MM-DD")
    
    # افتراضياً: آخر 30 يوم للحضور، آخر 12 شهر للرواتب
    return None, None


def get_employee_data(employee, request_origin=None):
    """جلب معلومات الموظف الكاملة"""
    # جلب القسم الأول
    department = employee.departments[0] if employee.departments else None
    
    # بناء روابط الصور الكاملة
    def build_image_url(image_path):
        if not image_path:
            return None
        if image_path.startswith('http'):
            return image_path
        # استخدام request_origin إذا توفر، وإلا استخدام رابط افتراضي
        if request_origin:
            return f"{request_origin}/static/uploads/{image_path}"
        return f"/static/uploads/{image_path}"
    
    return {
        'job_number': employee.employee_id,
        'name': employee.name,
        'name_en': None,  # غير متوفر في النموذج
        'national_id': employee.national_id,
        'birth_date': employee.birth_date.strftime('%Y-%m-%d') if employee.birth_date else None,
        'hire_date': employee.join_date.strftime('%Y-%m-%d') if employee.join_date else None,
        'nationality': employee.nationality,
        'residence_expiry_date': None,  # يمكن إضافته لاحقاً من Documents
        'sponsor_name': employee.current_sponsor_name,
        'absher_phone': employee.mobilePersonal,
        'department': department.name if department else None,
        'department_en': None,
        'section': None,  # غير متوفر
        'section_en': None,
        'position': employee.job_title,
        'position_en': None,
        'phone': employee.mobile,
        'email': employee.email,
        'address': employee.residence_details,
        'is_driver': employee.employee_type == 'driver',
        'photos': {
            'personal': build_image_url(employee.profile_image),
            'id': build_image_url(employee.national_id_image),
            'license': build_image_url(employee.license_image) if employee.employee_type == 'driver' else None
        }
    }


def get_vehicle_assignments(employee_id):
    """جلب السيارة الحالية والسيارات السابقة للموظف"""
    from models import Vehicle
    
    # جلب جميع عمليات التسليم والاستلام للموظف
    handovers = VehicleHandover.query.filter_by(
        employee_id=employee_id
    ).order_by(
        VehicleHandover.handover_date.desc(),
        VehicleHandover.handover_time.desc()
    ).all()
    
    current_car = None
    previous_cars = []
    processed_vehicles = set()
    
    # بناء map للتسليمات والاستلامات لكل سيارة
    vehicle_operations = {}
    for h in handovers:
        if h.vehicle_id not in vehicle_operations:
            vehicle_operations[h.vehicle_id] = []
        vehicle_operations[h.vehicle_id].append(h)
    
    # معالجة كل سيارة
    for vehicle_id, ops in vehicle_operations.items():
        # ترتيب العمليات حسب التاريخ (الأحدث أولاً)
        ops.sort(key=lambda x: (x.handover_date, x.handover_time or datetime.min.time()), reverse=True)
        
        latest_op = ops[0]
        vehicle = Vehicle.query.get(vehicle_id)
        
        if not vehicle:
            continue
        
        vehicle_data = {
            'car_id': str(vehicle.id),
            'plate_number': vehicle.plate_number,
            'plate_number_en': None,
            'model': f"{vehicle.make} {vehicle.model}",
            'model_en': None,
            'color': vehicle.color,
            'color_en': None,
            'status': vehicle.status,
            'assigned_date': latest_op.handover_date.isoformat() if latest_op.handover_date else None,
            'photo': None,  # يمكن إضافته لاحقاً
            'notes': vehicle.notes
        }
        
        # السيارة الحالية: آخر عملية هي تسليم ولم يتم استلامها بعد
        if latest_op.handover_type == 'delivery' and vehicle_id not in processed_vehicles:
            current_car = vehicle_data.copy()
            current_car.pop('unassigned_date', None)  # السيارة الحالية ليس لها unassigned_date
            processed_vehicles.add(vehicle_id)
        else:
            # السيارات السابقة
            if vehicle_id not in processed_vehicles:
                # البحث عن آخر استلام
                last_receipt = next((op for op in ops if op.handover_type == 'receipt'), None)
                vehicle_data['unassigned_date'] = last_receipt.handover_date.isoformat() if last_receipt and last_receipt.handover_date else None
                previous_cars.append(vehicle_data)
                processed_vehicles.add(vehicle_id)
    
    return current_car, previous_cars


def get_attendance_records(employee_id, start_date, end_date):
    """جلب سجلات الحضور للموظف مع فلترة التواريخ"""
    from models import Attendance as AttendanceModel
    from datetime import datetime, timedelta
    
    query = AttendanceModel.query.filter_by(employee_id=employee_id)
    
    # تطبيق الفلترة
    if start_date:
        query = query.filter(AttendanceModel.date >= start_date)
    if end_date:
        query = query.filter(AttendanceModel.date <= end_date)
    
    # إذا لم يتم تحديد فلترة، جلب آخر 30 يوم
    if not start_date and not end_date:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        query = query.filter(AttendanceModel.date >= start_date, AttendanceModel.date <= end_date)
    
    records = query.order_by(AttendanceModel.date.desc()).all()
    
    attendance_list = []
    for att in records:
        # حساب الساعات
        hours_worked = 0.0
        if att.check_in and att.check_out:
            check_in_dt = datetime.combine(att.date, att.check_in)
            check_out_dt = datetime.combine(att.date, att.check_out)
            hours_worked = (check_out_dt - check_in_dt).total_seconds() / 3600
        
        attendance_list.append({
            'date': att.date.strftime('%Y-%m-%d'),
            'check_in': att.check_in.strftime('%H:%M') if att.check_in else None,
            'check_out': att.check_out.strftime('%H:%M') if att.check_out else None,
            'status': att.status,
            'hours_worked': round(hours_worked, 2),
            'late_minutes': 0,  # يمكن حسابه لاحقاً
            'early_leave_minutes': 0,  # يمكن حسابه لاحقاً
            'notes': att.notes
        })
    
    return attendance_list


def get_salary_records(employee_id, start_date, end_date):
    """جلب سجلات الرواتب للموظف مع فلترة التواريخ"""
    from models import Salary as SalaryModel
    from datetime import datetime, date as date_cls
    from dateutil.relativedelta import relativedelta
    
    query = SalaryModel.query.filter_by(employee_id=employee_id)
    
    # تطبيق الفلترة حسب الشهر والسنة
    if start_date:
        query = query.filter(
            db.or_(
                SalaryModel.year > start_date.year,
                db.and_(
                    SalaryModel.year == start_date.year,
                    SalaryModel.month >= start_date.month
                )
            )
        )
    if end_date:
        query = query.filter(
            db.or_(
                SalaryModel.year < end_date.year,
                db.and_(
                    SalaryModel.year == end_date.year,
                    SalaryModel.month <= end_date.month
                )
            )
        )
    
    # إذا لم يتم تحديد فلترة، جلب آخر 12 شهر
    if not start_date and not end_date:
        end_date = datetime.now().date()
        start_date = end_date - relativedelta(months=12)
        query = query.filter(
            db.or_(
                SalaryModel.year > start_date.year,
                db.and_(
                    SalaryModel.year == start_date.year,
                    SalaryModel.month >= start_date.month
                )
            )
        )
    
    records = query.order_by(SalaryModel.year.desc(), SalaryModel.month.desc()).all()
    
    salary_list = []
    for sal in records:
        salary_list.append({
            'salary_id': f"SAL-{sal.year}-{sal.month:02d}",
            'month': f"{sal.year}-{sal.month:02d}",
            'amount': float(sal.net_salary),
            'currency': 'SAR',
            'paid_date': sal.created_at.isoformat() if sal.is_paid and sal.created_at else None,
            'status': 'paid' if sal.is_paid else 'pending',
            'details': {
                'base_salary': float(sal.basic_salary),
                'allowances': float(sal.allowances),
                'deductions': float(sal.deductions),
                'bonuses': float(sal.bonus),
                'overtime': float(sal.overtime_hours * (sal.basic_salary / 30 / 8)) if sal.overtime_hours else 0.0,  # تقدير تقريبي
                'tax': 0.0  # لا توجد ضرائب في السعودية
            },
            'notes': sal.notes
        })
    
    return salary_list


def get_operations_records(employee_id):
    """جلب سجلات العمليات (التسليم/الاستلام) للموظف"""
    from models import Vehicle
    
    # جلب جميع عمليات التسليم والاستلام
    handovers = VehicleHandover.query.filter_by(
        employee_id=employee_id
    ).order_by(VehicleHandover.handover_date.desc()).all()
    
    operations = []
    for h in handovers:
        vehicle = Vehicle.query.get(h.vehicle_id)
        
        operations.append({
            'operation_id': f"OP-{h.id}",
            'type': 'delivery' if h.handover_type == 'delivery' else 'pickup',
            'date': f"{h.handover_date.isoformat()}T{h.handover_time.isoformat() if h.handover_time else '00:00:00'}",
            'car_id': str(h.vehicle_id),
            'car_plate_number': vehicle.plate_number if vehicle else None,
            'client_name': h.supervisor_name or h.person_name,
            'client_phone': h.supervisor_phone_number,
            'address': h.city or h.project_name or '',
            'status': 'completed',  # جميع العمليات المسجلة تعتبر مكتملة
            'notes': h.notes
        })
    
    return operations


def calculate_statistics(attendance, salaries, current_car, previous_cars, operations):
    """حساب الإحصائيات الشاملة"""
    # إحصائيات الحضور
    total_days = len(attendance)
    present_days = len([a for a in attendance if a['status'] in ['present', 'late', 'early_leave']])
    absent_days = len([a for a in attendance if a['status'] == 'absent'])
    late_days = len([a for a in attendance if a['status'] == 'late'])
    early_leave_days = len([a for a in attendance if a['status'] == 'early_leave'])
    total_hours = sum([a['hours_worked'] for a in attendance])
    attendance_rate = round((present_days / total_days * 100) if total_days > 0 else 0.0, 2)
    
    # إحصائيات الرواتب
    total_salaries = len(salaries)
    total_amount = sum([s['amount'] for s in salaries])
    average_amount = round(total_amount / total_salaries if total_salaries > 0 else 0.0, 2)
    last_salary = salaries[0]['amount'] if salaries else 0.0
    last_paid_date = salaries[0]['paid_date'] if salaries and salaries[0]['paid_date'] else None
    
    # إحصائيات السيارات
    all_cars = previous_cars + ([current_car] if current_car else [])
    total_cars = len(all_cars)
    active_cars = len([c for c in all_cars if c['status'] == 'available'])
    maintenance_cars = len([c for c in all_cars if c['status'] == 'in_workshop'])
    retired_cars = len([c for c in all_cars if c['status'] == 'out_of_service'])
    
    # إحصائيات العمليات
    total_operations = len(operations)
    delivery_count = len([o for o in operations if o['type'] == 'delivery'])
    pickup_count = len([o for o in operations if o['type'] == 'pickup'])
    completed_count = len([o for o in operations if o['status'] == 'completed'])
    
    return {
        'attendance': {
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'late_days': late_days,
            'early_leave_days': early_leave_days,
            'total_hours': round(total_hours, 2),
            'attendance_rate': attendance_rate
        },
        'salaries': {
            'total_salaries': total_salaries,
            'total_amount': round(total_amount, 2),
            'average_amount': average_amount,
            'last_salary': last_salary,
            'last_paid_date': last_paid_date
        },
        'cars': {
            'current_car': current_car is not None,
            'total_cars': total_cars,
            'active_cars': active_cars,
            'maintenance_cars': maintenance_cars,
            'retired_cars': retired_cars
        },
        'operations': {
            'total_operations': total_operations,
            'delivery_count': delivery_count,
            'pickup_count': pickup_count,
            'completed_count': completed_count
        }
    }


@api_external_bp.route('/employee-complete-profile', methods=['POST'])
def get_employee_complete_profile():
    """
    جلب الملف الشامل للموظف
    يتضمن جميع المعلومات: الموظف، السيارات، الحضور، الرواتب، العمليات، الإحصائيات
    """
    try:
        # الحصول على البيانات
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'طلب فارغ',
                'error': 'No data provided'
            }), 400
        
        # التحقق من مفتاح API
        api_key = data.get('api_key')
        if not api_key or api_key != LOCATION_API_KEY:
            logger.warning(f"محاولة وصول بمفتاح خاطئ إلى employee-complete-profile من {request.remote_addr}")
            return jsonify({
                'success': False,
                'message': 'غير مصرح. يرجى التحقق من المفتاح',
                'error': 'Invalid API key'
            }), 401
        
        # التحقق من job_number
        job_number = data.get('job_number')
        if not job_number:
            return jsonify({
                'success': False,
                'message': 'طلب غير صحيح',
                'error': 'Missing required field: job_number'
            }), 400
        
        # البحث عن الموظف
        employee = Employee.query.filter_by(employee_id=job_number).first()
        
        if not employee:
            logger.warning(f"موظف غير موجود: {job_number}")
            return jsonify({
                'success': False,
                'message': 'الموظف غير موجود',
                'error': 'Employee not found'
            }), 404
        
        # تحليل فلاتر التواريخ
        try:
            start_date, end_date = parse_date_filters(data)
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': 'طلب غير صحيح',
                'error': str(e)
            }), 400
        
        # جلب معلومات الموظف
        request_origin = request.host_url.rstrip('/')
        employee_data = get_employee_data(employee, request_origin)
        
        # جلب السيارات
        current_car, previous_cars = get_vehicle_assignments(employee.id)
        
        # جلب الحضور
        attendance = get_attendance_records(employee.id, start_date, end_date)
        
        # جلب الرواتب
        salaries = get_salary_records(employee.id, start_date, end_date)
        
        # جلب العمليات
        operations = get_operations_records(employee.id)
        
        # حساب الإحصائيات
        statistics = calculate_statistics(attendance, salaries, current_car, previous_cars, operations)
        
        # بناء الاستجابة
        response_data = {
            'employee': employee_data,
            'current_car': current_car,
            'previous_cars': previous_cars,
            'attendance': attendance,
            'salaries': salaries,
            'operations': operations,
            'statistics': statistics
        }
        
        logger.info(f"✅ تم جلب الملف الشامل للموظف {employee.name} ({job_number})")
        
        return jsonify({
            'success': True,
            'message': 'تم جلب البيانات بنجاح',
            'data': response_data
        }), 200
        
    except Exception as e:
        logger.error(f"خطأ في جلب الملف الشامل للموظف: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'خطأ في السيرفر',
            'error': 'Internal server error'
        }), 500


@api_external_bp.route('/verify-employee/<employee_id>/<national_id>', methods=['GET'])
def verify_employee(employee_id, national_id):
    """
    التحقق من وجود الموظف باستخدام رقم الموظف الوظيفي ورقم الهوية
    
    نقطة نهاية بسيطة للطرف الثالث للتحقق من هوية الموظف
    لا تحتاج إلى مصادقة
    
    استخدام:
    GET /api/external/verify-employee/EMP001/1234567890
    
    استجابة:
    {
        "exists": true
    }
    أو
    {
        "exists": false
    }
    """
    try:
        # البحث عن الموظف باستخدام الرقم الوظيفي ورقم الهوية
        employee = Employee.query.filter_by(
            employee_id=employee_id,
            national_id=national_id
        ).first()
        
        if employee:
            logger.info(f"✅ تحقق ناجح: الموظف {employee.name} ({employee_id}) موجود")
            return jsonify({'exists': True}), 200
        else:
            logger.info(f"❌ تحقق فاشل: لا يوجد موظف بالرقم الوظيفي {employee_id} ورقم الهوية {national_id}")
            return jsonify({'exists': False}), 200
            
    except Exception as e:
        logger.error(f"خطأ في التحقق من الموظف: {str(e)}")
        return jsonify({
            'exists': False,
            'error': 'حدث خطأ في الخادم'
        }), 500
