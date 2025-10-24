"""
مولد PDF لإشعارات الرواتب
استخدام FPDF مع دعم كامل للنصوص العربية والتنسيق المحترف
"""
# salary_pdf_generator.py
from fpdf import FPDF
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display
import os
from io import BytesIO


# --- الإعدادات العامة والتصميم ---
FONT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'fonts')
LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'images', 'logo.png') # مسار الشعار
# تعريف ألوان الهوية البصرية (يمكن تغييرها بسهولة)
PRIMARY_COLOR = (41, 128, 185)  # درجة من اللون الأزرق (R, G, B)
HEADER_BG_COLOR = (236, 240, 241) # لون رمادي فاتح جداً لرؤوس الجداول
FONT_COLOR = (44, 62, 80) # لون رمادي غامق للنصوص

class SalaryPDF(FPDF):
    """
    كلاس مصمم لإنشاء تقارير PDF احترافية مع هوية بصرية مخصصة.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # استخدام خط Amiri لأنه أثبت فعاليته
        self.add_font('Amiri', '', os.path.join(FONT_PATH, 'Amiri-Regular.ttf'), uni=True)
        self.add_font('Amiri', 'B', os.path.join(FONT_PATH, 'Amiri-Bold.ttf'), uni=True)
        self.set_auto_page_break(auto=True, margin=15)
        self.alias_nb_pages() # لتمكين عرض العدد الكلي للصفحات
        

    def reshape(self, text):
        return get_display(arabic_reshaper.reshape(str(text)))

    def header(self):
        # Header - ترويسة الصفحة مع الشعار والألوان
        
        # 1. إضافة الشعار في الزاوية اليسرى العلوية
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=10, y=8, w=33)
        else:
            print(f"WARNING: Logo file not found at {LOGO_PATH}")

        # 2. إضافة عناوين الشركة في المنتصف
        self.set_y(15) # تحديد الارتفاع ليكون النص في مستوى جيد
        self.set_font('Amiri', 'B', 20)
        self.set_text_color(*FONT_COLOR)
        self.cell(0, 10, "Employee Management System", 0, 1, 'C')
        
        self.set_font('Amiri', 'B', 16)
        self.cell(0, 10, self.reshape("نظام إدارة الموظفين - نُظم"), 0, 1, 'C')
        
        # 3. خط أفقي ملون أسفل الترويسة
        self.set_draw_color(*PRIMARY_COLOR)
        self.set_line_width(0.5)
        self.line(10, 35, 200, 35)
        
        self.ln(15) # ترك مسافة بعد الترويسة

    def footer(self):
        # Footer - تذييل الصفحة
        self.set_y(-15)
        self.set_font('Amiri', '', 8)
        self.set_text_color(128) # لون رمادي باهت
        # التاريخ على اليسار
        self.cell(0, 10, datetime.now().strftime('%Y-%m-%d'), 0, 0, 'L')
        # رقم الصفحة في المنتصف
        self.cell(0, 10, self.reshape(f'صفحة {self.page_no()}/{{nb}}'), 0, 0, 'C')



# --- الدوال المساعدة للتصميم ---
def _draw_report_title(pdf, title_text):
    pdf.set_font('Amiri', 'B', 16)
    pdf.set_text_color(*PRIMARY_COLOR)
    pdf.cell(0, 10, pdf.reshape(title_text), 0, 1, 'C')
    pdf.ln(8) # مسافة بعد العنوان

def _draw_table(pdf, headers, widths, data_rows, total_row):
    # رسم رؤوس الجدول باللون الأزرق
    pdf.set_font('Amiri', 'B', 11)
    pdf.set_fill_color(*PRIMARY_COLOR)
    pdf.set_text_color(255, 255, 255) # لون النص أبيض
    for i, header in enumerate(headers):
        pdf.cell(widths[i], 12, pdf.reshape(header), 1, 0, 'C', fill=True)
    pdf.ln()

    # رسم صفوف البيانات بألوان متناوبة لتحسين القراءة
    pdf.set_text_color(*FONT_COLOR)
    fill = False
    for row in data_rows:
        pdf.set_fill_color(245, 245, 245) # لون خلفية فاتح للصفوف الفردية
        for i, cell_data in enumerate(row):
            # استخدام حجم خط أصغر للأسماء (العمود الأول) لضمان احتواء الأسماء الطويلة
            if i == 0:
                pdf.set_font('Amiri', '', 8)
            else:
                pdf.set_font('Amiri', '', 10)
            align = 'R' if i == 0 else 'C'
            pdf.cell(widths[i], 10, pdf.reshape(str(cell_data)), 1, 0, align, fill=fill)
        fill = not fill # عكس لون التعبئة للصف التالي
        pdf.ln()
    
    # رسم صف المجاميع بتنسيق مميز
    pdf.set_font('Amiri', 'B', 10)
    pdf.set_fill_color(*HEADER_BG_COLOR)
    for i, cell_data in enumerate(total_row):
        align = 'R' if i == 0 else 'C'
        pdf.cell(widths[i], 10, pdf.reshape(str(cell_data)), 1, 0, align, fill=True)
    pdf.ln()

# --- الدالة الرئيسية (نفس المنطق، مع استدعاء دوال التصميم الجديدة) ---
def generate_salary_summary_pdf(salaries, department_name=None, month=None, year=None):
    if not salaries: raise ValueError("لا يمكن إنشاء تقرير فارغ.")
    try:
        pdf = SalaryPDF()
        pdf.add_page()

        # ... بناء العنوان
        title_elements = ["تقرير الرواتب"]
        month_names = {1:'يناير', 2:'فبراير', 3:'مارس', 4:'أبريل', 5:'مايو', 6:'يونيو', 7:'يوليو', 8:'أغسطس', 9:'سبتمبر', 10:'أكتوبر', 11:'نوفمبر', 12:'ديسمبر'}
        if month: title_elements.append(month_names.get(int(month)))
        if year: title_elements.append(str(year))
        if department_name: title_elements.extend(["- قسم:", str(department_name)])
        title_text = " ".join([p for p in title_elements if p])
        
        _draw_report_title(pdf, title_text)
        
        # ترتيب الرواتب حسب اسم الموظف
        sorted_salaries = sorted(salaries, key=lambda s: s.employee.name)
        
        # دالة لتحسين عرض الأسماء
        def format_name(name):
            # تحويل الاسم من UPPERCASE إلى Title Case لتحسين القراءة
            if name and name.isupper():
                return name.title()
            return name
        
        # ... تحضير بيانات الجدول (نفس المنطق)
        headers = ["اسم الموظف", "الراتب الأساسي", "البدلات", "المكافآت", "الخصومات", "حضور", "غياب", "صافي الراتب"]
        widths = [65, 22, 18, 18, 18, 12, 12, 25] # تعديل الأعمدة لإضافة الحضور والغياب
        data_rows = [
            [format_name(s.employee.name), f"{float(s.basic_salary):,.0f}", f"{float(s.allowances):,.0f}", 
             f"{float(s.bonus):,.0f}", f"{float(s.deductions):,.0f}", 
             str(s.present_days) if s.attendance_calculated else "-",
             str(s.absent_days) if s.attendance_calculated else "-",
             f"{float(s.net_salary):,.0f}"]
            for s in sorted_salaries
        ]
        
        totals = {k: sum(float(getattr(s, k, 0)) for s in salaries) for k in ['basic_salary', 'allowances', 'bonus', 'deductions', 'net_salary']}
        total_row = ["المجموع:", f"{totals['basic_salary']:,.0f}", f"{totals['allowances']:,.0f}", f"{totals['bonus']:,.0f}", f"{totals['deductions']:,.0f}", "-", "-", f"{totals['net_salary']:,.0f}"]
        
        # استدعاء دالة رسم الجدول بالتصميم الجديد
        _draw_table(pdf, headers, widths, data_rows, total_row)
        
        pdf.ln(10)
        pdf.set_font('Amiri', '', 10)
        pdf.set_text_color(*FONT_COLOR)
        pdf.cell(0, 6, pdf.reshape(f'عدد الموظفين الإجمالي: {len(salaries)}'), 0, 1, 'R')
        
        return pdf.output()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise Exception(f"فشل إنشاء تقرير PDF: {e}")


def generate_salary_notification_pdf(salary):
    """
    إنشاء إشعار راتب محترف كملف PDF
    
    Args:
        salary: كائن Salary يحتوي على بيانات الراتب
        
    Returns:
        bytes: ملف PDF كـ bytes
    """
    try:
        # إنشاء كائن PDF
        pdf = SalaryPDF()
        pdf.add_page()
        
        # تحضير البيانات
        month_names = {
            1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
            5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
            9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
        }
        
        month = int(salary.month) if not isinstance(salary.month, int) else salary.month
        month_name = month_names.get(month, str(month))
        year = str(salary.year)
        
        # العنوان الرئيسي
        pdf.set_font('Arial', 'B', 18)
        title = pdf.reshape_arabic(f'إشعار راتب - {month_name} {year}')
        pdf.cell(0, 15, title, 0, 1, 'C')
        pdf.ln(10)
        
        # معلومات الموظف
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, pdf.reshape_arabic('بيانات الموظف'), 0, 1, 'R')
        pdf.ln(5)
        
        # جدول معلومات الموظف
        pdf.set_font('Arial', '', 12)
        
        # اسم الموظف
        pdf.cell(50, 8, pdf.reshape_arabic('اسم الموظف:'), 1, 0, 'R')
        pdf.cell(0, 8, pdf.reshape_arabic(salary.employee.name), 1, 1, 'R')
        
        # رقم الموظف
        pdf.cell(50, 8, pdf.reshape_arabic('رقم الموظف:'), 1, 0, 'R')
        pdf.cell(0, 8, str(salary.employee.employee_id), 1, 1, 'R')
        
        # المسمى الوظيفي
        pdf.cell(50, 8, pdf.reshape_arabic('المسمى الوظيفي:'), 1, 0, 'R')
        pdf.cell(0, 8, pdf.reshape_arabic(salary.employee.job_title), 1, 1, 'R')
        
        # القسم
        department_name = salary.employee.department.name if salary.employee.department else 'غير محدد'
        pdf.cell(50, 8, pdf.reshape_arabic('القسم:'), 1, 0, 'R')
        pdf.cell(0, 8, pdf.reshape_arabic(department_name), 1, 1, 'R')
        
        pdf.ln(10)
        
        # تفاصيل الراتب
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, pdf.reshape_arabic('تفاصيل الراتب'), 0, 1, 'R')
        pdf.ln(5)
        
        # جدول الراتب
        pdf.set_font('Arial', '', 12)
        
        # الراتب الأساسي
        pdf.cell(50, 8, pdf.reshape_arabic('الراتب الأساسي:'), 1, 0, 'R')
        pdf.cell(0, 8, f'{float(salary.basic_salary):,.2f} ريال', 1, 1, 'R')
        
        # البدلات
        pdf.cell(50, 8, pdf.reshape_arabic('البدلات:'), 1, 0, 'R')
        pdf.cell(0, 8, f'{float(salary.allowances):,.2f} ريال', 1, 1, 'R')
        
        # المكافآت
        pdf.cell(50, 8, pdf.reshape_arabic('المكافآت:'), 1, 0, 'R')
        pdf.cell(0, 8, f'{float(salary.bonus):,.2f} ريال', 1, 1, 'R')
        
        # إجمالي المستحقات
        total_earnings = float(salary.basic_salary) + float(salary.allowances) + float(salary.bonus)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(50, 8, pdf.reshape_arabic('إجمالي المستحقات:'), 1, 0, 'R')
        pdf.cell(0, 8, f'{total_earnings:,.2f} ريال', 1, 1, 'R')
        
        # الخصومات
        pdf.set_font('Arial', '', 12)
        pdf.cell(50, 8, pdf.reshape_arabic('الخصومات:'), 1, 0, 'R')
        pdf.cell(0, 8, f'{float(salary.deductions):,.2f} ريال', 1, 1, 'R')
        
        # صافي الراتب
        pdf.set_font('Arial', 'B', 14)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(50, 10, pdf.reshape_arabic('صافي الراتب:'), 1, 0, 'R', True)
        pdf.cell(0, 10, f'{float(salary.net_salary):,.2f} ريال', 1, 1, 'R', True)
        
        pdf.ln(10)
        
        # الملاحظات
        if salary.notes:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, pdf.reshape_arabic('ملاحظات:'), 0, 1, 'R')
            pdf.set_font('Arial', '', 10)
            pdf.multi_cell(0, 6, pdf.reshape_arabic(salary.notes), 1, 'R')
            pdf.ln(5)
        
        # معلومات إضافية
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, pdf.reshape_arabic(f'تاريخ الإصدار: {datetime.now().strftime("%Y-%m-%d")}'), 0, 1, 'R')
        pdf.cell(0, 6, pdf.reshape_arabic(f'رقم الإشعار: SAL-{salary.id}-{year}-{month:02d}'), 0, 1, 'R')
        
        # توقيع
        pdf.ln(15)
        pdf.cell(0, 6, pdf.reshape_arabic('التوقيع: ___________________'), 0, 1, 'L')
        pdf.cell(0, 6, pdf.reshape_arabic('التاريخ: ___________________'), 0, 1, 'L')
        
        # إرجاع PDF كـ bytes
        output = BytesIO()
        pdf_content = pdf.output(dest='S').encode('latin-1')
        output.write(pdf_content)
        output.seek(0)
        
        return output.getvalue()
        
    except Exception as e:
        print(f"خطأ في إنشاء إشعار الراتب: {str(e)}")
        raise Exception(f"فشل في إنشاء إشعار الراتب: {str(e)}")

def generate_batch_salary_notifications(department_id=None, month=None, year=None):
    """
    إنشاء إشعارات رواتب مجمعة
    
    Args:
        department_id: معرف القسم (اختياري)
        month: رقم الشهر
        year: السنة
        
    Returns:
        list: قائمة بأسماء الموظفين المعالجين
    """
    from models import Salary, Employee
    
    try:
        # بناء الاستعلام
        salary_query = Salary.query.filter_by(month=month, year=year)
        
        # تصفية حسب القسم إذا تم تحديده
        if department_id:
            employees = Employee.query.filter_by(department_id=department_id).all()
            employee_ids = [emp.id for emp in employees]
            salary_query = salary_query.filter(Salary.employee_id.in_(employee_ids))
        
        salaries = salary_query.all()
        processed_employees = []
        
        # معالجة كل راتب
        for salary in salaries:
            try:
                generate_salary_notification_pdf(salary)
                processed_employees.append(salary.employee.name)
            except Exception as e:
                print(f"خطأ في معالجة راتب {salary.employee.name}: {str(e)}")
        
        return processed_employees
        
    except Exception as e:
        print(f"خطأ في المعالجة المجمعة: {str(e)}")
        return []




# الاكواد القديمة التي تم تحديثها واستبدالها باكولد احرى





# class SalaryPDF(FPDF):
#     """
#     كلاس مخصص لإنشاء ملفات PDF لقسائم الرواتب.
#     - يستخدم خط القاهرة المخصص لدعم اللغة العربية بشكل كامل.
#     - يعالج تشكيل النصوص العربية لعرضها بشكل صحيح.
#     - يوفر رأس وتذييل موحد للمستندات.
#     """

#     # متغير ثابت لتخزين مسار الخط، مما يسهل إدارته وتحديثه مستقبلاً.
#     FONT_PATH = os.path.join('D:\projects\project',  'static', 'fonts', 'Cairo-Regular.ttf')
#     # نفترض وجود نسخة "Bold" من الخط في نفس المجلد
#     FONT_PATH_BOLD = os.path.join('D:\projects\project',  'static', 'fonts', 'Cairo-Bold.ttf')
    
#     def __init__(self, *args, **kwargs):
#         """
#         المُنشِئ (Constructor): يتم استدعاؤه عند إنشاء كائن جديد من هذا الكلاس.
#         يقوم بإعداد الصفحة وتحميل الخطوط الأساسية.
#         """
#         super().__init__(*args, **kwargs)
#         self._add_custom_font()  # استدعاء دالة تحميل الخط المخصصة
#         self.set_auto_page_break(auto=True, margin=15)
#         # تعيين الخط الافتراضي للمستند بالكامل لضمان التناسق
#         self.set_font(self.get_default_font_family(), '', 12)


#        #


#     def _add_custom_font(self):
#         """
#         دالة خاصة لتحميل خط "القاهرة" (Cairo).
#         هذه الدالة الآن تضمن استخدام الخط الصحيح أو تطلق خطأً واضحاً.
#         """
#         font_name = 'Cairo'
#         # تحقق من وجود المسارات أولاً
#         cairo_regular_exists = os.path.exists(self.FONT_PATH)
#         cairo_bold_exists = os.path.exists(self.FONT_PATH_BOLD)
        
#         print(f"DEBUG: Font Path (Regular): {self.FONT_PATH} | Exists: {cairo_regular_exists}")
#         print(f"DEBUG: Font Path (Bold): {self.FONT_PATH_BOLD} | Exists: {cairo_bold_exists}")
        
#         if cairo_regular_exists and cairo_bold_exists:
#             # إضافة الخط بنسختيه العادية (Regular) والعريضة (Bold)
#             try:
#                 self.add_font(font_name, '', self.FONT_PATH, uni=True)
#                 self.add_font(font_name, 'B', self.FONT_PATH_BOLD, uni=True)
#                 self._default_font_family = font_name
#                 print(f"SUCCESS: '{font_name}' font loaded successfully.")
#             except Exception as e:
#                 # هذا يحدث إذا كان الملف موجودًا ولكن تالفًا أو هناك مشكلة في fpdf
#                 raise RuntimeError(f"Failed to load the font file '{self.FONT_PATH}'. Error: {e}")
#         else:
#             # إذا لم يتم العثور على ملفات الخط، نطلق خطأً واضحاً بدلاً من الفشل بصمت
#             # هذا أفضل بكثير من إنشاء PDF تالف.
#             missing_files = []
#             if not cairo_regular_exists:
#                 missing_files.append(self.FONT_PATH)
#             if not cairo_bold_exists:
#                 missing_files.append(self.FONT_PATH_BOLD)
            
#             # إطلاق استثناء واضح جداً يخبر المطور بالضبط ما هي المشكلة.
#             raise FileNotFoundError(f"Could not create PDF. Required font files not found at the following locations: {', '.join(missing_files)}")



#     # def _add_custom_font(self):
#     #     """
#     #     دالة خاصة (Private) لتحميل خط "القاهرة" (Cairo).
#     #     هذا يغلف منطق تحميل الخط في مكان واحد ومنظم.
#     #     """
#     #     # التحقق من وجود ملفات الخط قبل محاولة استخدامها لتجنب الأخطاء
#     #     if os.path.exists(self.FONT_PATH) and os.path.exists(self.FONT_PATH_BOLD):
#     #         # إضافة الخط بنسختيه العادية (Regular) والعريضة (Bold)
#     #         self.add_font('Cairo', '', self.FONT_PATH, uni=True)
#     #         self.add_font('Cairo', 'B', self.FONT_PATH_BOLD, uni=True)
#     #         self._default_font_family = 'Cairo'
#     #     else:
#     #         # في حال عدم العثور على الخط، يتم استخدام خط بديل لمنع تعطل البرنامج
#     #         # مع طباعة رسالة تحذيرية للمطور.
#     #         print(f"تحذير: لم يتم العثور على ملفات الخط المطلوبة. سيتم استخدام خط Arial كبديل.")
#     #         # هنا يمكنك إضافة خط Arial كخط بديل إذا أردت
#     #         self._default_font_family = 'Arial' # أو 'Times'

#     def get_default_font_family(self):
#         """دالة مساعدة للحصول على اسم عائلة الخط الافتراضي المستخدم."""
#         return self._default_font_family

# class SalaryPDF(FPDF):
#     """
#     كلاس مخصص ومحسن لإنشاء ملفات PDF.
#     - يدير مسارات الخطوط بمرونة.
#     - يتعامل مع وجود أو عدم وجود نسخ مختلفة من الخط (مثل العادي والعريض).
#     - يوفر رسائل خطأ واضحة عند الفشل.
#     """

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # تحديد المسار الأساسي للمشروع بطريقة ديناميكية
#         self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        
#         self.font_path_regular = os.path.join(self.project_root, 'static', 'fonts', 'Cairo-Regular.ttf')
#         self.font_path_bold = os.path.join(self.project_root, 'static', 'fonts', 'Cairo-Bold.ttf')
        
#         self._default_font_family = 'Cairo'
#         self._load_fonts()

#         self.set_auto_page_break(auto=True, margin=15)
#         self.set_font(self._default_font_family, '', 12)

#     def _load_fonts(self):
#         """
#         دالة ذكية لتحميل الخطوط.
#         - تحمل الخط العادي (Regular) كشرط أساسي.
#         - تحمل الخط العريض (Bold) فقط إذا كان موجودًا، وإلا تستخدم العادي كبديل له.
#         """
#         font_name = 'Cairo'
        
#         # الخط العادي إلزامي
#         if not os.path.exists(self.font_path_regular):
#             raise FileNotFoundError(f"الخط الأساسي غير موجود! لا يمكن إنشاء PDF. المسار المتوقع: {self.font_path_regular}")
        
#         # تحميل الخط العادي
#         self.add_font(font_name, '', self.font_path_regular, uni=True)
#         print(f"SUCCESS: تم تحميل خط '{font_name}-Regular' بنجاح.")

#         # الخط العريض اختياري
#         if os.path.exists(self.font_path_bold):
#             self.add_font(font_name, 'B', self.font_path_bold, uni=True)
#             print(f"SUCCESS: تم تحميل خط '{font_name}-Bold' بنجاح.")
#         else:
#             # إذا لم يكن الخط العريض موجودًا، نربط النمط 'B' (Bold) بنفس ملف الخط العادي
#             # هذا يمنع الأخطاء عند محاولة استخدام `set_font` مع 'B'.
#             self.add_font(font_name, 'B', self.font_path_regular, uni=True)
#             print(f"WARNING: ملف الخط العريض '{self.font_path_bold}' غير موجود. سيتم استخدام الخط العادي بدلاً عنه.")

#     def reshape(self, text):
#             """
#             تقوم هذه الدالة بتشكيل وعكس اتجاه النص العربي لعرضه بشكل صحيح في ملف الـ PDF.
#             وتتعامل بأمان مع المدخلات التي ليست من نوع نص.
#             """
#             # التأكد من أن المدخل هو نص (string) لتجنب الأخطاء
#             if not isinstance(text, str):
#                 text = str(text) 
                
#             try:
#                 # تشكيل النص لدمج الحروف العربية بشكل صحيح
#                 reshaped_text = arabic_reshaper.reshape(text)
#                 # عكس اتجاه النص من اليمين إلى اليسار (RTL)
#                 return get_display(reshaped_text)
#             except Exception as e:
#                 # في حال حدوث أي خطأ أثناء التشكيل، يتم إرجاع النص الأصلي
#                 # وهذا يضمن عدم توقف عملية إنشاء الـ PDF.
#                 print(f"حدث خطأ أثناء تشكيل النص: {text}. الخطأ: {e}")
#                 return text
        
#     def header(self):
#             """إنشاء رأس الصفحة (Header) لكل صفحة تلقائياً."""
#             font_family = self.get_default_font_family()
            
#             # عنوان الشركة باللغة الإنجليزية
#             self.set_font(font_family, 'B', 20)
#             self.cell(0, 10, 'Employee Management System', 0, 1, 'C')
            
#             # عنوان فرعي باللغة العربية
#             self.set_font(font_family, 'B', 16)
#             arabic_subtitle = self.reshape('نظام إدارة الموظفين - نُظم')
#             self.cell(0, 15, arabic_subtitle, 0, 1, 'C')
            
#             # إضافة مسافة فاصلة لتحسين التنسيق
#             self.ln(10)
            
#     def footer(self):
#             """إنشاء تذييل الصفحة (Footer) لكل صفحة تلقائياً."""
#             font_family = self.get_default_font_family()

#             # تحديد موضع التذييل (1.5 سم من أسفل الصفحة)
#             self.set_y(-15)
#             self.set_font(font_family, 'I', 8) # خط مائل بحجم صغير
            
#             # رقم الصفحة في المنتصف
#             page_text = f'Page {self.page_no()}'
#             self.cell(0, 10, page_text, 0, 0, 'C')

#             # تاريخ إنشاء المستند على اليمين (للمستندات الإنجليزية) أو اليسار (للعربية)
#             # بما أن التنسيق العام قد يكون مختلطاً، سنضعه على اليمين حالياً
#             generation_date = datetime.now().strftime('%Y-%m-%d %H:%M')
#             self.set_font(font_family, '', 8)
#             self.cell(0, 10, generation_date, 0, 0, 'R')

#




# def generate_salary_summary_pdf(salaries, department_name=None, month=None, year=None):
#     """
#     إنشاء تقرير ملخص رواتب كملف PDF
    
#     Args:
#         salaries: قائمة بكائنات Salary
#         department_name: اسم القسم (اختياري)
#         month: رقم الشهر
#         year: السنة
        
#     Returns:
#         bytes: ملف PDF كـ bytes
#     """
#     try:
#         pdf = SalaryPDF()
#         pdf.add_page()
        
#         # تحضير البيانات
#         month_names = {
#             1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
#             5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
#             9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
#         }
#         print(' تحضير البيانات')
#         month_name = month_names.get(int(month), str(month)) if month else 'جميع الشهور'
        
#         # العنوان
#         pdf.set_font('Arial', 'B', 16)
#         title = f'تقرير الرواتب - {month_name} {year}'
#         if department_name:
#             title += f' - {department_name}'
#         pdf.cell(0, 15, pdf.reshape_arabic(title), 0, 1, 'C')
#         pdf.ln(10)
        
#         # جدول الرواتب
#         pdf.set_font('Arial', 'B', 10)
        
#         # رؤوس الجدول
#         pdf.cell(40, 8, pdf.reshape_arabic('اسم الموظف'), 1, 0, 'C')
#         pdf.cell(25, 8, pdf.reshape_arabic('الراتب الأساسي'), 1, 0, 'C')
#         pdf.cell(20, 8, pdf.reshape_arabic('البدلات'), 1, 0, 'C')
#         pdf.cell(20, 8, pdf.reshape_arabic('المكافآت'), 1, 0, 'C')
#         pdf.cell(20, 8, pdf.reshape_arabic('الخصومات'), 1, 0, 'C')
#         pdf.cell(25, 8, pdf.reshape_arabic('صافي الراتب'), 1, 1, 'C')
        
#         # بيانات الموظفين
#         pdf.set_font('Arial', '', 9)
#         total_basic = total_allowances = total_bonus = total_deductions = total_net = 0
        
#         for salary in salaries:
#             # التحقق من طول الاسم وتقسيمه إذا لزم الأمر
#             name = salary.employee.name[:15] + '...' if len(salary.employee.name) > 15 else salary.employee.name
            
#             pdf.cell(40, 6, pdf.reshape_arabic(name), 1, 0, 'R')
#             pdf.cell(25, 6, f'{float(salary.basic_salary):,.0f}', 1, 0, 'C')
#             pdf.cell(20, 6, f'{float(salary.allowances):,.0f}', 1, 0, 'C')
#             pdf.cell(20, 6, f'{float(salary.bonus):,.0f}', 1, 0, 'C')
#             pdf.cell(20, 6, f'{float(salary.deductions):,.0f}', 1, 0, 'C')
#             pdf.cell(25, 6, f'{float(salary.net_salary):,.0f}', 1, 1, 'C')
            
#             # إضافة للمجاميع
#             total_basic += float(salary.basic_salary)
#             total_allowances += float(salary.allowances)
#             total_bonus += float(salary.bonus)
#             total_deductions += float(salary.deductions)
#             total_net += float(salary.net_salary)
        
#         # المجاميع
#         pdf.set_font('Arial', 'B', 9)
#         pdf.cell(40, 8, pdf.reshape_arabic('المجموع:'), 1, 0, 'R')
#         pdf.cell(25, 8, f'{total_basic:,.0f}', 1, 0, 'C')
#         pdf.cell(20, 8, f'{total_allowances:,.0f}', 1, 0, 'C')
#         pdf.cell(20, 8, f'{total_bonus:,.0f}', 1, 0, 'C')
#         pdf.cell(20, 8, f'{total_deductions:,.0f}', 1, 0, 'C')
#         pdf.cell(25, 8, f'{total_net:,.0f}', 1, 1, 'C')
        
#         # معلومات إضافية
#         pdf.ln(10)
#         pdf.set_font('Arial', '', 10)
#         pdf.cell(0, 6, pdf.reshape_arabic(f'عدد الموظفين: {len(salaries)}'), 0, 1, 'R')
#         pdf.cell(0, 6, pdf.reshape_arabic(f'تاريخ التقرير: {datetime.now().strftime("%Y-%m-%d")}'), 0, 1, 'R')
        
#         # إرجاع PDF كـ bytes
#         output = BytesIO()
#         pdf_content = pdf.output(dest='S').encode('latin-1')
#         output.write(pdf_content)
#         output.seek(0)
        
#         return output.getvalue()
        
#     except Exception as e:
#         print(f"خطأ في إنشاء تقرير الرواتب: {str(e)}")
#         raise Exception(f"فشل في إنشاء تقرير الرواتب: {str(e)}")
