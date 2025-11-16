import os
import sys
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, MailSettings, SandBoxMode
import base64
import mimetypes
from flask import current_app
import requests
import json
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formataddr
import io

class EmailService:
    def __init__(self):
        self.sendgrid_key = None
        self.from_email = None
        self._load_sendgrid_credentials()
        
    def _load_sendgrid_credentials(self):
        """تحميل بيانات اعتماد SendGrid من Replit Connection أو المتغيرات البيئية"""
        try:
            # محاولة الحصول على البيانات من Replit Connection
            hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
            repl_identity = os.environ.get('REPL_IDENTITY')
            
            if hostname and repl_identity:
                x_replit_token = f'repl {repl_identity}'
                
                response = requests.get(
                    f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=sendgrid',
                    headers={
                        'Accept': 'application/json',
                        'X_REPLIT_TOKEN': x_replit_token
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('items') and len(data['items']) > 0:
                        connection_settings = data['items'][0]
                        self.sendgrid_key = connection_settings.get('settings', {}).get('api_key')
                        self.from_email = connection_settings.get('settings', {}).get('from_email')
                        
                        if self.sendgrid_key and self.from_email:
                            current_app.logger.info("تم تحميل بيانات SendGrid من Replit Connection بنجاح")
                            self.sg = SendGridAPIClient(self.sendgrid_key)
                            return
        except Exception as e:
            current_app.logger.warning(f"فشل تحميل بيانات SendGrid من Connection: {str(e)}")
        
        # الاحتياطي: استخدام المتغيرات البيئية القديمة
        self.sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        self.from_email = "test@sink.sendgrid.net"
        
        if self.sendgrid_key:
            current_app.logger.info("تم تحميل بيانات SendGrid من المتغيرات البيئية")
            self.sg = SendGridAPIClient(self.sendgrid_key)
        else:
            current_app.logger.error("SENDGRID_API_KEY غير متوفر")
    
    def send_vehicle_operation_files(self, to_email, to_name, operation, vehicle_plate, driver_name, excel_file_path=None, pdf_file_path=None, sender_email=None):
        """
        إرسال ملفات العملية مع تفاصيل السيارة عبر الإيميل
        """
        try:
            if not self.sendgrid_key:
                return {"success": False, "message": "SendGrid API key not configured"}
            
            # استخدام البريد الإلكتروني من الاتصال إذا لم يتم تحديد واحد
            if sender_email is None:
                sender_email = self.from_email or "test@sink.sendgrid.net"
            
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
    
    def send_handover_operation_email(self, to_email, to_name, handover_record, vehicle_plate, driver_name, excel_file_path=None, pdf_file_path=None, sender_email=None):
        """
        إرسال ملفات عملية التسليم/الاستلام عبر الإيميل بتنسيق محسّن
        """
        try:
            if not self.sendgrid_key:
                return {"success": False, "message": "SendGrid API key not configured"}
            
            # استخدام البريد الإلكتروني من الاتصال إذا لم يتم تحديد واحد
            if sender_email is None:
                sender_email = self.from_email or "test@sink.sendgrid.net"
            
            # تحديد نوع العملية
            operation_type_text = "تسليم" if handover_record.handover_type == 'delivery' else "استلام"
            
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
    
    def build_handover_eml(self, to_email, to_name, handover_record, vehicle_plate, driver_name, excel_file_path=None, pdf_file_path=None, sender_email=None):
        """
        إنشاء ملف .eml لعملية تسليم/استلام يمكن فتحه في Outlook
        يتضمن الموضوع، المحتوى، والمرفقات
        
        Returns:
            tuple: (bytes_io, filename) أو (None, None) في حالة الخطأ
        """
        try:
            # استخدام البريد الإلكتروني من الاتصال إذا لم يتم تحديد واحد
            if sender_email is None:
                sender_email = self.from_email or "noreply@nuzum.local"
            
            # تحديد نوع العملية
            operation_type_text = "تسليم" if handover_record.handover_type == 'delivery' else "استلام"
            
            # إنشاء الموضوع
            subject = f"عملية {operation_type_text}"
            
            # جلب معلومات الموظف الكاملة
            from models import Employee
            employee = None
            if handover_record.driver_employee:
                employee = handover_record.driver_employee
            else:
                employee = Employee.query.filter_by(name=handover_record.person_name).first()
            
            # بناء معلومات الموظف
            employee_info_html = ""
            employee_info_text = ""
            if employee:
                residency = handover_record.driver_residency_number or employee.national_id or "غير متوفر"
                emp_number = employee.employee_id or "غير متوفر"
                department_name = employee.department.name if employee.department else "غير متوفر"
                birth_date = employee.birth_date.strftime('%Y-%m-%d') if employee.birth_date else "غير متوفر"
                city = handover_record.city or employee.location or "غير متوفر"
                
                employee_info_html = f"""
                <div style="text-align: right; margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                    <h3 style="margin-top: 0; color: #495057;">👤 معلومات السائق</h3>
                    <p style="margin: 5px 0;"><strong>اسم الموظف:</strong> {handover_record.person_name}</p>
                    <p style="margin: 5px 0;"><strong>رقم الإقامة:</strong> {residency}</p>
                    <p style="margin: 5px 0;"><strong>رقم الموظف:</strong> {emp_number}</p>
                    <p style="margin: 5px 0;"><strong>القسم:</strong> {department_name}</p>
                    <p style="margin: 5px 0;"><strong>تاريخ الميلاد:</strong> {birth_date}</p>
                    <p style="margin: 5px 0;"><strong>المدينة:</strong> {city}</p>
                </div>
                """
                
                employee_info_text = f"""
👤 معلومات السائق:
• اسم الموظف: {handover_record.person_name}
• رقم الإقامة: {residency}
• رقم الموظف: {emp_number}
• القسم: {department_name}
• تاريخ الميلاد: {birth_date}
• المدينة: {city}
"""
            else:
                employee_info_html = f"""
                <div style="text-align: right; margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                    <h3 style="margin-top: 0; color: #495057;">👤 معلومات السائق</h3>
                    <p style="margin: 5px 0;"><strong>اسم الموظف:</strong> {handover_record.person_name}</p>
                </div>
                """
                employee_info_text = f"""
👤 معلومات السائق:
• اسم الموظف: {handover_record.person_name}
"""
            
            # إنشاء محتوى HTML
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
                        <p>السادة المعنيين، تحية طيبة وبعد،</p>
                        <p>مرفق لكم تفاصيل عملية استلام أو تسليم المركبة وفقاً للمعلومات التالية:</p>
                        
                        <div style="text-align: center; margin: 20px 0; padding: 15px; background: #d4edda; border: 2px solid #28a745; border-radius: 8px;">
                            <h2 style="margin-top: 0; color: #155724;">🔄 {operation_type_text} مركبة</h2>
                            <p style="margin: 5px 0;"><strong>رقم السيارة:</strong> <span class="vehicle-plate">{vehicle_plate}</span></p>
                            <p style="margin: 5px 0;"><strong>نوع العملية:</strong> {operation_type_text}</p>
                            <p style="margin: 5px 0;"><strong>تاريخ العملية:</strong> {handover_record.handover_date.strftime('%Y-%m-%d') if handover_record.handover_date else 'غير محدد'}</p>
                        </div>
                        
                        {employee_info_html}
                        
                        <div style="text-align: right; margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                            <h3 style="margin-top: 0; color: #495057;">📊 تفاصيل إضافية</h3>
                            <p style="margin: 5px 0;"><strong>المسافة:</strong> {handover_record.mileage:,} كم</p>
                        </div>
                        
                        <p style="margin-top: 30px;">شاكرين لكم تعاونكم المستمر، وفي حال الحاجة لأي تفاصيل إضافية أو استفسارات، نحن في خدمتكم.</p>
                        <p>مع خالص التحية،</p>
                    </div>
                    
                    <div class="footer">
                        <p>نظام نُظم لإدارة الموظفين والمركبات</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # النص البديل
            text_content = f"""
نظام نُظم

السادة المعنيين، تحية طيبة وبعد،

مرفق لكم تفاصيل عملية استلام أو تسليم المركبة وفقاً للمعلومات التالية:

🔄 {operation_type_text} مركبة
• رقم السيارة: {vehicle_plate}
• نوع العملية: {operation_type_text}
• تاريخ العملية: {handover_record.handover_date.strftime('%Y-%m-%d') if handover_record.handover_date else 'غير محدد'}

{employee_info_text}

📊 تفاصيل إضافية
• المسافة: {handover_record.mileage:,} كم

شاكرين لكم تعاونكم المستمر، وفي حال الحاجة لأي تفاصيل إضافية أو استفسارات، نحن في خدمتكم.

مع خالص التحية،

---
نظام نُظم لإدارة الموظفين والمركبات
            """
            
            # إنشاء رسالة البريد الإلكتروني
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = formataddr(("نظام نُظم", sender_email))
            msg['To'] = formataddr((to_name, to_email))
            
            # إضافة المحتوى النصي والـ HTML
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # إضافة المرفقات (فقط إذا كانت موجودة)
            attachments_added = False
            current_app.logger.info(f"DEBUG .eml: excel_file_path={excel_file_path}, pdf_file_path={pdf_file_path}")
            
            if excel_file_path and os.path.exists(excel_file_path):
                try:
                    file_size = os.path.getsize(excel_file_path)
                    current_app.logger.info(f"DEBUG .eml: Found Excel file at {excel_file_path}, size: {file_size} bytes")
                    with open(excel_file_path, 'rb') as f:
                        attachment = MIMEApplication(f.read(), _subtype='xlsx')
                        attachment.add_header('Content-Disposition', 'attachment', 
                                            filename=f'{operation_type_text}_{vehicle_plate}_details.xlsx')
                        msg.attach(attachment)
                        attachments_added = True
                        current_app.logger.info(f"DEBUG .eml: Successfully attached Excel file")
                except Exception as e:
                    current_app.logger.warning(f"فشل في إرفاق ملف Excel: {str(e)}")
            else:
                current_app.logger.warning(f"DEBUG .eml: Excel file NOT found or path is None")
            
            if pdf_file_path and os.path.exists(pdf_file_path):
                try:
                    file_size = os.path.getsize(pdf_file_path)
                    current_app.logger.info(f"DEBUG .eml: Found PDF file at {pdf_file_path}, size: {file_size} bytes")
                    with open(pdf_file_path, 'rb') as f:
                        attachment = MIMEApplication(f.read(), _subtype='pdf')
                        attachment.add_header('Content-Disposition', 'attachment',
                                            filename=f'{operation_type_text}_{vehicle_plate}_document.pdf')
                        msg.attach(attachment)
                        attachments_added = True
                        current_app.logger.info(f"DEBUG .eml: Successfully attached PDF file")
                except Exception as e:
                    current_app.logger.warning(f"فشل في إرفاق ملف PDF: {str(e)}")
            else:
                current_app.logger.warning(f"DEBUG .eml: PDF file NOT found or path is None")
            
            # تحويل الرسالة إلى BytesIO
            eml_bytes = io.BytesIO()
            eml_bytes.write(msg.as_bytes())
            eml_bytes.seek(0)
            
            # اسم الملف
            filename = f'{operation_type_text}_{vehicle_plate}.eml'
            
            current_app.logger.info(f"تم إنشاء ملف .eml لعملية {operation_type_text} - {vehicle_plate}")
            
            return eml_bytes, filename
            
        except Exception as e:
            current_app.logger.error(f"خطأ في إنشاء ملف .eml: {str(e)}")
            return None, None