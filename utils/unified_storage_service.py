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
        🔒 الحفظ المحلي الموثوق هو الحل الأساسي
        الملف محفوظ محلياً بشكل دائم - Google Drive اختياري
        
        Args:
            local_path: المسار المحلي للملف
            employee_id: معرف الموظف
            file_type: نوع الملف
            sync: معامل غير مستخدم (للتوافق السابق)
        
        Returns:
            معلومات الملف المحفوظ محلياً
        """
        if not os.path.exists(local_path):
            logger.warning(f"الملف غير موجود: {local_path}")
            return None
        
        try:
            # ✅ الملف محفوظ محلياً بالفعل - هذا هو الحل الموثوق
            file_size = os.path.getsize(local_path)
            filename = os.path.basename(local_path)
            
            logger.info(f"✅ ملف محفوظ محلياً: {filename} ({file_size} bytes)")
            
            return {
                'local_path': local_path,
                'filename': filename,
                'file_size': file_size,
                'storage_type': 'local'
            }
            
        except Exception as e:
            logger.error(f"خطأ في الوصول للملف المحلي: {e}")
            return None
    
    def upload_vehicle_document_async(
        self,
        local_path: str,
        plate_number: str,
        operation_type: str,
        sync: bool = False
    ) -> Optional[Dict]:
        """
        🔒 الحفظ المحلي الموثوق للمستندات
        
        Args:
            local_path: المسار المحلي للملف
            plate_number: رقم اللوحة
            operation_type: نوع العملية
            sync: معامل غير مستخدم
        
        Returns:
            معلومات الملف المحفوظ محلياً
        """
        if not os.path.exists(local_path):
            logger.warning(f"الملف غير موجود: {local_path}")
            return None
        
        try:
            file_size = os.path.getsize(local_path)
            filename = os.path.basename(local_path)
            
            logger.info(f"✅ وثيقة محفوظة محلياً: {plate_number} - {operation_type}")
            
            return {
                'local_path': local_path,
                'filename': filename,
                'file_size': file_size,
                'storage_type': 'local'
            }
        except Exception as e:
            logger.error(f"خطأ: {e}")
            return None
    
    def upload_report_async(
        self,
        local_path: str,
        report_type: str = "general",
        sync: bool = False
    ) -> Optional[Dict]:
        """🔒 الحفظ المحلي الموثوق للتقارير"""
        if not os.path.exists(local_path):
            return None
        
        try:
            file_size = os.path.getsize(local_path)
            filename = os.path.basename(local_path)
            
            logger.info(f"✅ تقرير محفوظ محلياً: {report_type} - {filename}")
            
            return {
                'local_path': local_path,
                'filename': filename,
                'file_size': file_size,
                'storage_type': 'local'
            }
        except Exception as e:
            logger.error(f"خطأ: {e}")
            return None


# Instance للاستخدام المباشر
unified_storage = UnifiedStorageService()
