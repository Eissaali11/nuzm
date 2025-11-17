from flask import Blueprint, jsonify, request, url_for
from models import Employee, Department, Document, Vehicle, VehicleHandover, VehicleHandoverImage, InspectionUploadToken, VehicleInspectionRecord, VehicleInspectionImage
from app import db
import os
import uuid
from datetime import timedelta

api_bp = Blueprint('api', __name__, url_prefix='/api')

def get_full_url(relative_path):
    """
    تحويل المسار النسبي إلى رابط كامل باستخدام النطاق الصحيح
    """
    # استخدام النطاق المخصص (nuzum.site) كافتراضي
    base_url = os.environ.get('CUSTOM_DOMAIN', 'http://nuzum.site')
    
    # إزالة / في نهاية base_url إن وجدت
    base_url = base_url.rstrip('/')
    
    # إزالة / في بداية relative_path إن وجدت  
    relative_path = relative_path.lstrip('/')
    
    # التأكد من أن المسار يبدأ بـ static/
    if not relative_path.startswith('static/'):
        relative_path = f"static/{relative_path}"
    
    return f"{base_url}/{relative_path}"

@api_bp.route('/employees')
def get_employees():
    """الحصول على قائمة الموظفين لاستخدامها في واجهات المستخدم"""
    employees = Employee.query.filter_by(status='active').all()
    employees_list = []
    
    for employee in employees:
        employee_data = {
            'id': employee.id,
            'employee_id': employee.employee_id,
            'name': employee.name,
            'job_title': employee.job_title,
            'department': employee.department.name if employee.department else None,
            'contract_type': employee.contract_type,
            'nationality': employee.nationality,
            'basic_salary': employee.basic_salary,
            'has_national_balance': employee.has_national_balance
        }
        employees_list.append(employee_data)
    
    return jsonify(employees_list)

@api_bp.route('/departments')
def get_departments():
    """الحصول على قائمة الأقسام لاستخدامها في واجهات المستخدم"""
    departments = Department.query.all()
    departments_list = []
    
    for department in departments:
        department_data = {
            'id': department.id,
            'name': department.name,
            'description': department.description,
            'manager': department.manager.name if department.manager else None,
            'employee_count': len(department.employees)
        }
        departments_list.append(department_data)
    
    return jsonify(departments_list)

@api_bp.route('/documents/expiring/<int:days>')
def get_expiring_documents(days):
    """الحصول على المستندات التي ستنتهي خلال عدد محدد من الأيام"""
    from datetime import datetime, timedelta
    
    # حساب تاريخ البداية والنهاية
    today = datetime.now().date()
    end_date = today + timedelta(days=days)
    
    # البحث عن المستندات التي تنتهي في هذه الفترة
    documents = Document.query.filter(
        Document.expiry_date >= today,
        Document.expiry_date <= end_date
    ).all()
    
    documents_list = []
    for doc in documents:
        days_remaining = (doc.expiry_date - today).days
        document_data = {
            'id': doc.id,
            'employee_id': doc.employee_id,
            'employee_name': doc.employee.name,
            'document_type': doc.document_type,
            'document_number': doc.document_number,
            'expiry_date': doc.expiry_date.strftime('%Y-%m-%d'),
            'days_remaining': days_remaining,
            'contract_type': doc.employee.contract_type,
            'nationality': doc.employee.nationality
        }
        documents_list.append(document_data)
    
    return jsonify(documents_list)





@api_bp.route('/employees/nationality/stats')
def get_nationality_stats():
    """إحصائيات عدد الموظفين حسب الجنسية ونوع العقد"""
    from sqlalchemy import func
    
    # إحصائيات حسب نوع العقد
    contract_stats = db.session.query(
        Employee.contract_type,
        func.count(Employee.id).label('count')
    ).group_by(Employee.contract_type).all()
    
    contract_summary = {
        'saudi': 0,
        'foreign': 0
    }
    
    for contract_type, count in contract_stats:
        if contract_type in contract_summary:
            contract_summary[contract_type] = count
        else:
            # افتراضيًا، إذا لم يكن النوع محددًا نعتبره وافد
            contract_summary['foreign'] += count
    
    # إحصائيات حسب الجنسية
    nationality_stats = db.session.query(
        Employee.nationality,
        func.count(Employee.id).label('count')
    ).filter(Employee.nationality != None)\
     .group_by(Employee.nationality)\
     .order_by(func.count(Employee.id).desc())\
     .limit(5)\
     .all()
    
    nationality_summary = {}
    for nationality, count in nationality_stats:
        nationality_summary[nationality] = count
    
    return jsonify({
        'contract_stats': contract_summary,
        'nationality_stats': nationality_summary,
        'total_employees': sum(contract_summary.values())
    })


@api_bp.route('/employees/<int:employee_id>/vehicle', methods=['GET'])
def get_employee_vehicle_details(employee_id):
    """
    جلب تفاصيل السيارة المربوطة بالموظف مع كافة المعلومات
    
    يشمل:
    - معلومات السيارة الأساسية
    - صور الاستمارة والتأمين
    - تواريخ انتهاء التفويض والفحص الدوري
    - سجلات التسليم والاستلام
    - صور نماذج التسليم والاستلام
    
    Parameters:
        employee_id: رقم الموظف في النظام
    
    Returns:
        JSON object with vehicle details or error message
    """
    try:
        # جلب بيانات الموظف
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({
                'success': False,
                'message': 'الموظف غير موجود'
            }), 404
        
        # جلب السيارة الحالية المربوطة بالموظف
        vehicle = Vehicle.query.filter_by(driver_name=employee.name).first()
        
        if not vehicle:
            return jsonify({
                'success': False,
                'message': 'لا توجد سيارة مربوطة بهذا الموظف حالياً'
            }), 404
        
        # جلب سجلات التسليم والاستلام للموظف
        handover_records = VehicleHandover.query.filter_by(
            employee_id=employee_id
        ).order_by(VehicleHandover.handover_date.desc()).all()
        
        # تحضير قائمة سجلات التسليم والاستلام
        handovers_list = []
        for handover in handover_records:
            # جلب صور نموذج التسليم/الاستلام
            handover_images = VehicleHandoverImage.query.filter_by(
                handover_record_id=handover.id
            ).all()
            
            # إنشاء رابط PDF لنموذج التسليم/الاستلام
            base_url = os.environ.get('CUSTOM_DOMAIN', 'http://nuzum.site')
            pdf_link = f"{base_url.rstrip('/')}/vehicles/handover/{handover.id}/pdf/public"
            
            handover_data = {
                'id': handover.id,
                'handover_type': handover.handover_type,
                'handover_type_arabic': 'تسليم' if handover.handover_type == 'delivery' else 'استلام',
                'handover_date': handover.handover_date.strftime('%Y-%m-%d') if handover.handover_date else None,
                'handover_time': handover.handover_time.strftime('%H:%M') if handover.handover_time else None,
                'mileage': handover.mileage,
                'vehicle_plate_number': handover.vehicle_plate_number,
                'vehicle_type': f"{handover.vehicle_car_type} {handover.vehicle_model_year}" if handover.vehicle_car_type else None,
                'project_name': handover.project_name,
                'city': handover.city,
                'person_name': handover.person_name,
                'supervisor_name': handover.supervisor_name,
                'fuel_level': handover.fuel_level,
                'notes': handover.notes,
                'reason_for_change': handover.reason_for_change,
                'vehicle_status_summary': handover.vehicle_status_summary,
                'form_link': handover.form_link,
                'form_link_2': handover.form_link_2,
                'pdf_link': pdf_link,
                'driver_signature': get_full_url(handover.driver_signature_path.replace('static/', '')) if handover.driver_signature_path else None,
                'supervisor_signature': get_full_url(handover.supervisor_signature_path.replace('static/', '')) if handover.supervisor_signature_path else None,
                'damage_diagram': get_full_url(handover.damage_diagram_path.replace('static/', '')) if handover.damage_diagram_path else None,
                'checklist': {
                    'spare_tire': handover.has_spare_tire,
                    'fire_extinguisher': handover.has_fire_extinguisher,
                    'first_aid_kit': handover.has_first_aid_kit,
                    'warning_triangle': handover.has_warning_triangle,
                    'tools': handover.has_tools,
                    'oil_leaks': handover.has_oil_leaks,
                    'gear_issue': handover.has_gear_issue,
                    'clutch_issue': handover.has_clutch_issue,
                    'engine_issue': handover.has_engine_issue,
                    'windows_issue': handover.has_windows_issue,
                    'tires_issue': handover.has_tires_issue,
                    'body_issue': handover.has_body_issue,
                    'electricity_issue': handover.has_electricity_issue,
                    'lights_issue': handover.has_lights_issue,
                    'ac_issue': handover.has_ac_issue
                },
                'images': [
                    {
                        'id': img.id,
                        'url': get_full_url(img.image_path.replace('static/', '')) if img.image_path else None,
                        'uploaded_at': img.uploaded_at.strftime('%Y-%m-%d %H:%M:%S') if img.uploaded_at else None
                    }
                    for img in handover_images
                ],
                'drive_folder_id': handover.drive_folder_id,
                'drive_pdf_link': handover.drive_pdf_link,
                'drive_upload_status': handover.drive_upload_status
            }
            handovers_list.append(handover_data)
        
        # تحضير بيانات السيارة الكاملة
        vehicle_data = {
            'success': True,
            'vehicle': {
                'id': vehicle.id,
                'plate_number': vehicle.plate_number,
                'make': vehicle.make,
                'model': vehicle.model,
                'year': vehicle.year,
                'color': vehicle.color,
                'type_of_car': vehicle.type_of_car,
                'status': vehicle.status,
                'status_arabic': vehicle.status_arabic,
                'driver_name': vehicle.driver_name,
                'project': vehicle.project,
                'department': vehicle.department.name if vehicle.department else None,
                'notes': vehicle.notes,
                'created_at': vehicle.created_at.strftime('%Y-%m-%d %H:%M:%S') if vehicle.created_at else None,
                'updated_at': vehicle.updated_at.strftime('%Y-%m-%d %H:%M:%S') if vehicle.updated_at else None,
                
                # تواريخ انتهاء الوثائق الهامة
                'authorization_expiry_date': vehicle.authorization_expiry_date.strftime('%Y-%m-%d') if vehicle.authorization_expiry_date else None,
                'registration_expiry_date': vehicle.registration_expiry_date.strftime('%Y-%m-%d') if vehicle.registration_expiry_date else None,
                'inspection_expiry_date': vehicle.inspection_expiry_date.strftime('%Y-%m-%d') if vehicle.inspection_expiry_date else None,
                
                # صور ووثائق السيارة
                'registration_form_image': get_full_url(vehicle.registration_form_image.replace('static/', '')) if vehicle.registration_form_image else None,
                'insurance_file': get_full_url(vehicle.insurance_file.replace('static/', '')) if vehicle.insurance_file else None,
                'license_image': get_full_url(vehicle.license_image.replace('static/', '')) if vehicle.license_image else None,
                'plate_image': get_full_url(vehicle.plate_image.replace('static/', '')) if vehicle.plate_image else None,
                
                # رابط Google Drive
                'drive_folder_link': vehicle.drive_folder_link
            },
            'employee': {
                'id': employee.id,
                'employee_id': employee.employee_id,
                'name': employee.name,
                'mobile': employee.mobile,
                'mobile_personal': employee.mobilePersonal,
                'job_title': employee.job_title,
                'department': employee.department.name if employee.department else None
            },
            'handover_records': handovers_list,
            'handover_count': len(handovers_list)
        }
        
        return jsonify(vehicle_data), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'حدث خطأ أثناء جلب البيانات: {str(e)}'
        }), 500


@api_bp.route('/vehicles/<int:vehicle_id>/details', methods=['GET'])
def get_vehicle_details_by_id(vehicle_id):
    """
    جلب تفاصيل السيارة بواسطة ID السيارة مع كافة المعلومات
    
    يشمل:
    - معلومات السيارة الأساسية
    - صور الاستمارة والتأمين
    - تواريخ انتهاء التفويض والفحص الدوري
    - معلومات السائق الحالي
    - سجلات التسليم والاستلام
    
    Parameters:
        vehicle_id: رقم السيارة في النظام
    
    Returns:
        JSON object with vehicle details or error message
    """
    try:
        # جلب بيانات السيارة
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            return jsonify({
                'success': False,
                'message': 'السيارة غير موجودة'
            }), 404
        
        # جلب بيانات السائق الحالي إذا كان موجوداً
        current_driver = None
        if vehicle.driver_name:
            current_driver = Employee.query.filter_by(name=vehicle.driver_name).first()
        
        # جلب سجلات التسليم والاستلام لهذه السيارة
        handover_records = VehicleHandover.query.filter_by(
            vehicle_id=vehicle_id
        ).order_by(VehicleHandover.handover_date.desc()).all()
        
        # تحضير قائمة سجلات التسليم والاستلام
        handovers_list = []
        for handover in handover_records:
            # جلب صور نموذج التسليم/الاستلام
            handover_images = VehicleHandoverImage.query.filter_by(
                handover_record_id=handover.id
            ).all()
            
            handover_data = {
                'id': handover.id,
                'handover_type': handover.handover_type,
                'handover_type_arabic': 'تسليم' if handover.handover_type == 'delivery' else 'استلام',
                'handover_date': handover.handover_date.strftime('%Y-%m-%d') if handover.handover_date else None,
                'handover_time': handover.handover_time.strftime('%H:%M') if handover.handover_time else None,
                'mileage': handover.mileage,
                'person_name': handover.person_name,
                'supervisor_name': handover.supervisor_name,
                'fuel_level': handover.fuel_level,
                'project_name': handover.project_name,
                'city': handover.city,
                'notes': handover.notes,
                'form_link': handover.form_link,
                'form_link_2': handover.form_link_2,
                'images': [
                    {
                        'id': img.id,
                        'url': url_for('static', filename=img.image_path.replace('static/', ''), _external=True) if img.image_path else None,
                        'uploaded_at': img.uploaded_at.strftime('%Y-%m-%d %H:%M:%S') if img.uploaded_at else None
                    }
                    for img in handover_images
                ],
                'drive_pdf_link': handover.drive_pdf_link
            }
            handovers_list.append(handover_data)
        
        # تحضير بيانات السيارة الكاملة
        vehicle_data = {
            'success': True,
            'vehicle': {
                'id': vehicle.id,
                'plate_number': vehicle.plate_number,
                'make': vehicle.make,
                'model': vehicle.model,
                'year': vehicle.year,
                'color': vehicle.color,
                'type_of_car': vehicle.type_of_car,
                'status': vehicle.status,
                'status_arabic': vehicle.status_arabic,
                'driver_name': vehicle.driver_name,
                'project': vehicle.project,
                'department': vehicle.department.name if vehicle.department else None,
                'notes': vehicle.notes,
                
                # تواريخ انتهاء الوثائق الهامة
                'authorization_expiry_date': vehicle.authorization_expiry_date.strftime('%Y-%m-%d') if vehicle.authorization_expiry_date else None,
                'registration_expiry_date': vehicle.registration_expiry_date.strftime('%Y-%m-%d') if vehicle.registration_expiry_date else None,
                'inspection_expiry_date': vehicle.inspection_expiry_date.strftime('%Y-%m-%d') if vehicle.inspection_expiry_date else None,
                
                # صور ووثائق السيارة
                'registration_form_image': get_full_url(vehicle.registration_form_image.replace('static/', '')) if vehicle.registration_form_image else None,
                'insurance_file': get_full_url(vehicle.insurance_file.replace('static/', '')) if vehicle.insurance_file else None,
                'license_image': get_full_url(vehicle.license_image.replace('static/', '')) if vehicle.license_image else None,
                'plate_image': get_full_url(vehicle.plate_image.replace('static/', '')) if vehicle.plate_image else None,
                
                # رابط Google Drive
                'drive_folder_link': vehicle.drive_folder_link
            },
            'current_driver': {
                'id': current_driver.id,
                'employee_id': current_driver.employee_id,
                'name': current_driver.name,
                'mobile': current_driver.mobile,
                'mobile_personal': current_driver.mobilePersonal,
                'job_title': current_driver.job_title,
                'department': current_driver.department.name if current_driver.department else None
            } if current_driver else None,
            'handover_records': handovers_list,
            'handover_count': len(handovers_list)
        }
        
        return jsonify(vehicle_data), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'حدث خطأ أثناء جلب البيانات: {str(e)}'
        }), 500

@api_bp.route('/vehicles/<int:vehicle_id>/generate-inspection-link', methods=['POST'])
def generate_inspection_link(vehicle_id):
    """
    توليد token ورابط رفع جديد لصور الفحص الدوري
    """
    try:
        from datetime import datetime
        
        vehicle = Vehicle.query.get_or_404(vehicle_id)
        
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=30)
        
        upload_token = InspectionUploadToken(
            vehicle_id=vehicle_id,
            token=token,
            created_by=None,
            expires_at=expires_at,
            is_active=True
        )
        db.session.add(upload_token)
        db.session.commit()
        
        base_url = os.environ.get('CUSTOM_DOMAIN', 'http://nuzum.site')
        upload_url = f"{base_url}/inspection-upload/{token}"
        
        return jsonify({
            'success': True,
            'upload_url': upload_url,
            'token': token,
            'expires_at': expires_at.strftime('%Y-%m-%d'),
            'vehicle': {
                'id': vehicle.id,
                'plate_number': vehicle.plate_number,
                'make': vehicle.make,
                'model': vehicle.model,
                'year': vehicle.year
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'فشل توليد الرابط: {str(e)}'
        }), 500


@api_bp.route('/inspection-status/<token>')
def get_inspection_status(token):
    """التحقق من حالة الفحص - للفلاتر"""
    try:
        upload_token = InspectionUploadToken.query.filter_by(token=token).first()
        
        if not upload_token:
            return jsonify({'success': False, 'message': 'رابط غير صحيح'}), 404
        
        inspection = VehicleInspectionRecord.query.filter_by(
            token_id=upload_token.id
        ).order_by(VehicleInspectionRecord.uploaded_at.desc()).first()
        
        if not inspection:
            return jsonify({'success': False, 'message': 'لم يتم رفع صور بعد'}), 404
        
        status_translations = {
            'pending': 'في الانتظار',
            'approved': 'تم الموافقة',
            'rejected': 'مرفوض',
            'needs_review': 'يحتاج مراجعة'
        }
        
        return jsonify({
            'success': True,
            'inspection': {
                'id': inspection.id,
                'vehicle_plate': inspection.vehicle.plate_number,
                'inspection_date': inspection.inspection_date.strftime('%Y-%m-%d'),
                'uploaded_at': inspection.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
                'images_count': inspection.images.count(),
                'status': inspection.review_status,
                'status_arabic': status_translations.get(inspection.review_status, 'غير محدد'),
                'approved_at': inspection.reviewed_at.strftime('%Y-%m-%d %H:%M:%S') if inspection.reviewed_at and inspection.review_status == 'approved' else None,
                'approved_by': inspection.reviewer.username if inspection.reviewer and inspection.review_status == 'approved' else None,
                'rejected_at': inspection.reviewed_at.strftime('%Y-%m-%d %H:%M:%S') if inspection.reviewed_at and inspection.review_status == 'rejected' else None,
                'rejection_reason': inspection.reviewer_notes if inspection.review_status == 'rejected' else None,
                'reviewer_notes': inspection.reviewer_notes if inspection.review_status not in ['rejected'] else None
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'}), 500
