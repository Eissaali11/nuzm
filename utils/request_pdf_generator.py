"""
خدمة تصدير ملفات PDF لطلبات الموظفين
"""
import os
import logging
from io import BytesIO
from datetime import datetime
from typing import Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class RequestPDFGenerator:
    """مولد ملفات PDF لطلبات الموظفين"""
    
    @staticmethod
    def generate_advance_payment_pdf(request_id: int) -> Optional[BytesIO]:
        """
        إنشاء PDF لطلب سلفة - نموذج رسمي
        
        Args:
            request_id: رقم الطلب
        
        Returns:
            BytesIO object يحتوي على PDF
        """
        try:
            from models import EmployeeRequest, AdvancePaymentRequest
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib.units import cm
            
            # جلب بيانات الطلب
            request = EmployeeRequest.query.get(request_id)
            if not request or not request.advance_data:
                logger.error(f"طلب السلفة غير موجود: {request_id}")
                return None
            
            advance = request.advance_data
            
            # إنشاء PDF
            buffer = BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            
            # تسجيل خط عربي
            try:
                font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('Arabic', font_path))
                    pdf.setFont('Arabic', 12)
            except:
                pdf.setFont('Helvetica', 12)
            
            # عنوان المستند
            pdf.setFont('Helvetica-Bold', 18)
            pdf.drawCentredString(width/2, height - 2*cm, "طلب سلفة")
            
            # رقم الطلب
            pdf.setFont('Helvetica', 12)
            pdf.drawRightString(width - 2*cm, height - 3*cm, f"رقم الطلب: #{request.id}")
            pdf.drawRightString(width - 2*cm, height - 3.5*cm, 
                               f"التاريخ: {request.created_at.strftime('%Y-%m-%d')}")
            
            # بيانات الموظف
            y = height - 5*cm
            pdf.setFont('Helvetica-Bold', 14)
            pdf.drawRightString(width - 2*cm, y, "بيانات الموظف")
            
            y -= 1*cm
            pdf.setFont('Helvetica', 12)
            pdf.drawRightString(width - 2*cm, y, f"الاسم: {advance.employee_name}")
            y -= 0.7*cm
            pdf.drawRightString(width - 2*cm, y, f"رقم الهوية: {advance.national_id}")
            y -= 0.7*cm
            pdf.drawRightString(width - 2*cm, y, f"الرقم الوظيفي: {advance.employee_number}")
            y -= 0.7*cm
            pdf.drawRightString(width - 2*cm, y, f"المسمى الوظيفي: {advance.job_title}")
            y -= 0.7*cm
            pdf.drawRightString(width - 2*cm, y, f"القسم: {advance.department_name}")
            
            # بيانات السلفة
            y -= 1.5*cm
            pdf.setFont('Helvetica-Bold', 14)
            pdf.drawRightString(width - 2*cm, y, "بيانات السلفة")
            
            y -= 1*cm
            pdf.setFont('Helvetica', 12)
            pdf.drawRightString(width - 2*cm, y, f"المبلغ المطلوب: {advance.requested_amount} ريال")
            
            if advance.installments:
                y -= 0.7*cm
                pdf.drawRightString(width - 2*cm, y, f"عدد الأقساط: {advance.installments} شهر")
                y -= 0.7*cm
                pdf.drawRightString(width - 2*cm, y, f"مبلغ القسط: {advance.installment_amount} ريال")
            
            if advance.reason:
                y -= 0.7*cm
                pdf.drawRightString(width - 2*cm, y, f"السبب: {advance.reason}")
            
            # التواقيع
            y -= 3*cm
            pdf.setFont('Helvetica-Bold', 12)
            pdf.drawRightString(width - 2*cm, y, "توقيع الموظف: _______________")
            y -= 1.5*cm
            pdf.drawRightString(width - 2*cm, y, "توقيع المدير المباشر: _______________")
            y -= 1.5*cm
            pdf.drawRightString(width - 2*cm, y, "ختم وتوقيع الموارد البشرية: _______________")
            
            pdf.save()
            buffer.seek(0)
            
            logger.info(f"تم إنشاء PDF لطلب السلفة: {request_id}")
            return buffer
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء PDF لطلب السلفة: {e}")
            return None
    
    @staticmethod
    def generate_invoice_pdf(request_id: int) -> Optional[BytesIO]:
        """
        إنشاء PDF لفاتورة
        
        Args:
            request_id: رقم الطلب
        
        Returns:
            BytesIO object يحتوي على PDF
        """
        try:
            from models import EmployeeRequest, InvoiceRequest
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import cm
            
            # جلب بيانات الطلب
            request = EmployeeRequest.query.get(request_id)
            if not request or not request.invoice_data:
                logger.error(f"طلب الفاتورة غير موجود: {request_id}")
                return None
            
            invoice = request.invoice_data
            
            # إنشاء PDF
            buffer = BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            
            # عنوان
            pdf.setFont('Helvetica-Bold', 18)
            pdf.drawCentredString(width/2, height - 2*cm, "فاتورة")
            
            # معلومات
            y = height - 4*cm
            pdf.setFont('Helvetica', 12)
            pdf.drawRightString(width - 2*cm, y, f"رقم الطلب: #{request.id}")
            y -= 0.7*cm
            pdf.drawRightString(width - 2*cm, y, f"الموظف: {request.employee.name}")
            y -= 0.7*cm
            pdf.drawRightString(width - 2*cm, y, f"المورد: {invoice.vendor_name}")
            y -= 0.7*cm
            pdf.drawRightString(width - 2*cm, y, f"المبلغ: {request.amount} ريال")
            
            if invoice.payment_method:
                y -= 0.7*cm
                pdf.drawRightString(width - 2*cm, y, f"طريقة الدفع: {invoice.payment_method}")
            
            # QR Code للدرايف
            if request.google_drive_folder_url:
                y -= 1.5*cm
                pdf.drawRightString(width - 2*cm, y, "مسح الكود للوصول للملفات:")
                # TODO: إضافة QR Code
            
            pdf.save()
            buffer.seek(0)
            
            logger.info(f"تم إنشاء PDF للفاتورة: {request_id}")
            return buffer
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء PDF للفاتورة: {e}")
            return None
    
    @staticmethod
    def generate_car_wash_pdf(request_id: int) -> Optional[BytesIO]:
        """إنشاء PDF لطلب غسيل سيارة"""
        # TODO: Implementation
        logger.warning("generate_car_wash_pdf لم يُطبق بعد")
        return None
    
    @staticmethod
    def generate_car_inspection_pdf(request_id: int) -> Optional[BytesIO]:
        """إنشاء PDF لطلب فحص سيارة"""
        # TODO: Implementation
        logger.warning("generate_car_inspection_pdf لم يُطبق بعد")
        return None
    
    @staticmethod
    def generate_liability_report_pdf(employee_id: int) -> Optional[BytesIO]:
        """إنشاء تقرير PDF للالتزامات المالية لموظف"""
        # TODO: Implementation
        logger.warning("generate_liability_report_pdf لم يُطبق بعد")
        return None


# Instance للاستخدام المباشر
pdf_generator = RequestPDFGenerator()
