"""
وحدة إنشاء تقارير PDF باستخدام FPDF2 مع دعم كامل للغة العربية وتصميم احترافي
"""

import os
import io
from datetime import datetime
from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display

# تعريف مسار المجلد الحالي
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)

class ProfessionalArabicPDF(FPDF):
    """فئة PDF احترافية مع دعم كامل للغة العربية والتصميم الحديث"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_auto_page_break(auto=True, margin=20)
        
        # تسجيل الخطوط العربية
        font_path = os.path.join(PROJECT_DIR, 'static', 'fonts')
        
        try:
            # إضافة خط Tajawal (خط عصري للعناوين)
            self.add_font('Tajawal', '', os.path.join(font_path, 'Tajawal-Regular.ttf'), uni=True)
            self.add_font('Tajawal', 'B', os.path.join(font_path, 'Tajawal-Bold.ttf'), uni=True)
            
            # إضافة خط Amiri (خط تقليدي للنصوص)
            self.add_font('Amiri', '', os.path.join(font_path, 'Amiri-Regular.ttf'), uni=True)
            self.add_font('Amiri', 'B', os.path.join(font_path, 'Amiri-Bold.ttf'), uni=True)
            
            self.fonts_available = True
        except Exception as e:
            print(f"خطأ في تحميل الخطوط: {e}")
            self.fonts_available = False
        
        # تعريف الألوان المستخدمة في التصميم
        self.colors = {
            'primary': (41, 128, 185),       # أزرق أساسي
            'secondary': (52, 73, 94),       # رمادي غامق
            'success': (39, 174, 96),        # أخضر
            'warning': (243, 156, 18),       # برتقالي
            'danger': (231, 76, 60),         # أحمر
            'light_gray': (236, 240, 241),   # رمادي فاتح
            'white': (255, 255, 255),        # أبيض
            'black': (0, 0, 0),              # أسود
            'text_dark': (44, 62, 80),       # نص غامق
            'text_light': (127, 140, 141),   # نص فاتح
            'gradient_start': (74, 144, 226), # بداية التدرج
            'gradient_end': (80, 170, 200)   # نهاية التدرج
        }
    
    def arabic_text(self, txt):
        """إعادة تشكيل النص العربي وتحويله ليعرض بشكل صحيح"""
        if txt is None or txt == '':
            return ''
        
        # تخطي المعالجة لغير النصوص
        if not isinstance(txt, str):
            return str(txt)
        
        # تخطي معالجة الأرقام والتواريخ والأحرف الإنجليزية فقط
        if txt.replace('.', '', 1).replace(',', '', 1).replace('-', '', 1).isdigit() or all(c.isdigit() or c in '/-:. ' for c in txt):
            return txt
        
        # إذا كان النص إنجليزي فقط، لا نحتاج معالجة
        if all(ord(c) < 256 for c in txt):
            return txt
        
        try:
            # إعادة تشكيل النص العربي وتحويله إلى النمط المناسب للعرض
            reshaped_text = arabic_reshaper.reshape(txt)
            bidi_text = get_display(reshaped_text)
            return bidi_text
        except Exception as e:
            print(f"خطأ في معالجة النص العربي: {e}")
            return txt
    
    def cell(self, w=0, h=0, txt='', border=0, ln=0, align='', fill=False, link=''):
        """تجاوز دالة الخلية لدعم النص العربي"""
        arabic_txt = self.arabic_text(txt)
        super().cell(w, h, arabic_txt, border, ln, align, fill, link)
    
    def multi_cell(self, w=0, h=0, txt='', border=0, align='', fill=False):
        """تجاوز دالة الخلايا المتعددة لدعم النص العربي"""
        arabic_txt = self.arabic_text(txt)
        super().multi_cell(w, h, arabic_txt, border, align, fill)
    
    def set_color(self, color_name):
        """تعيين لون من مجموعة الألوان المحددة"""
        if color_name in self.colors:
            r, g, b = self.colors[color_name]
            self.set_text_color(r, g, b)
            return r, g, b
        return 0, 0, 0
    
    def set_fill_color_custom(self, color_name):
        """تعيين لون الخلفية من مجموعة الألوان المحددة"""
        if color_name in self.colors:
            r, g, b = self.colors[color_name]
            self.set_fill_color(r, g, b)
            return r, g, b
        return 255, 255, 255
    
    def draw_header_background(self):
        """رسم خلفية متدرجة لرأس الصفحة"""
        # رسم مستطيل متدرج للخلفية
        self.set_fill_color_custom('primary')
        self.rect(0, 0, 210, 60, 'F')
        
        # إضافة نمط هندسي خفيف
        self.set_draw_color(255, 255, 255)
        self.set_line_width(0.3)
        
        # رسم خطوط قطرية خفيفة بدلاً من الشفافية
        for i in range(0, 220, 30):
            self.line(i, 0, i+15, 60)
            
        # إضافة تأثير بصري بدلاً من الشفافية
        self.set_fill_color(255, 255, 255)
        # رسم مستطيلات صغيرة كنقاط زخرفية
        for x in range(20, 200, 40):
            for y in range(10, 50, 20):
                self.rect(x, y, 2, 2, 'F')
    
    def add_decorative_border(self, x, y, w, h, color='primary'):
        """إضافة حدود زخرفية ملونة"""
        r, g, b = self.set_fill_color_custom(color)
        
        # الحد العلوي
        self.rect(x, y, w, 2, 'F')
        # الحد السفلي
        self.rect(x, y + h - 2, w, 2, 'F')
        # الحد الأيسر
        self.rect(x, y, 2, h, 'F')
        # الحد الأيمن
        self.rect(x + w - 2, y, 2, h, 'F')
    
    def add_section_header(self, title, icon='■'):
        """إضافة رأس قسم مع تصميم احترافي"""
        current_y = self.get_y()
        
        # خلفية القسم
        self.set_fill_color_custom('light_gray')
        self.rect(10, current_y, 190, 12, 'F')
        
        # شريط ملون على اليسار
        self.set_fill_color_custom('primary')
        self.rect(10, current_y, 4, 12, 'F')
        
        # النص
        self.set_xy(20, current_y + 2)
        if self.fonts_available:
            self.set_font('Tajawal', 'B', 14)
        else:
            self.set_font('Arial', 'B', 14)
        
        self.set_color('text_dark')
        self.cell(0, 8, f'{icon} {title}', 0, 1, 'R')
        self.ln(3)


def calculate_days_in_workshop(entry_date, exit_date=None):
    """
    حساب عدد الأيام التي قضتها السيارة في الورشة
    
    Args:
        entry_date: تاريخ دخول الورشة
        exit_date: تاريخ خروج الورشة (إذا كان None، يعني أنها لا تزال في الورشة)
    
    Returns:
        int: عدد الأيام في الورشة
    """
    if not entry_date:
        return 0
    
    # إذا لم يكن هناك تاريخ خروج، نستخدم تاريخ اليوم
    end_date = exit_date if exit_date else datetime.now().date()
    
    # حساب الفرق بين التواريخ
    if isinstance(entry_date, datetime):
        entry_date = entry_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()
    
    # محاولة حساب الفرق
    try:
        days = (end_date - entry_date).days
        return max(0, days)  # لا يمكن أن يكون عدد الأيام سالبًا
    except:
        return 0


def generate_workshop_report_pdf_fpdf(vehicle, workshop_records):
    """
    إنشاء تقرير سجلات الورشة للمركبة باستخدام FPDF مع تصميم احترافي
    
    Args:
        vehicle: كائن المركبة
        workshop_records: قائمة بسجلات الورشة
    
    Returns:
        BytesIO: كائن بايت يحتوي على ملف PDF
    """
    # إنشاء كائن PDF مع دعم اللغة العربية
    pdf = ProfessionalArabicPDF(orientation='P', unit='mm', format='A4')
    pdf.set_title('تقرير سجلات الورشة')
    pdf.set_author('نُظم - نظام إدارة المركبات')
    
    # إضافة صفحة جديدة
    pdf.add_page()
    
    # ===== رأس الصفحة الاحترافي =====
    pdf.draw_header_background()
    
    # إضافة الشعار في رأس الصفحة
    possible_logo_paths = [
        os.path.join(PROJECT_DIR, 'static', 'images', 'logo', 'logo_new.png'),
        os.path.join(PROJECT_DIR, 'static', 'images', 'logo_new.png'),
        os.path.join(PROJECT_DIR, 'static', 'images', 'logo.png')
    ]
    
    # البحث عن أول ملف شعار موجود
    logo_path = None
    for path in possible_logo_paths:
        if os.path.exists(path):
            logo_path = path
            break
    
    # إذا وجدنا شعارًا، قم بإضافته
    if logo_path:
        try:
            pdf.image(logo_path, x=15, y=10, w=40, h=40)
        except:
            # إذا فشل تحميل الشعار، نرسم شعار نصي بديل
            pdf.set_fill_color(255, 255, 255)
            pdf.set_xy(15, 20)
            pdf.rect(15, 20, 40, 20, 'F')
            pdf.set_text_color(41, 128, 185)
            if pdf.fonts_available:
                pdf.set_font('Tajawal', 'B', 16)
            else:
                pdf.set_font('Arial', 'B', 16)
            pdf.set_xy(15, 25)
            pdf.cell(40, 10, 'نُظم', 0, 0, 'C')
    else:
        # شعار نصي بديل
        pdf.set_fill_color(255, 255, 255)
        pdf.rect(15, 15, 40, 30, 'F')
        pdf.set_text_color(41, 128, 185)
        if pdf.fonts_available:
            pdf.set_font('Tajawal', 'B', 20)
        else:
            pdf.set_font('Arial', 'B', 20)
        pdf.set_xy(15, 25)
        pdf.cell(40, 10, 'نُظم', 0, 0, 'C')
    
    # عنوان التقرير
    pdf.set_text_color(255, 255, 255)
    if pdf.fonts_available:
        pdf.set_font('Tajawal', 'B', 24)
    else:
        pdf.set_font('Arial', 'B', 24)
    pdf.set_xy(70, 15)
    pdf.cell(120, 12, 'تقرير سجلات الورشة', 0, 1, 'C')
    
    # معلومات السيارة في الرأس
    if pdf.fonts_available:
        pdf.set_font('Tajawal', 'B', 16)
    else:
        pdf.set_font('Arial', 'B', 16)
    pdf.set_xy(70, 30)
    pdf.cell(120, 10, f'{vehicle.make} {vehicle.model} - {vehicle.plate_number}', 0, 1, 'C')
    
    # تاريخ التقرير
    if pdf.fonts_available:
        pdf.set_font('Amiri', '', 12)
    else:
        pdf.set_font('Arial', '', 12)
    pdf.set_xy(70, 42)
    pdf.cell(120, 8, f'تاريخ التقرير: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
    
    # إعادة تعيين اللون للنص العادي
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(70)
    
    # ===== معلومات المركبة =====
    pdf.add_section_header('معلومات المركبة', '🚗')
    
    # جدول معلومات المركبة مع تصميم احترافي
    vehicle_info = [
        ['رقم اللوحة:', vehicle.plate_number or 'غير محدد'],
        ['الماركة:', vehicle.make or 'غير محدد'],
        ['الموديل:', vehicle.model or 'غير محدد'],
        ['سنة الصنع:', str(vehicle.year) if hasattr(vehicle, 'year') and vehicle.year else 'غير محدد']
    ]
    
    # إضافة معلومات إضافية إذا كانت متوفرة
    if hasattr(vehicle, 'vin') and vehicle.vin:
        vehicle_info.append(['رقم الهيكل:', vehicle.vin])
    
    if hasattr(vehicle, 'odometer') and vehicle.odometer:
        vehicle_info.append(['قراءة العداد:', f'{vehicle.odometer:,} كم'])
    
    # رسم جدول معلومات المركبة بتصميم حديث
    current_y = pdf.get_y()
    
    # خلفية الجدول
    pdf.set_fill_color_custom('white')
    pdf.rect(15, current_y, 180, len(vehicle_info) * 8 + 4, 'F')
    
    # حدود ملونة للجدول
    pdf.add_decorative_border(15, current_y, 180, len(vehicle_info) * 8 + 4)
    
    pdf.set_y(current_y + 2)
    
    for i, info in enumerate(vehicle_info):
        # تناوب ألوان الصفوف
        if i % 2 == 0:
            pdf.set_fill_color(248, 249, 250)
        else:
            pdf.set_fill_color(255, 255, 255)
        
        pdf.set_x(17)
        
        # العمود الأول (التسمية)
        if pdf.fonts_available:
            pdf.set_font('Tajawal', 'B', 11)
        else:
            pdf.set_font('Arial', 'B', 11)
        pdf.set_color('text_dark')
        pdf.cell(80, 8, info[0], 0, 0, 'R', True)
        
        # العمود الثاني (القيمة)
        if pdf.fonts_available:
            pdf.set_font('Amiri', '', 11)
        else:
            pdf.set_font('Arial', '', 11)
        pdf.set_color('primary')
        pdf.cell(96, 8, info[1], 0, 1, 'R', True)
    
    pdf.ln(10)
    
    # ===== سجلات الورشة =====
    pdf.add_section_header('سجلات الورشة', '🔧')
    
    # التحقق من وجود سجلات
    if not workshop_records or len(workshop_records) == 0:
        # رسالة عدم وجود سجلات مع تصميم جميل
        pdf.set_fill_color_custom('light_gray')
        pdf.rect(15, pdf.get_y(), 180, 30, 'F')
        
        pdf.add_decorative_border(15, pdf.get_y(), 180, 30, 'warning')
        
        if pdf.fonts_available:
            pdf.set_font('Tajawal', 'B', 14)
        else:
            pdf.set_font('Arial', 'B', 14)
        pdf.set_color('text_light')
        pdf.set_y(pdf.get_y() + 12)
        pdf.cell(0, 6, '⚠️ لا توجد سجلات ورشة لهذه المركبة', 0, 1, 'C')
        
        pdf.ln(15)
    else:
        # إحصائيات سريعة
        total_records = len(workshop_records)
        total_cost = sum(float(record.cost) if hasattr(record, 'cost') and record.cost else 0 for record in workshop_records)
        total_days = sum(calculate_days_in_workshop(
            record.entry_date if hasattr(record, 'entry_date') else None,
            record.exit_date if hasattr(record, 'exit_date') else None
        ) for record in workshop_records)
        
        # صندوق الإحصائيات
        stats_y = pdf.get_y()
        
        # خلفية الإحصائيات
        pdf.set_fill_color_custom('primary')
        pdf.rect(15, stats_y, 180, 25, 'F')
        
        pdf.set_text_color(255, 255, 255)
        if pdf.fonts_available:
            pdf.set_font('Tajawal', 'B', 12)
        else:
            pdf.set_font('Arial', 'B', 12)
        
        # توزيع الإحصائيات على ثلاثة أعمدة
        pdf.set_xy(20, stats_y + 5)
        pdf.cell(56, 6, f'📊 عدد السجلات: {total_records}', 0, 0, 'R')
        
        pdf.set_xy(76, stats_y + 5)
        pdf.cell(58, 6, f'💰 إجمالي التكلفة: {total_cost:,.0f} ريال', 0, 0, 'C')
        
        pdf.set_xy(134, stats_y + 5)
        pdf.cell(56, 6, f'📅 إجمالي الأيام: {total_days} يوم', 0, 0, 'L')
        
        # متوسطات
        avg_cost = total_cost / total_records if total_records > 0 else 0
        avg_days = total_days / total_records if total_records > 0 else 0
        
        pdf.set_xy(20, stats_y + 14)
        pdf.cell(80, 6, f'📈 متوسط التكلفة: {avg_cost:,.0f} ريال', 0, 0, 'R')
        
        pdf.set_xy(110, stats_y + 14)
        pdf.cell(70, 6, f'⏱️ متوسط المدة: {avg_days:.1f} يوم', 0, 0, 'L')
        
        pdf.set_y(stats_y + 30)
        pdf.set_text_color(0, 0, 0)
        
        # جدول السجلات
        pdf.ln(5)
        
        # تحديد عرض الأعمدة المحسن
        col_widths = [25, 20, 20, 15, 22, 30, 25, 23]
        headers = ['سبب الدخول', 'تاريخ الدخول', 'تاريخ الخروج', 'الأيام', 'حالة الإصلاح', 'اسم الورشة', 'الفني المسؤول', 'التكلفة (ريال)']
        
        # رأس الجدول مع تصميم احترافي
        header_y = pdf.get_y()
        
        # خلفية رأس الجدول
        pdf.set_fill_color_custom('secondary')
        pdf.rect(15, header_y, 180, 12, 'F')
        
        pdf.set_text_color(255, 255, 255)
        if pdf.fonts_available:
            pdf.set_font('Tajawal', 'B', 9)
        else:
            pdf.set_font('Arial', 'B', 9)
        
        # عناوين الأعمدة
        x_pos = 15
        pdf.set_y(header_y + 2)
        for i, header in enumerate(headers):
            pdf.set_x(x_pos)
            pdf.cell(col_widths[i], 8, header, 0, 0, 'C')
            x_pos += col_widths[i]
        
        pdf.ln(12)
        
        # بيانات الجدول
        pdf.set_text_color(0, 0, 0)
        
        # ترجمة القيم
        reason_map = {
            'maintenance': '🔧 صيانة دورية', 
            'breakdown': '⚠️ عطل', 
            'accident': '🚗 حادث'
        }
        status_map = {
            'in_progress': '🔄 قيد التنفيذ', 
            'completed': '✅ تم الإصلاح', 
            'pending_approval': '⏳ بانتظار الموافقة'
        }
        
        # تحديد ألوان الصفوف المتناوبة
        row_colors = [(248, 249, 250), (255, 255, 255)]
        
        for i, record in enumerate(workshop_records):
            row_y = pdf.get_y()
            
            # خلفية الصف
            color = row_colors[i % 2]
            pdf.set_fill_color(color[0], color[1], color[2])
            pdf.rect(15, row_y, 180, 10, 'F')
            
            # حدود خفيفة بين الصفوف
            if i > 0:
                pdf.set_draw_color(220, 220, 220)
                pdf.set_line_width(0.2)
                pdf.line(15, row_y, 195, row_y)
            
            if pdf.fonts_available:
                pdf.set_font('Amiri', '', 8)
            else:
                pdf.set_font('Arial', '', 8)
            
            # تحضير البيانات
            reason = reason_map.get(record.reason, record.reason) if hasattr(record, 'reason') and record.reason else 'غير محدد'
            entry_date = record.entry_date.strftime('%Y-%m-%d') if hasattr(record, 'entry_date') and record.entry_date else 'غير محدد'
            exit_date = record.exit_date.strftime('%Y-%m-%d') if hasattr(record, 'exit_date') and record.exit_date else '⏳ قيد الإصلاح'
            
            # حساب عدد الأيام
            days_count = 0
            if hasattr(record, 'entry_date') and record.entry_date:
                days_count = calculate_days_in_workshop(
                    record.entry_date, 
                    record.exit_date if hasattr(record, 'exit_date') and record.exit_date else None
                )
            
            status = status_map.get(record.repair_status, record.repair_status) if hasattr(record, 'repair_status') and record.repair_status else 'غير محدد'
            workshop_name = record.workshop_name if hasattr(record, 'workshop_name') and record.workshop_name else 'غير محدد'
            technician = record.technician_name if hasattr(record, 'technician_name') and record.technician_name else 'غير محدد'
            cost = f'{float(record.cost):,.0f}' if hasattr(record, 'cost') and record.cost else '0'
            
            # بيانات الصف
            row_data = [reason, entry_date, exit_date, str(days_count), status, workshop_name, technician, cost]
            
            # طباعة البيانات
            x_pos = 15
            pdf.set_y(row_y + 1)
            
            for j, data in enumerate(row_data):
                pdf.set_x(x_pos)
                
                # تلوين خاص لبعض الحقول
                if j == 0:  # سبب الدخول
                    if 'عطل' in data:
                        pdf.set_color('danger')
                    elif 'حادث' in data:
                        pdf.set_color('warning')
                    else:
                        pdf.set_color('success')
                elif j == 4:  # حالة الإصلاح
                    if 'تم' in data:
                        pdf.set_color('success')
                    elif 'قيد' in data:
                        pdf.set_color('warning')
                    else:
                        pdf.set_color('text_light')
                elif j == 7:  # التكلفة
                    pdf.set_color('primary')
                else:
                    pdf.set_color('text_dark')
                
                pdf.cell(col_widths[j], 8, data, 0, 0, 'C')
                x_pos += col_widths[j]
            
            pdf.ln(10)
            
            # فحص إذا كنا نحتاج صفحة جديدة
            if pdf.get_y() > 250:
                pdf.add_page()
                
                # إعادة رسم رأس الجدول في الصفحة الجديدة
                header_y = pdf.get_y()
                pdf.set_fill_color_custom('secondary')
                pdf.rect(15, header_y, 180, 12, 'F')
                
                pdf.set_text_color(255, 255, 255)
                if pdf.fonts_available:
                    pdf.set_font('Tajawal', 'B', 9)
                else:
                    pdf.set_font('Arial', 'B', 9)
                
                x_pos = 15
                pdf.set_y(header_y + 2)
                for k, header in enumerate(headers):
                    pdf.set_x(x_pos)
                    pdf.cell(col_widths[k], 8, header, 0, 0, 'C')
                    x_pos += col_widths[k]
                
                pdf.ln(12)
                pdf.set_text_color(0, 0, 0)
    
    # ===== تذييل الصفحة =====
    pdf.set_y(-35)
    
    # خط فاصل
    pdf.set_draw_color(41, 128, 185)  # اللون الأساسي
    pdf.set_line_width(1)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    
    pdf.ln(5)
    
    # معلومات النظام
    if pdf.fonts_available:
        pdf.set_font('Tajawal', 'B', 10)
    else:
        pdf.set_font('Arial', 'B', 10)
    pdf.set_color('primary')
    pdf.cell(0, 6, 'تم إنشاء هذا التقرير بواسطة نُظم - نظام إدارة المركبات والموظفين', 0, 1, 'C')
    
    if pdf.fonts_available:
        pdf.set_font('Amiri', '', 9)
    else:
        pdf.set_font('Arial', '', 9)
    pdf.set_color('text_light')
    pdf.cell(0, 5, f'تاريخ ووقت الإنشاء: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
    
    pdf.cell(0, 4, 'نُظم © 2025 - جميع الحقوق محفوظة', 0, 0, 'C')
    
    # حفظ PDF مع معالجة محسنة للأخطاء
    try:
        # حفظ PDF كسلسلة بايتات
        pdf_content = pdf.output(dest='S')
        
        # في FPDF2، نحتاج للتعامل مع أنواع مختلفة من المخرجات
        if isinstance(pdf_content, str):
            # إذا كان نص، نحوله إلى بايتات
            pdf_content = pdf_content.encode('latin-1')
        elif isinstance(pdf_content, bytearray):
            # إذا كان bytearray، نحوله إلى bytes
            pdf_content = bytes(pdf_content)
        elif isinstance(pdf_content, bytes):
            # إذا كان بالفعل bytes، لا نحتاج تحويل
            pass
        else:
            # حالة غير متوقعة - نحاول التحويل إلى bytes
            pdf_content = bytes(pdf_content)
        
        # وضع المحتوى في بفر الذاكرة
        pdf_buffer = io.BytesIO(pdf_content)
        pdf_buffer.seek(0)
        
        import logging
        logging.info(f"تم إنشاء PDF بنجاح بحجم: {len(pdf_content)} بايت")
        
        return pdf_buffer
        
    except Exception as e:
        import logging, traceback
        logging.error(f"خطأ عند إنشاء PDF: {str(e)}")
        logging.error(traceback.format_exc())
        
        # إذا فشلت الطريقة الأولى، نستخدم ملفًا مؤقتًا
        import tempfile
        
        fd, temp_path = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)
        
        try:
            # حفظ إلى ملف مؤقت
            pdf.output(temp_path)
            
            # قراءة المحتوى
            with open(temp_path, 'rb') as f:
                pdf_content = f.read()
            
            pdf_buffer = io.BytesIO(pdf_content)
            pdf_buffer.seek(0)
            
            return pdf_buffer
        
        finally:
            # تأكد من حذف الملف المؤقت حتى في حالة حدوث خطأ
            if os.path.exists(temp_path):
                os.unlink(temp_path)


def generate_safety_check_report_pdf(safety_check):
    """
    إنشاء تقرير فحص السلامة الخارجي باستخدام FPDF مع تصميم احترافي
    
    Args:
        safety_check: كائن فحص السلامة الخارجي
    
    Returns:
        BytesIO: كائن بايت يحتوي على ملف PDF
    """
    # إنشاء كائن PDF مع دعم اللغة العربية
    pdf = ProfessionalArabicPDF(orientation='P', unit='mm', format='A4')
    pdf.set_title('تقرير فحص السلامة الخارجي')
    pdf.set_author('نُظم - نظام إدارة المركبات')
    
    # إضافة صفحة جديدة
    pdf.add_page()
    
    # ===== رأس الصفحة الاحترافي =====
    pdf.draw_header_background()
    
    # إضافة الشعار في رأس الصفحة
    possible_logo_paths = [
        os.path.join(PROJECT_DIR, 'static', 'images', 'logo', 'logo_new.png'),
        os.path.join(PROJECT_DIR, 'static', 'images', 'logo_new.png'),
        os.path.join(PROJECT_DIR, 'static', 'images', 'logo.png')
    ]
    
    # البحث عن أول ملف شعار موجود
    logo_path = None
    for path in possible_logo_paths:
        if os.path.exists(path):
            logo_path = path
            break
    
    # إذا وجدنا شعارًا، قم بإضافته
    if logo_path:
        try:
            pdf.image(logo_path, x=15, y=10, w=40, h=40)
        except:
            # شعار نصي بديل
            pdf.set_fill_color(255, 255, 255)
            pdf.rect(15, 20, 40, 20, 'F')
            pdf.set_text_color(41, 128, 185)
            if pdf.fonts_available:
                pdf.set_font('Tajawal', 'B', 16)
            else:
                pdf.set_font('Arial', 'B', 16)
            pdf.set_xy(15, 25)
            pdf.cell(40, 10, 'نُظم', 0, 0, 'C')
    else:
        # شعار نصي بديل
        pdf.set_fill_color(255, 255, 255)
        pdf.rect(15, 15, 40, 30, 'F')
        pdf.set_text_color(41, 128, 185)
        if pdf.fonts_available:
            pdf.set_font('Tajawal', 'B', 20)
        else:
            pdf.set_font('Arial', 'B', 20)
        pdf.set_xy(15, 25)
        pdf.cell(40, 10, 'نُظم', 0, 0, 'C')
    
    # عنوان التقرير
    pdf.set_text_color(255, 255, 255)
    if pdf.fonts_available:
        pdf.set_font('Tajawal', 'B', 24)
    else:
        pdf.set_font('Arial', 'B', 24)
    pdf.set_xy(70, 15)
    pdf.cell(120, 12, 'تقرير فحص السلامة الخارجي', 0, 1, 'C')
    
    # رقم التقرير
    if pdf.fonts_available:
        pdf.set_font('Tajawal', 'B', 16)
    else:
        pdf.set_font('Arial', 'B', 16)
    pdf.set_xy(70, 30)
    pdf.cell(120, 10, f'رقم التقرير: {safety_check.id}', 0, 1, 'C')
    
    # تاريخ التقرير
    if pdf.fonts_available:
        pdf.set_font('Amiri', '', 12)
    else:
        pdf.set_font('Arial', '', 12)
    pdf.set_xy(70, 42)
    pdf.cell(120, 8, f'تاريخ الفحص: {safety_check.inspection_date.strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
    
    # إعادة تعيين اللون للنص العادي
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(70)
    
    # ===== معلومات السيارة =====
    pdf.add_section_header('معلومات السيارة', '🚗')
    
    # جدول معلومات السيارة
    vehicle_info = [
        ['رقم اللوحة:', safety_check.vehicle_plate_number or 'غير محدد'],
        ['نوع السيارة:', safety_check.vehicle_make_model or 'غير محدد'],
        ['المفوض الحالي:', safety_check.current_delegate or 'غير محدد']
    ]
    
    # رسم جدول معلومات السيارة
    current_y = pdf.get_y()
    pdf.set_fill_color_custom('white')
    pdf.rect(15, current_y, 180, len(vehicle_info) * 8 + 4, 'F')
    pdf.add_decorative_border(15, current_y, 180, len(vehicle_info) * 8 + 4)
    pdf.set_y(current_y + 2)
    
    for i, info in enumerate(vehicle_info):
        if i % 2 == 0:
            pdf.set_fill_color(248, 249, 250)
        else:
            pdf.set_fill_color(255, 255, 255)
        
        pdf.set_x(17)
        if pdf.fonts_available:
            pdf.set_font('Tajawal', 'B', 11)
        else:
            pdf.set_font('Arial', 'B', 11)
        pdf.set_color('text_dark')
        pdf.cell(80, 8, info[0], 0, 0, 'R', True)
        
        if pdf.fonts_available:
            pdf.set_font('Amiri', '', 11)
        else:
            pdf.set_font('Arial', '', 11)
        pdf.set_color('primary')
        pdf.cell(96, 8, info[1], 0, 1, 'R', True)
    
    pdf.ln(10)
    
    # ===== معلومات السائق =====
    pdf.add_section_header('معلومات السائق', '👤')
    
    # جدول معلومات السائق
    driver_info = [
        ['اسم السائق:', safety_check.driver_name or 'غير محدد'],
        ['رقم الهوية:', safety_check.driver_national_id or 'غير محدد'],
        ['القسم:', safety_check.driver_department or 'غير محدد'],
        ['المدينة:', safety_check.driver_city or 'غير محدد']
    ]
    
    # رسم جدول معلومات السائق
    current_y = pdf.get_y()
    pdf.set_fill_color_custom('white')
    pdf.rect(15, current_y, 180, len(driver_info) * 8 + 4, 'F')
    pdf.add_decorative_border(15, current_y, 180, len(driver_info) * 8 + 4, 'success')
    pdf.set_y(current_y + 2)
    
    for i, info in enumerate(driver_info):
        if i % 2 == 0:
            pdf.set_fill_color(248, 249, 250)
        else:
            pdf.set_fill_color(255, 255, 255)
        
        pdf.set_x(17)
        if pdf.fonts_available:
            pdf.set_font('Tajawal', 'B', 11)
        else:
            pdf.set_font('Arial', 'B', 11)
        pdf.set_color('text_dark')
        pdf.cell(80, 8, info[0], 0, 0, 'R', True)
        
        if pdf.fonts_available:
            pdf.set_font('Amiri', '', 11)
        else:
            pdf.set_font('Arial', '', 11)
        pdf.set_color('success')
        pdf.cell(96, 8, info[1], 0, 1, 'R', True)
    
    pdf.ln(10)
    
    # ===== الملاحظات =====
    if safety_check.notes:
        pdf.add_section_header('الملاحظات والتوصيات', '📋')
        
        current_y = pdf.get_y()
        pdf.set_fill_color(235, 248, 255)
        pdf.rect(15, current_y, 180, 30, 'F')
        pdf.add_decorative_border(15, current_y, 180, 30, 'primary')
        
        if pdf.fonts_available:
            pdf.set_font('Amiri', '', 11)
        else:
            pdf.set_font('Arial', '', 11)
        pdf.set_color('text_dark')
        pdf.set_xy(20, current_y + 5)
        pdf.multi_cell(170, 6, safety_check.notes, 0, 'R')
        pdf.ln(5)
    
    # ===== حالة الاعتماد =====
    if hasattr(safety_check, 'approved_by') and safety_check.approved_by:
        pdf.add_section_header('حالة الاعتماد', '✅')
        
        status_color = 'success' if safety_check.approval_status == 'approved' else 'danger'
        status_text = 'معتمدة ✓' if safety_check.approval_status == 'approved' else 'مرفوضة ✗'
        
        current_y = pdf.get_y()
        pdf.set_fill_color_custom(status_color)
        pdf.rect(15, current_y, 180, 12, 'F')
        
        pdf.set_text_color(255, 255, 255)
        if pdf.fonts_available:
            pdf.set_font('Tajawal', 'B', 14)
        else:
            pdf.set_font('Arial', 'B', 14)
        pdf.set_xy(15, current_y + 2)
        pdf.cell(180, 8, f'الحالة: {status_text}', 0, 1, 'C')
        pdf.ln(5)
    
    # ===== صور فحص السلامة =====
    if hasattr(safety_check, 'safety_images') and safety_check.safety_images:
        pdf.add_section_header(f'صور فحص السلامة ({len(safety_check.safety_images)} صورة)', '📷')
        
        for i, image in enumerate(safety_check.safety_images):
            try:
                # المسار الكامل للصورة
                image_path = image.image_path
                if not image_path.startswith('/'):
                    image_path = os.path.join(PROJECT_DIR, image_path)
                
                # التحقق من وجود الصورة
                if os.path.exists(image_path):
                    # إضافة صفحة جديدة لكل صورة بعد الأولى
                    if i > 0:
                        pdf.add_page()
                        pdf.ln(10)
                    
                    # عنوان الصورة
                    description = image.image_description or f'صورة رقم {i+1}'
                    if pdf.fonts_available:
                        pdf.set_font('Tajawal', 'B', 14)
                    else:
                        pdf.set_font('Arial', 'B', 14)
                    pdf.set_color('primary')
                    pdf.cell(0, 10, description, 0, 1, 'C')
                    pdf.ln(5)
                    
                    # الحصول على أبعاد الصورة الأصلية
                    from PIL import Image as PILImage
                    try:
                        with PILImage.open(image_path) as img:
                            original_width, original_height = img.size
                    except:
                        original_width, original_height = 800, 600
                    
                    # حساب الأبعاد المناسبة مع الحفاظ على نسبة العرض إلى الارتفاع
                    max_width = 170  # عرض الصفحة - الهوامش
                    max_height = 200  # ارتفاع مناسب
                    
                    # حساب النسبة
                    width_ratio = max_width / original_width
                    height_ratio = max_height / original_height
                    ratio = min(width_ratio, height_ratio)
                    
                    # الأبعاد النهائية
                    final_width = original_width * ratio
                    final_height = original_height * ratio
                    
                    # مركز الصورة
                    x_position = (210 - final_width) / 2
                    y_position = pdf.get_y()
                    
                    # رسم إطار جميل حول الصورة
                    pdf.set_draw_color(41, 128, 185)
                    pdf.set_line_width(0.5)
                    pdf.rect(x_position - 2, y_position - 2, final_width + 4, final_height + 4)
                    
                    # إضافة ظل خفيف
                    pdf.set_fill_color(200, 200, 200)
                    pdf.rect(x_position + 2, y_position + 2, final_width + 4, final_height + 4, 'F')
                    
                    # إضافة الصورة
                    pdf.image(image_path, x_position, y_position, final_width, final_height)
                    
                    # مساحة بعد الصورة
                    pdf.set_y(y_position + final_height + 5)
                    
            except Exception as e:
                import logging
                logging.error(f"خطأ في إضافة الصورة: {str(e)}")
                # عرض رسالة خطأ في PDF
                pdf.set_color('danger')
                if pdf.fonts_available:
                    pdf.set_font('Amiri', '', 11)
                else:
                    pdf.set_font('Arial', '', 11)
                pdf.cell(0, 10, f'تعذر تحميل الصورة رقم {i+1}', 0, 1, 'C')
                continue
    
    # ===== تذييل التقرير =====
    pdf.set_y(-30)
    pdf.set_draw_color(41, 128, 185)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)
    
    if pdf.fonts_available:
        pdf.set_font('Amiri', '', 10)
    else:
        pdf.set_font('Arial', '', 10)
    pdf.set_color('text_light')
    pdf.cell(0, 6, f'تاريخ إنشاء التقرير: {datetime.now().strftime("%Y-%m-%d | %H:%M")}', 0, 1, 'C')
    pdf.cell(0, 5, 'نُظم - نظام إدارة المركبات والموظفين الشامل', 0, 1, 'C')
    pdf.cell(0, 5, 'تم إنشاؤه آلياً من النظام', 0, 0, 'C')
    
    # حفظ PDF إلى buffer
    pdf_buffer = io.BytesIO()
    try:
        pdf_content = pdf.output(dest='S').encode('latin1')
        pdf_buffer.write(pdf_content)
        pdf_buffer.seek(0)
        return pdf_buffer
    except Exception as e:
        import logging, traceback, tempfile
        logging.error(f"خطأ عند إنشاء PDF: {str(e)}")
        logging.error(traceback.format_exc())
        
        fd, temp_path = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)
        
        try:
            pdf.output(temp_path)
            with open(temp_path, 'rb') as f:
                pdf_content = f.read()
            pdf_buffer = io.BytesIO(pdf_content)
            pdf_buffer.seek(0)
            return pdf_buffer
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)