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
            # إضافة خط Cairo (خط عربي حديث يدعم كل الأحرف)
            self.add_font('Cairo', '', os.path.join(font_path, 'Cairo-Regular.ttf'), uni=True)
            self.add_font('Cairo', 'B', os.path.join(font_path, 'Cairo-Bold.ttf'), uni=True)
            
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
            'gradient_end': (80, 170, 200),  # نهاية التدرج
            # ألوان مستقبلية جديدة
            'cyan': (6, 182, 212),           # سيان (cyan-600)
            'cyan_dark': (8, 145, 178),      # سيان غامق (cyan-700)
            'cyan_light': (103, 232, 249),   # سيان فاتح (cyan-300)
            'purple': (147, 51, 234),        # بنفسجي (purple-600)
            'purple_dark': (126, 34, 206),   # بنفسجي غامق (purple-700)
            'purple_light': (216, 180, 254), # بنفسجي فاتح (purple-300)
            'pink': (236, 72, 153),          # وردي (pink-500)
            'pink_dark': (219, 39, 119),     # وردي غامق (pink-600)
            'pink_light': (249, 168, 212),   # وردي فاتح (pink-300)
            'blue': (37, 99, 235),           # أزرق (blue-600)
            'blue_dark': (29, 78, 216),      # أزرق غامق (blue-700)
            'blue_light': (147, 197, 253),   # أزرق فاتح (blue-300)
            'emerald': (16, 185, 129),       # زمردي (emerald-500)
            'emerald_dark': (5, 150, 105),   # زمردي غامق (emerald-600)
            'emerald_light': (110, 231, 183),# زمردي فاتح (emerald-300)
            'indigo': (79, 70, 229),         # نيلي (indigo-600)
            'indigo_dark': (67, 56, 202),    # نيلي غامق (indigo-700)
            'rose': (244, 63, 94),           # وردي غامق (rose-500)
            'amber': (245, 158, 11),         # كهرماني (amber-500)
            'teal': (20, 184, 166),          # تيل (teal-500)
            'violet': (139, 92, 246),        # بنفسجي فاتح (violet-500)
            'sky': (14, 165, 233)            # سماوي (sky-500)
        }
    
    def arabic_text(self, txt):
        """إعادة تشكيل النص العربي وتحويله ليعرض بشكل صحيح"""
        if txt is None or txt == '':
            return ''
        
        # تحويل إلى نص إذا لم يكن نصاً
        if not isinstance(txt, str):
            txt = str(txt)
        
        # تخطي النصوص الفارغة بعد التحويل
        if not txt or txt.strip() == '':
            return ''
        
        # فحص إذا كان النص يحتوي على أحرف عربية
        has_arabic = any('\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F' for c in txt)
        
        # إذا لم يكن هناك أحرف عربية، أرجع النص كما هو
        if not has_arabic:
            return txt
        
        # معالجة النصوص التي تحتوي على عربي
        try:
            # إعادة تشكيل النص العربي أولاً
            reshaped_text = arabic_reshaper.reshape(txt)
            # ثم تطبيق bidirectional algorithm
            bidi_text = get_display(reshaped_text)
            return bidi_text
        except Exception as e:
            # في حالة الخطأ، أرجع النص كما هو
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
    
    def draw_colored_badge(self, x, y, text, bg_color='cyan', text_color='white', width=None):
        """رسم badge ملون مميز"""
        # حساب عرض البادج بناءً على النص إذا لم يتم تحديده
        if width is None:
            text_width = self.get_string_width(self.arabic_text(text))
            width = text_width + 10
        
        # رسم الخلفية المستديرة
        self.set_fill_color_custom(bg_color)
        radius = 3
        # رسم شبه مستطيل دائري
        self.rect(x, y, width, 8, 'F')
        
        # رسم الدوائر في الأطراف لإعطاء شكل دائري
        self.ellipse(x, y, radius*2, 8, 'F')
        self.ellipse(x + width - radius*2, y, radius*2, 8, 'F')
        
        # النص
        self.set_text_color(*self.colors.get(text_color, (255, 255, 255)))
        if self.fonts_available:
            self.set_font('Cairo', 'B', 9)
        else:
            self.set_font('Arial', 'B', 9)
        self.set_xy(x, y + 1)
        self.cell(width, 6, text, 0, 0, 'C')
    
    def draw_gradient_header(self):
        """رسم رأس صفحة بتدرج لوني مستقبلي"""
        # رسم تدرج من cyan إلى purple إلى indigo
        num_stripes = 60
        stripe_height = 60 / num_stripes
        
        for i in range(num_stripes):
            # حساب النسبة
            ratio = i / num_stripes
            
            # التدرج من cyan إلى purple إلى indigo
            if ratio < 0.33:
                # cyan إلى purple
                local_ratio = ratio / 0.33
                r = int(6 + (147 - 6) * local_ratio)
                g = int(182 + (51 - 182) * local_ratio)
                b = int(212 + (234 - 212) * local_ratio)
            elif ratio < 0.66:
                # purple إلى indigo
                local_ratio = (ratio - 0.33) / 0.33
                r = int(147 + (79 - 147) * local_ratio)
                g = int(51 + (70 - 51) * local_ratio)
                b = int(234 + (229 - 234) * local_ratio)
            else:
                # indigo إلى نهاية أغمق
                local_ratio = (ratio - 0.66) / 0.34
                r = int(79 - (79 - 50) * local_ratio)
                g = int(70 - (70 - 50) * local_ratio)
                b = int(229 - (229 - 180) * local_ratio)
            
            self.set_fill_color(r, g, b)
            self.rect(0, i * stripe_height, 210, stripe_height + 0.5, 'F')
        
        # إضافة عناصر زخرفية (خطوط بيضاء خفيفة)
        self.set_draw_color(255, 255, 255)
        self.set_line_width(0.2)
        for i in range(0, 220, 25):
            self.line(i, 0, i+10, 60)
        
        # إضافة نقاط لامعة
        self.set_fill_color(255, 255, 255)
        import random
        random.seed(42)
        for _ in range(15):
            x = random.randint(10, 200)
            y = random.randint(5, 55)
            size = random.choice([0.5, 1, 1.5])
            self.rect(x, y, size, size, 'F')
    
    def draw_header_background(self):
        """رسم خلفية متدرجة لرأس الصفحة"""
        # استخدام الرأس المتدرج الجديد
        self.draw_gradient_header()
    
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
    
    def draw_decorative_separator(self, color1='cyan', color2='purple', color3='pink'):
        """رسم فاصل زخرفي ملون بين الأقسام"""
        current_y = self.get_y()
        
        # رسم خط تدرج
        num_segments = 180
        segment_width = 180 / num_segments
        
        for i in range(num_segments):
            ratio = i / num_segments
            
            # التدرج بين ثلاثة ألوان
            if ratio < 0.5:
                local_ratio = ratio / 0.5
                r1, g1, b1 = self.colors[color1]
                r2, g2, b2 = self.colors[color2]
            else:
                local_ratio = (ratio - 0.5) / 0.5
                r1, g1, b1 = self.colors[color2]
                r2, g2, b2 = self.colors[color3]
            
            r = int(r1 + (r2 - r1) * local_ratio)
            g = int(g1 + (g2 - g1) * local_ratio)
            b = int(b1 + (b2 - b1) * local_ratio)
            
            self.set_fill_color(r, g, b)
            self.rect(15 + i * segment_width, current_y, segment_width + 0.5, 1, 'F')
        
        # إضافة نجوم زخرفية
        self.set_fill_color(*self.colors[color2])
        for x_pos in [65, 105, 145]:
            # رسم نجمة صغيرة (معين)
            self.rect(x_pos - 1.5, current_y - 2, 3, 3, 'F')
        
        self.ln(6)
    
    def add_section_header(self, title, icon='■', color='cyan'):
        """إضافة رأس قسم مع تصميم مستقبلي مميز"""
        current_y = self.get_y()
        
        # خلفية متدرجة للقسم
        num_stripes = 12
        stripe_height = 12 / num_stripes
        base_color = self.colors[color]
        
        for i in range(num_stripes):
            ratio = i / num_stripes
            # تدرج من اللون الأساسي إلى أفتح
            r = int(base_color[0] + (255 - base_color[0]) * ratio * 0.7)
            g = int(base_color[1] + (255 - base_color[1]) * ratio * 0.7)
            b = int(base_color[2] + (255 - base_color[2]) * ratio * 0.7)
            
            self.set_fill_color(r, g, b)
            self.rect(15, current_y + i * stripe_height, 180, stripe_height + 0.5, 'F')
        
        # شريط ملون بارز على اليسار
        self.set_fill_color_custom(color)
        self.rect(15, current_y, 5, 12, 'F')
        
        # أيقونة/شعار في الجانب
        self.set_fill_color_custom('white')
        self.rect(22, current_y + 2, 8, 8, 'F')
        self.set_text_color(*self.colors[color])
        if self.fonts_available:
            self.set_font('Cairo', 'B', 10)
        else:
            self.set_font('Arial', 'B', 10)
        self.set_xy(22, current_y + 2.5)
        self.cell(8, 7, icon, 0, 0, 'C')
        
        # النص
        self.set_xy(35, current_y + 2)
        if self.fonts_available:
            self.set_font('Cairo', 'B', 14)
        else:
            self.set_font('Arial', 'B', 14)
        
        self.set_color('white')
        self.cell(0, 8, title, 0, 1, 'R')
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
                pdf.set_font('Cairo', 'B', 16)
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
            pdf.set_font('Cairo', 'B', 20)
        else:
            pdf.set_font('Arial', 'B', 20)
        pdf.set_xy(15, 25)
        pdf.cell(40, 10, 'نُظم', 0, 0, 'C')
    
    # عنوان التقرير
    pdf.set_text_color(255, 255, 255)
    if pdf.fonts_available:
        pdf.set_font('Cairo', 'B', 24)
    else:
        pdf.set_font('Arial', 'B', 24)
    pdf.set_xy(70, 15)
    pdf.cell(120, 12, 'تقرير سجلات الورشة', 0, 1, 'C')
    
    # معلومات السيارة في الرأس
    if pdf.fonts_available:
        pdf.set_font('Cairo', 'B', 16)
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
            pdf.set_font('Cairo', 'B', 11)
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
            pdf.set_font('Cairo', 'B', 14)
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
            pdf.set_font('Cairo', 'B', 12)
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
            pdf.set_font('Cairo', 'B', 9)
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
                    pdf.set_font('Cairo', 'B', 9)
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
        pdf.set_font('Cairo', 'B', 10)
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
    
    # ===== رأس الصفحة المستقبلي المميز =====
    pdf.draw_header_background()
    
    # إضافة الشعار في رأس الصفحة مع تصميم مميز
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
    
    # رسم إطار مميز للشعار (خلفية بيضاء خفيفة)
    pdf.set_fill_color(240, 245, 255)
    pdf.rect(13, 8, 44, 44, 'F')
    pdf.set_draw_color(255, 255, 255)
    pdf.set_line_width(2)
    pdf.rect(13, 8, 44, 44)
    
    # إذا وجدنا شعارًا، قم بإضافته
    if logo_path:
        try:
            pdf.image(logo_path, x=15, y=10, w=40, h=40)
        except:
            # شعار نصي بديل مميز
            pdf.set_fill_color(*pdf.colors['white'])
            pdf.rect(17, 18, 32, 24, 'F')
            pdf.set_text_color(*pdf.colors['cyan'])
            if pdf.fonts_available:
                pdf.set_font('Cairo', 'B', 20)
            else:
                pdf.set_font('Arial', 'B', 20)
            pdf.set_xy(17, 25)
            pdf.cell(32, 10, 'نُظم', 0, 0, 'C')
    else:
        # شعار نصي بديل مميز
        pdf.set_fill_color(*pdf.colors['white'])
        pdf.rect(17, 18, 32, 24, 'F')
        pdf.set_text_color(*pdf.colors['cyan'])
        if pdf.fonts_available:
            pdf.set_font('Cairo', 'B', 20)
        else:
            pdf.set_font('Arial', 'B', 20)
        pdf.set_xy(17, 25)
        pdf.cell(32, 10, 'نُظم', 0, 0, 'C')
    
    # عنوان التقرير المميز
    pdf.set_text_color(255, 255, 255)
    if pdf.fonts_available:
        pdf.set_font('Cairo', 'B', 26)
    else:
        pdf.set_font('Arial', 'B', 26)
    pdf.set_xy(65, 12)
    pdf.cell(130, 12, 'فحص السلامة الخارجي', 0, 1, 'C')
    
    # Badge لرقم اللوحة
    plate_number = safety_check.vehicle_plate_number or 'غير محدد'
    pdf.set_fill_color(240, 245, 255)
    pdf.rect(80, 28, 50, 10, 'F')
    pdf.set_draw_color(255, 255, 255)
    pdf.set_line_width(0.5)
    pdf.rect(80, 28, 50, 10)
    
    pdf.set_text_color(255, 255, 255)
    if pdf.fonts_available:
        pdf.set_font('Cairo', 'B', 14)
    else:
        pdf.set_font('Arial', 'B', 14)
    pdf.set_xy(80, 30)
    pdf.cell(50, 6, f'🚗 {plate_number}', 0, 1, 'C')
    
    # حالة الموافقة في الزاوية
    if hasattr(safety_check, 'approval_status') and safety_check.approval_status:
        status_text = '✓ معتمدة' if safety_check.approval_status == 'approved' else '✗ مرفوضة'
        status_color = 'emerald' if safety_check.approval_status == 'approved' else 'rose'
        
        pdf.set_fill_color(*pdf.colors[status_color])
        pdf.rect(138, 43, 50, 10, 'F')
        pdf.set_text_color(255, 255, 255)
        if pdf.fonts_available:
            pdf.set_font('Cairo', 'B', 12)
        else:
            pdf.set_font('Arial', 'B', 12)
        pdf.set_xy(138, 45)
        pdf.cell(50, 6, status_text, 0, 0, 'C')
    
    # إعادة تعيين اللون للنص العادي
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(68)
    
    # ===== معلومات السيارة =====
    pdf.add_section_header('معلومات السيارة', '🚗', 'cyan')
    
    # بطاقة معلومات السيارة المميزة
    vehicle_info = [
        ['رقم اللوحة:', safety_check.vehicle_plate_number or 'غير محدد', 'cyan'],
        ['نوع السيارة:', safety_check.vehicle_make_model or 'غير محدد', 'purple'],
        ['المفوض الحالي:', safety_check.current_delegate or 'غير محدد', 'pink']
    ]
    
    # رسم بطاقة بإطار ملون متدرج
    current_y = pdf.get_y()
    box_height = len(vehicle_info) * 12 + 8
    
    # خلفية فاتحة للبطاقة
    pdf.set_fill_color(248, 250, 252)
    pdf.rect(20, current_y, 170, box_height, 'F')
    
    # إطار متدرج للبطاقة
    pdf.set_draw_color(*pdf.colors['cyan'])
    pdf.set_line_width(0.8)
    pdf.rect(20, current_y, 170, box_height)
    
    pdf.set_y(current_y + 5)
    
    for i, info in enumerate(vehicle_info):
        field_color = info[2]
        
        # خط رفيع بين الحقول
        if i > 0:
            y_pos = pdf.get_y() - 1
            pdf.set_draw_color(220, 220, 220)
            pdf.set_line_width(0.2)
            pdf.line(25, y_pos, 185, y_pos)
        
        pdf.set_x(25)
        
        # أيقونة ملونة صغيرة
        pdf.set_fill_color(*pdf.colors[field_color])
        pdf.rect(25, pdf.get_y() + 2, 2, 6, 'F')
        
        # العنوان
        pdf.set_x(30)
        if pdf.fonts_available:
            pdf.set_font('Cairo', 'B', 11)
        else:
            pdf.set_font('Arial', 'B', 11)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(60, 10, info[0], 0, 0, 'R')
        
        # القيمة
        if pdf.fonts_available:
            pdf.set_font('Cairo', '', 11)
        else:
            pdf.set_font('Arial', '', 11)
        pdf.set_text_color(*pdf.colors[field_color])
        pdf.cell(95, 10, info[1], 0, 1, 'R')
    
    pdf.ln(8)
    
    # فاصل زخرفي
    pdf.draw_decorative_separator('cyan', 'purple', 'pink')
    
    # ===== معلومات السائق =====
    pdf.add_section_header('معلومات السائق', '👤', 'purple')
    
    # بطاقة معلومات السائق المميزة
    driver_info = [
        ['اسم السائق:', safety_check.driver_name or 'غير محدد', 'emerald'],
        ['رقم الهوية:', safety_check.driver_national_id or 'غير محدد', 'sky'],
        ['القسم:', safety_check.driver_department or 'غير محدد', 'violet'],
        ['المدينة:', safety_check.driver_city or 'غير محدد', 'amber']
    ]
    
    # رسم بطاقة بإطار ملون متدرج
    current_y = pdf.get_y()
    box_height = len(driver_info) * 12 + 8
    
    # خلفية فاتحة للبطاقة
    pdf.set_fill_color(252, 248, 255)
    pdf.rect(20, current_y, 170, box_height, 'F')
    
    # إطار متدرج للبطاقة
    pdf.set_draw_color(*pdf.colors['purple'])
    pdf.set_line_width(0.8)
    pdf.rect(20, current_y, 170, box_height)
    
    pdf.set_y(current_y + 5)
    
    for i, info in enumerate(driver_info):
        field_color = info[2]
        
        # خط رفيع بين الحقول
        if i > 0:
            y_pos = pdf.get_y() - 1
            pdf.set_draw_color(220, 220, 220)
            pdf.set_line_width(0.2)
            pdf.line(25, y_pos, 185, y_pos)
        
        pdf.set_x(25)
        
        # أيقونة ملونة صغيرة
        pdf.set_fill_color(*pdf.colors[field_color])
        pdf.rect(25, pdf.get_y() + 2, 2, 6, 'F')
        
        # العنوان
        pdf.set_x(30)
        if pdf.fonts_available:
            pdf.set_font('Cairo', 'B', 11)
        else:
            pdf.set_font('Arial', 'B', 11)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(60, 10, info[0], 0, 0, 'R')
        
        # القيمة
        if pdf.fonts_available:
            pdf.set_font('Cairo', '', 11)
        else:
            pdf.set_font('Arial', '', 11)
        pdf.set_text_color(*pdf.colors[field_color])
        pdf.cell(95, 10, info[1], 0, 1, 'R')
    
    pdf.ln(8)
    
    # فاصل زخرفي
    pdf.draw_decorative_separator('purple', 'indigo', 'pink')
    
    # ===== الملاحظات =====
    if safety_check.notes:
        pdf.add_section_header('الملاحظات والتوصيات', '📋', 'blue')
        
        current_y = pdf.get_y()
        
        # حساب ارتفاع الملاحظات
        notes_height = max(35, min(60, len(safety_check.notes) / 4))
        
        # خلفية متدرجة للملاحظات
        pdf.set_fill_color(245, 250, 255)
        pdf.rect(20, current_y, 170, notes_height, 'F')
        
        # إطار ملون
        pdf.set_draw_color(*pdf.colors['blue'])
        pdf.set_line_width(0.8)
        pdf.rect(20, current_y, 170, notes_height)
        
        # أيقونة التنبيه
        pdf.set_fill_color(*pdf.colors['blue'])
        pdf.rect(25, current_y + 4, 2, 6, 'F')
        
        # النص
        pdf.set_xy(30, current_y + 5)
        if pdf.fonts_available:
            pdf.set_font('Cairo', '', 10)
        else:
            pdf.set_font('Arial', '', 10)
        pdf.set_text_color(60, 60, 60)
        
        # تقسيم الملاحظات لأسطر متعددة
        pdf.multi_cell(155, 5, safety_check.notes, 0, 'R')
        
        pdf.ln(10)
        
        # فاصل زخرفي
        pdf.draw_decorative_separator('blue', 'cyan', 'purple')
    
    # ===== حالة الاعتماد (إذا كانت موجودة) =====
    # تم نقلها للرأس العلوي
    
    # ===== صور فحص السلامة =====
    if hasattr(safety_check, 'safety_images') and safety_check.safety_images:
        pdf.add_section_header(f'صور فحص السلامة ({len(safety_check.safety_images)} صورة)', '📷', 'pink')
        
        # ألوان مختلفة لكل صورة
        image_colors = ['cyan', 'purple', 'pink', 'emerald', 'blue', 'violet', 'rose', 'amber']
        
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
                        
                        # فاصل زخرفي في الصفحات الجديدة
                        pdf.draw_decorative_separator('cyan', 'purple', 'pink')
                        pdf.ln(5)
                    
                    # اختيار لون للصورة الحالية
                    image_color = image_colors[i % len(image_colors)]
                    
                    # عنوان الصورة مع badge ملون
                    description = image.image_description or f'صورة رقم {i+1}'
                    
                    current_y = pdf.get_y()
                    
                    # خلفية العنوان (لون فاتح جداً)
                    r, g, b = pdf.colors[image_color]
                    pdf.set_fill_color(int(r + (255-r)*0.85), int(g + (255-g)*0.85), int(b + (255-b)*0.85))
                    pdf.rect(15, current_y, 180, 12, 'F')
                    
                    # Badge رقم الصورة
                    pdf.set_fill_color(*pdf.colors[image_color])
                    pdf.rect(165, current_y + 2, 25, 8, 'F')
                    pdf.set_text_color(255, 255, 255)
                    if pdf.fonts_available:
                        pdf.set_font('Cairo', 'B', 10)
                    else:
                        pdf.set_font('Arial', 'B', 10)
                    pdf.set_xy(165, current_y + 3)
                    pdf.cell(25, 6, f'صورة {i+1}', 0, 0, 'C')
                    
                    # وصف الصورة
                    if pdf.fonts_available:
                        pdf.set_font('Cairo', 'B', 13)
                    else:
                        pdf.set_font('Arial', 'B', 13)
                    pdf.set_color(image_color)
                    pdf.set_xy(20, current_y + 3)
                    pdf.cell(140, 6, description, 0, 1, 'R')
                    
                    pdf.ln(5)
                    
                    # الحصول على أبعاد الصورة الأصلية
                    from PIL import Image as PILImage
                    try:
                        with PILImage.open(image_path) as img:
                            original_width, original_height = img.size
                    except:
                        original_width, original_height = 800, 600
                    
                    # حساب الأبعاد المناسبة مع الحفاظ على نسبة العرض إلى الارتفاع
                    max_width = 150
                    max_height = 120
                    
                    # حساب النسبة
                    width_ratio = max_width / original_width
                    height_ratio = max_height / original_height
                    ratio = min(width_ratio, height_ratio)
                    
                    # الأبعاد النهائية
                    final_width = original_width * ratio
                    final_height = original_height * ratio
                    
                    # مركز الصورة
                    padding = 4
                    x_position = (210 - final_width) / 2
                    y_position = pdf.get_y()
                    
                    # ظل خفيف خلف الإطار
                    pdf.set_fill_color(230, 230, 230)
                    pdf.rect(x_position - padding + 1, y_position - padding + 1, 
                            final_width + 2*padding, final_height + 2*padding, 'F')
                    
                    # خلفية بيضاء
                    pdf.set_fill_color(255, 255, 255)
                    pdf.rect(x_position - padding, y_position - padding, 
                            final_width + 2*padding, final_height + 2*padding, 'F')
                    
                    # إطار ملون مميز
                    pdf.set_draw_color(*pdf.colors[image_color])
                    pdf.set_line_width(1.5)
                    pdf.rect(x_position - padding, y_position - padding, 
                            final_width + 2*padding, final_height + 2*padding)
                    
                    # إضافة الصورة
                    pdf.image(image_path, x_position, y_position, final_width, final_height)
                    
                    # مساحة بعد الصورة
                    pdf.set_y(y_position + final_height + 10)
                    
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
    
    # ===== تذييل التقرير المميز =====
    pdf.set_y(-35)
    
    # خط تدرج في التذييل
    current_y = pdf.get_y()
    pdf.draw_decorative_separator('cyan', 'purple', 'pink')
    
    pdf.ln(2)
    
    # معلومات التذييل
    if pdf.fonts_available:
        pdf.set_font('Amiri', '', 9)
    else:
        pdf.set_font('Arial', '', 9)
    pdf.set_color('text_light')
    pdf.cell(0, 5, f'تاريخ إنشاء التقرير: {datetime.now().strftime("%Y-%m-%d | %H:%M")}', 0, 1, 'C')
    
    if pdf.fonts_available:
        pdf.set_font('Cairo', 'B', 10)
    else:
        pdf.set_font('Arial', 'B', 10)
    pdf.set_color('cyan')
    pdf.cell(0, 5, 'نُظم - نظام إدارة المركبات والموظفين الشامل', 0, 1, 'C')
    
    if pdf.fonts_available:
        pdf.set_font('Amiri', '', 8)
    else:
        pdf.set_font('Arial', '', 8)
    pdf.set_color('text_light')
    pdf.cell(0, 4, 'تم إنشاؤه آلياً من النظام • مصمم بتقنية احترافية', 0, 0, 'C')
    
    # نقاط زخرفية في التذييل
    footer_y = pdf.get_y() + 2
    for x_pos, color in [(70, 'cyan'), (105, 'purple'), (140, 'pink')]:
        pdf.set_fill_color(*pdf.colors[color])
        pdf.rect(x_pos, footer_y, 2, 2, 'F')
    
    # حفظ PDF إلى buffer
    pdf_buffer = io.BytesIO()
    try:
        # في fpdf2 الحديث، output يعيد bytearray مباشرة
        pdf_content = pdf.output(dest='S')
        if isinstance(pdf_content, str):
            pdf_content = pdf_content.encode('latin1')
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