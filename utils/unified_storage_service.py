"""
خدمة التخزين الموحدة - رفع تلقائي إلى Google Drive + حفظ محلي
"""
import os
import logging
from typing import Optional, Dict
from utils.google_drive_service import drive_service
from utils.employee_requests_drive_uploader import EmployeeRequestsDriveUploader
from threading import Thread
from datetime import datetime

logger = logging.getLogger(__name__)

class UnifiedStorageService:
    """خدمة موحدة للتخزين المحلي والخارجي"""
    
    def __init__(self):
        self.drive_service = drive_service
        self.requests_uploader = EmployeeRequestsDriveUploader()
        self.employees_folder_id = None
        self.vehicles_folder_id = None
        
    def _get_or_create_employees_folder(self) -> Optional[str]:
        """الحصول على مجلد الموظفين في Shared Drive"""
        if self.employees_folder_id:
            return self.employees_folder_id
            
        if not self.drive_service.is_configured():
            return None
            
        try:
            # استخدام Shared Drive مباشرة (لأن Service Account لا تملك مساحة شخصية)
            shared_drive_id = self.drive_service.get_root_folder()
            if not shared_drive_id:
                return None
            
            self.employees_folder_id = self.drive_service._get_or_create_folder(
                "الموظفين",
                parent_id=shared_drive_id
            )
            return self.employees_folder_id
        except Exception as e:
            logger.error(f"خطأ في الحصول على مجلد الموظفين: {e}")
            return None
    
    def _get_or_create_vehicles_folder(self) -> Optional[str]:
        """الحصول على مجلد السيارات في Shared Drive"""
        if self.vehicles_folder_id:
            return self.vehicles_folder_id
            
        if not self.drive_service.is_configured():
            return None
            
        try:
            # استخدام Shared Drive مباشرة
            shared_drive_id = self.drive_service.get_root_folder()
            if not shared_drive_id:
                return None
            
            self.vehicles_folder_id = self.drive_service._get_or_create_folder(
                "السيارات",
                parent_id=shared_drive_id
            )
            return self.vehicles_folder_id
        except Exception as e:
            logger.error(f"خطأ في الحصول على مجلد السيارات: {e}")
            return None
    
    def upload_employee_file_async(
        self,
        local_path: str,
        employee_id: int,
        file_type: str = "general",
        sync: bool = False
    ) -> Optional[Dict]:
        """
        رفع ملف موظف إلى Google Drive (غير متزامن بشكل افتراضي)
        الملف محفوظ محلياً بالفعل - هذا محاولة إضافية للرفع الخارجي
        
        Args:
            local_path: المسار المحلي للملف
            employee_id: معرف الموظف
            file_type: نوع الملف (housing, passport, national_id, profile, job_offer, iban, etc)
            sync: إذا كانت True، انتظر الرفع (blocking)
        
        Returns:
            معلومات الملف أو None
        """
        if not os.path.exists(local_path):
            logger.warning(f"الملف غير موجود: {local_path}")
            return None
        
        def _do_upload():
            try:
                if not self.drive_service.is_configured():
                    logger.debug("Google Drive غير مكوّن - الملف محفوظ محلياً فقط")
                    return None
                
                # محاولة الرفع (اختياري - الحفظ المحلي هو الأساسي)
                employees_folder = self._get_or_create_employees_folder()
                if not employees_folder:
                    logger.debug(f"لم نتمكن من الوصول إلى مجلد Shared Drive - الملف محفوظ محلياً")
                    return None
                
                # إنشاء مجلد الموظف
                employee_folder = self.drive_service._get_or_create_folder(
                    f"employee_{employee_id}",
                    parent_id=employees_folder
                )
                if not employee_folder:
                    return None
                
                # رفع الملف
                filename = os.path.basename(local_path)
                result = self.drive_service.upload_file(
                    file_path=local_path,
                    folder_id=employee_folder,
                    custom_name=f"{file_type}_{filename}"
                )
                
                if result:
                    logger.info(f"✅ تم رفع ملف الموظف: {file_type} - {filename}")
                    return result
                
                return None
                
            except Exception as e:
                logger.debug(f"تعذر رفع الملف إلى Drive (الملف محفوظ محلياً): {e}")
                return None
        
        if sync:
            return _do_upload()
        else:
            # تشغيل الرفع في خيط منفصل (غير متزامن)
            Thread(target=_do_upload, daemon=True).start()
            return None
    
    def upload_vehicle_document_async(
        self,
        local_path: str,
        plate_number: str,
        operation_type: str,
        sync: bool = False
    ) -> Optional[Dict]:
        """
        رفع وثيقة سيارة إلى Google Drive
        
        Args:
            local_path: المسار المحلي للملف
            plate_number: رقم اللوحة
            operation_type: نوع العملية (تسليم، استلام، فحص، إلخ)
            sync: إذا كانت True، انتظر الرفع
        
        Returns:
            معلومات الملف أو None
        """
        if not os.path.exists(local_path):
            logger.warning(f"الملف غير موجود: {local_path}")
            return None
        
        def _do_upload():
            try:
                if not self.drive_service.is_configured():
                    return None
                
                result = self.drive_service.upload_vehicle_operation(
                    vehicle_plate=plate_number,
                    operation_type=operation_type,
                    pdf_path=local_path if local_path.lower().endswith('.pdf') else None,
                    image_paths=[local_path] if not local_path.lower().endswith('.pdf') else None
                )
                
                if result:
                    logger.info(f"✅ تم رفع وثيقة السيارة: {plate_number} - {operation_type}")
                
                return result
            except Exception as e:
                logger.error(f"خطأ في رفع وثيقة السيارة: {e}")
                return None
        
        if sync:
            return _do_upload()
        else:
            Thread(target=_do_upload, daemon=True).start()
            return None
    
    def upload_report_async(
        self,
        local_path: str,
        report_type: str = "general",
        sync: bool = False
    ) -> Optional[Dict]:
        """رفع تقرير إلى Google Drive"""
        if not os.path.exists(local_path):
            return None
        
        def _do_upload():
            try:
                if not self.drive_service.is_configured():
                    return None
                
                root_folder = self.drive_service.get_root_folder()
                if not root_folder:
                    return None
                
                # إنشاء مجلد التقارير
                reports_folder = self.drive_service._get_or_create_folder(
                    "التقارير",
                    parent_id=root_folder
                )
                if not reports_folder:
                    return None
                
                # رفع التقرير
                filename = os.path.basename(local_path)
                result = self.drive_service.upload_file(
                    file_path=local_path,
                    folder_id=reports_folder,
                    custom_name=f"{report_type}_{filename}"
                )
                
                if result:
                    logger.info(f"✅ تم رفع التقرير: {report_type} - {filename}")
                
                return result
            except Exception as e:
                logger.error(f"خطأ في رفع التقرير: {e}")
                return None
        
        if sync:
            return _do_upload()
        else:
            Thread(target=_do_upload, daemon=True).start()
            return None


# Instance للاستخدام المباشر
unified_storage = UnifiedStorageService()
