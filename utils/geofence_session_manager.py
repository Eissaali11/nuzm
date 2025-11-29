"""
Geofence Session Manager - نظام ذكي لإدارة جلسات الموظفين
==========================================================
النظام يدمج الجلسات القريبة (نفس الساعة) تلقائياً ويتعامل مع الفترات الطويلة.

السياسة:
- إذا دخل وخرج ودخل وخرج في الساعة = دخول واحد
- إذا دخل صباحاً ولم يخرج، ثم عاد مساءً وخرج = جلستان (صباحي + مسائي)
"""
from models import GeofenceSession, GeofenceEvent, db
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# الإعدادات
MAX_GAP_BETWEEN_SESSIONS = 60  # 60 دقيقة - الفاصل الزمني المقبول لدمج الجلسات
MINIMUM_BREAK_FOR_NEW_SESSION = 120  # 120 دقيقة - فاصل زمني لاعتبار جلسة جديدة


class SessionManager:
    """مدير الجلسات الذكي - يدمج الجلسات القريبة ويتعامل مع الفترات الطويلة"""
    
    @staticmethod
    def find_mergeable_session(employee_id, geofence_id, current_time):
        """
        البحث عن جلسة مغلقة حديثة يمكن دمجها مع الجلسة الحالية
        الشروط:
        - جلسة مغلقة (لا نشطة)
        - من نفس الموظف والدائرة
        - خروج الجلسة السابقة قريب من الدخول الحالي (أقل من MAX_GAP_BETWEEN_SESSIONS)
        """
        last_closed_session = GeofenceSession.query.filter(
            GeofenceSession.employee_id == employee_id,
            GeofenceSession.geofence_id == geofence_id,
            GeofenceSession.is_active == False  # مغلقة
        ).order_by(GeofenceSession.exit_time.desc()).first()
        
        if not last_closed_session or not last_closed_session.exit_time:
            return None
        
        # حساب الفاصل الزمني بين الخروج السابق والدخول الحالي
        gap = (current_time - last_closed_session.exit_time).total_seconds() / 60
        
        if gap <= MAX_GAP_BETWEEN_SESSIONS:
            logger.info(
                f"🔀 دمج جلسات: الفاصل الزمني {gap:.1f} دقيقة "
                f"(أقل من {MAX_GAP_BETWEEN_SESSIONS} دقيقة)"
            )
            return last_closed_session
        else:
            logger.info(
                f"🆕 جلسة جديدة: الفاصل الزمني {gap:.1f} دقيقة "
                f"(أكثر من {MAX_GAP_BETWEEN_SESSIONS} دقيقة)"
            )
            return None
    
    @staticmethod
    def process_enter_event(employee_id, geofence_id, event):
        """
        معالجة حدث دخول - إنشاء أو دمج جلسة
        
        منطق ذكي:
        1. البحث عن جلسة مفتوحة نشطة
           - إذا وجدت: تحديث وقت الدخول (في حالة دخولات متتالية)
        2. البحث عن جلسة مغلقة حديثة (آخر دقيقة)
           - إذا وجدت: إعادة فتحها (دمج الجلسات)
        3. إذا لم توجد: إنشاء جلسة جديدة تماماً
        """
        try:
            # 1️⃣ التحقق من جلسة مفتوحة نشطة بالفعل
            existing_active_session = GeofenceSession.query.filter_by(
                employee_id=employee_id,
                geofence_id=geofence_id,
                is_active=True
            ).first()
            
            if existing_active_session:
                logger.warning(
                    f"⚠️ جلسة نشطة موجودة بالفعل للموظف {employee_id}. "
                    f"سيتم تحديث وقت الدخول من {existing_active_session.entry_time} "
                    f"إلى {event.recorded_at}"
                )
                existing_active_session.entry_time = event.recorded_at
                existing_active_session.entry_event_id = event.id
                existing_active_session.updated_at = datetime.utcnow()
                return existing_active_session
            
            # 2️⃣ البحث عن جلسة مغلقة حديثة لدمجها
            mergeable_session = SessionManager.find_mergeable_session(
                employee_id, geofence_id, event.recorded_at
            )
            
            if mergeable_session:
                # إعادة فتح الجلسة السابقة (دمج)
                logger.info(
                    f"🔄 إعادة فتح جلسة مدمجة: الموظف {employee_id}، "
                    f"الدخول السابق: {mergeable_session.entry_time}، "
                    f"الخروج السابق: {mergeable_session.exit_time}، "
                    f"الدخول الجديد: {event.recorded_at}"
                )
                mergeable_session.is_active = True
                mergeable_session.exit_time = None  # محو وقت الخروج السابق
                mergeable_session.duration_minutes = None
                mergeable_session.exit_event_id = None
                mergeable_session.entry_event_id = event.id  # تحديث حدث الدخول
                mergeable_session.updated_at = datetime.utcnow()
                
                logger.info(
                    f"✅ جلسة مدمجة: الموظف {employee_id} - "
                    f"بقيت من {mergeable_session.entry_time}"
                )
                return mergeable_session
            
            # 3️⃣ إنشاء جلسة جديدة تماماً
            session = GeofenceSession(
                geofence_id=geofence_id,
                employee_id=employee_id,
                entry_event_id=event.id,
                entry_time=event.recorded_at,
                is_active=True
            )
            db.session.add(session)
            
            logger.info(
                f"✅ جلسة جديدة: الموظف {employee_id} في الدائرة {geofence_id} "
                f"بدأت في {event.recorded_at}"
            )
            
            return session
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة حدث الدخول: {str(e)}")
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
                    f"⚠️ خروج بدون دخول للموظف {employee_id} في الدائرة {geofence_id}. "
                    f"سيتم إنشاء جلسة اصطناعية."
                )
                
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
                
                logger.info(f"📝 جلسة اصطناعية: الموظف {employee_id}")
                return session
            
            # إغلاق الجلسة المفتوحة
            open_session.exit_event_id = event.id
            open_session.exit_time = event.recorded_at
            open_session.is_active = False
            duration = open_session.calculate_duration()
            open_session.updated_at = datetime.utcnow()
            
            logger.info(
                f"✅ جلسة مغلقة: الموظف {employee_id} في الدائرة {geofence_id}. "
                f"الدخول: {open_session.entry_time.strftime('%H:%M')} | "
                f"الخروج: {event.recorded_at.strftime('%H:%M')} | "
                f"المدة: {duration} دقيقة"
            )
            
            return open_session
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة حدث الخروج: {str(e)}")
            raise
    
    @staticmethod
    def get_active_sessions(geofence_id=None, employee_id=None):
        """
        جلب الجلسات النشطة (الموظفون داخل الدائرة الآن)
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
        """
        query = GeofenceSession.query.filter_by(
            employee_id=employee_id,
            geofence_id=geofence_id,
            is_active=False
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
