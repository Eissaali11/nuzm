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
        self.root_folder_id = None  # مجلد "نُظم" الرئيسي
        self.shared_drive_id = "1sePOW03BZfjkybt8p8s7D3413gJzYhL_"  # Shared Drive ID
        
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
        """الحصول على مجلد أو إنشاؤه إذا لم يكن موجوداً"""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            # إنشاء الـ credentials
            SCOPES = [
                'https://www.googleapis.com/auth/drive.file',
                'https://www.googleapis.com/auth/drive'
            ]
            credentials = service_account.Credentials.from_service_account_info(
                self.credentials, scopes=SCOPES
            )
            
            # إنشاء خدمة Drive
            service = build('drive', 'v3', credentials=credentials)
            
            # البحث عن المجلد
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            else:
                query += f" and '{self.shared_drive_id}' in parents"
            
            results = service.files().list(
                q=query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            
            files = results.get('files', [])
            if files:
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
                supportsAllDrives=True
            ).execute()
            
            logger.info(f"تم إنشاء المجلد: {folder_name}")
            return folder.get('id')
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء/الحصول على المجلد {folder_name}: {e}")
            return None
    
    def get_root_folder(self) -> Optional[str]:
        """الحصول على Shared Drive ID كمجلد رئيسي"""
        if self.root_folder_id:
            return self.root_folder_id
        
        self.root_folder_id = self.shared_drive_id
        return self.root_folder_id
    
    def upload_file(self, file_path: str, folder_id: str, custom_name: Optional[str] = None) -> Optional[Dict]:
        """رفع ملف إلى Google Drive (Shared Drive)"""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            
            # إنشاء الـ credentials
            SCOPES = [
                'https://www.googleapis.com/auth/drive.file',
                'https://www.googleapis.com/auth/drive'
            ]
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
            
            # رفع الملف إلى Shared Drive
            # Note: استخدام non-resumable upload للملفات الصغيرة لتجنب مشكلة quota
            file_size = os.path.getsize(file_path)
            use_resumable = file_size > 5 * 1024 * 1024  # 5MB
            
            media = MediaFileUpload(file_path, resumable=use_resumable)
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,webContentLink',
                supportsAllDrives=True
            ).execute()
            
            logger.info(f"تم رفع الملف بنجاح: {file_name}")
            return {
                'file_id': file.get('id'),
                'file_name': file.get('name'),
                'web_view_link': file.get('webViewLink'),
                'download_link': file.get('webContentLink')
            }
                
        except Exception as e:
            logger.error(f"خطأ في رفع الملف {file_path}: {e}")
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
