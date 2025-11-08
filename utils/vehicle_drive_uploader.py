"""
نظام الرفع التلقائي لملفات السيارات إلى Google Drive
يعمل في الخلفية دون التأثير على العمليات الحالية
"""
import os
import json
import logging
from datetime import datetime
from typing import Optional, List
from utils.google_drive_service import drive_service

logger = logging.getLogger(__name__)


class VehicleDriveUploader:
    """مدير الرفع التلقائي لملفات السيارات"""
    
    @staticmethod
    def upload_workshop_record(workshop_record, pdf_path: Optional[str] = None):
        """
        رفع سجل ورشة إلى Google Drive
        
        Args:
            workshop_record: كائن VehicleWorkshop
            pdf_path: مسار ملف PDF الإيصال (اختياري)
        """
        if not drive_service.is_configured():
            logger.info("Google Drive غير مكوّن - تم تخطي الرفع")
            return
        
        try:
            # جمع بيانات العملية
            vehicle = workshop_record.vehicle
            plate_number = vehicle.plate_number if vehicle else "غير_معروف"
            
            # تحديد نوع العملية
            operation_type = "سجلات الورش"
            
            # جمع الصور
            image_paths = []
            for img in workshop_record.images:
                img_path = os.path.join('static/uploads', img.image_path)
                if os.path.exists(img_path):
                    image_paths.append(img_path)
            
            # رفع إلى Google Drive
            result = drive_service.upload_vehicle_operation(
                vehicle_plate=plate_number,
                operation_type=operation_type,
                pdf_path=pdf_path,
                image_paths=image_paths if image_paths else None,
                operation_date=workshop_record.entry_date
            )
            
            if result:
                # تحديث السجل بروابط Google Drive
                workshop_record.drive_folder_id = result.get('folder_id')
                if result.get('pdf_info'):
                    workshop_record.drive_pdf_link = result['pdf_info'].get('web_view_link')
                
                if result.get('images_info'):
                    workshop_record.drive_images_links = json.dumps([
                        img.get('web_view_link') for img in result['images_info']
                    ])
                
                workshop_record.drive_upload_status = 'success'
                workshop_record.drive_uploaded_at = datetime.utcnow()
                
                logger.info(f"تم رفع سجل الورشة {workshop_record.id} بنجاح")
            else:
                workshop_record.drive_upload_status = 'failed'
                
        except Exception as e:
            logger.error(f"خطأ في رفع سجل الورشة: {e}")
            workshop_record.drive_upload_status = 'failed'
    
    @staticmethod
    def upload_handover_record(handover_record, pdf_path: Optional[str] = None):
        """
        رفع سجل تسليم/استلام إلى Google Drive
        
        Args:
            handover_record: كائن VehicleHandover
            pdf_path: مسار ملف PDF الإيصال (اختياري)
        """
        if not drive_service.is_configured():
            logger.info("Google Drive غير مكوّن - تم تخطي الرفع")
            return
        
        try:
            # جمع بيانات العملية
            vehicle = handover_record.vehicle
            plate_number = handover_record.vehicle_plate_number or (vehicle.plate_number if vehicle else "غير_معروف")
            
            # تحديد نوع العملية
            if handover_record.handover_type == 'delivery':
                operation_type = "عمليات التسليم"
            else:
                operation_type = "عمليات الاستلام"
            
            # جمع الصور
            image_paths = []
            for img in handover_record.images:
                img_path = img.get_path()
                full_path = os.path.join('static/uploads', img_path) if img_path else None
                if full_path and os.path.exists(full_path):
                    image_paths.append(full_path)
            
            # رفع إلى Google Drive
            result = drive_service.upload_vehicle_operation(
                vehicle_plate=plate_number,
                operation_type=operation_type,
                pdf_path=pdf_path,
                image_paths=image_paths if image_paths else None,
                operation_date=handover_record.handover_date
            )
            
            if result:
                # تحديث السجل بروابط Google Drive
                handover_record.drive_folder_id = result.get('folder_id')
                if result.get('pdf_info'):
                    handover_record.drive_pdf_link = result['pdf_info'].get('web_view_link')
                
                if result.get('images_info'):
                    handover_record.drive_images_links = json.dumps([
                        img.get('web_view_link') for img in result['images_info']
                    ])
                
                handover_record.drive_upload_status = 'success'
                handover_record.drive_uploaded_at = datetime.utcnow()
                
                logger.info(f"تم رفع سجل التسليم/الاستلام {handover_record.id} بنجاح")
            else:
                handover_record.drive_upload_status = 'failed'
                
        except Exception as e:
            logger.error(f"خطأ في رفع سجل التسليم/الاستلام: {e}")
            handover_record.drive_upload_status = 'failed'
    
    @staticmethod
    def upload_safety_check(safety_check, pdf_path: Optional[str] = None):
        """
        رفع فحص سلامة خارجي إلى Google Drive
        
        Args:
            safety_check: كائن VehicleExternalSafetyCheck
            pdf_path: مسار ملف PDF الفحص (اختياري)
        """
        if not drive_service.is_configured():
            logger.info("Google Drive غير مكوّن - تم تخطي الرفع")
            return
        
        try:
            # جمع بيانات العملية
            plate_number = safety_check.vehicle_plate_number
            
            # نوع العملية
            operation_type = "فحوصات السلامة"
            
            # جمع الصور
            image_paths = []
            for img in safety_check.safety_images:
                img_path = os.path.join('static/uploads', img.image_path)
                if os.path.exists(img_path):
                    image_paths.append(img_path)
            
            # استخدام ملف PDF الموجود إذا لم يتم توفير واحد
            if not pdf_path and safety_check.pdf_file_path:
                pdf_path = os.path.join('static/uploads', safety_check.pdf_file_path)
                if not os.path.exists(pdf_path):
                    pdf_path = None
            
            # رفع إلى Google Drive
            result = drive_service.upload_vehicle_operation(
                vehicle_plate=plate_number,
                operation_type=operation_type,
                pdf_path=pdf_path,
                image_paths=image_paths if image_paths else None,
                operation_date=safety_check.inspection_date
            )
            
            if result:
                # تحديث السجل بروابط Google Drive
                safety_check.drive_folder_id = result.get('folder_id')
                if result.get('pdf_info'):
                    safety_check.drive_pdf_link = result['pdf_info'].get('web_view_link')
                
                if result.get('images_info'):
                    safety_check.drive_images_links = json.dumps([
                        img.get('web_view_link') for img in result['images_info']
                    ])
                
                safety_check.drive_upload_status = 'success'
                safety_check.drive_uploaded_at = datetime.utcnow()
                
                logger.info(f"تم رفع فحص السلامة {safety_check.id} بنجاح")
            else:
                safety_check.drive_upload_status = 'failed'
                
        except Exception as e:
            logger.error(f"خطأ في رفع فحص السلامة: {e}")
            safety_check.drive_upload_status = 'failed'


# إنشاء instance واحد للاستخدام
uploader = VehicleDriveUploader()
