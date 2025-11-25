"""
نظام الفاتورة الإلكترونية السعودية - ZATCA Integration
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from models_accounting_einvoice import EInvoice, EInvoiceLineItem, EInvoiceAudit, InvoiceType, VATSummary
from models import UserRole, Module
from datetime import datetime, timedelta
from sqlalchemy import func, extract
import qrcode
from io import BytesIO
import base64

e_invoicing_bp = Blueprint('e_invoicing', __name__, url_prefix='/e-invoicing')


@e_invoicing_bp.route('/dashboard')
@login_required
def dashboard():
    """لوحة تحكم الفاتورة الإلكترونية"""
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        flash('ليس لديك صلاحية للوصول لهذا القسم', 'danger')
        return redirect(url_for('dashboard.index'))
    
    try:
        # إحصائيات الفواتير
        total_invoices = EInvoice.query.count()
        compliant_invoices = EInvoice.query.filter_by(compliance_status='compliant').count()
        pending_invoices = EInvoice.query.filter_by(compliance_status='pending').count()
        rejected_invoices = EInvoice.query.filter_by(compliance_status='rejected').count()
        
        # إجمالي الضريبة
        current_month_start = datetime.now().replace(day=1)
        current_month_end = (current_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        total_vat = db.session.query(func.sum(EInvoice.vat_amount)).filter(
            EInvoice.issue_date >= current_month_start,
            EInvoice.issue_date <= current_month_end
        ).scalar() or 0
        
        total_sales = db.session.query(func.sum(EInvoice.total_amount)).filter(
            EInvoice.issue_date >= current_month_start,
            EInvoice.issue_date <= current_month_end
        ).scalar() or 0
        
        # آخر الفواتير
        recent_invoices = EInvoice.query.order_by(EInvoice.issue_date.desc()).limit(10).all()
        
        return render_template('e_invoicing/dashboard.html',
                             total_invoices=total_invoices,
                             compliant_invoices=compliant_invoices,
                             pending_invoices=pending_invoices,
                             rejected_invoices=rejected_invoices,
                             total_vat=total_vat,
                             total_sales=total_sales,
                             recent_invoices=recent_invoices)
    
    except Exception as e:
        flash(f'خطأ في تحميل لوحة التحكم: {str(e)}', 'danger')
        return redirect(url_for('dashboard.index'))


@e_invoicing_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_invoice():
    """إنشاء فاتورة إلكترونية جديدة"""
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        flash('ليس لديك صلاحية للوصول لهذا القسم', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        try:
            # بيانات المورد والمشتري
            invoice = EInvoice(
                invoice_number=request.form.get('invoice_number'),
                invoice_type=InvoiceType[request.form.get('invoice_type', 'STANDARD')],
                seller_name=request.form.get('seller_name'),
                seller_vat_number=request.form.get('seller_vat_number'),
                seller_commercial_register=request.form.get('seller_commercial_register'),
                buyer_name=request.form.get('buyer_name'),
                buyer_vat_number=request.form.get('buyer_vat_number'),
                buyer_email=request.form.get('buyer_email'),
                subtotal=float(request.form.get('subtotal', 0)),
                vat_rate=float(request.form.get('vat_rate', 15)),
            )
            
            # حساب الضريبة والمجموع
            invoice.vat_amount = invoice.subtotal * (invoice.vat_rate / 100)
            invoice.total_amount = invoice.subtotal + invoice.vat_amount
            
            # توليد التجزئة وQR Code
            invoice.generate_hash()
            
            # توليد رمز QR
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(f"SEL:{invoice.seller_vat_number}|INV:{invoice.invoice_number}|DATE:{invoice.issue_date.isoformat()}|TOTAL:{invoice.total_amount}|VAT:{invoice.vat_amount}|HASH:{invoice.hash_value}")
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img_io = BytesIO()
            img.save(img_io, 'PNG')
            img_io.seek(0)
            invoice.qr_code = base64.b64encode(img_io.getvalue()).decode()
            
            db.session.add(invoice)
            db.session.commit()
            
            # تسجيل التدقيق
            audit = EInvoiceAudit(
                invoice_id=invoice.id,
                action='created',
                status_after='pending',
                created_by=current_user.id
            )
            db.session.add(audit)
            db.session.commit()
            
            flash('تم إنشاء الفاتورة الإلكترونية بنجاح', 'success')
            return redirect(url_for('e_invoicing.view_invoice', invoice_id=invoice.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في إنشاء الفاتورة: {str(e)}', 'danger')
    
    return render_template('e_invoicing/create.html', invoice_types=InvoiceType)


@e_invoicing_bp.route('/<int:invoice_id>')
@login_required
def view_invoice(invoice_id):
    """عرض الفاتورة الإلكترونية"""
    invoice = EInvoice.query.get_or_404(invoice_id)
    
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        flash('ليس لديك صلاحية للوصول لهذه الفاتورة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    return render_template('e_invoicing/view.html', invoice=invoice)


@e_invoicing_bp.route('/<int:invoice_id>/submit', methods=['POST'])
@login_required
def submit_invoice(invoice_id):
    """إرسال الفاتورة إلى ZATCA"""
    invoice = EInvoice.query.get_or_404(invoice_id)
    
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        flash('ليس لديك صلاحية للوصول لهذه الفاتورة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    try:
        # في الواقع، يجب إرسال الفاتورة إلى ZATCA API
        # هنا نقوم بتحديث الحالة محاكاة
        invoice.compliance_status = 'submitted'
        
        audit = EInvoiceAudit(
            invoice_id=invoice.id,
            action='submitted',
            status_before='pending',
            status_after='submitted',
            created_by=current_user.id
        )
        
        db.session.add(audit)
        db.session.commit()
        
        flash('تم إرسال الفاتورة إلى ZATCA بنجاح', 'success')
        return redirect(url_for('e_invoicing.view_invoice', invoice_id=invoice_id))
    
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في إرسال الفاتورة: {str(e)}', 'danger')
        return redirect(url_for('e_invoicing.view_invoice', invoice_id=invoice_id))


@e_invoicing_bp.route('/vat-report')
@login_required
def vat_report():
    """تقرير الضريبة المضافة"""
    if not (current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.ACCOUNTING)):
        flash('ليس لديك صلاحية للوصول لهذا التقرير', 'danger')
        return redirect(url_for('dashboard.index'))
    
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    
    # الحصول على الفواتير في الشهر المحدد
    invoices = EInvoice.query.filter(
        extract('month', EInvoice.issue_date) == month,
        extract('year', EInvoice.issue_date) == year
    ).all()
    
    total_tax_due = sum(float(inv.vat_amount or 0) for inv in invoices)
    total_sales = sum(float(inv.total_amount or 0) for inv in invoices)
    
    return render_template('e_invoicing/vat_report.html',
                         invoices=invoices,
                         month=month,
                         year=year,
                         total_tax_due=total_tax_due,
                         total_sales=total_sales)


@e_invoicing_bp.route('/api/invoices')
@login_required
def api_invoices():
    """API للحصول على قائمة الفواتير"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = EInvoice.query
    
    # الفلترة حسب الحالة
    status = request.args.get('status')
    if status:
        query = query.filter_by(compliance_status=status)
    
    paginated = query.order_by(EInvoice.issue_date.desc()).paginate(page, per_page)
    
    return jsonify({
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page,
        'invoices': [{
            'id': inv.id,
            'invoice_number': inv.invoice_number,
            'seller_name': inv.seller_name,
            'buyer_name': inv.buyer_name,
            'total_amount': float(inv.total_amount),
            'vat_amount': float(inv.vat_amount),
            'compliance_status': inv.compliance_status,
            'issue_date': inv.issue_date.isoformat()
        } for inv in paginated.items]
    })
