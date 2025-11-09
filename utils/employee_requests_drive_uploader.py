"""
خدمة Google Drive لنظام طلبات الموظفين
البنية: نُظم - طلبات الموظفين / [نوع الطلب] / [رقم الطلب] - [اسم الموظف/رقم السيارة] - [التاريخ]
"""
import os
import logging
from typing import Optional, Dict, List
from datetime import datetime
from utils.google_drive_service import GoogleDriveService

logger = logging.getLogger(__name__)


class EmployeeRequestsDriveUploader:
    """خدمة رفع ملفات طلبات الموظفين إلى Google Drive"""
    
    def __init__(self):
        """تهيئة الخدمة"""
        self.drive_service = GoogleDriveService()
        self.requests_root_folder_id = None
    
    def is_available(self) -> bool:
        """التحقق من توفر الخدمة"""
        return self.drive_service.is_configured()
    
    def get_or_create_requests_root_folder(self) -> Optional[str]:
        """الحصول على مجلد 'نُظم - طلبات الموظفين' الرئيسي أو إنشاؤه"""
        if self.requests_root_folder_id:
            return self.requests_root_folder_id
        
        try:
            # الحصول على مجلد نُظم الرئيسي
            root_folder_id = self.drive_service.get_root_folder()
            if not root_folder_id:
                logger.error("فشل الحصول على المجلد الرئيسي 'نُظم'")
                return None
            
            # إنشاء مجلد طلبات الموظفين
            self.requests_root_folder_id = self.drive_service._get_or_create_folder(
                "طلبات الموظفين",
                parent_id=root_folder_id
            )
            
            if self.requests_root_folder_id:
                logger.info("تم الحصول على مجلد طلبات الموظفين الرئيسي")
            
            return self.requests_root_folder_id
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء مجلد طلبات الموظفين: {e}")
            return None
    
    def create_request_folder(
        self, 
        request_type: str, 
        request_id: int, 
        employee_name: str = None,
        vehicle_number: str = None,
        date: datetime = None
    ) -> Optional[Dict]:
        """
        إنشاء مجلد فرعي لطلب محدد
        
        Args:
            request_type: نوع الطلب (invoice/car_wash/car_inspection/advance_payment)
            request_id: رقم الطلب
            employee_name: اسم الموظف (للفواتير والسلف)
            vehicle_number: رقم السيارة (لطلبات السيارات)
            date: التاريخ (افتراضياً اليوم)
        
        Returns:
            Dict مع folder_id و folder_url
        """
        try:
            # الحصول على المجلد الرئيسي
            requests_root = self.get_or_create_requests_root_folder()
            if not requests_root:
                return None
            
            # تحديد اسم المجلد الفرعي حسب النوع
            type_folder_names = {
                'invoice': 'الفواتير',
                'car_wash': 'طلبات غسيل السيارات',
                'car_inspection': 'فحص وتوثيق السيارات',
                'advance_payment': 'طلبات السلف'
            }
            
            type_folder_name = type_folder_names.get(request_type, 'طلبات أخرى')
            
            # الحصول على مجلد النوع أو إنشاؤه
            type_folder_id = self.drive_service._get_or_create_folder(
                type_folder_name,
                parent_id=requests_root
            )
            
            if not type_folder_id:
                logger.error(f"فشل إنشاء مجلد النوع: {type_folder_name}")
                return None
            
            # تحديد التاريخ
            if date is None:
                date = datetime.now()
            date_str = date.strftime('%Y-%m-%d')
            
            # تسمية المجلد حسب النوع
            if request_type in ['invoice', 'advance_payment']:
                # للفواتير والسلف: رقم الطلب - اسم الموظف - التاريخ
                folder_name = f"{request_id} - {employee_name} - {date_str}"
            else:
                # لطلبات السيارات: رقم الطلب - رقم السيارة - التاريخ
                folder_name = f"{request_id} - {vehicle_number} - {date_str}"
            
            # إنشاء مجلد الطلب
            folder_id = self.drive_service._get_or_create_folder(
                folder_name,
                parent_id=type_folder_id
            )
            
            if folder_id:
                # الحصول على رابط المجلد
                folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
                
                logger.info(f"تم إنشاء مجلد الطلب: {folder_name}")
                
                return {
                    'folder_id': folder_id,
                    'folder_url': folder_url
                }
            
            return None
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء مجلد الطلب: {e}")
            return None
    
    def upload_invoice_image(
        self, 
        file_path: str, 
        folder_id: str,
        custom_name: str = None
    ) -> Optional[Dict]:
        """
        رفع صورة فاتورة
        
        Args:
            file_path: مسار الملف المحلي
            folder_id: معرف المجلد في Drive
            custom_name: اسم مخصص للملف (اختياري)
        
        Returns:
            Dict مع file_id, view_url, download_url
        """
        try:
            file_name = custom_name or f"invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            
            result = self.drive_service.upload_file(
                file_path=file_path,
                folder_id=folder_id,
                custom_name=file_name
            )
            
            if result:
                return {
                    'file_id': result['file_id'],
                    'view_url': result['web_view_link'],
                    'download_url': result.get('web_content_link'),
                    'file_size': os.path.getsize(file_path)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"خطأ في رفع صورة الفاتورة: {e}")
            return None
    
    def upload_car_wash_images(
        self, 
        images_dict: Dict[str, str], 
        folder_id: str
    ) -> Dict[str, Optional[Dict]]:
        """
        رفع صور طلب غسيل السيارة (5 صور)
        
        Args:
            images_dict: قاموس {media_type: file_path}
                        media_type: plate, front, back, right, left
            folder_id: معرف المجلد في Drive
        
        Returns:
            Dict مع نتائج رفع كل صورة {media_type: result_dict}
        """
        results = {}
        
        media_type_names = {
            'plate': 'اللوحة',
            'front': 'الأمام',
            'back': 'الخلف',
            'right': 'الجنب_الأيمن',
            'left': 'الجنب_الأيسر'
        }
        
        for media_type, file_path in images_dict.items():
            try:
                if not os.path.exists(file_path):
                    logger.warning(f"الملف غير موجود: {file_path}")
                    results[media_type] = None
                    continue
                
                file_name = f"{media_type_names.get(media_type, media_type)}.jpg"
                
                result = self.drive_service.upload_file(
                    file_path=file_path,
                    folder_id=folder_id,
                    custom_name=file_name
                )
                
                if result:
                    results[media_type] = {
                        'file_id': result['file_id'],
                        'view_url': result['web_view_link'],
                        'file_size': os.path.getsize(file_path)
                    }
                else:
                    results[media_type] = None
                    
            except Exception as e:
                logger.error(f"خطأ في رفع صورة {media_type}: {e}")
                results[media_type] = None
        
        return results
    
    def upload_large_video_resumable(
        self, 
        file_path: str, 
        folder_id: str,
        filename: str = None
    ) -> Optional[Dict]:
        """
        رفع فيديو كبير باستخدام Resumable Upload
        
        Args:
            file_path: مسار الملف المحلي
            folder_id: معرف المجلد في Drive
            filename: اسم الملف (اختياري)
        
        Returns:
            Dict مع file_id, view_url, embed_url, duration
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"الملف غير موجود: {file_path}")
                return None
            
            file_name = filename or os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            # للفيديوهات الصغيرة (< 50MB) نستخدم الطريقة العادية
            if file_size < 50 * 1024 * 1024:
                result = self.drive_service.upload_file(
                    file_path=file_path,
                    folder_id=folder_id,
                    custom_name=file_name
                )
                
                if result:
                    embed_url = f"https://drive.google.com/file/d/{result['file_id']}/preview"
                    
                    return {
                        'file_id': result['file_id'],
                        'view_url': result['web_view_link'],
                        'download_url': result.get('web_content_link'),
                        'embed_url': embed_url,
                        'file_size': file_size
                    }
            
            # TODO: للفيديوهات الكبيرة - تطبيق Resumable Upload API
            # الآن نستخدم الطريقة العادية حتى للملفات الكبيرة
            result = self.drive_service.upload_file(
                file_path=file_path,
                folder_id=folder_id,
                custom_name=file_name
            )
            
            if result:
                embed_url = f"https://drive.google.com/file/d/{result['file_id']}/preview"
                
                return {
                    'file_id': result['file_id'],
                    'view_url': result['web_view_link'],
                    'download_url': result.get('web_content_link'),
                    'embed_url': embed_url,
                    'file_size': file_size
                }
            
            return None
            
        except Exception as e:
            logger.error(f"خطأ في رفع الفيديو: {e}")
            return None
    
    def upload_inspection_images_batch(
        self, 
        images_list: List[str], 
        folder_id: str
    ) -> List[Optional[Dict]]:
        """
        رفع مجموعة صور للفحص دفعة واحدة
        
        Args:
            images_list: قائمة بمسارات الصور
            folder_id: معرف المجلد في Drive
        
        Returns:
            قائمة بنتائج رفع كل صورة
        """
        results = []
        
        for idx, file_path in enumerate(images_list, 1):
            try:
                if not os.path.exists(file_path):
                    logger.warning(f"الملف غير موجود: {file_path}")
                    results.append(None)
                    continue
                
                file_ext = os.path.splitext(file_path)[1]
                file_name = f"صورة_{idx}{file_ext}"
                
                result = self.drive_service.upload_file(
                    file_path=file_path,
                    folder_id=folder_id,
                    custom_name=file_name
                )
                
                if result:
                    results.append({
                        'file_id': result['file_id'],
                        'view_url': result['web_view_link'],
                        'download_url': result.get('web_content_link'),
                        'file_size': os.path.getsize(file_path),
                        'original_filename': os.path.basename(file_path)
                    })
                else:
                    results.append(None)
                    
            except Exception as e:
                logger.error(f"خطأ في رفع الصورة {idx}: {e}")
                results.append(None)
        
        return results
    
    def get_folder_url(self, folder_id: str) -> str:
        """الحصول على رابط المجلد"""
        return f"https://drive.google.com/drive/folders/{folder_id}"
    
    def delete_file(self, file_id: str) -> bool:
        """
        حذف ملف من Drive
        
        Args:
            file_id: معرف الملف
        
        Returns:
            True إذا نجح الحذف
        """
        try:
            if not self.drive_service.access_token:
                if not self.drive_service.authenticate():
                    return False
            
            import requests
            
            headers = {"Authorization": f"Bearer {self.drive_service.access_token}"}
            response = requests.delete(
                f"https://www.googleapis.com/drive/v3/files/{file_id}",
                headers=headers
            )
            
            if response.status_code == 204:
                logger.info(f"تم حذف الملف: {file_id}")
                return True
            else:
                logger.error(f"فشل حذف الملف: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في حذف الملف: {e}")
            return False
    
    def get_drive_storage_info(self) -> Optional[Dict]:
        """
        الحصول على معلومات المساحة المتاحة والمستخدمة
        
        Returns:
            Dict مع usage, limit, available
        """
        try:
            if not self.drive_service.access_token:
                if not self.drive_service.authenticate():
                    return None
            
            import requests
            
            headers = {"Authorization": f"Bearer {self.drive_service.access_token}"}
            response = requests.get(
                "https://www.googleapis.com/drive/v3/about?fields=storageQuota",
                headers=headers
            )
            
            if response.status_code == 200:
                quota = response.json().get('storageQuota', {})
                
                usage = int(quota.get('usage', 0))
                limit = int(quota.get('limit', 0))
                available = limit - usage if limit > 0 else 0
                
                return {
                    'usage': usage,
                    'limit': limit,
                    'available': available,
                    'usage_gb': round(usage / (1024**3), 2),
                    'limit_gb': round(limit / (1024**3), 2),
                    'available_gb': round(available / (1024**3), 2),
                    'usage_percentage': round((usage / limit * 100), 2) if limit > 0 else 0
                }
            
            return None
            
        except Exception as e:
            logger.error(f"خطأ في الحصول على معلومات المساحة: {e}")
            return None


# Instance للاستخدام المباشر
requests_drive_uploader = EmployeeRequestsDriveUploader()
