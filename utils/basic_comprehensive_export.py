from datetime import date, datetime
from io import BytesIO
import pandas as pd

def generate_comprehensive_employee_excel(employees):
    """إنشاء ملف Excel شامل لبيانات الموظفين - نسخة أساسية جداً"""
    try:
        # قائمة البيانات
        data_rows = []
        
        for employee in employees:
            try:
                # بيانات أساسية فقط بدون التعقيدات
                row = {
                    'رقم الموظف': str(employee.employee_id) if employee.employee_id else '',
                    'الاسم': str(employee.name) if employee.name else '',
                    'رقم الهوية': str(employee.national_id) if employee.national_id else '',
                    'رقم الجوال': str(employee.mobile) if employee.mobile else '',
                    'الإيميل': str(employee.email) if employee.email else '',
                    'المنصب': str(employee.job_title) if employee.job_title else '',
                    'الحالة': str(employee.status) if employee.status else '',
                    'الموقع': str(employee.location) if employee.location else '',
                    'المشروع': str(employee.project) if employee.project else '',
                    'الجنسية': str(employee.nationality) if employee.nationality else '',
                    'نوع العقد': str(employee.contract_type) if employee.contract_type else '',
                    'الراتب الأساسي': employee.basic_salary if employee.basic_salary else 0,
                    'حالة العقد': str(employee.contract_status) if employee.contract_status else '',
                    'حالة الرخصة': str(employee.license_status) if employee.license_status else '',
                    'ملاحظات': str(employee.notes) if hasattr(employee, 'notes') and employee.notes else '',
                    'نوع الموظف': str(employee.employee_type) if employee.employee_type else '',
                    'عهدة جوال': 'نعم' if employee.has_mobile_custody else 'لا',
                    'نوع الجوال': str(employee.mobile_type) if employee.mobile_type else '',
                    'رقم IMEI': str(employee.mobile_imei) if employee.mobile_imei else '',
                    'حالة الكفالة': str(employee.sponsorship_status) if employee.sponsorship_status else '',
                    'اسم الكفيل': str(employee.current_sponsor_name) if employee.current_sponsor_name else '',
                    'رقم الإيبان': str(employee.bank_iban) if employee.bank_iban else '',
                    'صورة إيبان': 'نعم' if employee.bank_iban_image else 'لا',
                    'صورة شخصية': 'نعم' if employee.profile_image else 'لا',
                    'صورة هوية': 'نعم' if employee.national_id_image else 'لا',
                    'صورة رخصة': 'نعم' if employee.license_image else 'لا',
                    'تفاصيل السكن': str(employee.residence_details) if employee.residence_details else '',
                    'رابط موقع السكن': str(employee.residence_location_url) if employee.residence_location_url else '',
                    'مقاس البنطلون': str(employee.pants_size) if employee.pants_size else '',
                    'مقاس التيشرت': str(employee.shirt_size) if employee.shirt_size else ''
                }
                
                # إضافة التواريخ بأمان
                if employee.join_date:
                    row['تاريخ الانضمام'] = employee.join_date.strftime('%Y-%m-%d')
                else:
                    row['تاريخ الانضمام'] = ''
                    
                if employee.birth_date:
                    row['تاريخ الميلاد'] = employee.birth_date.strftime('%Y-%m-%d')
                else:
                    row['تاريخ الميلاد'] = ''
                
                if employee.created_at:
                    row['تاريخ الإنشاء'] = employee.created_at.strftime('%Y-%m-%d %H:%M')
                else:
                    row['تاريخ الإنشاء'] = ''
                
                # محاولة جلب الأقسام بأمان
                departments_text = ''
                try:
                    if hasattr(employee, 'departments') and employee.departments:
                        dept_names = []
                        for dept in employee.departments:
                            # تجنب استخدام .name مباشرة
                            if hasattr(dept, 'name') and dept.name:
                                dept_names.append(str(dept.name))
                        departments_text = ' | '.join(dept_names)
                except Exception as dept_error:
                    print(f"خطأ في جلب الأقسام للموظف {employee.name}: {str(dept_error)}")
                    departments_text = 'خطأ في جلب الأقسام'
                
                row['الأقسام'] = departments_text
                
                # إحصائيات بسيطة للوثائق
                try:
                    if hasattr(employee, 'documents') and employee.documents:
                        row['عدد الوثائق'] = len(employee.documents)
                    else:
                        row['عدد الوثائق'] = 0
                except:
                    row['عدد الوثائق'] = 0
                
                # إحصائيات بسيطة للرواتب
                try:
                    if hasattr(employee, 'salaries') and employee.salaries:
                        row['عدد سجلات الراتب'] = len(employee.salaries)
                    else:
                        row['عدد سجلات الراتب'] = 0
                except:
                    row['عدد سجلات الراتب'] = 0
                
                # إحصائيات بسيطة للحضور
                try:
                    if hasattr(employee, 'attendances') and employee.attendances:
                        row['عدد سجلات الحضور'] = len(employee.attendances)
                    else:
                        row['عدد سجلات الحضور'] = 0
                except:
                    row['عدد سجلات الحضور'] = 0
                
                data_rows.append(row)
                
            except Exception as employee_error:
                print(f"خطأ في معالجة موظف: {str(employee_error)}")
                # إضافة سجل خطأ للموظف
                error_row = {
                    'رقم الموظف': 'خطأ',
                    'الاسم': f'خطأ في معالجة الموظف: {str(employee_error)}',
                    'رقم الهوية': '',
                    'رقم الجوال': '',
                    'الإيميل': '',
                    'المنصب': '',
                    'الحالة': '',
                    'الموقع': '',
                    'المشروع': '',
                    'الجنسية': '',
                    'نوع العقد': '',
                    'الراتب الأساسي': 0,
                    'حالة العقد': '',
                    'حالة الرخصة': '',
                    'ملاحظات': '',
                    'نوع الموظف': '',
                    'عهدة جوال': '',
                    'نوع الجوال': '',
                    'رقم IMEI': '',
                    'حالة الكفالة': '',
                    'اسم الكفيل': '',
                    'رقم الإيبان': '',
                    'صورة إيبان': '',
                    'صورة شخصية': '',
                    'صورة هوية': '',
                    'صورة رخصة': '',
                    'تفاصيل السكن': '',
                    'رابط موقع السكن': '',
                    'مقاس البنطلون': '',
                    'مقاس التيشرت': '',
                    'تاريخ الانضمام': '',
                    'تاريخ الميلاد': '',
                    'تاريخ الإنشاء': '',
                    'الأقسام': '',
                    'عدد الوثائق': 0,
                    'عدد سجلات الراتب': 0,
                    'عدد سجلات الحضور': 0
                }
                data_rows.append(error_row)
                continue
        
        # إنشاء DataFrame
        if not data_rows:
            # إذا لم تكن هناك بيانات
            df = pd.DataFrame([{
                'رسالة': 'لا توجد بيانات موظفين متاحة',
                'التاريخ': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }])
        else:
            df = pd.DataFrame(data_rows)
        
        # إنشاء ملف Excel في الذاكرة
        output = BytesIO()
        
        # استخدام pandas لكتابة Excel
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='بيانات الموظفين الشاملة', index=False)
            
            # إضافة ورقة إحصائيات بسيطة
            if data_rows:
                stats = {
                    'إجمالي الموظفين': len(data_rows),
                    'موظفون نشطون': len([r for r in data_rows if r.get('الحالة') == 'active']),
                    'لديهم عهدة جوال': len([r for r in data_rows if r.get('عهدة جوال') == 'نعم']),
                    'لديهم صورة شخصية': len([r for r in data_rows if r.get('صورة شخصية') == 'نعم']),
                    'لديهم رقم إيبان': len([r for r in data_rows if r.get('رقم الإيبان', '') != '']),
                    'تاريخ التصدير': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                stats_df = pd.DataFrame(list(stats.items()), columns=['البيان', 'القيمة'])
                stats_df.to_excel(writer, sheet_name='إحصائيات سريعة', index=False)
        
        output.seek(0)
        return output
        
    except Exception as main_error:
        print(f"خطأ رئيسي في إنشاء ملف Excel: {str(main_error)}")
        
        # إنشاء ملف Excel بسيط جداً مع رسالة الخطأ
        error_output = BytesIO()
        error_df = pd.DataFrame([{
            'رسالة الخطأ': f'فشل في إنشاء التصدير: {str(main_error)}',
            'الوقت': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'نصيحة': 'تواصل مع الدعم الفني'
        }])
        
        with pd.ExcelWriter(error_output, engine='openpyxl') as writer:
            error_df.to_excel(writer, sheet_name='رسالة خطأ', index=False)
        
        error_output.seek(0)
        return error_output