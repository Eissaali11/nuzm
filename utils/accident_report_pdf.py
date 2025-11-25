"""
مولد PDF احترافي لتقارير حوادث المركبات
يتضمن جميع البيانات والصور والوثائق
"""

import os
from fpdf import FPDF
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image
import io

PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))


class AccidentReportPDF(FPDF):
    """فئة PDF احترافية لتقارير الحوادث مع دعم كامل للعربية"""
    
    def __init__(self, accident):
        super().__init__('P', 'mm', 'A4')
        self.accident = accident
        self.set_auto_page_break(auto=True, margin=20)
        
        # تسجيل الخطوط العربية
        font_path = os.path.join(PROJECT_DIR, 'static', 'fonts')
        
        try:
            self.add_font('Cairo', '', os.path.join(font_path, 'Cairo-Regular.ttf'), uni=True)
            self.add_font('Cairo', 'B', os.path.join(font_path, 'Cairo-Bold.ttf'), uni=True)
            self.fonts_available = True
        except Exception as e:
            print(f"خطأ في تحميل الخطوط: {e}")
            self.fonts_available = False
        
        # الألوان
        self.colors = {
            'primary': (41, 128, 185),
            'danger': (231, 76, 60),
            'warning': (243, 156, 18),
            'success': (39, 174, 96),
            'dark': (44, 62, 80),
            'light_gray': (236, 240, 241),
        }
    
    def arabic_text(self, text):
        """معالجة النص العربي للعرض الصحيح"""
        if not text:
            return ''
        try:
            reshaped = arabic_reshaper.reshape(str(text))
            return get_display(reshaped)
        except:
            return str(text)
    
    def header(self):
        """رأس كل صفحة"""
        # الشعار
        logo_path = os.path.join(PROJECT_DIR, 'static', 'images', 'logo.png')
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 30)
        
        # العنوان الرئيسي
        self.set_font('Cairo', 'B', 20)
        self.set_text_color(*self.colors['primary'])
        self.cell(0, 15, self.arabic_text('تقرير حادث مركبة'), 0, 1, 'C')
        
        # خط فاصل
        self.set_draw_color(*self.colors['primary'])
        self.set_line_width(0.5)
        self.line(10, 30, 200, 30)
        
        self.ln(5)
    
    def footer(self):
        """تذييل كل صفحة"""
        self.set_y(-15)
        self.set_font('Cairo', '', 8)
        self.set_text_color(128, 128, 128)
        
        # رقم الصفحة
        page_text = self.arabic_text(f'صفحة {self.page_no()}/{{nb}}')
        self.cell(0, 10, page_text, 0, 0, 'C')
        
        # التاريخ
        date_text = self.arabic_text(f'طُبع في: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
        self.cell(0, 10, date_text, 0, 0, 'L')
    
    def add_section_title(self, title, icon=''):
        """إضافة عنوان قسم"""
        self.ln(3)
        self.set_fill_color(*self.colors['primary'])
        self.set_text_color(255, 255, 255)
        self.set_font('Cairo', 'B', 14)
        
        full_title = f'{icon} {title}' if icon else title
        self.cell(0, 10, self.arabic_text(full_title), 0, 1, 'R', True)
        self.set_text_color(0, 0, 0)
        self.ln(2)
    
    def add_field(self, label, value, width=95):
        """إضافة حقل بيانات"""
        self.set_font('Cairo', '', 11)
        
        # القيمة
        value_str = str(value) if value else '-'
        self.cell(width, 8, self.arabic_text(value_str), 1, 0, 'R')
        
        # التسمية
        self.set_font('Cairo', 'B', 11)
        self.set_fill_color(*self.colors['light_gray'])
        self.cell(width, 8, self.arabic_text(label), 1, 1, 'R', True)
    
    def add_status_badge(self, status):
        """إضافة شارة الحالة"""
        status_colors = {
            'pending': self.colors['warning'],
            'under_review': self.colors['primary'],
            'approved': self.colors['success'],
            'rejected': self.colors['danger']
        }
        
        status_text = {
            'pending': 'قيد الانتظار',
            'under_review': 'قيد المراجعة',
            'approved': 'معتمد',
            'rejected': 'مرفوض'
        }
        
        color = status_colors.get(status, self.colors['dark'])
        text = status_text.get(status, status)
        
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.set_font('Cairo', 'B', 12)
        self.cell(60, 10, self.arabic_text(text), 0, 1, 'C', True)
        self.set_text_color(0, 0, 0)
    
    def add_document_image(self, image_path, title, width=85):
        """إضافة صورة وثيقة أو رابط لملف PDF"""
        full_path = os.path.join(PROJECT_DIR, 'static', image_path) if not image_path.startswith('/') else image_path
        
        if not os.path.exists(full_path):
            return False
        
        # العنوان
        self.set_font('Cairo', 'B', 10)
        self.cell(width, 6, self.arabic_text(title), 0, 1, 'C')
        
        # التحقق من نوع الملف
        file_ext = os.path.splitext(full_path)[1].lower()
        
        if file_ext == '.pdf':
            # ملف PDF - إضافة رابط مع أيقونة
            x = self.get_x()
            y = self.get_y()
            
            # إطار الرابط
            self.set_draw_color(*self.colors['danger'])
            self.set_fill_color(255, 245, 245)
            self.rect(x, y, width, 50, 'FD')
            
            # أيقونة PDF
            self.set_font('Cairo', 'B', 30)
            self.set_text_color(*self.colors['danger'])
            self.set_xy(x + width/2 - 10, y + 10)
            self.cell(20, 15, '📄', 0, 0, 'C')
            
            # نص الرابط
            self.set_font('Cairo', 'B', 9)
            self.set_xy(x, y + 30)
            self.cell(width, 6, self.arabic_text('ملف PDF مرفق'), 0, 1, 'C')
            
            # مسار الملف
            self.set_font('Cairo', '', 7)
            self.set_text_color(100, 100, 100)
            self.set_xy(x, y + 38)
            filename = os.path.basename(image_path)
            self.cell(width, 5, filename[:30], 0, 1, 'C')
            
            # رابط قابل للنقر
            web_path = f'/static/{image_path}'
            self.set_xy(x, y)
            self.link(x, y, width, 50, web_path)
            
            self.set_text_color(0, 0, 0)
            self.ln(52)
            return True
        else:
            # ملف صورة - عرض الصورة
            try:
                x = self.get_x()
                y = self.get_y()
                
                # إطار الصورة
                self.set_draw_color(*self.colors['light_gray'])
                self.rect(x, y, width, 50)
                
                # الصورة
                self.image(full_path, x + 2, y + 2, width - 4)
                self.ln(52)
                
                return True
            except Exception as e:
                print(f"خطأ في إضافة الصورة {image_path}: {e}")
                # عرض بديل في حالة الخطأ
                x = self.get_x()
                y = self.get_y()
                self.set_draw_color(*self.colors['light_gray'])
                self.set_fill_color(245, 245, 245)
                self.rect(x, y, width, 50, 'FD')
                
                self.set_font('Cairo', '', 8)
                self.set_xy(x, y + 22)
                self.cell(width, 6, self.arabic_text('خطأ في تحميل الصورة'), 0, 1, 'C')
                self.ln(52)
                return False
    
    def add_accident_photo(self, image_path, caption, x_pos, y_pos, width=60, height=45):
        """إضافة صورة حادث"""
        full_path = os.path.join(PROJECT_DIR, 'static', image_path)
        
        if os.path.exists(full_path):
            try:
                # إطار الصورة
                self.set_draw_color(*self.colors['light_gray'])
                self.set_line_width(0.3)
                self.rect(x_pos, y_pos, width, height + 8)
                
                # الصورة
                self.image(full_path, x_pos + 2, y_pos + 2, width - 4, height - 2)
                
                # التعليق
                self.set_xy(x_pos, y_pos + height + 2)
                self.set_font('Cairo', '', 8)
                self.cell(width, 6, self.arabic_text(caption), 0, 0, 'C')
                
                return True
            except Exception as e:
                print(f"خطأ في إضافة صورة الحادث: {e}")
                return False
        return False
    
    def generate(self):
        """توليد تقرير PDF الكامل"""
        self.alias_nb_pages()
        self.add_page()
        
        accident = self.accident
        vehicle = accident.vehicle
        
        # معلومات التقرير الأساسية
        self.set_font('Cairo', 'B', 12)
        self.cell(0, 8, self.arabic_text(f'رقم التقرير: {accident.id}'), 0, 1, 'R')
        
        # حالة المراجعة
        self.cell(0, 8, self.arabic_text('حالة المراجعة:'), 0, 0, 'R')
        self.ln(2)
        self.add_status_badge(accident.review_status)
        self.ln(5)
        
        # قسم معلومات المركبة
        self.add_section_title('معلومات المركبة', '🚗')
        self.add_field('رقم اللوحة', vehicle.plate_number)
        self.add_field('نوع المركبة', f'{vehicle.make} {vehicle.model}')
        self.add_field('سنة الصنع', vehicle.year)
        self.add_field('اللون', vehicle.color)
        self.ln(3)
        
        # قسم معلومات السائق
        self.add_section_title('معلومات السائق', '👤')
        self.add_field('اسم السائق', accident.driver_name)
        self.add_field('رقم الهاتف', accident.driver_phone)
        self.ln(3)
        
        # قسم تفاصيل الحادث
        self.add_section_title('تفاصيل الحادث', '📋')
        self.add_field('تاريخ الحادث', accident.accident_date.strftime('%Y-%m-%d'))
        
        if accident.accident_time:
            self.add_field('وقت الحادث', accident.accident_time.strftime('%H:%M'))
        
        self.add_field('الموقع', accident.location or '-')
        self.add_field('درجة الخطورة', accident.severity or 'متوسط')
        self.add_field('حالة المركبة', accident.vehicle_condition or '-')
        
        # الوصف
        if accident.description:
            self.set_font('Cairo', 'B', 11)
            self.set_fill_color(*self.colors['light_gray'])
            self.cell(0, 8, self.arabic_text('وصف الحادث'), 1, 1, 'R', True)
            
            self.set_font('Cairo', '', 10)
            self.multi_cell(0, 6, self.arabic_text(accident.description), 1, 'R')
        
        self.ln(3)
        
        # محضر الشرطة
        if accident.police_report:
            self.add_field('محضر شرطة', 'نعم ✓')
            if accident.police_report_number:
                self.add_field('رقم المحضر', accident.police_report_number)
        
        # صفحة جديدة للوثائق
        self.add_page()
        
        # قسم الوثائق
        self.add_section_title('وثائق الحادث', '📄')
        self.ln(3)
        
        current_y = self.get_y()
        
        # صورة الهوية
        if accident.driver_id_image:
            self.set_xy(15, current_y)
            self.add_document_image(accident.driver_id_image, 'صورة الهوية')
        
        # صورة الرخصة
        if accident.driver_license_image:
            self.set_xy(110, current_y)
            self.add_document_image(accident.driver_license_image, 'صورة الرخصة')
        
        self.ln(60)
        
        # تقرير الحادث
        if accident.accident_report_file:
            self.add_document_image(accident.accident_report_file, 'تقرير الحادث', width=180)
        
        # صور الحادث
        images = accident.images.all()
        if images:
            self.add_page()
            self.add_section_title('صور الحادث', '📸')
            self.ln(5)
            
            images_per_page = 6
            current_row = 0
            
            for idx, img in enumerate(images):
                row = idx // 2
                col = idx % 2
                
                # صفحة جديدة كل 6 صور
                if idx > 0 and idx % images_per_page == 0:
                    self.add_page()
                    current_row = 0
                    row = 0
                
                x_pos = 15 if col == 1 else 110
                y_pos = 50 + (row % 3) * 60
                
                caption = img.caption or f'صورة {idx + 1}'
                self.add_accident_photo(img.image_path, caption, x_pos, y_pos)
        
        # قسم المراجعة
        if accident.reviewed_at:
            self.add_page()
            self.add_section_title('معلومات المراجعة', '✓')
            
            if accident.reviewed_at:
                self.add_field('تاريخ المراجعة', accident.reviewed_at.strftime('%Y-%m-%d %H:%M'))
            
            if accident.reviewer_notes:
                self.set_font('Cairo', 'B', 11)
                self.set_fill_color(*self.colors['light_gray'])
                self.cell(0, 8, self.arabic_text('ملاحظات المراجع'), 1, 1, 'R', True)
                
                self.set_font('Cairo', '', 10)
                self.multi_cell(0, 6, self.arabic_text(accident.reviewer_notes), 1, 'R')
            
            if accident.liability_percentage:
                self.add_field('نسبة المسؤولية', f'{accident.liability_percentage}%')
            
            if accident.deduction_amount:
                self.add_field('المبلغ المخصوم', f'{accident.deduction_amount} ريال')
        
        return self


def generate_accident_report_pdf(accident):
    """إنشاء تقرير PDF للحادث"""
    try:
        pdf = AccidentReportPDF(accident)
        pdf.generate()
        return pdf
    except Exception as e:
        print(f"خطأ في إنشاء PDF: {e}")
        raise
