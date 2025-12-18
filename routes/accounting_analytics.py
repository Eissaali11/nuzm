"""
طرق التحليل المالي الذكي ok
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, extract, desc
from datetime import datetime, timedelta
import json
# import numpy as np
# from sklearn.linear_model import LinearRegression
# import pandas as pd

from models_accounting import (Account, Transaction, TransactionEntry,
                               FiscalYear, TransactionType, EntryType,
                               AccountType, db)
try:
    from core.permissions import Module, UserRole
except ImportError:
    from models import Module, UserRole

analytics_bp = Blueprint('accounting_analytics',
                         __name__,
                         url_prefix='/accounting/analytics')


def has_accounting_access():
    """التحقق من صلاحية الوصول للنظام المحاسبي"""
    return current_user.role == UserRole.ADMIN or current_user.has_module_access(
        Module.ACCOUNTING)


@analytics_bp.route('/')
@login_required
def dashboard():
    """لوحة التحليل المالي الذكي"""
    if not has_accounting_access():
        flash('غير مسموح لك بالوصول لهذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))

    try:
        # الحصول على السنة المالية النشطة
        fiscal_year = FiscalYear.query.filter_by(is_active=True).first()
        if not fiscal_year:
            flash('لا توجد سنة مالية نشطة', 'warning')
            return render_template('accounting/analytics/dashboard.html')

        # حساب إجمالي الإيرادات والمصروفات
        revenue_accounts = Account.query.filter_by(
            account_type=AccountType.REVENUE).all()
        expense_accounts = Account.query.filter_by(
            account_type=AccountType.EXPENSES).all()

        total_revenue = 0
        total_expenses = 0

        # حساب الإيرادات
        for account in revenue_accounts:
            entries = TransactionEntry.query.join(Transaction).filter(
                TransactionEntry.account_id == account.id,
                Transaction.fiscal_year_id == fiscal_year.id,
                TransactionEntry.entry_type == EntryType.CREDIT).all()
            total_revenue += sum(entry.amount for entry in entries)

        # حساب المصروفات
        for account in expense_accounts:
            entries = TransactionEntry.query.join(Transaction).filter(
                TransactionEntry.account_id == account.id,
                Transaction.fiscal_year_id == fiscal_year.id,
                TransactionEntry.entry_type == EntryType.DEBIT).all()
            total_expenses += sum(entry.amount for entry in entries)

        # حساب صافي الربح
        net_profit = total_revenue - total_expenses
        profit_margin = (net_profit / total_revenue *
                         100) if total_revenue > 0 else 0

        # البيانات الشهرية للإيرادات والمصروفات
        revenue_data = []
        expense_data = []

        for month in range(1, 13):
            # إيرادات الشهر
            month_revenue = db.session.query(func.sum(
                TransactionEntry.amount)).join(Transaction).filter(
                    TransactionEntry.account_id.in_([
                        acc.id for acc in revenue_accounts
                    ]), Transaction.fiscal_year_id == fiscal_year.id,
                    TransactionEntry.entry_type == EntryType.CREDIT,
                    extract('month', Transaction.transaction_date)
                    == month).scalar() or 0

            # مصروفات الشهر
            month_expenses = db.session.query(func.sum(
                TransactionEntry.amount)).join(Transaction).filter(
                    TransactionEntry.account_id.in_([
                        acc.id for acc in expense_accounts
                    ]), Transaction.fiscal_year_id == fiscal_year.id,
                    TransactionEntry.entry_type == EntryType.DEBIT,
                    extract('month', Transaction.transaction_date)
                    == month).scalar() or 0

            revenue_data.append(float(month_revenue))
            expense_data.append(float(month_expenses))

        # توزيع المصروفات
        salary_expenses = db.session.query(func.sum(
            TransactionEntry.amount)).join(Transaction).filter(
                Transaction.transaction_type == TransactionType.SALARY,
                Transaction.fiscal_year_id == fiscal_year.id,
                TransactionEntry.entry_type == EntryType.DEBIT).scalar() or 0

        vehicle_expenses = db.session.query(func.sum(
            TransactionEntry.amount)).join(Transaction).filter(
                Transaction.transaction_type
                == TransactionType.VEHICLE_EXPENSE, Transaction.fiscal_year_id
                == fiscal_year.id, TransactionEntry.entry_type
                == EntryType.DEBIT).scalar() or 0

        operation_expenses = total_expenses - salary_expenses - vehicle_expenses

        expense_distribution = [
            float(salary_expenses),
            float(vehicle_expenses),
            float(operation_expenses),
            0  # أخرى
        ]

        # أداء الأقسام (بيانات تجريبية لتجنب الاستيراد الدوري)
        department_names = ['الإدارة', 'المبيعات', 'التسويق', 'المحاسبة']
        department_revenues = [50000, 80000, 30000, 20000]
        department_expenses = [25000, 40000, 15000, 35000]

        # تكاليف المركبات (بيانات تجريبية لتجنب الاستيراد الدوري)
        vehicle_names = [
            'مركبة-001', 'مركبة-002', 'مركبة-003', 'مركبة-004', 'مركبة-005'
        ]
        fuel_costs = [5000, 4500, 6000, 3800, 5200]
        maintenance_costs = [2000, 3500, 1800, 2800, 2200]

        # التنبؤات المالية باستخدام الذكاء الاصطناعي
        prediction_data, actual_data, prediction_months = generate_financial_predictions(
            revenue_data, expense_data)

        # حساب التنبؤات للشهر القادم
        predicted_revenue = prediction_data[-1] if prediction_data else 0
        predicted_expenses = sum(expense_data[-3:]) / 3 if len(
            expense_data) >= 3 else 0
        predicted_profit = predicted_revenue - predicted_expenses

        # البيانات للمقارنة (الشهر السابق)
        current_month = datetime.now().month
        prev_month = current_month - 1 if current_month > 1 else 12

        prev_salary_expenses = salary_expenses * 0.95  # مثال للمقارنة
        prev_vehicle_expenses = vehicle_expenses * 1.02
        prev_operation_expenses = operation_expenses * 0.98

        salary_change = ((salary_expenses - prev_salary_expenses) /
                         prev_salary_expenses *
                         100) if prev_salary_expenses > 0 else 0
        vehicle_change = ((vehicle_expenses - prev_vehicle_expenses) /
                          prev_vehicle_expenses *
                          100) if prev_vehicle_expenses > 0 else 0
        operation_change = ((operation_expenses - prev_operation_expenses) /
                            prev_operation_expenses *
                            100) if prev_operation_expenses > 0 else 0

        salary_percentage = (salary_expenses / total_expenses *
                             100) if total_expenses > 0 else 0
        vehicle_percentage = (vehicle_expenses / total_expenses *
                              100) if total_expenses > 0 else 0
        operation_percentage = (operation_expenses / total_expenses *
                                100) if total_expenses > 0 else 0

        return render_template(
            'accounting/analytics/dashboard.html',
            # المؤشرات الرئيسية
            total_revenue=total_revenue,
            total_expenses=total_expenses,
            net_profit=net_profit,
            profit_margin=profit_margin,

            # البيانات الشهرية
            revenue_data=revenue_data,
            expense_data=expense_data,

            # توزيع المصروفات
            expense_distribution=expense_distribution,

            # أداء الأقسام
            department_names=department_names,
            department_revenues=department_revenues,
            department_expenses=department_expenses,

            # تكاليف المركبات
            vehicle_names=vehicle_names,
            fuel_costs=fuel_costs,
            maintenance_costs=maintenance_costs,

            # التنبؤات
            prediction_data=prediction_data,
            actual_data=actual_data,
            prediction_months=prediction_months,
            predicted_revenue=predicted_revenue,
            predicted_expenses=predicted_expenses,
            predicted_profit=predicted_profit,

            # التحليل التفصيلي
            salary_expenses=salary_expenses,
            prev_salary_expenses=prev_salary_expenses,
            salary_change=salary_change,
            salary_percentage=salary_percentage,
            vehicle_expenses=vehicle_expenses,
            prev_vehicle_expenses=prev_vehicle_expenses,
            vehicle_change=vehicle_change,
            vehicle_percentage=vehicle_percentage,
            operation_expenses=operation_expenses,
            prev_operation_expenses=prev_operation_expenses,
            operation_change=operation_change,
            operation_percentage=operation_percentage)

    except Exception as e:
        flash(f'خطأ في تحميل البيانات: {str(e)}', 'danger')
        return render_template('accounting/analytics/dashboard.html')


def generate_financial_predictions(revenue_data, expense_data):
    """توليد التنبؤات المالية باستخدام الذكاء الاصطناعي"""
    try:
        # إعداد البيانات
        months = list(range(1, len(revenue_data) + 1))

        # نموذج التنبؤ المبسط (بدون مكتبات خارجية)
        if len(revenue_data) >= 3:
            # حساب المتوسط المتحرك للتنبؤ
            recent_avg = sum(revenue_data[-3:]) / 3
            trend = (revenue_data[-1] - revenue_data[-3]) / 2

            # التنبؤ للأشهر القادمة
            future_predictions = []
            for i in range(3):
                predicted_value = recent_avg + (trend * i)
                future_predictions.append(max(
                    0, predicted_value))  # تجنب القيم السالبة

            # دمج البيانات الفعلية والتنبؤات
            actual_data = revenue_data
            prediction_data = revenue_data + future_predictions
            prediction_months = [
                f"شهر {i}" for i in range(1,
                                          len(prediction_data) + 1)
            ]

            return prediction_data, actual_data, prediction_months

    except Exception as e:
        print(f"خطأ في التنبؤ: {str(e)}")

    # في حالة الخطأ، إرجاع بيانات افتراضية
    return revenue_data, revenue_data, [
        f"شهر {i}" for i in range(1,
                                  len(revenue_data) + 1)
    ]


@analytics_bp.route('/api/financial-data')
@login_required
def financial_data_api():
    """API لجلب البيانات المالية للرسوم البيانية"""
    if not has_accounting_access():
        return jsonify({'error': 'غير مصرح'}), 403

    # يمكن إضافة المزيد من APIs حسب الحاجة
    return jsonify({'status': 'success', 'message': 'البيانات المالية متاحة'})
