from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, DateField, SelectField, BooleanField, IntegerField, FileField
from wtforms.validators import DataRequired, Optional, NumberRange, URL
from flask_wtf.file import FileAllowed, FileSize

class RentalPropertyForm(FlaskForm):
    """نموذج إضافة وتعديل العقار المستأجر"""
    
    # معلومات العقار
    city = StringField('المدينة', validators=[DataRequired()])
    address = TextAreaField('العنوان', validators=[DataRequired()])
    map_link = StringField('رابط الموقع على الخريطة', validators=[Optional(), URL()])
    
    # بيانات عقد الإيجار
    contract_number = StringField('رقم العقد', validators=[DataRequired()])
    owner_name = StringField('اسم المالك', validators=[DataRequired()])
    owner_id = StringField('رقم هوية المالك / السجل التجاري', validators=[DataRequired()])
    contract_start_date = DateField('تاريخ بداية العقد', validators=[DataRequired()], format='%Y-%m-%d')
    contract_end_date = DateField('تاريخ نهاية العقد', validators=[DataRequired()], format='%Y-%m-%d')
    
    # تفاصيل الإيجار
    annual_rent_amount = FloatField('مبلغ الإيجار السنوي (ريال)', validators=[DataRequired(), NumberRange(min=0)])
    includes_utilities = BooleanField('يشمل الماء والكهرباء؟')
    payment_method = SelectField('طريقة السداد', 
                                choices=[
                                    ('monthly', 'شهري'),
                                    ('quarterly', 'ربع سنوي'),
                                    ('semi_annually', 'نصف سنوي'),
                                    ('annually', 'سنوي كامل')
                                ],
                                validators=[DataRequired()])
    
    # حالة العقار
    status = SelectField('حالة العقار',
                        choices=[
                            ('active', 'نشط'),
                            ('expired', 'منتهي'),
                            ('cancelled', 'ملغي')
                        ],
                        validators=[DataRequired()])
    
    # ملاحظات
    notes = TextAreaField('ملاحظات')


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
                                    ('شيك', 'شيك')
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
