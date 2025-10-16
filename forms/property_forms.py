from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, DateField, SelectField, BooleanField, IntegerField, FileField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange, URL
from flask_wtf.file import FileAllowed, FileSize

class RentalPropertyForm(FlaskForm):
    """نموذج إضافة وتعديل العقار المستأجر"""
    
    # معلومات العقار الأساسية
    name = StringField('اسم العقار', validators=[DataRequired()])
    property_type = SelectField('نوع العقار',
                               choices=[
                                   ('apartment', 'شقة'),
                                   ('villa', 'فيلا'),
                                   ('building', 'عمارة'),
                                   ('full_floor', 'دور كامل'),
                                   ('office', 'مكتب'),
                                   ('warehouse', 'مستودع'),
                                   ('other', 'أخرى')
                               ],
                               validators=[DataRequired()])
    address = TextAreaField('العنوان', validators=[DataRequired()])
    area = FloatField('المساحة (م²)', validators=[Optional(), NumberRange(min=0)])
    rooms = IntegerField('عدد الغرف', validators=[Optional(), NumberRange(min=0)])
    notes = TextAreaField('ملاحظات')
    
    # معلومات المالك والعقد
    landlord_name = StringField('اسم المالك', validators=[DataRequired()])
    landlord_phone = StringField('رقم هاتف المالك', validators=[Optional()])
    contract_number = StringField('رقم العقد', validators=[Optional()])
    contract_start_date = DateField('تاريخ بداية العقد', validators=[DataRequired()], format='%Y-%m-%d')
    contract_end_date = DateField('تاريخ نهاية العقد', validators=[DataRequired()], format='%Y-%m-%d')
    contract_file = FileField('ملف العقد (PDF أو صورة)', 
                             validators=[
                                 FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 
                                           'الملفات المسموح بها: PDF, JPG, PNG فقط!')
                             ])
    location_link = StringField('رابط موقع السكن', validators=[Optional(), URL(message='الرجاء إدخال رابط صحيح')])
    
    # المعلومات المالية
    monthly_rent = FloatField('الإيجار الشهري (ريال)', validators=[DataRequired(), NumberRange(min=0)])
    payment_method = SelectField('طريقة السداد', 
                                choices=[
                                    ('monthly', 'شهري'),
                                    ('quarterly', 'ربع سنوي'),
                                    ('semi_annually', 'نصف سنوي'),
                                    ('annually', 'سنوي')
                                ],
                                validators=[DataRequired()])
    payment_day = IntegerField('يوم الدفع من الشهر', validators=[Optional(), NumberRange(min=1, max=31)])
    payment_notes = TextAreaField('ملاحظات الدفع')
    
    # صور العقار
    images = FileField('صور العقار', 
                      validators=[
                          FileAllowed(['jpg', 'jpeg', 'png', 'heic', 'webp'], 
                                    'الصور المسموح بها: JPG, PNG, HEIC, WEBP فقط!')
                      ],
                      render_kw={"multiple": True})


class PropertyImagesForm(FlaskForm):
    """نموذج رفع صور العقار"""
    
    image_type = SelectField('نوع الصورة',
                            choices=[
                                ('واجهة', 'واجهة'),
                                ('غرف', 'غرف'),
                                ('مطبخ', 'مطبخ'),
                                ('دورة مياه', 'دورة مياه'),
                                ('أخرى', 'أخرى')
                            ],
                            validators=[DataRequired()])
    description = StringField('وصف الصورة', validators=[Optional()])
    images = FileField('صور العقار', 
                      validators=[
                          FileAllowed(['jpg', 'jpeg', 'png', 'heic', 'webp'], 
                                    'الصور المسموح بها: JPG, PNG, HEIC, WEBP فقط!')
                      ],
                      render_kw={"multiple": True})


class PropertyPaymentForm(FlaskForm):
    """نموذج إضافة وتعديل دفعة إيجار"""
    
    payment_date = DateField('تاريخ الدفعة المتوقع', validators=[DataRequired()], format='%Y-%m-%d')
    amount = FloatField('مبلغ الدفعة (ريال)', validators=[DataRequired(), NumberRange(min=0)])
    status = SelectField('حالة الدفع',
                        choices=[
                            ('pending', 'معلق'),
                            ('paid', 'مدفوع'),
                            ('overdue', 'متأخر')
                        ],
                        validators=[DataRequired()])
    actual_payment_date = DateField('التاريخ الفعلي للدفع', validators=[Optional()], format='%Y-%m-%d')
    payment_method = SelectField('طريقة الدفع',
                                choices=[
                                    ('', '-- اختر --'),
                                    ('نقدي', 'نقدي'),
                                    ('تحويل بنكي', 'تحويل بنكي'),
                                    ('شيك', 'شيك'),
                                    ('الدفع في منصة ايجار', 'الدفع في منصة ايجار')
                                ],
                                validators=[Optional()])
    reference_number = StringField('الرقم المرجعي للدفعة', validators=[Optional()])
    notes = TextAreaField('ملاحظات')


class PropertyFurnishingForm(FlaskForm):
    """نموذج تجهيزات العقار"""
    
    # أنواع التجهيزات
    gas_cylinder = IntegerField('عدد جرات الغاز', validators=[Optional(), NumberRange(min=0)], default=0)
    stoves = IntegerField('عدد الطباخات', validators=[Optional(), NumberRange(min=0)], default=0)
    beds = IntegerField('عدد الأسرّة', validators=[Optional(), NumberRange(min=0)], default=0)
    blankets = IntegerField('عدد البطانيات', validators=[Optional(), NumberRange(min=0)], default=0)
    pillows = IntegerField('عدد المخدات', validators=[Optional(), NumberRange(min=0)], default=0)
    
    # تجهيزات إضافية
    other_items = TextAreaField('تجهيزات إضافية (أخرى)')
    notes = TextAreaField('ملاحظات')
    
    # زر الإرسال
    submit = SubmitField('حفظ التجهيزات')
