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
                                     other_deductions=0, working_days_in_month=26,
                                     exclude_leave=True, exclude_sick=True):
    """
    حساب الراتب النهائي مع الأخذ في الاعتبار الحضور والغياب
    
    Args:
        employee_id: معرف الموظف
        month: الشهر
        year: السنة
        basic_salary: الراتب الأساسي
        allowances: البدلات
        bonus: المكافآت
        other_deductions: خصومات أخرى
        working_days_in_month: عدد أيام العمل في الشهر (افتراضي: 26 يوم)
        exclude_leave: عدم خصم أيام الإجازة الرسمية
        exclude_sick: عدم خصم أيام الإجازة المرضية
    
    Returns:
        dict: تفاصيل الراتب المحسوب
    """
    try:
        # جلب إحصائيات الحضور
        attendance_stats = get_attendance_statistics(employee_id, month, year)
        
        if not attendance_stats:
            # في حالة عدم وجود سجلات، نرجع الراتب كاملاً
            net_salary = basic_salary + allowances + bonus - other_deductions
            return {
                'basic_salary': basic_salary,
                'allowances': allowances,
                'bonus': bonus,
                'attendance_deduction': 0.0,
                'other_deductions': other_deductions,
                'total_deductions': other_deductions,
                'net_salary': net_salary,
                'attendance_stats': None,
                'warning': 'لا توجد سجلات حضور للشهر المحدد'
            }
        
        # حساب أيام الغياب التي سيتم خصمها (الغياب الصريح فقط)
        # لا نخصم الأيام غير المسجلة بشكل افتراضي (عطلات نهاية الأسبوع والعطل الرسمية)
        deductible_absent_days = attendance_stats['absent_days']
        
        # إضافة أيام الإجازة الرسمية إذا كانت السياسة تقتضي خصمها
        if not exclude_leave:
            deductible_absent_days += attendance_stats['leave_days']
        
        # إضافة أيام الإجازة المرضية إذا كانت السياسة تقتضي خصمها
        if not exclude_sick:
            deductible_absent_days += attendance_stats['sick_days']
        
        # حساب قيمة الخصم بناءً على أيام العمل فقط
        attendance_deduction = calculate_absence_deduction(
            basic_salary,
            working_days_in_month,
            deductible_absent_days,
            'working_days'
        )
        
        # حساب إجمالي الخصومات
        total_deductions = attendance_deduction + other_deductions
        
        # حساب صافي الراتب
        net_salary = basic_salary + allowances + bonus - total_deductions
        
        return {
            'basic_salary': basic_salary,
            'allowances': allowances,
            'bonus': bonus,
            'attendance_deduction': attendance_deduction,
            'other_deductions': other_deductions,
            'total_deductions': total_deductions,
            'net_salary': net_salary,
            'attendance_stats': attendance_stats,
            'deductible_days': deductible_absent_days,
            'working_days_in_month': working_days_in_month
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
