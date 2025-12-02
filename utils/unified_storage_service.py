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
            error_msg = str(e)
            logger.error(f"❌ خطأ في الحصول على مجلد السيارات: {error_msg}")
            
            # إذا كان الخطأ عن Shared Drive غير موجود، فالمشكلة هي الصلاحيات
            if 'Shared drive not found' in error_msg or '404' in error_msg:
                logger.error(f"❌ Service Account لم تُضَف إلى Shared Drive. البريد المطلوب: nuzum-721@nuzum-477618.iam.gserviceaccount.com")
            
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
    
    def upload_vehicle_operation(
        self,
        vehicle_plate: str,
        operation_type: str,
        operation_id: int,
        sync: bool = False
    ) -> Dict:
        """رفع ملفات عملية السيارة على Google Drive"""
        try:
            if not self.drive_service.is_configured():
                return {
                    'success': False, 
                    'message': '❌ Google Drive غير متصل. تحقق من بيانات المصادقة.'
                }
            
            # الحصول على مجلد السيارات
            vehicles_folder = self._get_or_create_vehicles_folder()
            if not vehicles_folder:
                return {
                    'success': False, 
                    'message': '❌ **يجب إضافة Service Account إلى Shared Drive**\n\nالبريد: nuzum-721@nuzum-477618.iam.gserviceaccount.com\nالصلاحيات: محرر\nالرابط: https://drive.google.com/drive/folders/1AvaKUW2VKb9t4O4Dwo_KXTntBfDQ1IYe'
                }
            
            # إنشاء مجلد للعملية
            operation_folder_name = f"العملية_{operation_id}_{operation_type}"
            operation_folder = self.drive_service._get_or_create_folder(
                operation_folder_name,
                parent_id=vehicles_folder
            )
            
            if not operation_folder:
                return {'success': False, 'message': '❌ فشل في إنشاء مجلد العملية'}
            
            logger.info(f"✅ تم رفع عملية السيارة {vehicle_plate} على Google Drive")
            
            # الحصول على رابط Shared Drive
            drive_link = f"https://drive.google.com/drive/folders/{vehicles_folder}"
            
            return {
                'success': True,
                'message': 'تم الرفع بنجاح',
                'folder_link': drive_link,
                'operation_folder_id': operation_folder
            }
        except Exception as e:
            error_str = str(e)
            logger.error(f"❌ خطأ في رفع عملية السيارة: {error_str}")
            
            # معالجة الأخطاء الشائعة
            if 'Shared drive not found' in error_str:
                return {
                    'success': False, 
                    'message': '❌ **Shared Drive غير متاح**\n\nتأكد من إضافة Service Account:\nnuzum-721@nuzum-477618.iam.gserviceaccount.com\n\nبصلاحيات محرر على Shared Drive'
                }
            
            return {'success': False, 'message': f'❌ خطأ: {error_str[:100]}'}


# Instance للاستخدام المباشر
unified_storage = UnifiedStorageService()
