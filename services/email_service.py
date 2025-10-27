import os
import sys
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, MailSettings, SandBoxMode
import base64
import mimetypes
from flask import current_app

class EmailService:
    def __init__(self):
        self.sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        if not self.sendgrid_key:
            current_app.logger.error("SENDGRID_API_KEY environment variable must be set")
            return
        self.sg = SendGridAPIClient(self.sendgrid_key)
    
    def send_vehicle_operation_files(self, to_email, to_name, operation, vehicle_plate, driver_name, excel_file_path=None, pdf_file_path=None, sender_email="test@sink.sendgrid.net"):
        """
        إرسال ملفات العملية مع تفاصيل السيارة عبر الإيميل
        """
        try:
            if not self.sendgrid_key:
                return {"success": False, "message": "SendGrid API key not configured"}
            
            # إنشاء الموضوع
            subject = f"تفاصيل العملية #{operation.id} - مركبة رقم {vehicle_plate}"
            
            # إنشاء محتوى الرسالة
            operation_type_ar = {
                'handover': 'تسليم/استلام',
                'workshop': 'ورشة صيانة',
                'external_authorization': 'تفويض خارجي',
                'safety_inspection': 'فحص سلامة'
            }.get(operation.operation_type, operation.operation_type)
            
            status_ar = {
                'pending': 'معلقة',
                'approved': 'موافق عليها',
                'rejected': 'مرفوضة',
                'under_review': 'تحت المراجعة'
            }.get(operation.status, operation.status)
            
            priority_ar = {
                'urgent': 'عاجل',
                'high': 'عالية',
                'normal': 'عادية',
                'low': 'منخفضة'
            }.get(operation.priority, operation.priority)
            
            html_content = f"""
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>تفاصيل العملية</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        direction: rtl;
                        text-align: right;
                        background-color: #f8f9fa;
                        margin: 0;
                        padding: 20px;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 12px;
                        overflow: hidden;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 30px;
                        text-align: center;
                    }}
                    .header h1 {{
                        margin: 0 0 10px 0;
                        font-size: 24px;
                    }}
                    .header p {{
                        margin: 0;
                        opacity: 0.9;
                    }}
                    .content {{
                        padding: 30px;
                    }}
                    .info-section {{
                        background: #f8f9fa;
                        border-radius: 8px;
                        padding: 20px;
                        margin-bottom: 20px;
                    }}
                    .info-title {{
                        font-size: 18px;
                        font-weight: bold;
                        color: #333;
                        margin-bottom: 15px;
                        border-bottom: 2px solid #667eea;
                        padding-bottom: 5px;
                    }}
                    .info-row {{
                        display: flex;
                        justify-content: space-between;
                        margin-bottom: 10px;
                        padding: 8px 0;
                        border-bottom: 1px solid #e9ecef;
                    }}
                    .info-row:last-child {{
                        border-bottom: none;
                        margin-bottom: 0;
                    }}
                    .info-label {{
                        font-weight: 600;
                        color: #6c757d;
                    }}
                    .info-value {{
                        color: #333;
                    }}
                    .status-badge {{
                        display: inline-block;
                        padding: 4px 12px;
                        border-radius: 20px;
                        font-size: 12px;
                        font-weight: 600;
                        text-transform: uppercase;
                    }}
                    .status-pending {{ background: #fff3cd; color: #856404; }}
                    .status-approved {{ background: #d4edda; color: #155724; }}
                    .status-rejected {{ background: #f8d7da; color: #721c24; }}
                    .status-under_review {{ background: #d1ecf1; color: #0c5460; }}
                    .vehicle-plate {{
                        background: linear-gradient(135deg, #667eea, #764ba2);
                        color: white;
                        padding: 8px 16px;
                        border-radius: 6px;
                        font-weight: bold;
                        text-align: center;
                        display: inline-block;
                    }}
                    .footer {{
                        background: #f8f9fa;
                        padding: 20px;
                        text-align: center;
                        color: #6c757d;
                        font-size: 14px;
                        border-top: 1px solid #e9ecef;
                    }}
                    .attachments {{
                        background: #e3f2fd;
                        border: 1px solid #2196f3;
                        border-radius: 8px;
                        padding: 15px;
                        margin-top: 20px;
                    }}
                    .attachments h4 {{
                        margin: 0 0 10px 0;
                        color: #1976d2;
                    }}
                    .attachment-item {{
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        margin: 5px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>نظام نُظم</h1>
                        <p>تفاصيل العملية #{operation.id}</p>
                    </div>
                    
                    <div class="content">
                        <div class="info-section">
                            <div class="info-title">معلومات المركبة</div>
                            <div class="info-row">
                                <span class="info-label">رقم اللوحة:</span>
                                <span class="vehicle-plate">{vehicle_plate}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">السائق:</span>
                                <span class="info-value">{driver_name or 'غير محدد'}</span>
                            </div>
                        </div>
                        
                        <div class="info-section">
                            <div class="info-title">تفاصيل العملية</div>
                            <div class="info-row">
                                <span class="info-label">عنوان العملية:</span>
                                <span class="info-value">{operation.title}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">نوع العملية:</span>
                                <span class="info-value">{operation_type_ar}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">حالة العملية:</span>
                                <span class="status-badge status-{operation.status}">{status_ar}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">الأولوية:</span>
                                <span class="info-value">{priority_ar}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">تاريخ الطلب:</span>
                                <span class="info-value">{operation.requested_at.strftime('%Y/%m/%d الساعة %H:%M') if operation.requested_at else operation.created_at.strftime('%Y/%m/%d الساعة %H:%M')}</span>
                            </div>
                        </div>
                        
                        {f'<div class="info-section"><div class="info-title">الوصف</div><p>{operation.description}</p></div>' if operation.description else ''}
                        
                        {f'<div class="info-section"><div class="info-title">ملاحظات المراجعة</div><p>{operation.review_notes}</p></div>' if operation.review_notes else ''}
                        
                        <div class="attachments">
                            <h4>الملفات المرفقة:</h4>
                            {f'<div class="attachment-item">📊 ملف Excel - تفاصيل العملية</div>' if excel_file_path else ''}
                            {f'<div class="attachment-item">📄 ملف PDF - تقرير العملية</div>' if pdf_file_path else ''}
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>نظام نُظم لإدارة الموظفين والمركبات</p>
                        <p>تم إنشاء هذه الرسالة تلقائياً من النظام</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # النص البديل
            text_content = f"""
نظام نُظم - تفاصيل العملية #{operation.id}

معلومات المركبة:
- رقم اللوحة: {vehicle_plate}
- السائق: {driver_name or 'غير محدد'}

تفاصيل العملية:
- العنوان: {operation.title}
- النوع: {operation_type_ar}
- الحالة: {status_ar}
- الأولوية: {priority_ar}
- تاريخ الطلب: {operation.requested_at.strftime('%Y/%m/%d الساعة %H:%M') if operation.requested_at else operation.created_at.strftime('%Y/%m/%d الساعة %H:%M')}

{f'الوصف: {operation.description}' if operation.description else ''}

{f'ملاحظات المراجعة: {operation.review_notes}' if operation.review_notes else ''}

الملفات المرفقة:
{f'- ملف Excel: تفاصيل العملية' if excel_file_path else ''}
{f'- ملف PDF: تقرير العملية' if pdf_file_path else ''}

---
نظام نُظم لإدارة الموظفين والمركبات
تم إنشاء هذه الرسالة تلقائياً من النظام
            """
            
            # إنشاء الرسالة مع تفعيل وضع Sandbox للاختبار
            message = Mail(
                from_email=Email(sender_email, "نظام نُظم"),
                to_emails=To(to_email, to_name),
                subject=subject
            )
            
            # إزالة وضع Sandbox للإرسال الفعلي
            # ملاحظة: قد تحتاج لإعداد Single Sender Verification في SendGrid
            
            message.content = [
                Content("text/plain", text_content),
                Content("text/html", html_content)
            ]
            
            # إضافة الملفات المرفقة
            attachments = []
            
            if excel_file_path and os.path.exists(excel_file_path):
                with open(excel_file_path, 'rb') as f:
                    data = f.read()
                    encoded = base64.b64encode(data).decode()
                    attachment = Attachment()
                    attachment.file_content = encoded
                    attachment.file_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    attachment.file_name = f'operation_{operation.id}_details.xlsx'
                    attachment.disposition = 'attachment'
                    attachments.append(attachment)
            
            if pdf_file_path and os.path.exists(pdf_file_path):
                with open(pdf_file_path, 'rb') as f:
                    data = f.read()
                    encoded = base64.b64encode(data).decode()
                    attachment = Attachment()
                    attachment.file_content = encoded
                    attachment.file_type = 'application/pdf'
                    attachment.file_name = f'operation_{operation.id}_report.pdf'
                    attachment.disposition = 'attachment'
                    attachments.append(attachment)
            
            if attachments:
                message.attachment = attachments
            
            # إرسال الرسالة
            response = self.sg.send(message)
            
            current_app.logger.info(f"Email sent successfully to {to_email} for operation {operation.id}")
            
            return {
                "success": True, 
                "message": "تم إرسال الإيميل بنجاح",
                "status_code": response.status_code
            }
            
        except Exception as e:
            current_app.logger.error(f"SendGrid error: {str(e)}")
            return {
                "success": False, 
                "message": "SendGrid يتطلب إعداد Single Sender Verification. يُرجى إعداد مرسل مُتحقق في حساب SendGrid لتفعيل الإرسال الفعلي.",
                "technical_details": str(e),
                "solution": "1. دخول حساب SendGrid\n2. Settings → Sender Authentication\n3. إضافة Single Sender مع الإيميل المطلوب\n4. تأكيد الإيميل من صندوق الوارد"
            }
    
    def send_handover_operation_email(self, to_email, to_name, handover_record, vehicle_plate, driver_name, excel_file_path=None, pdf_file_path=None, sender_email="test@sink.sendgrid.net"):
        """
        إرسال ملفات عملية التسليم/الاستلام عبر الإيميل بتنسيق محسّن
        """
        try:
            if not self.sendgrid_key:
                return {"success": False, "message": "SendGrid API key not configured"}
            
            # تحديد نوع العملية
            operation_type_text = "تسليم" if handover_record.is_driver_receiving else "استلام"
            
            # إنشاء الموضوع
            subject = f"عملية {operation_type_text}"
            
            # إنشاء محتوى الرسالة المبسّط والمباشر
            html_content = f"""
            <!DOCTYPE html>
            <html dir="rtl" lang="ar">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>عملية {operation_type_text}</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        direction: rtl;
                        text-align: right;
                        background-color: #f8f9fa;
                        margin: 0;
                        padding: 20px;
                    }}
                    .container {{
                        max-width: 500px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 12px;
                        overflow: hidden;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 25px;
                        text-align: center;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 24px;
                    }}
                    .content {{
                        padding: 30px;
                    }}
                    .message {{
                        background: #d4edda;
                        border: 2px solid #28a745;
                        border-radius: 8px;
                        padding: 25px;
                        text-align: center;
                        margin-bottom: 20px;
                    }}
                    .icon {{
                        font-size: 48px;
                        margin-bottom: 15px;
                    }}
                    .message p {{
                        color: #155724;
                        margin: 0;
                        font-size: 18px;
                        line-height: 1.8;
                        font-weight: 500;
                    }}
                    .vehicle-plate {{
                        background: linear-gradient(135deg, #667eea, #764ba2);
                        color: white;
                        padding: 6px 14px;
                        border-radius: 5px;
                        font-weight: bold;
                        display: inline-block;
                        margin: 0 5px;
                    }}
                    .footer {{
                        background: #f8f9fa;
                        padding: 15px;
                        text-align: center;
                        color: #6c757d;
                        font-size: 13px;
                        border-top: 1px solid #e9ecef;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>نظام نُظم</h1>
                    </div>
                    
                    <div class="content">
                        <div class="message">
                            <div class="icon">✓</div>
                            <p>تمت عملية {operation_type_text} <span class="vehicle-plate">{vehicle_plate}</span> - {driver_name or 'غير محدد'} بنجاح.<br><br>
                            يرجى مراجعة التفاصيل في المرفقات.</p>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>نظام نُظم لإدارة الموظفين والمركبات</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # النص البديل - بسيط ومباشر
            text_content = f"""
نظام نُظم

تمت عملية {operation_type_text} {vehicle_plate} - {driver_name or 'غير محدد'} بنجاح.

يرجى مراجعة التفاصيل في المرفقات.

---
نظام نُظم لإدارة الموظفين والمركبات
            """
            
            # إنشاء الرسالة
            message = Mail(
                from_email=Email(sender_email, "نظام نُظم"),
                to_emails=To(to_email, to_name),
                subject=subject
            )
            
            message.content = [
                Content("text/plain", text_content),
                Content("text/html", html_content)
            ]
            
            # إضافة الملفات المرفقة
            attachments = []
            
            if excel_file_path and os.path.exists(excel_file_path):
                with open(excel_file_path, 'rb') as f:
                    data = f.read()
                    encoded = base64.b64encode(data).decode()
                    attachment = Attachment()
                    attachment.file_content = encoded
                    attachment.file_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    attachment.file_name = f'{operation_type_text}_{vehicle_plate}_details.xlsx'
                    attachment.disposition = 'attachment'
                    attachments.append(attachment)
            
            if pdf_file_path and os.path.exists(pdf_file_path):
                with open(pdf_file_path, 'rb') as f:
                    data = f.read()
                    encoded = base64.b64encode(data).decode()
                    attachment = Attachment()
                    attachment.file_content = encoded
                    attachment.file_type = 'application/pdf'
                    attachment.file_name = f'{operation_type_text}_{vehicle_plate}_document.pdf'
                    attachment.disposition = 'attachment'
                    attachments.append(attachment)
            
            if attachments:
                message.attachment = attachments
            
            # إرسال الرسالة
            response = self.sg.send(message)
            
            current_app.logger.info(f"Email sent successfully to {to_email} for handover operation")
            
            return {
                "success": True, 
                "message": "تم إرسال الإيميل بنجاح",
                "status_code": response.status_code
            }
            
        except Exception as e:
            current_app.logger.error(f"SendGrid error: {str(e)}")
            return {
                "success": False, 
                "message": "SendGrid يتطلب إعداد Single Sender Verification. يُرجى إعداد مرسل مُتحقق في حساب SendGrid لتفعيل الإرسال الفعلي.",
                "technical_details": str(e),
                "solution": "1. دخول حساب SendGrid\n2. Settings → Sender Authentication\n3. إضافة Single Sender مع الإيميل المطلوب\n4. تأكيد الإيميل من صندوق الوارد"
            }
    
    def send_simple_email(self, to_email, subject, content, sender_email="test@sink.sendgrid.net"):
        """
        إرسال إيميل بسيط
        """
        try:
            if not self.sendgrid_key:
                return {"success": False, "message": "SendGrid API key not configured"}
            
            message = Mail(
                from_email=Email(sender_email, "نظام نُظم"),
                to_emails=To(to_email),
                subject=subject,
                html_content=content
            )
            
            response = self.sg.send(message)
            
            return {
                "success": True,
                "message": "تم إرسال الإيميل بنجاح",
                "status_code": response.status_code
            }
            
        except Exception as e:
            current_app.logger.error(f"SendGrid error: {str(e)}")
            return {
                "success": False,
                "message": f"فشل في إرسال الإيميل: {str(e)}"
            }