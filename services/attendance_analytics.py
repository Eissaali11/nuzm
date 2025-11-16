"""
خدمة تحليل الحضور والغياب - مشتركة بين Dashboard و Excel Export
توفر بيانات تحليلية محسّنة للحضور حسب القسم والفترة
"""

from datetime import datetime, timedelta, date
import calendar
from sqlalchemy import func, and_, or_
from app import db
from models import Attendance, Employee, Department, employee_departments


class AttendanceAnalytics:
    """خدمة تحليل بيانات الحضور"""
    
    @staticmethod
    def get_period_dates(period='daily', custom_start=None, custom_end=None):
        """
        الحصول على تواريخ البداية والنهاية للفترة المحددة
        
        Args:
            period: نوع الفترة (daily, weekly, monthly)
            custom_start: تاريخ بداية مخصص
            custom_end: تاريخ نهاية مخصص
            
        Returns:
            tuple: (start_date, end_date)
        """
        today = datetime.now().date()
        
        if custom_start and custom_end:
            return custom_start, custom_end
        
        if period == 'daily':
            return today, today
        elif period == 'weekly':
            # حساب بداية الأسبوع من بداية الشهر
            start_of_month = today.replace(day=1)
            days_since_month_start = (today - start_of_month).days
            weeks_since_month_start = days_since_month_start // 7
            start_of_week = start_of_month + timedelta(days=weeks_since_month_start * 7)
            end_of_week = start_of_week + timedelta(days=6)
            
            # التأكد من عدم تجاوز نهاية الشهر
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_of_month = today.replace(day=last_day)
            if end_of_week > end_of_month:
                end_of_week = end_of_month
            
            return start_of_week, min(end_of_week, today)
        elif period == 'monthly':
            start_of_month = today.replace(day=1)
            return start_of_month, today
        else:
            return today, today
    
    @staticmethod
    def get_department_summary(department_id=None, start_date=None, end_date=None, project_name=None):
        """
        الحصول على ملخص الحضور لقسم معين أو جميع الأقسام
        
        Args:
            department_id: معرف القسم (اختياري)
            start_date: تاريخ البداية
            end_date: تاريخ النهاية
            project_name: اسم المشروع للفلترة (اختياري)
            
        Returns:
            dict: ملخص الحضور بالتفاصيل
        """
        if not start_date:
            start_date = datetime.now().date()
        if not end_date:
            end_date = start_date
        
        # جلب الأقسام
        if department_id:
            departments = [Department.query.get(department_id)]
        else:
            departments = Department.query.all()
        
        summary = {
            'total_employees': 0,
            'total_present': 0,
            'total_absent': 0,
            'total_leave': 0,
            'total_sick': 0,
            'total_records': 0,
            'departments': []
        }
        
        for dept in departments:
            if not dept:
                continue
            
            # جلب موظفي القسم النشطين
            employees_query = Employee.query.filter_by(department_id=dept.id, status='active')
            
            # فلترة حسب المشروع إذا تم تحديده
            if project_name:
                employees_query = employees_query.filter_by(project=project_name)
            
            employees = employees_query.all()
            
            if not employees:
                continue
            
            employee_ids = [emp.id for emp in employees]
            
            # جلب سجلات الحضور للفترة المحددة
            attendance_records = Attendance.query.filter(
                Attendance.employee_id.in_(employee_ids),
                Attendance.date >= start_date,
                Attendance.date <= end_date
            ).all()
            
            # حساب الإحصائيات
            present_count = sum(1 for r in attendance_records if r.status == 'present')
            absent_count = sum(1 for r in attendance_records if r.status == 'absent')
            leave_count = sum(1 for r in attendance_records if r.status == 'leave')
            sick_count = sum(1 for r in attendance_records if r.status == 'sick')
            total_records = len(attendance_records)
            
            # حساب نسبة الحضور
            attendance_rate = (present_count / total_records * 100) if total_records > 0 else 0
            
            # جمع أسماء الموظفين الغائبين
            absentees = []
            for record in attendance_records:
                if record.status == 'absent':
                    employee = next((e for e in employees if e.id == record.employee_id), None)
                    if employee:
                        absentees.append({
                            'id': employee.id,
                            'name': employee.name,
                            'employee_id': employee.employee_id,
                            'date': record.date,
                            'notes': record.notes
                        })
            
            # جمع الموظفين في إجازة
            on_leave = []
            for record in attendance_records:
                if record.status == 'leave':
                    employee = next((e for e in employees if e.id == record.employee_id), None)
                    if employee:
                        on_leave.append({
                            'id': employee.id,
                            'name': employee.name,
                            'employee_id': employee.employee_id,
                            'date': record.date,
                            'notes': record.notes
                        })
            
            # جمع الموظفين المرضى
            sick_employees = []
            for record in attendance_records:
                if record.status == 'sick':
                    employee = next((e for e in employees if e.id == record.employee_id), None)
                    if employee:
                        sick_employees.append({
                            'id': employee.id,
                            'name': employee.name,
                            'employee_id': employee.employee_id,
                            'date': record.date,
                            'notes': record.notes
                        })
            
            dept_summary = {
                'id': dept.id,
                'name': dept.name,
                'total_employees': len(employees),
                'present': present_count,
                'absent': absent_count,
                'leave': leave_count,
                'sick': sick_count,
                'total_records': total_records,
                'attendance_rate': round(attendance_rate, 1),
                'absentees': absentees,
                'on_leave': on_leave,
                'sick_employees': sick_employees
            }
            
            summary['departments'].append(dept_summary)
            summary['total_employees'] += len(employees)
            summary['total_present'] += present_count
            summary['total_absent'] += absent_count
            summary['total_leave'] += leave_count
            summary['total_sick'] += sick_count
            summary['total_records'] += total_records
        
        # ترتيب الأقسام حسب نسبة الحضور (تنازلي)
        summary['departments'].sort(key=lambda x: x['attendance_rate'], reverse=True)
        
        # حساب نسبة الحضور الإجمالية
        if summary['total_records'] > 0:
            summary['overall_attendance_rate'] = round(
                summary['total_present'] / summary['total_records'] * 100, 1
            )
        else:
            summary['overall_attendance_rate'] = 0
        
        return summary
    
    @staticmethod
    def get_daily_trend(department_id=None, days=7, project_name=None):
        """
        الحصول على اتجاه الحضور اليومي للأيام السابقة
        
        Args:
            department_id: معرف القسم (اختياري)
            days: عدد الأيام السابقة
            project_name: اسم المشروع للفلترة (اختياري)
            
        Returns:
            list: قائمة بالحضور اليومي
        """
        today = datetime.now().date()
        start_date = today - timedelta(days=days - 1)
        
        trend = []
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            summary = AttendanceAnalytics.get_department_summary(
                department_id=department_id,
                start_date=current_date,
                end_date=current_date,
                project_name=project_name
            )
            
            trend.append({
                'date': current_date,
                'present': summary['total_present'],
                'absent': summary['total_absent'],
                'leave': summary['total_leave'],
                'sick': summary['total_sick'],
                'attendance_rate': summary['overall_attendance_rate']
            })
        
        return trend
    
    @staticmethod
    def get_all_absentees(start_date=None, end_date=None, department_id=None, project_name=None):
        """
        الحصول على قائمة كاملة بجميع الغائبين بالتفاصيل
        
        Args:
            start_date: تاريخ البداية
            end_date: تاريخ النهاية
            department_id: معرف القسم (اختياري)
            project_name: اسم المشروع (اختياري)
            
        Returns:
            list: قائمة الغائبين
        """
        if not start_date:
            start_date = datetime.now().date()
        if not end_date:
            end_date = start_date
        
        # بناء الاستعلام
        query = db.session.query(
            Attendance, Employee, Department
        ).join(
            Employee, Attendance.employee_id == Employee.id
        ).join(
            employee_departments
        ).join(
            Department, employee_departments.c.department_id == Department.id
        ).filter(
            Attendance.date >= start_date,
            Attendance.date <= end_date,
            Attendance.status == 'absent',
            Employee.status == 'active'
        )
        
        # فلترة حسب القسم
        if department_id:
            query = query.filter(Department.id == department_id)
        
        # فلترة حسب المشروع
        if project_name:
            query = query.filter(Employee.project == project_name)
        
        results = query.all()
        
        absentees = []
        for attendance, employee, department in results:
            absentees.append({
                'date': attendance.date,
                'employee_id': employee.employee_id,
                'employee_name': employee.name,
                'department_name': department.name,
                'mobile': employee.mobile or employee.mobilePersonal,
                'notes': attendance.notes or ''
            })
        
        return absentees
