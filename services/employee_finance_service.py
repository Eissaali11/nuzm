"""
خدمة الشؤون المالية للموظفين
تتعامل مع الالتزامات المالية، السلف، الأقساط، والملخصات المالية
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import func, and_, or_
from app import db
from models import (
    Employee, EmployeeLiability, LiabilityInstallment, EmployeeRequest,
    Salary, LiabilityType, LiabilityStatus, InstallmentStatus, AdvancePaymentRequest
)


class EmployeeFinanceService:
    """خدمة إدارة الشؤون المالية للموظفين"""
    
    @staticmethod
    def get_liability_type_arabic(liability_type):
        """ترجمة نوع الالتزام للعربية"""
        translations = {
            'damage': 'تلفيات',
            'debt': 'ديون',
            'advance_repayment': 'سداد سلفة',
            'other': 'أخرى'
        }
        if isinstance(liability_type, str):
            return translations.get(liability_type, liability_type)
        return translations.get(liability_type.value, liability_type.value)
    
    @staticmethod
    def get_status_arabic(status):
        """ترجمة الحالة للعربية"""
        translations = {
            'active': 'نشط',
            'paid': 'مدفوع',
            'cancelled': 'ملغي',
            'pending': 'قيد الانتظار',
            'overdue': 'متأخر'
        }
        if isinstance(status, str):
            return translations.get(status, status)
        return translations.get(status.value, status.value)
    
    @staticmethod
    def get_employee_liabilities(employee_id, status_filter=None, liability_type_filter=None):
        """
        جلب التزامات الموظف مع حساب الأقساط
        
        Args:
            employee_id: رقم الموظف
            status_filter: تصفية حسب الحالة ('active', 'paid', 'all')
            liability_type_filter: تصفية حسب النوع
        
        Returns:
            dict: بيانات الالتزامات مع الإحصائيات
        
        Raises:
            ValueError: إذا كانت القيمة المدخلة لـ liability_type غير صالحة
        """
        query = EmployeeLiability.query.filter_by(employee_id=employee_id)
        
        if status_filter and status_filter != 'all':
            valid_statuses = ['active', 'paid', 'cancelled']
            if status_filter not in valid_statuses:
                raise ValueError(f"حالة غير صالحة. القيم المسموح بها: {', '.join(valid_statuses)}")
            
            if status_filter == 'active':
                query = query.filter_by(status=LiabilityStatus.ACTIVE)
            elif status_filter == 'paid':
                query = query.filter_by(status=LiabilityStatus.PAID)
            elif status_filter == 'cancelled':
                query = query.filter_by(status=LiabilityStatus.CANCELLED)
        
        if liability_type_filter:
            try:
                liability_type_enum = LiabilityType(liability_type_filter)
                query = query.filter_by(liability_type=liability_type_enum)
            except ValueError:
                valid_types = [t.value for t in LiabilityType]
                raise ValueError(f"نوع التزام غير صالح. القيم المسموح بها: {', '.join(valid_types)}")
        
        liabilities = query.order_by(EmployeeLiability.created_at.desc()).all()
        
        result = []
        total_liabilities = Decimal('0')
        active_liabilities = Decimal('0')
        paid_liabilities = Decimal('0')
        
        for liability in liabilities:
            installments_data = []
            installments_list = liability.installments.order_by(LiabilityInstallment.installment_number).all()
            
            for inst in installments_list:
                installments_data.append({
                    'id': inst.id,
                    'installment_number': inst.installment_number,
                    'amount': float(inst.amount) if inst.amount else 0.0,
                    'due_date': inst.due_date.isoformat() if inst.due_date else None,
                    'status': inst.status.value if inst.status else 'pending',
                    'status_ar': EmployeeFinanceService.get_status_arabic(inst.status) if inst.status else 'قيد الانتظار',
                    'paid_date': inst.paid_date.isoformat() if inst.paid_date else None,
                    'paid_amount': float(inst.paid_amount) if inst.paid_amount else 0.0
                })
            
            total_liabilities += liability.amount
            if liability.status == LiabilityStatus.ACTIVE:
                active_liabilities += liability.remaining_amount
            elif liability.status == LiabilityStatus.PAID:
                paid_liabilities += liability.amount
            
            next_installment = liability.installments.filter_by(status=InstallmentStatus.PENDING).order_by(
                LiabilityInstallment.due_date).first()
            
            result.append({
                'id': liability.id,
                'type': liability.liability_type.value if liability.liability_type else 'other',
                'type_ar': EmployeeFinanceService.get_liability_type_arabic(liability.liability_type) if liability.liability_type else 'أخرى',
                'total_amount': float(liability.amount) if liability.amount else 0.0,
                'remaining_amount': float(liability.remaining_amount) if liability.remaining_amount else 0.0,
                'paid_amount': float(liability.paid_amount) if liability.paid_amount else 0.0,
                'status': liability.status.value if liability.status else 'active',
                'status_ar': EmployeeFinanceService.get_status_arabic(liability.status) if liability.status else 'نشط',
                'start_date': liability.created_at.date().isoformat() if liability.created_at else datetime.now().date().isoformat(),
                'due_date': liability.due_date.isoformat() if liability.due_date else None,
                'description': liability.description if liability.description else '',
                'installments_total': len(installments_list),
                'installments_paid': liability.installments.filter_by(status=InstallmentStatus.PAID).count(),
                'installments': installments_data,
                'next_due_date': next_installment.due_date.isoformat() if next_installment and next_installment.due_date else None,
                'next_due_amount': float(next_installment.amount) if next_installment and next_installment.amount else 0.0
            })
        
        return {
            'total_liabilities': float(total_liabilities),
            'active_liabilities': float(active_liabilities),
            'paid_liabilities': float(paid_liabilities),
            'liabilities': result
        }
    
    @staticmethod
    def get_financial_summary(employee_id):
        """
        حساب الملخص المالي الشامل للموظف
        
        Args:
            employee_id: رقم الموظف
        
        Returns:
            dict: الملخص المالي الشامل
        """
        employee = Employee.query.get(employee_id)
        if not employee:
            return None
        
        liabilities_data = EmployeeFinanceService.get_employee_liabilities(employee_id)
        
        last_salary = Salary.query.filter_by(employee_id=employee_id).order_by(
            Salary.year.desc(), Salary.month.desc()).first()
        
        from models import RequestStatus
        
        requests_stats = {
            'pending': EmployeeRequest.query.filter_by(
                employee_id=employee_id, status=RequestStatus.PENDING).count(),
            'approved': EmployeeRequest.query.filter_by(
                employee_id=employee_id, status=RequestStatus.APPROVED).count(),
            'rejected': EmployeeRequest.query.filter_by(
                employee_id=employee_id, status=RequestStatus.REJECTED).count()
        }
        
        next_installment = db.session.query(LiabilityInstallment).join(EmployeeLiability).filter(
            EmployeeLiability.employee_id == employee_id,
            LiabilityInstallment.status == InstallmentStatus.PENDING
        ).order_by(LiabilityInstallment.due_date).first()
        
        total_earnings = db.session.query(func.coalesce(func.sum(Salary.net_salary), 0)).filter(
            Salary.employee_id == employee_id).scalar()
        
        total_deductions = db.session.query(func.coalesce(func.sum(Salary.deductions), 0)).filter(
            Salary.employee_id == employee_id).scalar()
        
        current_balance = float(total_earnings or 0) - float(total_deductions or 0)
        
        monthly_summary = None
        if last_salary:
            total_income = float(last_salary.net_salary or 0)
            total_deductions_monthly = float(last_salary.deductions or 0)
            
            monthly_installments = db.session.query(func.coalesce(func.sum(LiabilityInstallment.amount), 0)).join(
                EmployeeLiability
            ).filter(
                EmployeeLiability.employee_id == employee_id,
                LiabilityInstallment.status.in_([InstallmentStatus.PENDING, InstallmentStatus.PAID]),
                LiabilityInstallment.due_date >= date.today().replace(day=1),
                LiabilityInstallment.due_date < (date.today().replace(day=1) + timedelta(days=32)).replace(day=1)
            ).scalar()
            
            monthly_summary = {
                'total_income': total_income,
                'total_deductions': total_deductions_monthly,
                'installments': float(monthly_installments or 0),
                'net_income': total_income - total_deductions_monthly - float(monthly_installments or 0)
            }
        
        return {
            'current_balance': current_balance,
            'total_earnings': float(total_earnings or 0),
            'total_deductions': float(total_deductions or 0),
            'active_liabilities': liabilities_data.get('active_liabilities', 0) if liabilities_data else 0,
            'paid_liabilities': liabilities_data.get('paid_liabilities', 0) if liabilities_data else 0,
            'pending_requests': requests_stats.get('pending', 0),
            'approved_requests': requests_stats.get('approved', 0),
            'rejected_requests': requests_stats.get('rejected', 0),
            'last_salary': {
                'amount': float(last_salary.net_salary) if last_salary and last_salary.net_salary else 0,
                'month': f"{last_salary.year}-{last_salary.month:02d}" if last_salary and last_salary.year and last_salary.month else None,
                'paid_date': last_salary.created_at.isoformat() if last_salary and last_salary.created_at else None
            } if last_salary else None,
            'upcoming_installment': {
                'amount': float(next_installment.amount) if next_installment.amount else 0,
                'due_date': next_installment.due_date.isoformat() if next_installment.due_date else None,
                'liability_type': next_installment.liability.liability_type.value if next_installment.liability and next_installment.liability.liability_type else 'other',
                'liability_type_ar': EmployeeFinanceService.get_liability_type_arabic(next_installment.liability.liability_type) if next_installment.liability and next_installment.liability.liability_type else 'أخرى'
            } if next_installment else None,
            'monthly_summary': monthly_summary
        }
    
    @staticmethod
    def create_liability_from_advance_payment(advance_request, approved_by_user_id=None):
        """
        إنشاء التزام مالي من طلب سلفة معتمد
        
        Args:
            advance_request: كائن AdvancePaymentRequest
            approved_by_user_id: معرف المستخدم الذي اعتمد السلفة
        
        Returns:
            EmployeeLiability: الالتزام المنشأ
        """
        employee_request = advance_request.request
        
        liability = EmployeeLiability(
            employee_id=employee_request.employee_id,
            liability_type=LiabilityType.ADVANCE_REPAYMENT,
            amount=advance_request.requested_amount,
            remaining_amount=advance_request.requested_amount,
            paid_amount=Decimal('0'),
            description=f"سداد سلفة - {advance_request.reason or 'بدون سبب'}",
            reference_type='advance_payment',
            employee_request_id=employee_request.id,
            status=LiabilityStatus.ACTIVE,
            created_by=approved_by_user_id
        )
        
        monthly_installment = advance_request.requested_amount / advance_request.installments
        
        for i in range(1, advance_request.installments + 1):
            installment = LiabilityInstallment(
                liability=liability,
                installment_number=i,
                amount=monthly_installment,
                due_date=date.today() + timedelta(days=30 * i),
                status=InstallmentStatus.PENDING
            )
            db.session.add(installment)
        
        db.session.add(liability)
        
        return liability
    
    @staticmethod
    def validate_advance_payment_request(employee_id, requested_amount, installments):
        """
        التحقق من صحة طلب السلفة
        
        Args:
            employee_id: رقم الموظف
            requested_amount: المبلغ المطلوب
            installments: عدد الأقساط
        
        Returns:
            tuple: (is_valid: bool, message: str)
        """
        employee = Employee.query.get(employee_id)
        if not employee:
            return False, "الموظف غير موجود"
        
        if requested_amount <= 0:
            return False, "المبلغ يجب أن يكون أكبر من صفر"
        
        if installments < 1 or installments > 12:
            return False, "عدد الأقساط يجب أن يكون بين 1 و 12"
        
        active_advances = EmployeeLiability.query.filter_by(
            employee_id=employee_id,
            liability_type=LiabilityType.ADVANCE_REPAYMENT,
            status=LiabilityStatus.ACTIVE
        ).count()
        
        if active_advances > 0:
            return False, "لديك سلفة نشطة بالفعل، يجب سدادها أولاً"
        
        monthly_installment = requested_amount / installments
        if employee.basic_salary and monthly_installment > (float(employee.basic_salary) * 0.4):
            return False, "قيمة القسط الشهري تتجاوز 40% من الراتب"
        
        if employee.basic_salary and requested_amount > (float(employee.basic_salary) * 3):
            max_advance = float(employee.basic_salary) * 3
            return False, f"الحد الأقصى للسلفة هو {max_advance:.2f} ريال (3 أضعاف الراتب)"
        
        return True, "صحيح"
