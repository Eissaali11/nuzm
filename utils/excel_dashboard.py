"""
دالة التصدير مع داش بورد خيالي لنظام الحضور
"""
from io import BytesIO
from datetime import timedelta
import xlsxwriter


def export_attendance_by_department_with_dashboard(employees, attendances, start_date, end_date=None):
    """
    تصدير بيانات الحضور مع داش بورد خيالي ومبهر
    
    Args:
        employees: قائمة بجميع الموظفين
        attendances: قائمة بسجلات الحضور
        start_date: تاريخ البداية
        end_date: تاريخ النهاية
    
    Returns:
        BytesIO: كائن يحتوي على ملف اكسل
    """
    try:
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        # تحديد الفترة الزمنية
        if end_date is None:
            end_date = start_date
        
        # ========== تنسيقات الداش بورد ==========
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 24,
            'font_color': 'white',
            'bg_color': '#667EEA',
            'align': 'center',
            'valign': 'vcenter',
            'border': 2
        })
        
        subtitle_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'font_color': 'white',
            'bg_color': '#764BA2',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        kpi_label_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#E9ECEF',
            'border': 1
        })
        
        kpi_value_success = workbook.add_format({
            'bold': True,
            'font_size': 20,
            'font_color': '#28A745',
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#D4EDDA',
            'border': 2
        })
        
        kpi_value_danger = workbook.add_format({
            'bold': True,
            'font_size': 20,
            'font_color': '#DC3545',
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#F8D7DA',
            'border': 2
        })
        
        kpi_value_warning = workbook.add_format({
            'bold': True,
            'font_size': 20,
            'font_color': '#FFC107',
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#FFF3CD',
            'border': 2
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#00B0B0',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        normal_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        absent_row_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#FFEBEE'
        })
        
        # ========== إنشاء ورقة الداش بورد ==========
        dashboard = workbook.add_worksheet('📊 لوحة المعلومات')
        
        # العنوان الرئيسي
        dashboard.merge_range('A1:H1', '📊 لوحة معلومات الحضور الشهري - جميع الأقسام', title_format)
        dashboard.set_row(0, 40)
        
        # الفترة الزمنية
        period_text = f'الفترة: من {start_date.strftime("%Y-%m-%d")} إلى {end_date.strftime("%Y-%m-%d")}'
        dashboard.merge_range('A2:H2', period_text, subtitle_format)
        dashboard.set_row(1, 30)
        
        # حساب الإحصائيات العامة
        attendance_data = {}
        for att in attendances:
            emp_id = att.employee_id
            if emp_id not in attendance_data:
                attendance_data[emp_id] = {}
            attendance_data[emp_id][att.date] = att.status
        
        total_present = sum(1 for att in attendances if att.status == 'present')
        total_absent = sum(1 for att in attendances if att.status == 'absent')
        total_leave = sum(1 for att in attendances if att.status == 'leave')
        total_sick = sum(1 for att in attendances if att.status == 'sick')
        total_records = len(attendances)
        
        # حساب نسبة الحضور
        attendance_rate = (total_present / total_records * 100) if total_records > 0 else 0
        
        # بطاقات KPI
        row = 4
        dashboard.merge_range(f'A{row}:B{row}', '✅ إجمالي الحضور', kpi_label_format)
        dashboard.merge_range(f'C{row}:D{row}', total_present, kpi_value_success)
        
        dashboard.merge_range(f'E{row}:F{row}', '❌ إجمالي الغياب', kpi_label_format)
        dashboard.merge_range(f'G{row}:H{row}', total_absent, kpi_value_danger)
        dashboard.set_row(row-1, 35)
        
        row += 2
        dashboard.merge_range(f'A{row}:B{row}', '🏖️ إجازات', kpi_label_format)
        dashboard.merge_range(f'C{row}:D{row}', total_leave, kpi_value_warning)
        
        dashboard.merge_range(f'E{row}:F{row}', '🏥 إجازات مرضية', kpi_label_format)
        dashboard.merge_range(f'G{row}:H{row}', total_sick, kpi_value_warning)
        dashboard.set_row(row-1, 35)
        
        row += 2
        dashboard.merge_range(f'A{row}:D{row}', '📈 نسبة الحضور', kpi_label_format)
        dashboard.merge_range(f'E{row}:H{row}', f'{attendance_rate:.1f}%', kpi_value_success)
        dashboard.set_row(row-1, 35)
        
        # إحصائيات الأقسام
        row += 3
        dashboard.merge_range(f'A{row}:H{row}', '📋 إحصائيات الأقسام', subtitle_format)
        dashboard.set_row(row-1, 30)
        
        row += 1
        headers = ['القسم', 'عدد الموظفين', 'الحضور', 'الغياب', 'الإجازات', 'الإجازات المرضية', 'إجمالي السجلات', 'نسبة الحضور %']
        for col, header in enumerate(headers):
            dashboard.write(row-1, col, header, header_format)
        
        # تنظيم الموظفين حسب الأقسام
        departments = {}
        for employee in employees:
            dept_name = ', '.join([dept.name for dept in employee.departments]) if employee.departments else 'بدون قسم'
            if dept_name not in departments:
                departments[dept_name] = []
            departments[dept_name].append(employee)
        
        # حساب إحصائيات كل قسم
        for dept_name, dept_employees in sorted(departments.items()):
            emp_ids = [emp.id for emp in dept_employees]
            dept_attendances = [att for att in attendances if att.employee_id in emp_ids]
            
            dept_present = sum(1 for att in dept_attendances if att.status == 'present')
            dept_absent = sum(1 for att in dept_attendances if att.status == 'absent')
            dept_leave = sum(1 for att in dept_attendances if att.status == 'leave')
            dept_sick = sum(1 for att in dept_attendances if att.status == 'sick')
            dept_total = len(dept_attendances)
            dept_rate = (dept_present / dept_total * 100) if dept_total > 0 else 0
            
            dashboard.write(row, 0, dept_name, normal_format)
            dashboard.write(row, 1, len(dept_employees), normal_format)
            dashboard.write(row, 2, dept_present, normal_format)
            dashboard.write(row, 3, dept_absent, normal_format)
            dashboard.write(row, 4, dept_leave, normal_format)
            dashboard.write(row, 5, dept_sick, normal_format)
            dashboard.write(row, 6, dept_total, normal_format)
            dashboard.write(row, 7, f'{dept_rate:.1f}%', normal_format)
            row += 1
        
        # قائمة الموظفين الغائبين
        row += 2
        dashboard.merge_range(f'A{row}:H{row}', '🚨 قائمة الموظفين الغائبين', subtitle_format)
        dashboard.set_row(row-1, 30)
        
        row += 1
        headers = ['التاريخ', 'اسم الموظف', 'رقم الموظف', 'القسم', 'المسمى الوظيفي', 'نوع الغياب']
        for col, header in enumerate(headers[:6]):
            dashboard.write(row-1, col, header, header_format)
        
        # جمع جميع حالات الغياب
        absent_records = []
        for att in attendances:
            if att.status in ['absent', 'leave', 'sick']:
                emp = next((e for e in employees if e.id == att.employee_id), None)
                if emp:
                    dept_name = ', '.join([d.name for d in emp.departments]) if emp.departments else 'بدون قسم'
                    status_ar = {'absent': '❌ غياب', 'leave': '🏖️ إجازة', 'sick': '🏥 مرضي'}
                    absent_records.append({
                        'date': att.date,
                        'name': emp.name,
                        'emp_id': emp.employee_id,
                        'dept': dept_name,
                        'job': emp.job_title or '-',
                        'status': status_ar.get(att.status, att.status)
                    })
        
        # ترتيب حسب التاريخ
        absent_records.sort(key=lambda x: x['date'], reverse=True)
        
        # كتابة سجلات الغياب
        for record in absent_records[:50]:  # أول 50 سجل
            dashboard.write(row, 0, record['date'].strftime('%Y-%m-%d'), absent_row_format)
            dashboard.write(row, 1, record['name'], absent_row_format)
            dashboard.write(row, 2, record['emp_id'], absent_row_format)
            dashboard.write(row, 3, record['dept'], absent_row_format)
            dashboard.write(row, 4, record['job'], absent_row_format)
            dashboard.write(row, 5, record['status'], absent_row_format)
            row += 1
        
        # ضبط عرض الأعمدة
        dashboard.set_column('A:A', 15)
        dashboard.set_column('B:B', 25)
        dashboard.set_column('C:C', 15)
        dashboard.set_column('D:D', 20)
        dashboard.set_column('E:E', 20)
        dashboard.set_column('F:F', 15)
        dashboard.set_column('G:G', 18)
        dashboard.set_column('H:H', 18)
        
        # ========== إضافة أوراق الأقسام ==========
        # تنسيقات للأقسام
        date_header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#00B0B0',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True
        })
        
        right_aligned_format = workbook.add_format({
            'border': 1,
            'align': 'right',
            'valign': 'vcenter'
        })
        
        present_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'bold': True,
            'font_color': '#006100'
        })
        
        absent_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'bold': True,
            'font_color': '#FF0000'
        })
        
        leave_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': '#FF9900'
        })
        
        sick_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': '#0070C0'
        })
        
        # تحديد قائمة التواريخ
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)
        
        weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        
        # إنشاء ورقة لكل قسم
        for dept_name, dept_employees in sorted(departments.items()):
            sheet_name = dept_name[:31]
            worksheet = workbook.add_worksheet(sheet_name)
            
            col_headers = ["Name", "ID Number", "Emp. No.", "Job Title", "No. Mobile", "Car", "Location", "Project", "Total"]
            
            for col_idx, header in enumerate(col_headers):
                worksheet.write(1, col_idx, header, header_format)
            
            first_date_col = len(col_headers)
            
            for col_idx, date in enumerate(date_list):
                day_of_week = weekdays[date.weekday()]
                date_str = date.strftime("%d/%m/%Y")
                day_header = f"{day_of_week}\n{date_str}"
                col = first_date_col + col_idx
                worksheet.write(0, col, day_header, date_header_format)
            
            worksheet.set_column(0, 0, 30)
            worksheet.set_column(1, 1, 15)
            worksheet.set_column(2, 2, 12)
            worksheet.set_column(3, 3, 20)
            worksheet.set_column(4, 4, 15)
            worksheet.set_column(5, 5, 10)
            worksheet.set_column(6, 6, 15)
            worksheet.set_column(7, 7, 15)
            worksheet.set_column(8, 8, 10)
            
            for col_idx in range(len(date_list)):
                col = first_date_col + col_idx
                worksheet.set_column(col, col, 4)
            
            worksheet.set_row(0, 30)
            worksheet.set_row(1, 20)
            
            row = 2
            for employee in dept_employees:
                worksheet.write(row, 0, employee.name, right_aligned_format)
                worksheet.write(row, 1, employee.national_id or '', normal_format)
                worksheet.write(row, 2, employee.employee_id, normal_format)
                worksheet.write(row, 3, employee.job_title or '', right_aligned_format)
                worksheet.write(row, 4, employee.mobile or '', normal_format)
                worksheet.write(row, 5, '', normal_format)
                worksheet.write(row, 6, '', normal_format)
                worksheet.write(row, 7, employee.project or '', right_aligned_format)
                
                present_days = 0
                for col_idx, date in enumerate(date_list):
                    col = first_date_col + col_idx
                    
                    if employee.id in attendance_data and date in attendance_data[employee.id]:
                        status = attendance_data[employee.id][date]
                        if status == 'present':
                            cell_value = "P"
                            cell_format = present_format
                            present_days += 1
                        elif status == 'absent':
                            cell_value = "A"
                            cell_format = absent_format
                        elif status == 'leave':
                            cell_value = "L"
                            cell_format = leave_format
                        elif status == 'sick':
                            cell_value = "S"
                            cell_format = sick_format
                    else:
                        cell_value = "P"
                        cell_format = present_format
                        present_days += 1
                    
                    worksheet.write(row, col, cell_value, cell_format)
                
                worksheet.write(row, 8, present_days, normal_format)
                row += 1
        
        # ورقة دليل الرموز
        legend_sheet = workbook.add_worksheet('دليل الرموز')
        
        title_format2 = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        description_format = workbook.add_format({
            'align': 'right',
            'valign': 'vcenter',
            'text_wrap': True
        })
        
        legend_sheet.merge_range('A1:B1', 'دليل رموز الحضور والغياب', title_format2)
        legend_sheet.set_column(0, 0, 10)
        legend_sheet.set_column(1, 1, 40)
        
        legend_sheet.write(2, 0, 'P', present_format)
        legend_sheet.write(2, 1, 'حاضر (Present)', description_format)
        
        legend_sheet.write(3, 0, 'A', absent_format)
        legend_sheet.write(3, 1, 'غائب (Absent)', description_format)
        
        legend_sheet.write(4, 0, 'L', leave_format)
        legend_sheet.write(4, 1, 'إجازة (Leave)', description_format)
        
        legend_sheet.write(5, 0, 'S', sick_format)
        legend_sheet.write(5, 1, 'مرضي (Sick Leave)', description_format)
        
        workbook.close()
        output.seek(0)
        return output
    
    except Exception as e:
        import traceback
        print(f"Error generating dashboard Excel: {str(e)}")
        print(traceback.format_exc())
        raise
