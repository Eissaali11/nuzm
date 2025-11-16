"""
مولد PDF عربي محسن لتسليم المركبات مع معالجة متقدمة للنصوص
"""

import os
from io import BytesIO
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def safe_arabic_text(text):
    """
    تحويل النص العربي إلى نص آمن للعرض في PDF
    """
    if not text:
        return "Not Available"
    
    # قاموس تحويل النصوص العربية الشائعة
    arabic_translations = {
        'وثيقة تسليم واستلام المركبة': 'Vehicle Handover Document',
        'رقم الوثيقة': 'Document ID',
        'تاريخ الإنشاء': 'Creation Date',
        'نوع العملية': 'Operation Type',
        'تسليم': 'Delivery',
        'استلام': 'Return',
        'معلومات المركبة': 'Vehicle Information',
        'رقم اللوحة': 'Plate Number',
        'الصنع': 'Make',
        'الموديل': 'Model',
        'السنة': 'Year',
        'اللون': 'Color',
        'تفاصيل التسليم': 'Handover Details',
        'التاريخ': 'Date',
        'الوقت': 'Time',
        'اسم الشخص': 'Person Name',
        'رقم الهاتف': 'Phone Number',
        'قراءة العداد': 'Odometer Reading',
        'مستوى الوقود': 'Fuel Level',
        'معدات المركبة': 'Vehicle Equipment',
        'الإطار الاحتياطي': 'Spare Tire',
        'طفاية الحريق': 'Fire Extinguisher',
        'حقيبة الإسعافات الأولية': 'First Aid Kit',
        'مثلث التحذير': 'Warning Triangle',
        'عدة الأدوات': 'Tool Kit',
        'ملاحظات إضافية': 'Additional Notes',
        'توقيع المسلم': 'Deliverer Signature',
        'توقيع المستلم': 'Receiver Signature',
        'غير محدد': 'Not Specified',
        'غير متوفرة': 'Not Available'
    }
    
    # البحث عن ترجمة مباشرة
    if str(text) in arabic_translations:
        return arabic_translations[str(text)]
    
    # فحص وجود أحرف عربية
    has_arabic = any('\u0600' <= char <= '\u06FF' for char in str(text))
    
    if has_arabic:
        # ترجمة الأسماء العربية الشائعة
        name_translations = {
            'محمد': 'Mohammed',
            'أحمد': 'Ahmed',
            'علي': 'Ali',
            'عبدالله': 'Abdullah',
            'فاطمة': 'Fatima',
            'عائشة': 'Aisha',
            'خديجة': 'Khadija',
            'سارة': 'Sarah',
            'مريم': 'Mariam',
            'نورا': 'Nora'
        }
        
        if str(text) in name_translations:
            return name_translations[str(text)]
        
        # إزالة الأحرف العربية كحل أخير
        cleaned = ''.join(char for char in str(text) if ord(char) < 128)
        return cleaned.strip() or "Arabic Text"
    
    return str(text)

def create_vehicle_handover_pdf(handover_data):
    """
    إنشاء PDF محسن لتسليم المركبة بنصوص آمنة
    """
    try:
        print("Starting enhanced Arabic handover PDF generation...")
        
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # الألوان الاحترافية
        primary_color = colors.HexColor('#2E86AB')
        secondary_color = colors.HexColor('#A23B72')
        accent_color = colors.HexColor('#F18F01')
        
        # شعار الشركة
        try:
            logo_path = os.path.join(os.path.dirname(__file__), '..', 'attached_assets', 'logo.png')
            if os.path.exists(logo_path):
                c.drawImage(logo_path, 50, height - 80, width=60, height=40, preserveAspectRatio=True)
        except:
            pass
        
        # العنوان الرئيسي
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(primary_color)
        title = safe_arabic_text("وثيقة تسليم واستلام المركبة")
        title_width = c.stringWidth(title, "Helvetica-Bold", 18)
        c.drawString((width - title_width)/2, height - 60, title)
        
        # صندوق معلومات الوثيقة الأساسية
        c.setStrokeColor(primary_color)
        c.setLineWidth(2)
        c.rect(50, height - 180, 500, 100)
        
        # معلومات الوثيقة
        y_position = height - 50
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        
        # الحصول على رابط النموذج الإلكتروني من البيانات
        form_link = getattr(handover_data, 'form_link', None)
        
        # الحصول على اسم الشخص ورقم المركبة
        person_name = getattr(handover_data, 'person_name', 'غير محدد')
        # التعامل مع ربط المركبة
        if hasattr(handover_data, 'vehicle') and handover_data.vehicle:
            vehicle_number = getattr(handover_data.vehicle, 'plate_number', 'غير محدد')
        else:
            vehicle_number = getattr(handover_data, 'vehicle_plate_number', 'غير محدد')
        
        doc_info = [
            f"Document ID: {getattr(handover_data, 'id', 85)}",
            f"Date: {datetime.now().strftime('%Y-%m-%d')}",
            f"Time: {datetime.now().strftime('%H:%M')}",
            "Operation: Return",
            f"Vehicle: {vehicle_number} - {person_name}"
        ]
        
        # عرض المعلومات في الصندوق الموحد
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.black)
        
        # القسم الأيسر - المعلومات الأساسية
        basic_info = [
            f"Document ID: {handover_data.id}",
            f"Type: {'Delivery' if handover_data.handover_type == 'delivery' else 'Return'}",
            "Operation: Return",
            f"Vehicle: {vehicle_number} - {person_name}"
        ]
        
        for i, info in enumerate(basic_info):
            y_pos = height - 100 - (i * 12)
            c.drawString(60, y_pos, info)
        
        # القسم الأيمن - الرابط الإلكتروني
        if form_link and form_link.strip():
            # عنوان القسم
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(colors.blue)
            c.drawString(320, height - 100, "Electronic Form Link:")
            
            # استخراج الرابط الفعلي
            if 'https://' in form_link:
                url_start = form_link.find('https://')
                url_part = form_link[url_start:].split(' ')[0]
                text_part = form_link.replace(url_part, '').strip()
                
                # عرض الرابط باللون الأزرق وقابل للنقر
                c.setFont("Helvetica", 7)
                c.setFillColor(colors.blue)
                
                # تقسيم الرابط إلى أجزاء للعرض
                max_chars = 30
                url_lines = [url_part[i:i+max_chars] for i in range(0, len(url_part), max_chars)]
                
                for i, line in enumerate(url_lines):
                    y_pos = height - 115 - (i * 10)
                    c.drawString(320, y_pos, line)
                    # إضافة منطقة قابلة للنقر على كامل الرابط
                    if i == 0:
                        # إنشاء منطقة قابلة للنقر تغطي كل أجزاء الرابط
                        link_height = len(url_lines) * 10
                        c.linkURL(url_part, (320, y_pos - link_height + 8, 540, y_pos + 12))
                
                # عرض النص الإضافي إن وجد
                if text_part:
                    c.setFont("Helvetica", 6)
                    c.setFillColor(colors.darkgray)
                    c.drawString(320, height - 115 - (len(url_lines) * 10) - 8, f"Description: {text_part[:25]}")
            else:
                # عرض النص كما هو
                c.setFont("Helvetica", 7)
                c.setFillColor(colors.black)
                wrapped_link = [form_link[i:i+30] for i in range(0, len(form_link), 30)]
                for i, line in enumerate(wrapped_link):
                    c.drawString(320, height - 115 - (i * 10), line)
        else:
            # عرض رسالة عدم وجود رابط
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(colors.gray)
            c.drawString(320, height - 100, "Electronic Form Link:")
            c.setFont("Helvetica", 7)
            c.drawString(320, height - 115, "Not Available")
        
        c.setFillColor(colors.black)  # إعادة اللون الأسود
        
        # خط فاصل
        y_position = height - 170
        c.setStrokeColor(primary_color)
        c.setLineWidth(2)
        c.line(50, y_position, width - 50, y_position)
        
        # معلومات المركبة
        y_position -= 40
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(secondary_color)
        vehicle_title = safe_arabic_text("معلومات المركبة")
        c.drawString(50, y_position, vehicle_title)
        
        # جدول معلومات المركبة المفصل
        vehicle_data = []
        if hasattr(handover_data, 'vehicle_rel') and handover_data.vehicle_rel:
            vehicle = handover_data.vehicle_rel
            vehicle_data = [
                [safe_arabic_text("رقم اللوحة"), safe_arabic_text(str(vehicle.plate_number) if vehicle.plate_number else "Not Specified")],
                [safe_arabic_text("الصنع"), safe_arabic_text(str(vehicle.make) if vehicle.make else "Not Specified")],
                [safe_arabic_text("الموديل"), safe_arabic_text(str(vehicle.model) if vehicle.model else "Not Specified")],
                [safe_arabic_text("السنة"), safe_arabic_text(str(vehicle.year) if hasattr(vehicle, 'year') and vehicle.year else "Not Specified")],
                [safe_arabic_text("اللون"), safe_arabic_text(str(vehicle.color) if hasattr(vehicle, 'color') and vehicle.color else "Not Specified")],
                ["VIN Number", safe_arabic_text(str(vehicle.vin_number) if hasattr(vehicle, 'vin_number') and vehicle.vin_number else "Not Available")],
                ["Engine Number", safe_arabic_text(str(vehicle.engine_number) if hasattr(vehicle, 'engine_number') and vehicle.engine_number else "Not Available")],
                ["Vehicle Status", safe_arabic_text(str(vehicle.status) if hasattr(vehicle, 'status') and vehicle.status else "Active")]
            ]
        else:
            vehicle_data = [[safe_arabic_text("معلومات المركبة"), safe_arabic_text("غير متوفرة")]]
        
        # إنشاء جدول المركبة مع تحسين التخطيط
        vehicle_table = Table(vehicle_data, colWidths=[2.2*inch, 2.8*inch])
        vehicle_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        table_width, table_height = vehicle_table.wrap(width, height)
        y_position -= 30
        vehicle_table.drawOn(c, 50, y_position - table_height)
        y_position -= table_height + 30
        
        # تفاصيل التسليم
        y_position -= 40
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(secondary_color)
        handover_title = safe_arabic_text("تفاصيل التسليم")
        c.drawString(50, y_position, handover_title)
        
        # الحصول على بيانات الموظف إذا كان موجوداً
        employee_data = None
        if handover_data.employee_id:
            try:
                from models import Employee
                employee_data = Employee.query.get(handover_data.employee_id)
                print(f"DEBUG: Found employee by ID {handover_data.employee_id}: {employee_data}")
            except Exception as e:
                print(f"DEBUG: Error finding employee by ID: {str(e)}")
                pass
        
        # إذا لم يكن هناك employee_id، حاول البحث بالاسم
        if not employee_data and handover_data.person_name:
            try:
                from models import Employee
                employee_data = Employee.query.filter_by(name=handover_data.person_name).first()
                print(f"DEBUG: Found employee by name '{handover_data.person_name}': {employee_data}")
                if employee_data:
                    print(f"DEBUG: Employee data - ID: {employee_data.employee_id}, National ID: {employee_data.national_id}, Mobile: {employee_data.mobile}, MobilePersonal: {employee_data.mobilePersonal}")
            except Exception as e:
                print(f"DEBUG: Error finding employee by name: {str(e)}")
                pass
        
        print(f"DEBUG: Final employee_data: {employee_data}")
        
        # جدول تفاصيل التسليم المفصل مع بيانات الموظف الكاملة
        handover_details = [
            [safe_arabic_text("التاريخ"), safe_arabic_text(handover_data.handover_date.strftime('%Y-%m-%d') if handover_data.handover_date else "Not Specified")],
            [safe_arabic_text("الوقت"), safe_arabic_text(handover_data.handover_date.strftime('%H:%M') if handover_data.handover_date else "Not Specified")],
            [safe_arabic_text("اسم السائق"), safe_arabic_text(str(handover_data.person_name) if handover_data.person_name else "Not Specified")],
        ]
        
        # إضافة بيانات الموظف إذا كانت متوفرة
        if employee_data:
            # رقم الموظف (employee_id في قاعدة البيانات)
            if hasattr(employee_data, 'employee_id') and employee_data.employee_id:
                handover_details.append(["Company No", safe_arabic_text(str(employee_data.employee_id))])
            
            # رقم الإقامة (national_id في قاعدة البيانات)
            if hasattr(employee_data, 'national_id') and employee_data.national_id:
                handover_details.append(["Residency No", safe_arabic_text(str(employee_data.national_id))])
            
            # رقم الجوال الشخصي (mobilePersonal في قاعدة البيانات)
            if hasattr(employee_data, 'mobilePersonal') and employee_data.mobilePersonal:
                handover_details.append(["Personal Phone", safe_arabic_text(str(employee_data.mobilePersonal))])
            
            # رقم جوال العمل (mobile في قاعدة البيانات)
            if hasattr(employee_data, 'mobile') and employee_data.mobile:
                handover_details.append(["Work Phone", safe_arabic_text(str(employee_data.mobile))])
            
            # القسم
            if hasattr(employee_data, 'department') and employee_data.department:
                if hasattr(employee_data.department, 'name'):
                    handover_details.append(["Department", safe_arabic_text(str(employee_data.department.name))])
        
        # معلومات إضافية عن العملية
        handover_details.extend([
            ["Supervisor", safe_arabic_text(str(handover_data.supervisor_name) if handover_data.supervisor_name else "Not Specified")],
            [safe_arabic_text("قراءة العداد"), safe_arabic_text(f"{handover_data.mileage} km" if handover_data.mileage else "Not Specified")],
            [safe_arabic_text("مستوى الوقود"), safe_arabic_text(f"{handover_data.fuel_level}%" if handover_data.fuel_level else "Not Specified")],
            ["Vehicle Status", safe_arabic_text(str(handover_data.vehicle_status_summary) if hasattr(handover_data, 'vehicle_status_summary') and handover_data.vehicle_status_summary else "Normal")]
        ])
        
        handover_table = Table(handover_details, colWidths=[2.2*inch, 2.8*inch])
        handover_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('BACKGROUND', (1, 0), (1, -1), colors.lightcyan),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        table_width, table_height = handover_table.wrap(width, height)
        y_position -= 30
        handover_table.drawOn(c, 50, y_position - table_height)
        y_position -= table_height + 30
        
        # قائمة تحقق المعدات
        y_position -= 50
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(secondary_color)
        equipment_title = safe_arabic_text("معدات المركبة")
        c.drawString(50, y_position, equipment_title)
        
        # جلب قائمة معدات المركبة من البيانات الفعلية
        equipment_items = [
            (safe_arabic_text("الإطار الاحتياطي"), getattr(handover_data, 'has_spare_tire', False)),
            (safe_arabic_text("طفاية الحريق"), getattr(handover_data, 'has_fire_extinguisher', False)),
            (safe_arabic_text("حقيبة الإسعافات الأولية"), getattr(handover_data, 'has_first_aid_kit', False)),
            (safe_arabic_text("مثلث التحذير"), getattr(handover_data, 'has_warning_triangle', False)),
            (safe_arabic_text("عدة الأدوات"), getattr(handover_data, 'has_tools', False))
        ]
        
        y_position -= 30
        c.setFont("Helvetica", 10)
        
        for item, available in equipment_items:
            # رمز الحالة
            status_color = colors.green if available else colors.red
            status_text = "✓" if available else "✗"
            c.setFillColor(status_color)
            c.drawString(50, y_position, status_text)
            
            # نص المعدات
            c.setFillColor(colors.black)
            c.drawString(70, y_position, item)
            y_position -= 20
        
        # قسم الملاحظات
        y_position -= 30
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(secondary_color)
        notes_title = safe_arabic_text("ملاحظات إضافية")
        c.drawString(50, y_position, notes_title)
        
        # مربع الملاحظات
        y_position -= 30
        c.setStrokeColor(colors.grey)
        c.setLineWidth(1)
        c.rect(50, y_position - 80, width - 100, 70)
        
        # نص الملاحظات
        if handover_data.notes:
            c.setFont("Helvetica", 10)
            c.setFillColor(colors.black)
            notes_text = safe_arabic_text(str(handover_data.notes))
            c.drawString(60, y_position - 20, notes_text)
        
        # قسم التوقيعات
        y_position -= 100
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.black)
        
        # جدول التوقيعات
        signature_data = [
            [safe_arabic_text("توقيع المسلم"), safe_arabic_text("توقيع المستلم")],
            ["", ""],
            [safe_arabic_text("التاريخ") + ": ___________", safe_arabic_text("التاريخ") + ": ___________"]
        ]
        
        signature_table = Table(signature_data, colWidths=[2.4*inch, 2.4*inch], rowHeights=[25, 50, 25])
        signature_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        table_width, table_height = signature_table.wrap(width, height)
        y_position -= 30
        signature_table.drawOn(c, 50, y_position - table_height)
        
        # تذييل الصفحة
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.grey)
        footer_text = f"Generated by Nuzum Vehicle Management System - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        footer_width = c.stringWidth(footer_text, "Helvetica", 8)
        c.drawString((width - footer_width)/2, 30, footer_text)
        
        # إطار الصفحة
        c.setStrokeColor(primary_color)
        c.setLineWidth(2)
        c.rect(30, 20, width - 60, height - 40)
        
        c.save()
        buffer.seek(0)
        
        print("Enhanced Arabic handover PDF generated successfully!")
        return buffer
        
    except Exception as e:
        print(f"Error generating enhanced Arabic handover PDF: {str(e)}")
        # في حالة الفشل، استخدم النسخة الإنجليزية
        from utils.professional_handover_pdf import create_vehicle_handover_pdf as create_english_pdf
        return create_english_pdf(handover_data)