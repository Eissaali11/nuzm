"""
نماذج الفاتورة الإلكترونية السعودية ZATCA
النظام السعودي للفواتير الإلكترونية - ZATCA Electronic Invoice
"""
from app import db
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Enum
import hashlib
import json


class InvoiceType(PyEnum):
    """أنواع الفواتير"""
    STANDARD = "standard"  # فاتورة عادية
    SIMPLIFIED = "simplified"  # فاتورة مبسطة
    DEBIT_NOTE = "debit_note"  # إشعار خصم
    CREDIT_NOTE = "credit_note"  # إشعار دائن


class TaxTreatment(PyEnum):
    """معاملة الضريبة"""
    SUBJECT_TO_VAT = "subject_to_vat"  # خاضع للضريبة
    EXEMPT = "exempt"  # معفى من الضريبة
    REVERSE_CHARGE = "reverse_charge"  # انقلاب الخصم


class EInvoice(db.Model):
    """الفاتورة الإلكترونية السعودية"""
    __tablename__ = 'e_invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # بيانات الفاتورة الأساسية
    invoice_number = db.Column(db.String(100), unique=True, nullable=False, index=True)
    invoice_type = db.Column(Enum(InvoiceType), default=InvoiceType.STANDARD)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    currency = db.Column(db.String(3), default='SAR')
    
    # بيانات المورد (البائع)
    seller_name = db.Column(db.String(200), nullable=False)
    seller_vat_number = db.Column(db.String(20), nullable=False)  # رقم ضريبة المبيعات
    seller_commercial_register = db.Column(db.String(50))  # السجل التجاري
    seller_city = db.Column(db.String(100))
    seller_tax_scheme_id = db.Column(db.String(50), default='KSA-VAT')  # معرف نظام الضريبة السعودي
    
    # بيانات المشتري
    buyer_name = db.Column(db.String(200), nullable=False)
    buyer_vat_number = db.Column(db.String(20))
    buyer_national_id = db.Column(db.String(20))  # معرف وطني للأفراد
    buyer_email = db.Column(db.String(120))
    buyer_city = db.Column(db.String(100))
    
    # المبالغ المالية
    subtotal = db.Column(db.Numeric(15, 2), default=0)
    vat_amount = db.Column(db.Numeric(15, 2), default=0)
    vat_rate = db.Column(db.Numeric(5, 2), default=15)  # معدل الضريبة - السعودية 15%
    total_amount = db.Column(db.Numeric(15, 2), default=0)
    
    # خصومات وإضافات
    discount_amount = db.Column(db.Numeric(15, 2), default=0)
    additional_charges = db.Column(db.Numeric(15, 2), default=0)
    
    # التوقيع الرقمي
    digital_signature = db.Column(db.Text)  # التوقيع الرقمي للفاتورة
    hash_value = db.Column(db.String(256))  # قيمة التجزئة
    
    # رمز الاستجابة السريعة
    qr_code = db.Column(db.Text)  # رمز QR يحتوي على بيانات الفاتورة
    
    # حالة التوافقية
    compliance_status = db.Column(db.String(50), default='pending')  # pending, submitted, compliant, rejected
    zatca_response = db.Column(db.JSON)  # رد ZATCA
    
    # بيانات إضافية
    notes = db.Column(db.Text)
    attachment = db.Column(db.String(500))  # مسار المرفقات
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def generate_hash(self):
        """توليد قيمة التجزئة للفاتورة"""
        invoice_string = f"{self.seller_vat_number}{self.invoice_number}{self.issue_date.isoformat()}{self.subtotal}{self.vat_amount}{self.total_amount}"
        self.hash_value = hashlib.sha256(invoice_string.encode()).hexdigest()
        return self.hash_value
    
    def to_zatca_xml(self):
        """تحويل الفاتورة إلى صيغة XML معيارية ZATCA"""
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
    <ID>{self.invoice_number}</ID>
    <IssueDate>{self.issue_date.date()}</IssueDate>
    <InvoiceTypeCode>{self.invoice_type.value}</InvoiceTypeCode>
    <Currency>{self.currency}</Currency>
    
    <AccountingSupplierParty>
        <Party>
            <PartyLegalEntity>
                <RegistrationName>{self.seller_name}</RegistrationName>
                <CompanyID schemeID="KSA-CR">{self.seller_commercial_register}</CompanyID>
            </PartyLegalEntity>
            <PartyTaxScheme>
                <CompanyID schemeID="{self.seller_tax_scheme_id}">{self.seller_vat_number}</CompanyID>
            </PartyTaxScheme>
        </Party>
    </AccountingSupplierParty>
    
    <AccountingCustomerParty>
        <Party>
            <PartyLegalEntity>
                <RegistrationName>{self.buyer_name}</RegistrationName>
            </PartyLegalEntity>
        </Party>
    </AccountingCustomerParty>
    
    <LegalMonetaryTotal>
        <LineExtensionAmount>{self.subtotal}</LineExtensionAmount>
        <TaxTotal>
            <TaxAmount>{self.vat_amount}</TaxAmount>
        </TaxTotal>
        <PayableAmount>{self.total_amount}</PayableAmount>
    </LegalMonetaryTotal>
</Invoice>"""
        return xml
    
    def __repr__(self):
        return f'<EInvoice {self.invoice_number} - {self.total_amount} SAR>'


class EInvoiceLineItem(db.Model):
    """بنود الفاتورة الإلكترونية"""
    __tablename__ = 'e_invoice_line_items'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('e_invoices.id', ondelete='CASCADE'), nullable=False)
    
    # بيانات البند
    line_number = db.Column(db.Integer)
    description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Numeric(15, 2), nullable=False)
    unit = db.Column(db.String(50), default='EA')  # وحدة القياس
    unit_price = db.Column(db.Numeric(15, 2), nullable=False)
    
    # الضريبة
    line_total = db.Column(db.Numeric(15, 2))
    vat_rate = db.Column(db.Numeric(5, 2), default=15)
    vat_amount = db.Column(db.Numeric(15, 2))
    line_total_with_vat = db.Column(db.Numeric(15, 2))
    
    # العلاقات
    invoice = db.relationship('EInvoice', backref='line_items')
    
    def __repr__(self):
        return f'<EInvoiceLineItem {self.description} - {self.quantity} {self.unit}>'


class EInvoiceAudit(db.Model):
    """سجل تدقيق الفواتير الإلكترونية"""
    __tablename__ = 'e_invoice_audit'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('e_invoices.id', ondelete='CASCADE'))
    
    # تفاصيل التدقيق
    action = db.Column(db.String(50))  # created, submitted, approved, rejected, modified
    status_before = db.Column(db.String(50))
    status_after = db.Column(db.String(50))
    
    # بيانات ZATCA
    zatca_uuid = db.Column(db.String(255))  # معرف فريد من ZATCA
    zatca_timestamp = db.Column(db.DateTime)
    zatca_message = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __repr__(self):
        return f'<EInvoiceAudit Invoice#{self.invoice_id} - {self.action}>'


class VATSummary(db.Model):
    """ملخص الضريبة المضافة - للتقارير الشهرية"""
    __tablename__ = 'vat_summary'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # الفترة الزمنية
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    
    # ملخص الضريبة
    total_tax_due = db.Column(db.Numeric(15, 2), default=0)
    total_tax_recovered = db.Column(db.Numeric(15, 2), default=0)
    net_tax_payable = db.Column(db.Numeric(15, 2), default=0)
    
    # الفواتير
    invoices_count = db.Column(db.Integer, default=0)
    credit_notes_count = db.Column(db.Integer, default=0)
    
    # التوافقية
    compliance_status = db.Column(db.String(50))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<VATSummary {self.month}/{self.year}>'
