"""
خدمة Google Drive لرفع ملفات السيارات تلقائياً
البنية: نُظم / [رقم اللوحة] / [نوع العملية] / [التاريخ والوقت]
"""
import os
import json
import requests
from datetime import datetime
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class GoogleDriveService:
    """خدمة رفع الملفات إلى Google Drive"""
    
    def __init__(self):
        """تهيئة الخدمة"""
        self.credentials = self._load_credentials()
        self.access_token = None
        self.root_folder_id = "1AvaKUW2VKb9t4O4Dwo_KXTntBfDQ1IYe"  # مجلد "نُظم" الرئيسي (Shared Drive)
        self.shared_drive_id = "1AvaKUW2VKb9t4O4Dwo_KXTntBfDQ1IYe"  # Shared Drive ID (نفس المجلد الرئيسي)
        self.requests_folder_id = "1AvaKUW2VKb9t4O4Dwo_KXTntBfDQ1IYe"  # مجلد طلبات الموظفين (نفس المجلد الرئيسي)
        
    def _load_credentials(self) -> Optional[Dict]:
        """تحميل بيانات الاعتماد من المتغيرات البيئية أو ملف"""
        # محاولة التحميل من متغير بيئي
        creds_json = os.environ.get('GOOGLE_DRIVE_CREDENTIALS')
        if creds_json:
            try:
                return json.loads(creds_json)
            except json.JSONDecodeError:
                logger.error("خطأ في تحليل بيانات الاعتماد من المتغير البيئي")
                
        # محاولة التحميل من ملف
        creds_file = os.path.join(os.path.dirname(__file__), 'google_drive_credentials.json')
        if os.path.exists(creds_file):
            try:
                with open(creds_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"خطأ في تحميل بيانات الاعتماد من الملف: {e}")
                
        return None
    
    def is_configured(self) -> bool:
        """التحقق من وجود بيانات الاعتماد"""
        return self.credentials is not None
    
    def authenticate(self) -> bool:
        """المصادقة والحصول على access token"""
        if not self.is_configured():
            logger.warning("لم يتم تكوين بيانات الاعتماد")
            return False
            
        try:
            # استخدام Service Account للمصادقة مع صلاحيات Shared Drive
            from google.oauth2 import service_account
            from google.auth.transport.requests import Request
            
            SCOPES = [
                'https://www.googleapis.com/auth/drive.file',
                'https://www.googleapis.com/auth/drive'
            ]
            credentials = service_account.Credentials.from_service_account_info(
                self.credentials, scopes=SCOPES
            )
            
            # تحديث التوكن
            credentials.refresh(Request())
            self.access_token = credentials.token
            
            logger.info("تمت المصادقة بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في المصادقة: {e}")
            return False
    
    def _get_or_create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """الحصول على مجلد أو إنشاؤه إذا لم يكن موجوداً - مع دعم Shared Drive"""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            # إنشاء الـ credentials مع الصلاحيات الكاملة
            SCOPES = [
                'https://www.googleapis.com/auth/drive'  # صلاحيات كاملة
            ]
            credentials = service_account.Credentials.from_service_account_info(
                self.credentials, scopes=SCOPES
            )
            
            # إنشاء خدمة Drive
            service = build('drive', 'v3', credentials=credentials)
            
            # البحث عن المجلد مع دعم Shared Drive
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            else:
                query += f" and '{self.shared_drive_id}' in parents"
            
            # البحث مع دعم كامل للـ Shared Drive
            results = service.files().list(
                q=query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                corpora='drive',  # ✅ مهم جداً لـ Shared Drive
                driveId=self.shared_drive_id  # ✅ مطلوب عند استخدام corpora='drive'
            ).execute()
            
            files = results.get('files', [])
            if files:
                logger.info(f"✅ وجد المجلد الموجود: {folder_name}")
                return files[0]['id']
            
            # إنشاء المجلد إذا لم يكن موجوداً
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id if parent_id else self.shared_drive_id]
            }
            
            folder = service.files().create(
                body=file_metadata,
                fields='id',
                supportsAllDrives=True  # ✅ مهم للكتابة على Shared Drive
            ).execute()
            
            logger.info(f"✅ تم إنشاء المجلد: {folder_name} (ID: {folder.get('id')})")
            return folder.get('id')
                
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء/الحصول على المجلد {folder_name}: {e}")
            return None
    
    def get_root_folder(self) -> Optional[str]:
        """الحصول على Shared Drive ID كمجلد رئيسي"""
        if self.root_folder_id:
            return self.root_folder_id
        
        self.root_folder_id = self.shared_drive_id
        return self.root_folder_id
    
    def upload_file(self, file_path: str, folder_id: str, custom_name: Optional[str] = None) -> Optional[Dict]:
        """رفع ملف إلى Google Drive Shared Drive مع الصلاحيات الكاملة"""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaIoBaseUpload
            import io
            
            # التحقق من وجود الملف وحجمه
            if not os.path.exists(file_path):
                logger.error(f"الملف غير موجود: {file_path}")
                return None
            
            file_size = os.path.getsize(file_path)
            logger.info(f"⏳ جاري رفع ملف بحجم {file_size} بايت: {file_path}")
            
            if file_size == 0:
                logger.warning(f"⚠️ تحذير: الملف فارغ: {file_path}")
            
            # قراءة الملف بالكامل في الذاكرة
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            logger.info(f"✅ تم قراءة الملف: {len(file_content)} بايت")
            
            # إنشاء الـ credentials مع الصلاحيات الكاملة
            SCOPES = ['https://www.googleapis.com/auth/drive']  # صلاحيات كاملة
            credentials = service_account.Credentials.from_service_account_info(
                self.credentials, scopes=SCOPES
            )
            
            # إنشاء خدمة Drive
            service = build('drive', 'v3', credentials=credentials)
            
            # اسم الملف
            file_name = custom_name or os.path.basename(file_path)
            
            # metadata للملف
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            
            # تحويل البيانات إلى BytesIO لرفعها
            file_stream = io.BytesIO(file_content)
            media = MediaIoBaseUpload(file_stream, mimetype='application/octet-stream', resumable=True, chunksize=1024*1024*5)
            
            request = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,webContentLink',
                supportsAllDrives=True  # ✅ مهم للـ Shared Drive
            )
            
            # إكمال الرفع مع تتبع التقدم
            response = None
            retry_count = 0
            max_retries = 3
            
            while response is None and retry_count < max_retries:
                try:
                    status, response = request.next_chunk()
                    if status:
                        progress_pct = int(status.progress() * 100)
                        logger.info(f"⏳ تم رفع {progress_pct}% من {file_name}")
                    retry_count = 0  # إعادة تعيين العداد عند النجاح
                except Exception as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(f"❌ فشل الرفع بعد {max_retries} محاولات: {str(e)[:100]}")
                        return None
                    logger.warning(f"⚠️ خطأ في الرفع، إعادة محاولة {retry_count}: {str(e)[:100]}")
            
            logger.info(f"✅ تم رفع الملف بنجاح: {file_name} (ID: {response.get('id')})")
            return {
                'file_id': response.get('id'),
                'file_name': response.get('name'),
                'web_view_link': response.get('webViewLink'),
                'download_link': response.get('webContentLink')
            }
                
        except Exception as e:
            logger.error(f"❌ خطأ في رفع الملف {file_path}: {str(e)[:200]}", exc_info=False)
            return None
    
    def upload_vehicle_operation(
        self,
        vehicle_plate: str,
        operation_type: str,  # "سجل ورشة", "تسليم", "استلام", "فحص سلامة"
        pdf_path: Optional[str] = None,
        image_paths: Optional[List[str]] = None,
        operation_date: Optional[datetime] = None
    ) -> Optional[Dict]:
        """
        رفع عملية سيارة كاملة (PDF + صور) إلى Google Drive
        
        البنية: نُظم / [رقم اللوحة] / [نوع العملية] / [التاريخ والوقت]
        """
        if not self.is_configured():
            logger.warning("Google Drive غير مكوّن - تم تخطي الرفع")
            return None
        
        try:
            # الحصول على المجلد الرئيسي
            root_folder = self.get_root_folder()
            if not root_folder:
                logger.error("فشل في الحصول على المجلد الرئيسي")
                return None
            
            # إنشاء مجلد السيارة
            vehicle_folder = self._get_or_create_folder(vehicle_plate, root_folder)
            if not vehicle_folder:
                return None
            
            # إنشاء مجلد نوع العملية
            operation_folder = self._get_or_create_folder(operation_type, vehicle_folder)
            if not operation_folder:
                return None
            
            # إنشاء مجلد التاريخ
            if operation_date is None:
                operation_date = datetime.now()
            
            date_folder_name = operation_date.strftime("%Y-%m-%d_%H-%M-%S")
            date_folder = self._get_or_create_folder(date_folder_name, operation_folder)
            if not date_folder:
                return None
            
            result = {
                'vehicle_plate': vehicle_plate,
                'operation_type': operation_type,
                'folder_id': date_folder,
                'pdf_info': None,
                'images_info': []
            }
            
            # رفع ملف PDF
            if pdf_path and os.path.exists(pdf_path):
                pdf_info = self.upload_file(pdf_path, date_folder)
                if pdf_info:
                    result['pdf_info'] = pdf_info
            
            # رفع الصور
            if image_paths:
                for img_path in image_paths:
                    if os.path.exists(img_path):
                        img_info = self.upload_file(img_path, date_folder)
                        if img_info:
                            result['images_info'].append(img_info)
            
            logger.info(f"تم رفع العملية بنجاح: {vehicle_plate} - {operation_type}")
            return result
            
        except Exception as e:
            logger.error(f"خطأ في رفع العملية: {e}")
            return None


# إنشاء instance واحد للاستخدام في التطبيق
drive_service = GoogleDriveService()
