"""
طرق النظام المحاسبي
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user
from sqlalchemy import func, and_, or_, extract, desc, asc
from sqlalchemy.orm import joinedload
from datetime import datetime, date, timedelta
from decimal import Decimal
import json

from app import db
from models import UserRole, Module, Permission
from models_accounting import *
from forms.accounting import *
from utils.helpers import log_activity
from utils.chart_of_accounts import create_default_chart_of_accounts, get_accounts_tree, get_account_hierarchy, calculate_account_balance

# إنشاء البلوبرينت
accounting_bp = Blueprint('accounting', __name__, url_prefix='/accounting')


# ==================== الصفحة الرئيسية ====================

@accounting_bp.route('/')
@login_required
def dashboard():
    """لوحة تحكم المحاسبة"""
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        flash('غير مسموح لك بالوصول لهذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    try:
        # السنة المالية النشطة
        active_fiscal_year = FiscalYear.query.filter_by(is_active=True).first()
        if not active_fiscal_year:
            flash('لا توجد سنة مالية نشطة. يرجى إنشاء سنة مالية أولاً.', 'warning')
            return redirect(url_for('accounting.fiscal_years'))
        
        # إحصائيات سريعة
        current_month_start = date.today().replace(day=1)
        current_month_end = (current_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # إجمالي الأصول
        total_assets = db.session.query(func.sum(Account.balance)).filter(
            Account.account_type == AccountType.ASSETS,
            Account.is_active == True
        ).scalar() or 0
        
        # إجمالي الخصوم
        total_liabilities = db.session.query(func.sum(Account.balance)).filter(
            Account.account_type == AccountType.LIABILITIES,
            Account.is_active == True
        ).scalar() or 0
        
        # حقوق الملكية
        total_equity = db.session.query(func.sum(Account.balance)).filter(
            Account.account_type == AccountType.EQUITY,
            Account.is_active == True
        ).scalar() or 0
        
        # صافي الأرباح هذا الشهر
        monthly_revenue = db.session.query(func.sum(Account.balance)).filter(
            Account.account_type == AccountType.REVENUE,
            Account.is_active == True
        ).scalar() or 0
        
        monthly_expenses = db.session.query(func.sum(Account.balance)).filter(
            Account.account_type == AccountType.EXPENSES,
            Account.is_active == True
        ).scalar() or 0
        
        net_profit = monthly_revenue - monthly_expenses
        
        # النسب المالية المهمة
        current_ratio = float(total_assets) / float(total_liabilities) if total_liabilities != 0 else 0
        debt_to_equity = float(total_liabilities) / float(total_equity) if total_equity != 0 else 0
        roa = (float(net_profit) / float(total_assets) * 100) if total_assets != 0 else 0  # معدل العائد على الأصول
        roe = (float(net_profit) / float(total_equity) * 100) if total_equity != 0 else 0  # معدل العائد على حقوق الملكية
        
        # أحدث المعاملات
        recent_transactions = Transaction.query.filter(
            Transaction.fiscal_year_id == active_fiscal_year.id,
            Transaction.is_approved == True
        ).order_by(desc(Transaction.transaction_date)).limit(10).all()
        
        # معاملات في انتظار الاعتماد
        pending_transactions = Transaction.query.filter(
            Transaction.fiscal_year_id == active_fiscal_year.id,
            Transaction.is_approved == False
        ).count()
        
        # مراكز التكلفة الأكثر إنفاقاً هذا الشهر
        top_cost_centers = db.session.query(
            CostCenter.name,
            func.sum(Transaction.total_amount).label('total_spent')
        ).join(Transaction).filter(
            Transaction.transaction_date >= current_month_start,
            Transaction.transaction_date <= current_month_end,
            Transaction.is_approved == True,
            Transaction.transaction_type.in_([TransactionType.VEHICLE_EXPENSE, TransactionType.SALARY])
        ).group_by(CostCenter.id).order_by(desc('total_spent')).limit(5).all()
        
        # بيانات الرسوم البيانية - توزيع الأصول
        account_types_data = db.session.query(
            Account.account_type,
            func.sum(Account.balance).label('total')
        ).filter(Account.is_active == True).group_by(Account.account_type).all()
        
        # بيانات المصروفات عبر الأشهر (آخر 6 أشهر)
        six_months_ago = date.today() - timedelta(days=180)
        monthly_expenses_data = db.session.query(
            extract('month', Transaction.transaction_date).label('month'),
            func.sum(Transaction.total_amount).label('total')
        ).filter(
            Transaction.transaction_date >= six_months_ago,
            Transaction.is_approved == True,
            Transaction.transaction_type == TransactionType.SALARY
        ).group_by('month').order_by('month').all()
        
        return render_template('accounting/dashboard.html',
                             total_assets=total_assets,
                             total_liabilities=total_liabilities,
                             total_equity=total_equity,
                             net_profit=net_profit,
                             current_ratio=current_ratio,
                             debt_to_equity=debt_to_equity,
                             roa=roa,
                             roe=roe,
                             recent_transactions=recent_transactions,
                             pending_transactions=pending_transactions,
                             top_cost_centers=top_cost_centers,
                             active_fiscal_year=active_fiscal_year,
                             account_types_data=account_types_data,
                             monthly_expenses_data=monthly_expenses_data)
    
    except Exception as e:
        flash(f'خطأ في تحميل لوحة التحكم: {str(e)}', 'danger')
        return redirect(url_for('dashboard.index'))


# ==================== دليل الحسابات ====================

@accounting_bp.route('/accounts')
@login_required
def accounts():
    """قائمة الحسابات"""
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        flash('غير مسموح لك بالوصول لهذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    search_term = request.args.get('search', '')
    account_type_filter = request.args.get('type', '')
    page = request.args.get('page', 1, type=int)
    
    query = Account.query
    
    if search_term:
        query = query.filter(or_(
            Account.name.contains(search_term),
            Account.code.contains(search_term)
        ))
    
    if account_type_filter:
        query = query.filter(Account.account_type == account_type_filter)
    
    accounts_list = query.order_by(Account.code).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('accounting/accounts/index.html',
                         accounts=accounts_list,
                         search_term=search_term,
                         account_type_filter=account_type_filter)


@accounting_bp.route('/accounts/add', methods=['POST'])
@login_required
def add_account():
    """إضافة حساب جديد من شجرة الحسابات"""
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        flash('غير مسموح لك بالوصول لهذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    try:
        # التحقق من عدم وجود رمز مكرر
        existing = Account.query.filter_by(code=request.form.get('code')).first()
        if existing:
            flash('رمز الحساب موجود مسبقاً', 'danger')
            return redirect(url_for('accounting.chart_of_accounts'))
        
        account = Account(
            code=request.form.get('code'),
            name=request.form.get('name'),
            name_en=request.form.get('name_en', ''),
            account_type=AccountType(request.form.get('account_type')),
            parent_id=request.form.get('parent_id') if request.form.get('parent_id') else None,
            balance=float(request.form.get('balance', 0)),
            is_active=request.form.get('is_active') == 'on'
        )
        
        # حساب المستوى
        if account.parent_id:
            parent = Account.query.get(account.parent_id)
            account.level = parent.level + 1 if parent else 0
        else:
            account.level = 0
        
        db.session.add(account)
        db.session.commit()
        
        log_activity(f"إضافة حساب جديد: {account.name} ({account.code})")
        flash('تم إضافة الحساب بنجاح', 'success')
        return redirect(url_for('accounting.chart_of_accounts'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في إضافة الحساب: {str(e)}', 'danger')
        return redirect(url_for('accounting.chart_of_accounts'))

@accounting_bp.route('/accounts/create', methods=['GET', 'POST'])
@login_required
def create_account():
    """إضافة حساب جديد"""
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        flash('غير مسموح لك بالوصول لهذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    form = AccountForm()
    
    # تحميل الحسابات الأب
    parent_accounts = Account.query.filter_by(is_active=True).all()
    form.parent_id.choices = [('', 'لا يوجد')] + [(acc.id, f"{acc.code} - {acc.name}") for acc in parent_accounts]
    
    if form.validate_on_submit():
        try:
            # التحقق من عدم وجود رمز مكرر
            existing = Account.query.filter_by(code=form.code.data).first()
            if existing:
                flash('رمز الحساب موجود مسبقاً', 'danger')
                return render_template('accounting/accounts/form.html', form=form, title='إضافة حساب جديد')
            
            account = Account(
                code=form.code.data,
                name=form.name.data,
                name_en=form.name_en.data,
                account_type=AccountType(form.account_type.data),
                parent_id=form.parent_id.data if form.parent_id.data else None,
                description=form.description.data,
                is_active=form.is_active.data
            )
            
            # حساب المستوى
            if account.parent_id:
                parent = Account.query.get(account.parent_id)
                account.level = parent.level + 1
            else:
                account.level = 0
            
            db.session.add(account)
            db.session.commit()
            
            log_activity(f"إضافة حساب جديد: {account.name} ({account.code})")
            flash('تم إضافة الحساب بنجاح', 'success')
            return redirect(url_for('accounting.accounts'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في إضافة الحساب: {str(e)}', 'danger')
    
    return render_template('accounting/accounts/form.html', form=form, title='إضافة حساب جديد')


@accounting_bp.route('/accounts/<int:account_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_account(account_id):
    """تعديل حساب"""
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        flash('غير مسموح لك بالوصول لهذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    account = Account.query.get_or_404(account_id)
    form = AccountForm(obj=account)
    
    # تحميل الحسابات الأب (ما عدا الحساب نفسه)
    parent_accounts = Account.query.filter(
        Account.is_active == True,
        Account.id != account.id
    ).all()
    form.parent_id.choices = [('', 'لا يوجد')] + [(acc.id, f"{acc.code} - {acc.name}") for acc in parent_accounts]
    
    if form.validate_on_submit():
        try:
            # التحقق من عدم وجود رمز مكرر
            existing = Account.query.filter(
                Account.code == form.code.data,
                Account.id != account.id
            ).first()
            if existing:
                flash('رمز الحساب موجود مسبقاً', 'danger')
                return render_template('accounting/accounts/form.html', form=form, title='تعديل حساب', account=account)
            
            account.code = form.code.data
            account.name = form.name.data
            account.name_en = form.name_en.data
            account.account_type = AccountType(form.account_type.data)
            account.parent_id = form.parent_id.data if form.parent_id.data else None
            account.description = form.description.data
            account.is_active = form.is_active.data
            account.updated_at = datetime.utcnow()
            
            # إعادة حساب المستوى
            if account.parent_id:
                parent = Account.query.get(account.parent_id)
                account.level = parent.level + 1
            else:
                account.level = 0
            
            db.session.commit()
            
            log_activity(f"تعديل حساب: {account.name} ({account.code})")
            flash('تم تعديل الحساب بنجاح', 'success')
            return redirect(url_for('accounting.accounts'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في تعديل الحساب: {str(e)}', 'danger')
    
    return render_template('accounting/accounts/form.html', form=form, title='تعديل حساب', account=account)


@accounting_bp.route('/accounts/<int:account_id>/confirm-delete', methods=['GET', 'POST'])
@login_required
def confirm_delete_account(account_id):
    """صفحة تأكيد حذف الحساب"""
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        flash('غير مسموح لك بالوصول لهذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    account = Account.query.get_or_404(account_id)
    
    # التحقق من وجود معاملات مرتبطة بالحساب
    from models_accounting import TransactionEntry
    has_transactions = TransactionEntry.query.filter_by(account_id=account.id).count() > 0
    
    # التحقق من وجود حسابات فرعية
    has_children = Account.query.filter_by(parent_id=account.id).count() > 0
    
    if request.method == 'POST':
        if has_transactions:
            flash('لا يمكن حذف الحساب لوجود معاملات مرتبطة به', 'danger')
            return redirect(url_for('accounting.accounts'))
        
        if has_children:
            flash('لا يمكن حذف الحساب لوجود حسابات فرعية تابعة له', 'danger')
            return redirect(url_for('accounting.accounts'))
        
        try:
            account_name = account.name
            account_code = account.code
            
            db.session.delete(account)
            db.session.commit()
            
            log_activity(f"حذف حساب: {account_name} ({account_code})")
            flash('تم حذف الحساب بنجاح', 'success')
            
            return redirect(url_for('accounting.accounts'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في حذف الحساب: {str(e)}', 'danger')
    
    return render_template('accounting/accounts/confirm_delete.html', 
                         account=account,
                         has_transactions=has_transactions,
                         has_children=has_children)


@accounting_bp.route('/accounts/<int:account_id>/view')
@login_required
def view_account(account_id):
    """عرض تفاصيل حساب"""
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        flash('غير مسموح لك بالوصول لهذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    account = Account.query.get_or_404(account_id)
    
    # آخر المعاملات
    recent_entries = TransactionEntry.query.filter_by(account_id=account.id)\
        .join(Transaction)\
        .filter(Transaction.is_approved == True)\
        .order_by(desc(Transaction.transaction_date))\
        .limit(20).all()
    
    # الرصيد الشهري للسنة الحالية
    current_year = datetime.now().year
    monthly_balances = []
    
    for month in range(1, 13):
        month_start = date(current_year, month, 1)
        if month == 12:
            month_end = date(current_year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(current_year, month + 1, 1) - timedelta(days=1)
        
        # حساب الرصيد حتى نهاية الشهر
        debits = db.session.query(func.sum(TransactionEntry.amount)).join(Transaction).filter(
            TransactionEntry.account_id == account.id,
            TransactionEntry.entry_type == EntryType.DEBIT,
            Transaction.transaction_date <= month_end,
            Transaction.is_approved == True
        ).scalar() or 0
        
        credits = db.session.query(func.sum(TransactionEntry.amount)).join(Transaction).filter(
            TransactionEntry.account_id == account.id,
            TransactionEntry.entry_type == EntryType.CREDIT,
            Transaction.transaction_date <= month_end,
            Transaction.is_approved == True
        ).scalar() or 0
        
        balance = debits - credits if account.account_type in [AccountType.ASSETS, AccountType.EXPENSES] else credits - debits
        monthly_balances.append(balance)
    
    return render_template('accounting/accounts/view.html',
                         account=account,
                         recent_entries=recent_entries,
                         monthly_balances=monthly_balances)


# ==================== القيود المحاسبية ====================

@accounting_bp.route('/transaction/<int:transaction_id>')
@login_required
def view_transaction(transaction_id):
    """عرض تفاصيل معاملة مالية"""
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        flash('غير مسموح لك بالوصول لهذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    transaction = Transaction.query.get_or_404(transaction_id)
    entries = TransactionEntry.query.filter_by(transaction_id=transaction_id).all()
    
    return render_template('accounting/view_transaction.html',
                         transaction=transaction,
                         entries=entries)

@accounting_bp.route('/transactions')
@login_required
def transactions():
    """قائمة القيود المحاسبية"""
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        flash('غير مسموح لك بالوصول لهذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    search_term = request.args.get('search', '')
    transaction_type_filter = request.args.get('type', '')
    status_filter = request.args.get('status', '')
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    page = request.args.get('page', 1, type=int)
    
    query = Transaction.query.options(joinedload(Transaction.created_by))
    
    if search_term:
        query = query.filter(or_(
            Transaction.description.contains(search_term),
            Transaction.reference_number.contains(search_term),
            Transaction.transaction_number.contains(search_term)
        ))
    
    if transaction_type_filter:
        query = query.filter(Transaction.transaction_type == transaction_type_filter)
    
    if status_filter == 'pending':
        query = query.filter(Transaction.is_approved == False)
    elif status_filter == 'approved':
        query = query.filter(Transaction.is_approved == True)
    
    if from_date:
        query = query.filter(Transaction.transaction_date >= datetime.strptime(from_date, '%Y-%m-%d').date())
    
    if to_date:
        query = query.filter(Transaction.transaction_date <= datetime.strptime(to_date, '%Y-%m-%d').date())
    
    transactions_list = query.order_by(desc(Transaction.transaction_date), desc(Transaction.id)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('accounting/transactions/index.html',
                         transactions=transactions_list,
                         search_term=search_term,
                         transaction_type_filter=transaction_type_filter,
                         status_filter=status_filter,
                         from_date=from_date,
                         to_date=to_date)


@accounting_bp.route('/transactions/new', methods=['GET', 'POST'])
@login_required
def add_transaction():
    """إضافة قيد محاسبي جديد"""
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        flash('غير مسموح لك بالوصول لهذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    form = TransactionForm()
    
    # تحميل البيانات للقوائم المنسدلة
    accounts = Account.query.filter_by(is_active=True).order_by(Account.code).all()
    cost_centers = CostCenter.query.filter_by(is_active=True).all()
    vendors = Vendor.query.filter_by(is_active=True).all()
    customers = Customer.query.filter_by(is_active=True).all()
    
    # تحديث خيارات النماذج
    for entry_form in form.entries:
        entry_form.account_id.choices = [(acc.id, f"{acc.code} - {acc.name}") for acc in accounts]
    
    form.cost_center_id.choices = [('', 'لا يوجد')] + [(cc.id, cc.name) for cc in cost_centers]
    form.vendor_id.choices = [('', 'لا يوجد')] + [(v.id, v.name) for v in vendors]
    form.customer_id.choices = [('', 'لا يوجد')] + [(c.id, c.name) for c in customers]
    
    if request.method == 'POST':
        # التحقق من توازن القيد
        total_debits = sum(float(entry.amount.data) for entry in form.entries if entry.entry_type.data == 'debit' and entry.amount.data)
        total_credits = sum(float(entry.amount.data) for entry in form.entries if entry.entry_type.data == 'credit' and entry.amount.data)
        
        if abs(total_debits - total_credits) > 0.01:
            flash('خطأ: القيد غير متوازن. مجموع المدين يجب أن يساوي مجموع الدائن', 'danger')
        elif form.validate_on_submit() and total_debits > 0:
            try:
                # الحصول على رقم القيد التالي
                settings = AccountingSettings.query.first()
                if not settings:
                    settings = AccountingSettings(
                        company_name='شركة نُظم',
                        next_transaction_number=1
                    )
                    db.session.add(settings)
                    db.session.flush()
                
                transaction_number = f"{settings.transaction_prefix}{settings.next_transaction_number:06d}"
                
                # السنة المالية النشطة
                fiscal_year = FiscalYear.query.filter_by(is_active=True).first()
                if not fiscal_year:
                    flash('لا توجد سنة مالية نشطة', 'danger')
                    return render_template('accounting/transactions/form.html', form=form, title='إضافة قيد جديد')
                
                # إنشاء المعاملة
                transaction = Transaction(
                    transaction_number=transaction_number,
                    transaction_date=form.transaction_date.data,
                    transaction_type=TransactionType(form.transaction_type.data),
                    reference_number=form.reference_number.data,
                    description=form.description.data,
                    total_amount=Decimal(str(total_debits)),
                    fiscal_year_id=fiscal_year.id,
                    cost_center_id=form.cost_center_id.data if form.cost_center_id.data else None,
                    vendor_id=form.vendor_id.data if form.vendor_id.data else None,
                    customer_id=form.customer_id.data if form.customer_id.data else None,
                    created_by_id=current_user.id
                )
                
                db.session.add(transaction)
                db.session.flush()
                
                # إضافة تفاصيل القيد
                for entry_form in form.entries:
                    if entry_form.account_id.data and entry_form.amount.data:
                        entry = TransactionEntry(
                            transaction_id=transaction.id,
                            account_id=entry_form.account_id.data,
                            entry_type=EntryType(entry_form.entry_type.data),
                            amount=Decimal(str(entry_form.amount.data)),
                            description=entry_form.description.data
                        )
                        db.session.add(entry)
                
                # تحديث رقم القيد التالي
                settings.next_transaction_number += 1
                
                db.session.commit()
                
                log_activity(f"إضافة قيد محاسبي: {transaction.transaction_number}")
                flash('تم إضافة القيد بنجاح', 'success')
                return redirect(url_for('accounting.transactions'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'خطأ في إضافة القيد: {str(e)}', 'danger')
    
    return render_template('accounting/transactions/form.html', form=form, title='إضافة قيد جديد')


# ==================== شجرة الحسابات ====================

@accounting_bp.route('/chart-of-accounts')
@login_required
def chart_of_accounts():
    """شجرة الحسابات"""
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        flash('غير مسموح لك بالوصول لهذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # جلب شجرة الحسابات
    accounts_tree = get_accounts_tree()
    
    # إحصائيات سريعة
    total_accounts = Account.query.filter_by(is_active=True).count()
    main_accounts = Account.query.filter_by(level=1, is_active=True).count()
    sub_accounts = Account.query.filter_by(level=2, is_active=True).count()
    detail_accounts = Account.query.filter_by(level=3, is_active=True).count()
    
    return render_template('accounting/chart_of_accounts.html',
                         accounts_tree=accounts_tree,
                         total_accounts=total_accounts,
                         main_accounts=main_accounts,
                         sub_accounts=sub_accounts,
                         detail_accounts=detail_accounts)


@accounting_bp.route('/create-default-accounts', methods=['POST'])
@login_required
def create_default_accounts():
    """إنشاء الحسابات الافتراضية"""
    if not current_user.role == UserRole.ADMIN:
        flash('غير مسموح لك بتنفيذ هذا الإجراء', 'danger')
        return redirect(url_for('accounting.chart_of_accounts'))
    
    try:
        success, message = create_default_chart_of_accounts()
        if success:
            log_activity("إنشاء شجرة الحسابات الافتراضية")
            flash(message, 'success')
        else:
            flash(message, 'warning')
    except Exception as e:
        flash(f'خطأ في إنشاء الحسابات: {str(e)}', 'danger')
    
    return redirect(url_for('accounting.chart_of_accounts'))


@accounting_bp.route('/account/<int:account_id>/balance')
@login_required
def account_balance(account_id):
    """عرض رصيد حساب مع التفاصيل"""
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        return jsonify({'error': 'غير مسموح'}), 403
    
    try:
        account = Account.query.get_or_404(account_id)
        
        # حساب الرصيد مع الحسابات الفرعية
        total_balance = calculate_account_balance(account_id, True)
        account_balance_only = account.balance
        
        # التسلسل الهرمي
        hierarchy = get_account_hierarchy(account_id)
        
        # الحسابات الفرعية
        children = Account.query.filter_by(parent_id=account_id, is_active=True).all()
        
        return jsonify({
            'account': {
                'id': account.id,
                'code': account.code,
                'name': account.name,
                'name_en': account.name_en,
                'type': account.account_type.value,
                'level': account.level
            },
            'balances': {
                'account_only': float(account_balance_only),
                'with_children': float(total_balance)
            },
            'hierarchy': [{'code': acc.code, 'name': acc.name} for acc in hierarchy],
            'children': [{'id': child.id, 'code': child.code, 'name': child.name, 'balance': float(child.balance)} for child in children]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@accounting_bp.route('/account/<int:account_id>/balance-page')
@login_required
def account_balance_page(account_id):
    """صفحة تفاصيل رصيد الحساب"""
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        flash('غير مسموح لك بالوصول لهذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    try:
        account = Account.query.get_or_404(account_id)
        
        # حساب الرصيد مع الحسابات الفرعية
        total_balance = calculate_account_balance(account_id, True)
        
        # التسلسل الهرمي
        hierarchy = get_account_hierarchy(account_id)
        
        # الحسابات الفرعية
        children = Account.query.filter_by(parent_id=account_id, is_active=True).all()
        
        # أحدث المعاملات على هذا الحساب
        recent_transactions = TransactionEntry.query.filter_by(account_id=account_id)\
            .join(Transaction)\
            .filter(Transaction.is_approved == True)\
            .order_by(desc(Transaction.transaction_date))\
            .limit(10).all()
        
        return render_template('accounting/account_balance.html',
                             account=account,
                             total_balance=total_balance,
                             hierarchy=hierarchy,
                             children=children,
                             recent_transactions=recent_transactions)
        
    except Exception as e:
        flash(f'خطأ في جلب تفاصيل الحساب: {str(e)}', 'danger')
        return redirect(url_for('accounting.chart_of_accounts'))


@accounting_bp.route('/account/<int:account_id>/delete', methods=['POST'])
@login_required
def delete_account(account_id):
    """حذف حساب"""
    if not current_user.role == UserRole.ADMIN:
        flash('غير مسموح لك بتنفيذ هذا الإجراء', 'danger')
        return redirect(url_for('accounting.chart_of_accounts'))
    
    try:
        account = Account.query.get_or_404(account_id)
        
        # التحقق من الشروط قبل الحذف
        
        # 1. التحقق من وجود حسابات فرعية
        children_count = Account.query.filter_by(parent_id=account_id, is_active=True).count()
        if children_count > 0:
            flash(f'لا يمكن حذف الحساب لأنه يحتوي على {children_count} حساب فرعي', 'danger')
            return redirect(url_for('accounting.account_balance_page', account_id=account_id))
        
        # 2. التحقق من وجود معاملات
        transactions_count = TransactionEntry.query.filter_by(account_id=account_id).count()
        if transactions_count > 0:
            flash(f'لا يمكن حذف الحساب لأنه يحتوي على {transactions_count} معاملة مسجلة', 'danger')
            return redirect(url_for('accounting.account_balance_page', account_id=account_id))
        
        # 3. التحقق من أن الرصيد صفر
        if account.balance != 0:
            flash(f'لا يمكن حذف الحساب لأن رصيده غير صفر ({account.balance} ريال)', 'danger')
            return redirect(url_for('accounting.account_balance_page', account_id=account_id))
        
        # حفظ معلومات الحساب للسجل
        account_info = f"{account.code} - {account.name}"
        
        # حذف الحساب
        db.session.delete(account)
        db.session.commit()
        
        log_activity(f"حذف الحساب: {account_info}")
        flash(f'تم حذف الحساب {account_info} بنجاح', 'success')
        return redirect(url_for('accounting.chart_of_accounts'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في حذف الحساب: {str(e)}', 'danger')
        return redirect(url_for('accounting.account_balance_page', account_id=account_id))


@accounting_bp.route('/journal-entry/create', methods=['GET', 'POST'])
@login_required
def create_journal_entry():
    """إنشاء قيد يومية جديد"""
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        flash('غير مسموح لك بالوصول لهذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'GET':
        # جلب جميع الحسابات النشطة
        accounts = Account.query.filter_by(is_active=True).order_by(Account.code).all()
        accounts_list = [
            {
                'id': acc.id,
                'code': acc.code,
                'name': acc.name,
                'account_type': acc.account_type.value
            }
            for acc in accounts
        ]
        
        # إنشاء رقم قيد جديد
        last_transaction = Transaction.query.order_by(desc(Transaction.id)).first()
        next_number = f"JE{(last_transaction.id + 1) if last_transaction else 1:06d}"
        
        # التاريخ الحالي
        today = datetime.now().strftime('%Y-%m-%d')
        
        return render_template('accounting/create_journal_entry.html',
                             accounts=json.dumps(accounts_list),
                             next_number=next_number,
                             today=today)
    
    # معالجة POST
    try:
        # إنشاء المعاملة الأساسية
        transaction = Transaction()
        transaction.transaction_number = request.form.get('transaction_number')
        transaction.transaction_date = datetime.strptime(request.form.get('transaction_date'), '%Y-%m-%d').date()
        transaction.description = request.form.get('description')
        transaction.reference_number = request.form.get('reference_number', '')
        # transaction.notes = request.form.get('notes', '')  # مؤقت حتى يتم إضافة الحقل
        transaction.transaction_type = TransactionType.JOURNAL
        transaction.created_by = current_user.id
        
        # تحديد حالة الاعتماد
        action = request.form.get('action', 'draft')
        transaction.is_approved = (action == 'approve')
        if transaction.is_approved:
            transaction.approved_by = current_user.id
            # transaction.approved_at = datetime.utcnow()  # مؤقت حتى يتم إضافة الحقل
        
        db.session.add(transaction)
        db.session.flush()  # للحصول على ID المعاملة
        
        # معالجة تفاصيل القيد
        account_ids = request.form.getlist('account_id[]')
        descriptions = request.form.getlist('description[]')
        debits = request.form.getlist('debit[]')
        credits = request.form.getlist('credit[]')
        
        total_debit = 0
        total_credit = 0
        entry_count = 0
        
        for i in range(len(account_ids)):
            if account_ids[i] and account_ids[i] != '':
                debit_amount = float(debits[i]) if debits[i] else 0
                credit_amount = float(credits[i]) if credits[i] else 0
                
                if debit_amount > 0 or credit_amount > 0:
                    # إنشاء قيد المدين
                    if debit_amount > 0:
                        debit_entry = TransactionEntry()
                        debit_entry.transaction_id = transaction.id
                        debit_entry.account_id = int(account_ids[i])
                        debit_entry.entry_type = EntryType.DEBIT
                        debit_entry.amount = debit_amount
                        debit_entry.description = descriptions[i] if descriptions[i] else transaction.description
                        db.session.add(debit_entry)
                        total_debit += debit_amount
                        entry_count += 1
                    
                    # إنشاء قيد الدائن
                    if credit_amount > 0:
                        credit_entry = TransactionEntry()
                        credit_entry.transaction_id = transaction.id
                        credit_entry.account_id = int(account_ids[i])
                        credit_entry.entry_type = EntryType.CREDIT
                        credit_entry.amount = credit_amount
                        credit_entry.description = descriptions[i] if descriptions[i] else transaction.description
                        db.session.add(credit_entry)
                        total_credit += credit_amount
                        entry_count += 1
        
        # التحقق من وجود قيود
        if entry_count == 0:
            flash('يجب إدخال قيد واحد على الأقل', 'danger')
            return redirect(request.url)
        
        # التحقق من التوازن للقيود المعتمدة
        if action == 'approve' and abs(total_debit - total_credit) >= 0.01:
            flash('لا يمكن اعتماد القيد غير المتوازن', 'danger')
            return redirect(request.url)
        
        # تحديث أرصدة الحسابات إذا كان القيد معتمداً
        if transaction.is_approved:
            for i in range(len(account_ids)):
                if account_ids[i] and account_ids[i] != '':
                    debit_amount = float(debits[i]) if debits[i] else 0
                    credit_amount = float(credits[i]) if credits[i] else 0
                    
                    if debit_amount > 0 or credit_amount > 0:
                        account = Account.query.get(int(account_ids[i]))
                        if account:
                            account.balance += (debit_amount - credit_amount)
        
        # إضافة المبلغ الإجمالي للمعاملة
        # transaction.amount = max(total_debit, total_credit)  # مؤقت حتى يتم إضافة الحقل
        
        db.session.commit()
        
        status_text = "واعتُمد" if transaction.is_approved else "كمسودة"
        log_activity(f"إنشاء قيد يومية: {transaction.transaction_number} {status_text}")
        flash(f'تم حفظ القيد {transaction.transaction_number} {status_text} بنجاح', 'success')
        
        return redirect(url_for('accounting.view_transaction', transaction_id=transaction.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في حفظ القيد: {str(e)}', 'danger')
        return redirect(request.url)


@accounting_bp.route('/cost-centers')
@login_required
def cost_centers():
    """عرض مراكز التكلفة"""
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        flash('غير مسموح لك بالوصول لهذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    # جلب جميع مراكز التكلفة
    cost_centers = CostCenter.query.order_by(CostCenter.code).all()
    
    # مراكز التكلفة الرئيسية (بدون أب)
    main_centers = CostCenter.query.filter_by(parent_id=None).order_by(CostCenter.code).all()
    
    # حساب الإحصائيات
    total_budget = sum(center.budget_amount or 0 for center in cost_centers)
    total_expenses = sum(center.get_actual_expenses() for center in cost_centers)
    active_centers = len([c for c in cost_centers if c.is_active])
    
    return render_template('accounting/cost_centers.html',
                         cost_centers=cost_centers,
                         main_centers=main_centers,
                         total_budget=total_budget,
                         total_expenses=total_expenses,
                         active_centers=active_centers)


@accounting_bp.route('/cost-centers/create', methods=['GET', 'POST'])
@login_required
def create_cost_center():
    """إنشاء مركز تكلفة جديد"""
    if not current_user.role == UserRole.ADMIN:
        flash('غير مسموح لك بالوصول لهذه الصفحة', 'danger')
        return redirect(url_for('accounting.cost_centers'))
    
    if request.method == 'POST':
        try:
            center = CostCenter()
            center.code = request.form.get('code')
            center.name = request.form.get('name')
            center.name_en = request.form.get('name_en', '')
            center.description = request.form.get('description', '')
            
            parent_id = request.form.get('parent_id')
            if parent_id and parent_id != '':
                center.parent_id = int(parent_id)
            
            budget_amount = request.form.get('budget_amount', '0')
            center.budget_amount = float(budget_amount) if budget_amount else 0
            
            center.is_active = request.form.get('is_active') == 'on'
            
            db.session.add(center)
            db.session.commit()
            
            log_activity(f"إنشاء مركز تكلفة: {center.code} - {center.name}")
            flash(f'تم إنشاء مركز التكلفة {center.name} بنجاح', 'success')
            
            return redirect(url_for('accounting.cost_centers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في إنشاء مركز التكلفة: {str(e)}', 'danger')
            return redirect(request.url)
    
    # جلب مراكز التكلفة الموجودة لإمكانية اختيار الأب
    parent_centers = CostCenter.query.filter_by(is_active=True).order_by(CostCenter.code).all()
    
    return render_template('accounting/create_cost_center.html',
                         parent_centers=parent_centers)


@accounting_bp.route('/cost-centers/<int:center_id>')
@login_required
def view_cost_center(center_id):
    """عرض تفاصيل مركز التكلفة"""
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        flash('غير مسموح لك بالوصول لهذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    center = CostCenter.query.get_or_404(center_id)
    
    # جلب المعاملات المرتبطة بهذا المركز
    transactions = TransactionEntry.query.filter_by(cost_center_id=center_id).order_by(
        desc(TransactionEntry.created_at)).limit(20).all()
    
    return render_template('accounting/view_cost_center.html',
                         center=center,
                         transactions=transactions)


@accounting_bp.route('/cost-centers/<int:center_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_cost_center(center_id):
    """تعديل مركز التكلفة"""
    if not current_user.role == UserRole.ADMIN:
        flash('غير مسموح لك بالوصول لهذه الصفحة', 'danger')
        return redirect(url_for('accounting.cost_centers'))
    
    center = CostCenter.query.get_or_404(center_id)
    
    # إنشاء النموذج وملء الخيارات
    form = CostCenterForm(obj=center)
    
    # تحديد خيارات المركز الأب (باستثناء المركز الحالي)
    parent_centers = CostCenter.query.filter(
        CostCenter.id != center.id, 
        CostCenter.is_active == True
    ).order_by(CostCenter.code).all()
    
    form.parent_id.choices = [('', 'لا يوجد')] + [(c.id, f"{c.code} - {c.name}") for c in parent_centers]
    
    if form.validate_on_submit():
        try:
            # التحقق من عدم اختيار المركز نفسه كأب
            if form.parent_id.data and form.parent_id.data == center.id:
                flash('لا يمكن اختيار المركز نفسه كمركز أب', 'danger')
                return render_template('accounting/edit_cost_center.html', form=form, center=center)
            
            # تحديث بيانات المركز
            center.code = form.code.data
            center.name = form.name.data
            center.name_en = form.name_en.data or ''
            center.description = form.description.data or ''
            center.parent_id = form.parent_id.data
            center.budget_amount = form.budget_amount.data or 0
            center.is_active = form.is_active.data
            center.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            log_activity(f"تعديل مركز تكلفة: {center.code} - {center.name}")
            flash(f'تم تعديل مركز التكلفة {center.name} بنجاح', 'success')
            
            return redirect(url_for('accounting.view_cost_center', center_id=center.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في تعديل مركز التكلفة: {str(e)}', 'danger')
    
    return render_template('accounting/edit_cost_center.html', form=form, center=center)


@accounting_bp.route('/cost-centers/<int:center_id>/delete', methods=['POST'])
@login_required
def delete_cost_center(center_id):
    """حذف مركز التكلفة"""
    if not current_user.role == UserRole.ADMIN:
        flash('غير مسموح لك بالوصول لهذه الصفحة', 'danger')
        return redirect(url_for('accounting.cost_centers'))
    
    try:
        center = CostCenter.query.get_or_404(center_id)
        
        children_count = CostCenter.query.filter_by(parent_id=center_id).count()
        if children_count > 0:
            flash(f'لا يمكن حذف المركز لأنه يحتوي على {children_count} مركز فرعي', 'danger')
            return redirect(url_for('accounting.view_cost_center', center_id=center_id))
        
        transactions_count = TransactionEntry.query.filter_by(cost_center_id=center_id).count()
        if transactions_count > 0:
            flash(f'لا يمكن حذف المركز لأنه يحتوي على {transactions_count} معاملة مسجلة', 'danger')
            return redirect(url_for('accounting.view_cost_center', center_id=center_id))
        
        center_info = f"{center.code} - {center.name}"
        
        db.session.delete(center)
        db.session.commit()
        
        log_activity(f"حذف مركز تكلفة: {center_info}")
        flash(f'تم حذف مركز التكلفة {center_info} بنجاح', 'success')
        return redirect(url_for('accounting.cost_centers'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في حذف مركز التكلفة: {str(e)}', 'danger')
        return redirect(url_for('accounting.view_cost_center', center_id=center_id))