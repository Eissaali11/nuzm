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
                         recent_calls=recent_calls)
