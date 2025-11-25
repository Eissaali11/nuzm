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
            from utils.storage_helper import download_image
            import tempfile
            
            # جمع بيانات العملية
            plate_number = safety_check.vehicle_plate_number
            
            # نوع العملية
            operation_type = "فحوصات السلامة"
            
            # جمع الصور
            image_paths = []
            for img in safety_check.safety_images:
                if not img.image_path:
                    continue
                
                # إصلاح المسار - لا نضيف static/uploads إذا كانت موجودة بالفعل
                img_path = img.image_path
                if not img_path.startswith('static/uploads'):
                    img_path = os.path.join('static/uploads', img_path)
                
                # البحث عن الملف محلياً أولاً
                if os.path.exists(img_path):
                    image_paths.append(img_path)
                    logger.info(f"تم العثور على صورة محلياً: {img_path}")
                else:
                    # محاولة تحميل الصورة من Object Storage وحفظها مؤقتاً
                    try:
                        image_data = download_image(img.image_path)
                        if image_data:
                            # إنشاء ملف مؤقت
                            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                                tmp.write(image_data)
                                tmp_path = tmp.name
                            image_paths.append(tmp_path)
                            logger.info(f"تم تحميل صورة من Object Storage: {img.image_path}")
                        else:
                            logger.warning(f"لم يتم العثور على صورة: {img.image_path}")
                    except Exception as e:
                        logger.warning(f"خطأ في تحميل صورة {img.image_path}: {e}")
            
            # استخدام ملف PDF الموجود إذا لم يتم توفير واحد
            if not pdf_path and safety_check.pdf_file_path:
                pdf_path = safety_check.pdf_file_path
                if not pdf_path.startswith('static/uploads'):
                    pdf_path = os.path.join('static/uploads', pdf_path)
                
                if not os.path.exists(pdf_path):
                    logger.warning(f"ملف PDF غير موجود: {pdf_path}")
                    pdf_path = None
            
            logger.info(f"جاري رفع فحص السلامة {safety_check.id} - {len(image_paths)} صورة، PDF: {pdf_path is not None}")
            
            # رفع إلى Google Drive
            result = drive_service.upload_vehicle_operation(
                vehicle_plate=plate_number,
                operation_type=operation_type,
                pdf_path=pdf_path,
                image_paths=image_paths if image_paths else None,
                operation_date=safety_check.inspection_date
            )
            
            # تنظيف الملفات المؤقتة
            for img_path in image_paths:
                if img_path.startswith('/tmp'):
                    try:
                        os.remove(img_path)
                    except:
                        pass
            
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
                
                logger.info(f"تم رفع فحص السلامة {safety_check.id} بنجاح - Folder ID: {result.get('folder_id')}")
            else:
                safety_check.drive_upload_status = 'failed'
                logger.warning(f"فشل رفع فحص السلامة {safety_check.id} - لم يتم استلام نتيجة من Google Drive")
                
        except Exception as e:
            logger.error(f"خطأ في رفع فحص السلامة: {e}", exc_info=True)
            safety_check.drive_upload_status = 'failed'


# إنشاء instance واحد للاستخدام
uploader = VehicleDriveUploader()
