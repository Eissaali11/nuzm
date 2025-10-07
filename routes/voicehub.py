from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from models import VoiceHubCall, VoiceHubAnalysis, Employee, Department
import json
import os
from datetime import datetime
import requests
import logging

voicehub_bp = Blueprint('voicehub', __name__)
logger = logging.getLogger(__name__)

# سر Webhook للتحقق من الطلبات
WEBHOOK_SECRET = os.environ.get('VOICEHUB_WEBHOOK_SECRET', 'default_secret')
VOICEHUB_API_KEY = os.environ.get('VOICEHUB_API_KEY')


@voicehub_bp.route('/webhook', methods=['POST'])
def webhook():
    """استقبال إشعارات Webhook من VoiceHub"""
    try:
        # التحقق من السر
        webhook_secret = request.headers.get('x-webhook-secret')
        if webhook_secret != WEBHOOK_SECRET:
            logger.warning(f"Invalid webhook secret received: {webhook_secret}")
            return jsonify({'error': 'Invalid secret'}), 401
        
        # استخراج البيانات
        data = request.json
        event_type = data.get('eventType')
        call_id = data.get('callId')
        
        logger.info(f"Received webhook event: {event_type} for call: {call_id}")
        
        # معالجة حسب نوع الحدث
        if event_type == 'CallStatusChanged':
            handle_call_status_changed(data)
        elif event_type == 'RecordingsAvailable':
            handle_recordings_available(data)
        elif event_type == 'AnalysisResultReady':
            handle_analysis_result_ready(data)
        else:
            logger.warning(f"Unknown event type: {event_type}")
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500


def handle_call_status_changed(data):
    """معالجة تغيير حالة المكالمة"""
    call_id = data.get('callId')
    status = data.get('status')
    timestamp = data.get('timestamp')
    
    # البحث عن المكالمة أو إنشاء واحدة جديدة
    call = VoiceHubCall.query.filter_by(call_id=call_id).first()
    
    if not call:
        call = VoiceHubCall(
            call_id=call_id,
            status=status,
            event_data=json.dumps(data)
        )
        db.session.add(call)
    else:
        call.status = status
        call.updated_at = datetime.utcnow()
        
        # تحديث البيانات الإضافية
        existing_data = json.loads(call.event_data or '{}')
        existing_data.update(data)
        call.event_data = json.dumps(existing_data)
    
    # تحديث توقيت المكالمة
    if status == 'started' and not call.call_started_at:
        call.call_started_at = datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if timestamp else datetime.utcnow()
    elif status in ['completed', 'failed', 'cancelled'] and not call.call_ended_at:
        call.call_ended_at = datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if timestamp else datetime.utcnow()
    
    db.session.commit()
    logger.info(f"Updated call {call_id} status to {status}")


def handle_recordings_available(data):
    """معالجة توفر التسجيلات"""
    call_id = data.get('callId')
    
    call = VoiceHubCall.query.filter_by(call_id=call_id).first()
    
    if call:
        call.has_recordings = True
        call.updated_at = datetime.utcnow()
        db.session.commit()
        logger.info(f"Marked recordings available for call {call_id}")
    else:
        logger.warning(f"Call {call_id} not found for recordings update")


def handle_analysis_result_ready(data):
    """معالجة جاهزية نتائج التحليل"""
    call_id = data.get('callId')
    analysis_id = data.get('analysisId')
    analysis_url = data.get('analysisResultUrl')
    
    call = VoiceHubCall.query.filter_by(call_id=call_id).first()
    
    if not call:
        logger.warning(f"Call {call_id} not found for analysis update")
        return
    
    # تحديث معلومات التحليل في المكالمة
    call.has_analysis = True
    call.analysis_id = analysis_id
    
    # جلب نتائج التحليل من API
    if analysis_url and VOICEHUB_API_KEY:
        try:
            headers = {'x-dq-api-key': VOICEHUB_API_KEY}
            response = requests.get(analysis_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                analysis_data = response.json()
                
                # إنشاء أو تحديث سجل التحليل
                analysis = VoiceHubAnalysis.query.filter_by(analysis_id=analysis_id).first()
                
                if not analysis:
                    analysis = VoiceHubAnalysis(
                        call_id=call.id,
                        analysis_id=analysis_id
                    )
                    db.session.add(analysis)
                
                # تخزين البيانات
                analysis.summary = analysis_data.get('summary')
                analysis.main_topics = json.dumps(analysis_data.get('mainTopics', []))
                
                # التحليل العاطفي
                sentiment = analysis_data.get('sentiment', {})
                analysis.sentiment_score = sentiment.get('score')
                analysis.sentiment_label = sentiment.get('label')
                analysis.positive_keywords = json.dumps(sentiment.get('positiveKeywords', []))
                analysis.negative_keywords = json.dumps(sentiment.get('negativeKeywords', []))
                
                # المقاييس
                analysis.empathy_score = analysis_data.get('empathyScore')
                analysis.resolution_status = analysis_data.get('resolutionStatus')
                analysis.user_interruptions_count = analysis_data.get('userInterruptionsCount')
                
                # ملخص المستخدم
                user_summary = analysis_data.get('userSummary', {})
                analysis.user_speech_duration = user_summary.get('totalSpeechDuration')
                analysis.user_silence_duration = user_summary.get('totalSilenceDuration')
                analysis.user_wps = user_summary.get('wps')
                
                # ملخص المساعد
                assistant_summary = analysis_data.get('assistantSummary', {})
                analysis.assistant_speech_duration = assistant_summary.get('totalSpeechDuration')
                analysis.assistant_silence_duration = assistant_summary.get('totalSilenceDuration')
                analysis.assistant_wps = assistant_summary.get('wps')
                
                # البيانات الكاملة
                analysis.full_analysis = json.dumps(analysis_data)
                
                # النص الكامل
                transcript_analysis = analysis_data.get('transcriptAnalysis', [])
                transcript_text = '\n'.join([item.get('text', '') for item in transcript_analysis])
                analysis.transcript = transcript_text
                
                # مؤشرات الولاء
                analysis.loyalty_indicators = json.dumps(analysis_data.get('loyaltyIndicators', []))
                
                # روابط التسجيلات
                recording_urls = analysis_data.get('recordingUrls', [])
                if recording_urls:
                    call.recording_urls = json.dumps(recording_urls)
                
                # المدة
                duration = analysis_data.get('duration')
                if duration:
                    call.duration = duration
                
                db.session.commit()
                logger.info(f"Saved analysis for call {call_id}")
            else:
                logger.error(f"Failed to fetch analysis: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching analysis: {str(e)}")
    
    db.session.commit()


@voicehub_bp.route('/calls')
@login_required
def calls_list():
    """عرض قائمة المكالمات"""
    # فلترة حسب القسم المخصص للمستخدم
    if current_user.assigned_department_id:
        calls = VoiceHubCall.query.filter_by(department_id=current_user.assigned_department_id).order_by(VoiceHubCall.created_at.desc()).all()
    else:
        calls = VoiceHubCall.query.order_by(VoiceHubCall.created_at.desc()).all()
    
    return render_template('voicehub/calls_list.html', calls=calls)


@voicehub_bp.route('/calls/<int:call_id>')
@login_required
def call_detail(call_id):
    """عرض تفاصيل المكالمة"""
    call = VoiceHubCall.query.get_or_404(call_id)
    
    # التحقق من الصلاحيات
    if current_user.assigned_department_id and call.department_id != current_user.assigned_department_id:
        flash('ليس لديك صلاحية لعرض هذه المكالمة', 'error')
        return redirect(url_for('voicehub.calls_list'))
    
    return render_template('voicehub/call_detail.html', call=call)


@voicehub_bp.route('/calls/<int:call_id>/assign', methods=['POST'])
@login_required
def assign_call(call_id):
    """ربط المكالمة بموظف أو قسم"""
    call = VoiceHubCall.query.get_or_404(call_id)
    
    employee_id = request.form.get('employee_id')
    department_id = request.form.get('department_id')
    notes = request.form.get('notes')
    
    if employee_id:
        call.employee_id = int(employee_id)
    if department_id:
        call.department_id = int(department_id)
    if notes:
        call.notes = notes
    
    call.assigned_by = current_user.id
    call.updated_at = datetime.utcnow()
    
    db.session.commit()
    flash('تم ربط المكالمة بنجاح', 'success')
    
    return redirect(url_for('voicehub.call_detail', call_id=call_id))


@voicehub_bp.route('/dashboard')
@login_required
def dashboard():
    """لوحة تحكم VoiceHub"""
    # إحصائيات عامة
    if current_user.assigned_department_id:
        total_calls = VoiceHubCall.query.filter_by(department_id=current_user.assigned_department_id).count()
        completed_calls = VoiceHubCall.query.filter_by(department_id=current_user.assigned_department_id, status='completed').count()
        calls_with_analysis = VoiceHubCall.query.filter_by(department_id=current_user.assigned_department_id, has_analysis=True).count()
    else:
        total_calls = VoiceHubCall.query.count()
        completed_calls = VoiceHubCall.query.filter_by(status='completed').count()
        calls_with_analysis = VoiceHubCall.query.filter_by(has_analysis=True).count()
    
    # آخر المكالمات
    if current_user.assigned_department_id:
        recent_calls = VoiceHubCall.query.filter_by(department_id=current_user.assigned_department_id).order_by(VoiceHubCall.created_at.desc()).limit(10).all()
    else:
        recent_calls = VoiceHubCall.query.order_by(VoiceHubCall.created_at.desc()).limit(10).all()
    
    return render_template('voicehub/dashboard.html',
                         total_calls=total_calls,
                         completed_calls=completed_calls,
                         calls_with_analysis=calls_with_analysis,
                         recent_calls=recent_calls,
                         api_key=VOICEHUB_API_KEY)


# ==========================================
# VoiceHub Knowledge API
# API للسماح لـ VoiceHub بالوصول لبيانات النظام
# ==========================================

def verify_knowledge_api_key():
    """التحقق من مفتاح API للوصول إلى Knowledge API"""
    api_key = request.headers.get('X-VoiceHub-API-Key')
    if not api_key or api_key != VOICEHUB_API_KEY:
        return False
    return True


@voicehub_bp.route('/api/knowledge/employee/<search_term>')
def knowledge_employee(search_term):
    """البحث عن موظف بالاسم أو رقم الهوية"""
    if not verify_knowledge_api_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    from models import Employee
    
    # البحث بالاسم أو رقم الهوية
    employees = Employee.query.filter(
        db.or_(
            Employee.name.ilike(f'%{search_term}%'),
            Employee.national_id.ilike(f'%{search_term}%')
        )
    ).limit(10).all()
    
    results = []
    for emp in employees:
        results.append({
            'id': emp.id,
            'name': emp.name,
            'national_id': emp.national_id,
            'mobile': emp.mobile if hasattr(emp, 'mobile') else None,
            'email': emp.email if emp.email else None,
            'job_title': emp.job_title if emp.job_title else None,
            'department': emp.department.name if emp.department else None,
            'basic_salary': float(emp.basic_salary) if emp.basic_salary else None
        })
    
    return jsonify({
        'success': True,
        'count': len(results),
        'employees': results
    })


@voicehub_bp.route('/api/knowledge/vehicle/<search_term>')
def knowledge_vehicle(search_term):
    """البحث عن مركبة برقم اللوحة أو رقم الهيكل"""
    if not verify_knowledge_api_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    from models import Vehicle
    
    # البحث برقم اللوحة أو الماركة
    vehicles = Vehicle.query.filter(
        db.or_(
            Vehicle.plate_number.ilike(f'%{search_term}%'),
            Vehicle.make.ilike(f'%{search_term}%'),
            Vehicle.model.ilike(f'%{search_term}%')
        )
    ).limit(10).all()
    
    results = []
    for veh in vehicles:
        results.append({
            'id': veh.id,
            'plate_number': veh.plate_number,
            'make': veh.make if hasattr(veh, 'make') else None,
            'model': veh.model if hasattr(veh, 'model') else None,
            'year': veh.year if hasattr(veh, 'year') else None,
            'color': veh.color if hasattr(veh, 'color') else None,
            'type': veh.type_of_car if hasattr(veh, 'type_of_car') else None,
            'driver': veh.driver_name if hasattr(veh, 'driver_name') else None,
            'status': veh.status if hasattr(veh, 'status') else None
        })
    
    return jsonify({
        'success': True,
        'count': len(results),
        'vehicles': results
    })


@voicehub_bp.route('/api/knowledge/department/<search_term>')
def knowledge_department(search_term):
    """البحث عن قسم"""
    if not verify_knowledge_api_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    # البحث بالاسم
    departments = Department.query.filter(
        Department.name.ilike(f'%{search_term}%')
    ).limit(10).all()
    
    results = []
    for dept in departments:
        # حساب عدد الموظفين في القسم
        employee_count = len(dept.employees) if dept.employees else 0
        
        results.append({
            'id': dept.id,
            'name': dept.name,
            'employee_count': employee_count
        })
    
    return jsonify({
        'success': True,
        'count': len(results),
        'departments': results
    })


@voicehub_bp.route('/api/knowledge/stats')
def knowledge_stats():
    """إحصائيات عامة عن النظام"""
    if not verify_knowledge_api_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    from models import Employee, Vehicle
    
    stats = {
        'total_employees': Employee.query.count(),
        'total_vehicles': Vehicle.query.count(),
        'total_departments': Department.query.count(),
        'departments': []
    }
    
    # إحصائيات الأقسام
    departments = Department.query.all()
    for dept in departments:
        stats['departments'].append({
            'name': dept.name,
            'employee_count': len(dept.employees) if dept.employees else 0
        })
    
    return jsonify({
        'success': True,
        'stats': stats
    })


@voicehub_bp.route('/api/employee-inquiry', methods=['POST', 'GET'])
def employee_inquiry():
    """
    API استفسارات الموظفين - للاستخدام مع VoiceHub
    
    يستقبل:
    - employee_name: اسم الموظف
    - employee_id: رقم الموظف أو الهوية الوطنية
    - service_type: نوع الخدمة (إجازات، راتب، قسم، تواصل)
    
    يرجع معلومات الموظف حسب نوع الخدمة المطلوبة
    """
    if not verify_knowledge_api_key():
        return jsonify({'error': 'Unauthorized', 'message': 'مفتاح API غير صحيح'}), 401
    
    try:
        # Log request details for debugging
        logger.info(f"Request method: {request.method}")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Request data: {request.data}")
        logger.info(f"Request form: {request.form}")
        logger.info(f"Request is_json: {request.is_json}")
        
        # محاولة قراءة البيانات من مصادر متعددة بالترتيب الصحيح
        data = {}
        
        # 1. أولوية للـ JSON body إذا كان موجود وليس فارغ
        if request.is_json:
            try:
                json_data = request.get_json(silent=True, force=True)
                if json_data and any(json_data.values()):  # تحقق من أن JSON ليس فارغ
                    data = json_data
                    logger.info(f"Data from JSON: {data}")
            except:
                pass
        
        # 2. إذا لم يوجد JSON، حاول query parameters
        if not data and request.args:
            data = request.args.to_dict()
            logger.info(f"Data from query params: {data}")
        
        # 3. إذا لم يوجد، حاول form data
        if not data and request.form:
            data = request.form.to_dict()
            logger.info(f"Data from form: {data}")
        
        # 4. آخر محاولة من request.values
        if not data:
            data = request.values.to_dict()
            logger.info(f"Data from request.values: {data}")
        
        employee_name = data.get('employee_name', '').strip() if data else ''
        employee_id = data.get('employee_id', '').strip() if data else ''
        service_type = data.get('service_type', '').strip() if data else ''
        
        logger.info(f"Employee inquiry: name={employee_name}, id={employee_id}, service={service_type}")
        
        # البحث عن الموظف
        employee = None
        
        if employee_id:
            # البحث برقم الهوية أو رقم الموظف
            employee = Employee.query.filter(
                db.or_(
                    Employee.national_id == employee_id,
                    Employee.employee_id == employee_id
                )
            ).first()
        
        if not employee and employee_name:
            # البحث بالاسم
            employee = Employee.query.filter(
                Employee.name.ilike(f'%{employee_name}%')
            ).first()
        
        if not employee:
            return jsonify({
                'success': False,
                'message': f'عذراً، لم أجد موظف باسم {employee_name or employee_id} في النظام',
                'arabic_response': f'عذراً، لم أجد موظف باسم {employee_name or employee_id} في قاعدة البيانات. يرجى التأكد من الاسم أو رقم الهوية.'
            }), 404
        
        # بناء الاستجابة حسب نوع الخدمة
        response_data = {
            'success': True,
            'employee': {
                'name': employee.name,
                'employee_id': employee.employee_id,
                'national_id': employee.national_id
            }
        }
        
        # استفسار عن الإجازات
        if 'إجاز' in service_type or 'vacation' in service_type.lower() or 'leave' in service_type.lower():
            total_leave_days = employee.total_leave_days if hasattr(employee, 'total_leave_days') and employee.total_leave_days else 30
            used_leave_days = employee.used_leave_days if hasattr(employee, 'used_leave_days') and employee.used_leave_days else 0
            remaining_leave = total_leave_days - used_leave_days
            
            response_data['leave_info'] = {
                'total_leave_days': total_leave_days,
                'used_leave_days': used_leave_days,
                'remaining_leave_days': remaining_leave
            }
            
            response_data['arabic_response'] = (
                f'الموظف {employee.name}، '
                f'رصيد إجازاتك الحالي هو {remaining_leave} يوم من أصل {total_leave_days} يوم. '
                f'لقد استخدمت {used_leave_days} يوم حتى الآن.'
            )
        
        # استفسار عن الراتب
        elif 'راتب' in service_type or 'salary' in service_type.lower():
            basic_salary = float(employee.basic_salary) if employee.basic_salary else 0
            
            response_data['salary_info'] = {
                'basic_salary': basic_salary,
                'currency': 'ريال سعودي'
            }
            
            if basic_salary > 0:
                response_data['arabic_response'] = (
                    f'الموظف {employee.name}، '
                    f'راتبك الأساسي المسجل في النظام هو {basic_salary:,.0f} ريال سعودي. '
                    f'للاستفسار عن البدلات أو الخصومات، يرجى التواصل مع قسم الموارد البشرية.'
                )
            else:
                response_data['arabic_response'] = (
                    f'الموظف {employee.name}، '
                    f'معلومات الراتب غير متوفرة في النظام حالياً. '
                    f'يرجى التواصل مع قسم الموارد البشرية للحصول على التفاصيل.'
                )
        
        # استفسار عن القسم
        elif 'قسم' in service_type or 'department' in service_type.lower():
            departments_list = []
            if hasattr(employee, 'departments') and employee.departments:
                for dept in employee.departments:
                    departments_list.append(dept.name)
                dept_names = '، '.join(departments_list)
            else:
                dept_names = 'غير محدد'
            
            job_title = employee.job_title if employee.job_title else 'غير محدد'
            
            response_data['department_info'] = {
                'departments': departments_list if departments_list else ['غير محدد'],
                'job_title': job_title
            }
            
            response_data['arabic_response'] = (
                f'الموظف {employee.name}، '
                f'أنت تعمل في {"قسم " + dept_names if departments_list else "لا يوجد قسم محدد"}، '
                f'ومسماك الوظيفي هو {job_title}.'
            )
        
        # استفسار عن بيانات التواصل
        elif 'تواصل' in service_type or 'contact' in service_type.lower():
            mobile = employee.mobile if employee.mobile else 'غير مسجل'
            email = employee.email if employee.email else 'غير مسجل'
            
            response_data['contact_info'] = {
                'mobile': mobile,
                'email': email
            }
            
            response_data['arabic_response'] = (
                f'الموظف {employee.name}، '
                f'رقم الجوال المسجل: {mobile}، '
                f'البريد الإلكتروني: {email}. '
                f'إذا كنت ترغب بتحديث بياناتك، يرجى التواصل مع قسم الموارد البشرية.'
            )
        
        # نوع خدمة غير معروف
        else:
            response_data['arabic_response'] = (
                f'الموظف {employee.name}، '
                f'يمكنني مساعدتك في الاستفسار عن: رصيد الإجازات، حالة الراتب، بيانات القسم، أو بيانات التواصل. '
                f'أي نوع من المعلومات تحتاج؟'
            )
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error in employee inquiry: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'arabic_response': 'عذراً، حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى.'
        }), 500
