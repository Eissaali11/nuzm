"""
Geofence Session Manager
إدارة جلسات دخول/خروج الموظفين من الدوائر الجغرافية
"""
from models import GeofenceSession, GeofenceEvent, db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """مدير الجلسات - يربط أحداث الدخول والخروج في جلسات كاملة"""
    
    @staticmethod
    def process_enter_event(employee_id, geofence_id, event):
        """
        معالجة حدث دخول - إنشاء جلسة جديدة
        
        Args:
            employee_id: معرف الموظف
            geofence_id: معرف الدائرة الجغرافية
            event: كائن GeofenceEvent
        """
        try:
            # التحقق من وجود جلسة مفتوحة بالفعل
            existing_session = GeofenceSession.query.filter_by(
                employee_id=employee_id,
                geofence_id=geofence_id,
                is_active=True
            ).first()
            
            if existing_session:
                # موجود جلسة مفتوحة - تحديث بيانات الدخول
                logger.warning(
                    f"⚠️ جلسة مفتوحة موجودة بالفعل للموظف {employee_id} في الدائرة {geofence_id}. "
                    "سيتم تحديث وقت الدخول."
                )
                existing_session.entry_time = event.recorded_at
                existing_session.entry_event_id = event.id
                existing_session.updated_at = datetime.utcnow()
                return existing_session
            
            # إنشاء جلسة جديدة
            session = GeofenceSession(
                geofence_id=geofence_id,
                employee_id=employee_id,
                entry_event_id=event.id,
                entry_time=event.recorded_at,
                is_active=True
            )
            db.session.add(session)
            
            logger.info(
                f"✅ جلسة جديدة للموظف {employee_id} في الدائرة {geofence_id} "
                f"بدأت في {event.recorded_at}"
            )
            
            return session
            
        except Exception as e:
            logger.error(f"خطأ في معالجة حدث الدخول: {str(e)}")
            raise
    
    @staticmethod
    def process_exit_event(employee_id, geofence_id, event):
        """
        معالجة حدث خروج - إغلاق الجلسة المفتوحة
        
        Args:
            employee_id: معرف الموظف
            geofence_id: معرف الدائرة الجغرافية
            event: كائن GeofenceEvent
        """
        try:
            # البحث عن آخر جلسة مفتوحة
            open_session = GeofenceSession.query.filter_by(
                employee_id=employee_id,
                geofence_id=geofence_id,
                is_active=True
            ).order_by(GeofenceSession.entry_time.desc()).first()
            
            if not open_session:
                # خروج بدون دخول - إنشاء جلسة اصطناعية
                logger.warning(
                    f"⚠️ حدث خروج بدون دخول للموظف {employee_id} في الدائرة {geofence_id}. "
                    "سيتم إنشاء جلسة اصطناعية."
                )
                
                # إنشاء جلسة بوقت دخول افتراضي (قبل ساعة من الخروج)
                from datetime import timedelta
                synthetic_entry_time = event.recorded_at - timedelta(hours=1)
                
                session = GeofenceSession(
                    geofence_id=geofence_id,
                    employee_id=employee_id,
                    exit_event_id=event.id,
                    entry_time=synthetic_entry_time,
                    exit_time=event.recorded_at,
                    is_active=False
                )
                session.calculate_duration()
                db.session.add(session)
                
                logger.info(f"📝 جلسة اصطناعية تم إنشاؤها للموظف {employee_id}")
                return session
            
            # إغلاق الجلسة المفتوحة
            open_session.exit_event_id = event.id
            open_session.exit_time = event.recorded_at
            open_session.is_active = False
            open_session.calculate_duration()
            open_session.updated_at = datetime.utcnow()
            
            logger.info(
                f"✅ جلسة مغلقة للموظف {employee_id} في الدائرة {geofence_id}. "
                f"المدة: {open_session.duration_minutes} دقيقة"
            )
            
            return open_session
            
        except Exception as e:
            logger.error(f"خطأ في معالجة حدث الخروج: {str(e)}")
            raise
    
    @staticmethod
    def get_active_sessions(geofence_id=None, employee_id=None):
        """
        جلب الجلسات النشطة (الموظفون داخل الدائرة الآن)
        
        Args:
            geofence_id: معرف الدائرة (اختياري)
            employee_id: معرف الموظف (اختياري)
        
        Returns:
            قائمة الجلسات النشطة
        """
        query = GeofenceSession.query.filter_by(is_active=True)
        
        if geofence_id:
            query = query.filter_by(geofence_id=geofence_id)
        
        if employee_id:
            query = query.filter_by(employee_id=employee_id)
        
        return query.all()
    
    @staticmethod
    def get_employee_total_time(employee_id, geofence_id, start_date=None, end_date=None):
        """
        حساب إجمالي الوقت الذي قضاه الموظف في الدائرة
        
        Args:
            employee_id: معرف الموظف
            geofence_id: معرف الدائرة
            start_date: تاريخ البداية (اختياري)
            end_date: تاريخ النهاية (اختياري)
        
        Returns:
            إجمالي الوقت بالدقائق
        """
        query = GeofenceSession.query.filter_by(
            employee_id=employee_id,
            geofence_id=geofence_id,
            is_active=False  # جلسات مغلقة فقط
        )
        
        if start_date:
            query = query.filter(GeofenceSession.entry_time >= start_date)
        
        if end_date:
            query = query.filter(GeofenceSession.entry_time <= end_date)
        
        sessions = query.all()
        total_minutes = sum(s.duration_minutes or 0 for s in sessions)
        
        return total_minutes
    
    @staticmethod
    def get_employee_visit_count(employee_id, geofence_id, start_date=None, end_date=None):
        """
        حساب عدد زيارات الموظف للدائرة
        
        Args:
            employee_id: معرف الموظف
            geofence_id: معرف الدائرة
            start_date: تاريخ البداية (اختياري)
            end_date: تاريخ النهاية (اختياري)
        
        Returns:
            عدد الزيارات
        """
        query = GeofenceSession.query.filter_by(
            employee_id=employee_id,
            geofence_id=geofence_id
        )
        
        if start_date:
            query = query.filter(GeofenceSession.entry_time >= start_date)
        
        if end_date:
            query = query.filter(GeofenceSession.entry_time <= end_date)
        
        return query.count()
