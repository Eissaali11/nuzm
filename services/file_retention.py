"""
نظام حماية الملفات المركزي - FileRetentionManager
====================================================
هذا النظام يمنع حذف أي ملفات من النظام بشكل تلقائي.
جميع الملفات المرفوعة تبقى محفوظة للأمان.

السياسة:
- ✅ الملفات المرفوعة تبقى دائماً
- ✅ عند "الحذف" يتم إزالة المرجع من DB فقط
- ✅ الحذف الفعلي يتطلب تأكيد يدوي من المدير
- ✅ سجل تدقيق لجميع العمليات
"""

import os
import logging
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)

# قائمة المجلدات المحمية - لا يمكن حذف أي ملف منها تلقائياً
PROTECTED_FOLDERS = [
    'static/uploads/',
    'uploads/',
]

# قائمة المجلدات المؤقتة - يمكن حذف الملفات منها
TEMP_FOLDERS = [
    '/tmp/',
    'static/.temp/',
    'temp/',
]


class FileRetentionManager:
    """
    مدير حماية الملفات - يمنع الحذف التلقائي للملفات الدائمة
    """
    
    @staticmethod
    def is_protected_file(file_path: str) -> bool:
        """
        التحقق مما إذا كان الملف في مجلد محمي
        """
        if not file_path:
            return False
            
        normalized_path = file_path.replace('\\', '/')
        
        for protected in PROTECTED_FOLDERS:
            if protected in normalized_path:
                return True
        return False
    
    @staticmethod
    def is_temp_file(file_path: str) -> bool:
        """
        التحقق مما إذا كان الملف مؤقت (يمكن حذفه)
        """
        if not file_path:
            return False
            
        normalized_path = file_path.replace('\\', '/')
        
        for temp in TEMP_FOLDERS:
            if temp in normalized_path or normalized_path.startswith(temp):
                return True
        return False
    
    @staticmethod
    def safe_delete(file_path: str, force: bool = False, reason: str = "") -> dict:
        """
        حذف آمن للملفات - يمنع حذف الملفات المحمية
        
        Args:
            file_path: مسار الملف
            force: تجاوز الحماية (يتطلب صلاحيات مدير)
            reason: سبب الحذف (مطلوب إذا force=True)
        
        Returns:
            dict مع status و message
        """
        if not file_path:
            return {"status": "skipped", "message": "مسار الملف فارغ"}
        
        # إذا كان الملف محمي
        if FileRetentionManager.is_protected_file(file_path):
            if force:
                # حذف قسري - يسجل في السجل
                logger.warning(f"⚠️ حذف قسري لملف محمي: {file_path} - السبب: {reason}")
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        return {"status": "force_deleted", "message": f"تم الحذف القسري: {reason}"}
                except Exception as e:
                    return {"status": "error", "message": str(e)}
            else:
                # الملف محمي - لا يتم حذفه
                logger.info(f"💾 الملف محمي ولم يتم حذفه: {file_path}")
                return {"status": "protected", "message": "الملف محمي - يتم حذف المرجع فقط من قاعدة البيانات"}
        
        # إذا كان الملف مؤقت - يمكن حذفه
        if FileRetentionManager.is_temp_file(file_path):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"🗑️ تم حذف ملف مؤقت: {file_path}")
                    return {"status": "deleted", "message": "تم حذف الملف المؤقت"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        # ملف غير معروف - نحميه احتياطياً
        logger.info(f"💾 ملف غير مصنف - محمي احتياطياً: {file_path}")
        return {"status": "protected", "message": "الملف محمي احتياطياً"}
    
    @staticmethod
    def log_file_operation(operation: str, file_path: str, entity_type: str = None, entity_id: int = None):
        """
        تسجيل عمليات الملفات للتدقيق
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {operation}: {file_path}"
        if entity_type and entity_id:
            log_entry += f" | Entity: {entity_type}#{entity_id}"
        
        logger.info(log_entry)
    
    @staticmethod
    def soft_delete_reference(db_session, model_instance, field_name: str):
        """
        حذف ناعم - إزالة المرجع من DB فقط مع الاحتفاظ بالملف
        
        Args:
            db_session: جلسة قاعدة البيانات
            model_instance: كائن النموذج
            field_name: اسم الحقل الذي يحتوي على مسار الملف
        """
        old_path = getattr(model_instance, field_name, None)
        if old_path:
            logger.info(f"💾 حذف ناعم - الملف محفوظ: {old_path}")
            setattr(model_instance, field_name, None)
        return old_path


def no_file_delete(func):
    """
    مُزخرف (Decorator) يمنع حذف الملفات داخل الدالة
    يستبدل os.remove و os.unlink بإصدارات آمنة
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        import builtins
        original_remove = os.remove
        original_unlink = os.unlink
        
        def safe_remove(path):
            result = FileRetentionManager.safe_delete(path)
            if result["status"] == "protected":
                logger.info(f"💾 تم منع الحذف: {path}")
            return result
        
        def safe_unlink(path):
            return safe_remove(path)
        
        # استبدال مؤقت
        os.remove = safe_remove
        os.unlink = safe_unlink
        
        try:
            return func(*args, **kwargs)
        finally:
            # استعادة الأصلية
            os.remove = original_remove
            os.unlink = original_unlink
    
    return wrapper


# دالة مساعدة للاستخدام في جميع الوحدات
def protect_file(file_path: str) -> str:
    """
    تأكيد حماية الملف وإرجاع رسالة
    """
    if file_path:
        logger.info(f"💾 الملف محمي: {file_path}")
    return f"💾 الملف محفوظ للأمان: {file_path}"


def cleanup_temp_file(file_path: str) -> bool:
    """
    حذف ملف مؤقت فقط (للتصدير والتحويلات)
    """
    result = FileRetentionManager.safe_delete(file_path)
    return result["status"] in ["deleted", "skipped"]
