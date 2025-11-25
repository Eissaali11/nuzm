"""
نماذج وحدة السيارات
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, DateField, BooleanField, DecimalField, HiddenField, IntegerField, SubmitField, FileField
from wtforms.validators import DataRequired, Optional, NumberRange, URL, Length
from datetime import date


class VehicleDocumentsForm(FlaskForm):
    """نموذج تحديث تواريخ انتهاء وثائق السيارة الهامة"""
    vehicle_id = HiddenField('معرف السيارة')
    authorization_expiry_date = DateField('تاريخ انتهاء التفويض', validators=[Optional()])
    registration_expiry_date = DateField('تاريخ انتهاء استمارة السيارة', validators=[Optional()])
    inspection_expiry_date = DateField('تاريخ انتهاء الفحص الدوري', validators=[Optional()])
    submit = SubmitField('حفظ')


class VehicleAccidentForm(FlaskForm):
    """نموذج إضافة وتعديل سجل حادث مروري"""
    vehicle_id = HiddenField('معرف السيارة')
    accident_date = DateField('تاريخ الحادث', validators=[DataRequired()], default=date.today)
    driver_name = StringField('اسم السائق', validators=[DataRequired(), Length(min=2, max=100)])
    accident_status = SelectField('حالة الحادث', choices=[
        ('قيد المعالجة', 'قيد المعالجة'),
        ('مغلق', 'مغلق'),
        ('معلق', 'معلق'),
        ('في التأمين', 'في التأمين')
    ], default='قيد المعالجة')
    vehicle_condition = StringField('حالة السيارة', validators=[Optional(), Length(max=100)])
    deduction_amount = DecimalField('مبلغ الخصم على السائق', validators=[Optional(), NumberRange(min=0)], default=0.0)
    deduction_status = BooleanField('تم الخصم')
    liability_percentage = SelectField('نسبة تحمل السائق', choices=[
        ('0', 'لا يوجد تحمل (0%)'),
        ('25', 'تحمل جزئي (25%)'),
        ('50', 'تحمل متوسط (50%)'),
        ('75', 'تحمل كبير (75%)'),
        ('100', 'تحمل كامل (100%)')
    ], default='0', coerce=int)
    accident_file_link = StringField('رابط ملف الحادث', validators=[Optional()])
    location = StringField('موقع الحادث', validators=[Optional(), Length(max=255)])
    police_report = BooleanField('تم عمل محضر شرطة')
    insurance_claim = BooleanField('تم رفع مطالبة للتأمين')
    description = TextAreaField('وصف الحادث', validators=[Optional()])
    notes = TextAreaField('ملاحظات إضافية', validators=[Optional()])
    submit = SubmitField('حفظ')