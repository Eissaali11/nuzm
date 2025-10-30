"""
حاسبة الرواتب - ربط الحضور بالرواتب
تحسب الخصومات بناءً على الغياب
"""
from datetime import datetime, timedelta
from models import Attendance, Employee
from calendar import monthrange


def get_attendance_statistics(employee_id, month, year):
    """
    حساب إحصائيات الحضور للموظف في شهر معين
    
    Args:
        employee_id: معرف الموظف
        month: الشهر (1-12)
        year: السنة
        
    Returns:
        dict: إحصائيات الحضور
    """
    try:
        # التأكد من تحويل month و year إلى أرقام
        month = int(month)
        year = int(year)
        employee_id = int(employee_id)
        
        # الحصول على أول وآخر يوم في الشهر
        first_day = datetime(year, month, 1).date()
        _, last_day_num = monthrange(year, month)
        last_day = datetime(year, month, last_day_num).date()
        
        # جلب سجلات الحضور للموظف في هذا الشهر
        attendances = Attendance.query.filter(
            Attendance.employee_id == employee_id,
            Attendance.date >= first_day,
            Attendance.date <= last_day
        ).all()
        
        # حساب الإحصائيات
        total_days = last_day_num
        present_days = sum(1 for a in attendances if a.status == 'present')
        absent_days = sum(1 for a in attendances if a.status == 'absent')
        leave_days = sum(1 for a in attendances if a.status == 'leave')
        sick_days = sum(1 for a in attendances if a.status == 'sick')
        
        # أيام بدون سجل (للمعلومات فقط - لا تُخصم)
        recorded_days = len(attendances)
        unrecorded_days = total_days - recorded_days
        
        return {
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,  # الغياب الصريح فقط
            'leave_days': leave_days,
            'sick_days': sick_days,
            'unrecorded_days': unrecorded_days,  # للمعلومات فقط
            'working_days': present_days,
            'total_absent': absent_days  # نخصم الغياب الصريح فقط
        }
    except Exception as e:
        print(f"خطأ في حساب إحصائيات الحضور: {str(e)}")
        return None


def calculate_absence_deduction(basic_salary, working_days_in_month, absent_days, deduction_policy='working_days'):
    """
    حساب قيمة الخصم بناءً على أيام الغياب
    
    Args:
        basic_salary: الراتب الأساسي الشهري
        working_days_in_month: عدد أيام العمل في الشهر (عادة 26 يوم)
        absent_days: عدد أيام الغياب
        deduction_policy: سياسة الخصم
            - 'working_days': خصم بناءً على أيام العمل فقط (الافتراضي)
            - 'calendar_days': خصم بناءً على جميع أيام الشهر
    
    Returns:
        float: قيمة الخصم
    """
    try:
        if absent_days <= 0:
            return 0.0
        
        # حساب قيمة اليوم الواحد بناءً على أيام العمل فقط
        daily_salary = basic_salary / working_days_in_month
        
        # حساب الخصم
        deduction = daily_salary * absent_days
        
        return round(deduction, 2)
    except Exception as e:
        print(f"خطأ في حساب الخصم: {str(e)}")
        return 0.0


def calculate_salary_with_attendance(employee_id, month, year, basic_salary, allowances=0, bonus=0, 
                                     other_deductions=0, working_days_in_month=30,
                                     exclude_leave=True, exclude_sick=True, attendance_bonus=300.0):
    """
    حساب الراتب بناءً على (أيام الحضور × الأجر اليومي) + حافز 300 ريال للدوام الكامل
    
    Args:
        employee_id: معرف الموظف
        month: الشهر
        year: السنة
        basic_salary: الراتب الأساسي (يُقسم على 30 للحصول على الأجر اليومي)
        allowances: البدلات
        bonus: المكافآت
        other_deductions: خصومات أخرى
        working_days_in_month: عدد الأيام المطلوبة للحافز (افتراضي: 30 يوم)
        exclude_leave: عدم خصم أيام الإجازة الرسمية
        exclude_sick: عدم خصم أيام الإجازة المرضية
        attendance_bonus: حافز الدوام الكامل 300 ريال (يُمنح فقط للحضور 30 يوم)
    
    Returns:
        dict: تفاصيل الراتب المحسوب
    """
    try:
        # جلب إحصائيات الحضور
        attendance_stats = get_attendance_statistics(employee_id, month, year)
        
        # حساب الأجر اليومي من الراتب الأساسي
        daily_wage = round(basic_salary / 30.0, 2)
        
        if not attendance_stats:
            # في حالة عدم وجود سجلات، نرجع الراتب كاملاً + الحافز
            net_salary = basic_salary + attendance_bonus + allowances + bonus - other_deductions
            return {
                'basic_salary': basic_salary,
                'daily_wage': daily_wage,
                'attendance_bonus': attendance_bonus,
                'allowances': allowances,
                'bonus': bonus,
                'attendance_deduction': 0.0,
                'bonus_deduction': 0.0,
                'other_deductions': other_deductions,
                'total_deductions': other_deductions,
                'net_salary': net_salary,
                'attendance_stats': None,
                'paid_days': 30,
                'warning': 'لا توجد سجلات حضور للشهر المحدد'
            }
        
        # حساب أيام الحضور الفعلية التي تستحق الراتب
        paid_days = attendance_stats['present_days']
        
        # إضافة أيام الإجازة الرسمية إذا كانت السياسة تستثنيها من الخصم
        if exclude_leave:
            paid_days += attendance_stats['leave_days']
        
        # إضافة أيام الإجازة المرضية إذا كانت السياسة تستثنيها من الخصم
        if exclude_sick:
            paid_days += attendance_stats['sick_days']
        
        # حساب الراتب المكتسب = أيام الحضور × الأجر اليومي
        earned_salary = round(daily_wage * paid_days, 2)
        
        # الحد الأقصى للراتب المكتسب هو الراتب الأساسي
        if earned_salary > basic_salary:
            earned_salary = basic_salary
        
        # حساب "الخصم" للعرض فقط (الفرق بين الراتب الأساسي والمكتسب)
        attendance_deduction = round(basic_salary - earned_salary, 2)
        
        # الحافز 300 ريال يُمنح فقط إذا حضر الموظف 30 يوم كاملة
        if paid_days >= working_days_in_month:
            earned_bonus = attendance_bonus
            bonus_deduction = 0.0
        else:
            earned_bonus = 0.0
            bonus_deduction = attendance_bonus
        
        # حساب إجمالي الخصومات
        total_deductions = round(attendance_deduction + bonus_deduction + other_deductions, 2)
        
        # حساب صافي الراتب = الراتب المكتسب + الحافز + البدلات + المكافآت - الخصومات الأخرى
        net_salary = round(earned_salary + earned_bonus + allowances + bonus - other_deductions, 2)
        
        print(f"[DEBUG] الموظف {employee_id}: أيام الحضور={paid_days}, الأجر اليومي={daily_wage}, المكتسب={earned_salary}, الحافز={earned_bonus}, الصافي={net_salary}")
        
        return {
            'basic_salary': basic_salary,
            'daily_wage': daily_wage,
            'attendance_bonus': earned_bonus,
            'bonus_deduction': bonus_deduction,
            'allowances': allowances,
            'bonus': bonus,
            'attendance_deduction': attendance_deduction,
            'other_deductions': other_deductions,
            'total_deductions': total_deductions,
            'net_salary': net_salary,
            'attendance_stats': attendance_stats,
            'deductible_days': 30 - paid_days,
            'working_days_in_month': working_days_in_month,
            'paid_days': paid_days,
            'earned_salary': earned_salary,
            'total_days_in_month': attendance_stats['total_days']
        }
    except Exception as e:
        print(f"خطأ في حساب الراتب: {str(e)}")
        return None


def get_attendance_summary_text(attendance_stats):
    """
    إنشاء نص ملخص لإحصائيات الحضور
    
    Args:
        attendance_stats: إحصائيات الحضور
        
    Returns:
        str: نص الملخص
    """
    if not attendance_stats:
        return "لا توجد بيانات حضور"
    
    summary = f"""
    📊 ملخص الحضور:
    - إجمالي أيام الشهر: {attendance_stats['total_days']} يوم
    - أيام الحضور: {attendance_stats['present_days']} يوم ✅
    - أيام الغياب: {attendance_stats['absent_days']} يوم ❌
    - أيام الإجازة: {attendance_stats['leave_days']} يوم 📅
    - أيام الإجازة المرضية: {attendance_stats['sick_days']} يوم 🏥
    - أيام بدون سجل: {attendance_stats['unrecorded_days']} يوم ⚠️
    """
    
    return summary.strip()
