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
        
        # أيام بدون سجل (تعتبر غياب افتراضياً)
        recorded_days = len(attendances)
        unrecorded_days = total_days - recorded_days
        
        return {
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'leave_days': leave_days,
            'sick_days': sick_days,
            'unrecorded_days': unrecorded_days,
            'working_days': present_days,  # الأيام الفعلية للعمل
            'total_absent': absent_days + unrecorded_days  # إجمالي الغياب (المسجل + غير المسجل)
        }
    except Exception as e:
        print(f"خطأ في حساب إحصائيات الحضور: {str(e)}")
        return None


def calculate_absence_deduction(basic_salary, total_days, absent_days, deduction_policy='full'):
    """
    حساب قيمة الخصم بناءً على أيام الغياب
    
    Args:
        basic_salary: الراتب الأساسي الشهري
        total_days: إجمالي أيام الشهر
        absent_days: عدد أيام الغياب
        deduction_policy: سياسة الخصم
            - 'full': خصم كامل قيمة الأيام
            - 'working_days_only': خصم فقط أيام العمل (استبعاد الجمعة والسبت)
            - 'custom_rate': معدل خصم مخصص
    
    Returns:
        float: قيمة الخصم
    """
    try:
        if absent_days <= 0:
            return 0.0
        
        # حساب قيمة اليوم الواحد
        daily_salary = basic_salary / total_days
        
        # حساب الخصم
        if deduction_policy == 'full':
            deduction = daily_salary * absent_days
        elif deduction_policy == 'working_days_only':
            # افتراض 26 يوم عمل في الشهر (استبعاد الجمعة)
            working_days_salary = basic_salary / 26
            deduction = working_days_salary * absent_days
        else:
            # السياسة الافتراضية
            deduction = daily_salary * absent_days
        
        return round(deduction, 2)
    except Exception as e:
        print(f"خطأ في حساب الخصم: {str(e)}")
        return 0.0


def calculate_salary_with_attendance(employee_id, month, year, basic_salary, allowances=0, bonus=0, 
                                     other_deductions=0, deduction_policy='full', 
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
        deduction_policy: سياسة الخصم
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
        
        # حساب أيام الغياب التي سيتم خصمها
        deductible_absent_days = attendance_stats['absent_days'] + attendance_stats['unrecorded_days']
        
        # استبعاد أيام الإجازة الرسمية إذا كانت السياسة تسمح
        if exclude_leave:
            # لا نخصم أيام الإجازة الرسمية
            pass
        else:
            deductible_absent_days += attendance_stats['leave_days']
        
        # استبعاد أيام الإجازة المرضية إذا كانت السياسة تسمح
        if exclude_sick:
            # لا نخصم أيام الإجازة المرضية
            pass
        else:
            deductible_absent_days += attendance_stats['sick_days']
        
        # حساب قيمة الخصم
        attendance_deduction = calculate_absence_deduction(
            basic_salary,
            attendance_stats['total_days'],
            deductible_absent_days,
            deduction_policy
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
            'deductible_days': deductible_absent_days
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
