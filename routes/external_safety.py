from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app, send_file
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from PIL import Image
from pillow_heif import register_heif_opener

# تسجيل plugin الـ HEIC/HEIF للتعامل مع صور الآيفون
register_heif_opener()
from models import VehicleExternalSafetyCheck, VehicleSafetyImage, Vehicle, Employee, User, UserRole, VehicleHandover
from app import db
from utils.audit_logger import log_audit
from flask_login import current_user
from sqlalchemy import func, select
from sqlalchemy.orm import aliased, contains_eager

from dotenv import load_dotenv
import resend

from whatsapp_client import WhatsAppWrapper # <-- استيراد الكلاس



# قم بتحميل المتغيرات من ملف .env
load_dotenv()
# قم بإعداد مفتاح Resend مرة واحدة عند بدء التطبيق
resend.api_key = os.environ.get("RESEND_API_KEY")
supervisor_email = os.environ.get("SAFETY_CHECK_SUPERVISOR_EMAIL")
company_name = os.environ.get("COMPANY_NAME")
external_safety_bp = Blueprint('external_safety', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'heic', 'heif'}

def get_all_current_driversWithEmil():
    """
    تسترجع قاموساً يحتوي على معلومات السائق الحالي لكل مركبة.
    المفتاح هو ID المركبة، والقيمة هي قاموس يحتوي على (name, email, mobile).
    """
    # 1. نحدد أنواع التسليم
    delivery_handover_types = ['delivery', 'تسليم', 'handover']
    
    # 2. إنشاء استعلام فرعي لتحديد أحدث سجل تسليم لكل مركبة
    # (نفس منطق Window Function السابق)
    subq = select(
        VehicleHandover.id,
        func.row_number().over(
            partition_by=VehicleHandover.vehicle_id,
            order_by=VehicleHandover.handover_date.desc()
        ).label('row_num')
    ).where(
        VehicleHandover.handover_type.in_(delivery_handover_types)
    ).subquery()

    # 3. إنشاء الاستعلام الرئيسي
    # سنربط (JOIN) بين السجلات الأحدث والموظفين المرتبطين بها
    # ونستخدم `contains_eager` لجلب بيانات الموظف بكفاءة عالية في نفس الاستعلام
    stmt = select(VehicleHandover).join(
        subq, VehicleHandover.id == subq.c.id
    ).join(
        Employee, VehicleHandover.employee_id == Employee.id  # الربط باستخدام جدول Employee
    ).where(subq.c.row_num == 1)

    # 4. تنفيذ الاستعلام وجلب النتائج
    latest_handovers_with_drivers = db.session.execute(stmt).scalars().all()
    
    # 5. تحويل النتائج إلى القاموس (dictionary) بالصيغة الجديدة
    current_drivers_map = {
        record.vehicle_id: {
            'name': record.driver_employee.name,
            'email': record.driver_employee.email,
            'mobile': record.driver_employee.mobile,
            'phone' : record.driver_employee.mobile
        }
        for record in latest_handovers_with_drivers if record.driver_employee # نتأكد من وجود سائق
    }
    
    return current_drivers_map



# في نفس ملف الراوت external_safety_bp




# قم بإنشاء نسخة واحدة من الكلاس على مستوى الـ Blueprint أو التطبيق
# من الأفضل وضعها في __init__.py الخاص بالتطبيق و استيرادها
whatsapp_service = WhatsAppWrapper() 

# ----- أضف هذه الدالة الجديدة بجانب دالة send_vehicle_email -----

@external_safety_bp.route('/api/send-whatsapp', methods=['POST'])
def send_vehicle_whatsapp():
    """
    نقطة نهاية (API endpoint) لإرسال طلب فحص المركبة عبر واتساب.
    """
    # 1. استلام البيانات من الطلب (نفس بيانات البريد الإلكتروني)
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'الطلب فارغ'}), 400

    # استخراج البيانات. لاحظ أننا نحتاج رقم هاتف السائق بدلاً من البريد
    driver_phone = data.get('driver_phone') # <-- أهم معلومة جديدة
    driver_name = data.get('driver_name', 'زميلنا العزيز')
    plate_number = data.get('plate_number')
    vehicle_model = data.get('vehicle_model')
    form_url = data.get('form_url')

    # التحقق من وجود البيانات الضرورية
    if not all([driver_phone, plate_number, vehicle_model, form_url]):
        error_message = "بيانات ناقصة. تأكد من إرسال: driver_phone, driver_name, plate_number, vehicle_model, form_url."
        return jsonify({'success': False, 'error': error_message}), 400

    # 2. تجهيز مكونات قالب واتساب
    template_name = "vehicle_safety_check_request" # <-- اسم القالب الذي وافقت عليه Meta

    # ترتيب المتغيرات مهم جداً ويجب أن يطابق ترتيبها في القالب
    components = [
        {
            "type": "body",
            "parameters": [
                {"type": "text", "text": driver_name},     # يحل محل {{1}}
                {"type": "text", "text": plate_number},    # يحل محل {{2}}
                {"type": "text", "text": vehicle_model},   # يحل محل {{3}}
                {"type": "text", "text": form_url},        # يحل محل {{4}} في الجسم
            ]
         }
        #  ,
        # # إذا كان زر الرابط ديناميكياً، نضيف له مكوناً أيضاً
        # {
        #     "type": "button",
        #     "sub_type": "url",
        #     "index": "0",  # رقم الزر (يبدأ من 0)
        #     "parameters": [
        #         {"type": "text", "text": form_url.split('/')[-1]} # الرابط يجب أن يكون الجزء الأخير بعد /
        #                                                         # مثال: "external_safety_check/vehicle_id"
        #     ]
        # }
    ]

    # ملاحظة على رابط الزر: واتساب يتطلب أن يكون الجزء المتغير من الرابط
    # فقط. الرابط الأساسي (e.g. https://nuzum.sa) تضعه عند تصميم القالب.

    # 3. استدعاء خدمة واتساب للإرسال
    try:
        response = whatsapp_service.send_template_message(
            recipient_number=driver_phone, # رقم السائق مع رمز الدولة
            template_name=template_name,
            language_code="ar",
            components=components
        )
        
        if response:
            return jsonify({'success': True, 'message': f"تم إرسال رسالة واتساب بنجاح إلى {driver_name}"})
        else:
            # إذا فشلت دالتنا في الإرسال (مثلاً خطأ في الاتصال)
            return jsonify({'success': False, 'error': 'فشل إرسال رسالة واتساب من الخادم'}), 500

    except Exception as e:
        # لأي خطأ آخر غير متوقع
        print(f"Error sending WhatsApp message: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def get_all_current_drivers():
    """
    تسترجع قاموساً يحتوي على السائق الحالي لكل مركبة. (بصيغة حديثة)
    المفتاح هو ID المركبة، والقيمة هي اسم السائق.
    """
    
    # 1. نحدد أنواع التسليم
    delivery_handover_types = ['delivery', 'تسليم', 'handover']
    
    # 2. إنشاء استعلام فرعي (Subquery) باستخدام Window Function
    subq = select(
        VehicleHandover.id,
        func.row_number().over(
            partition_by=VehicleHandover.vehicle_id,
            order_by=VehicleHandover.handover_date.desc()
        ).label('row_num')
    ).where(
        VehicleHandover.handover_type.in_(delivery_handover_types)
    ).subquery()

    # 3. الآن، نحصل على أحدث السجلات عن طريق اختيار التي لها row_num = 1
    stmt = select(VehicleHandover).join(
        subq, VehicleHandover.id == subq.c.id
    ).where(subq.c.row_num == 1)

    # 4. تنفيذ الاستعلام وجلب النتائج
    # .scalars() تجلب الكائنات (objects) مباشرة بدلاً من الصفوف (rows)
    latest_handovers = db.session.execute(stmt).scalars().all()
    
    # 5. تحويل النتائج إلى قاموس (dictionary) سهل الاستخدام
    current_drivers_map = {
        record.vehicle_id: record.person_name for record in latest_handovers
    }
    
    return current_drivers_map


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def compress_image(image_path, max_size=1200, quality=85):
    """ضغط الصورة لتقليل حجمها مع دعم HEIC من الآيفون"""
    try:
        with Image.open(image_path) as img:
            # تحويل RGBA أو أي تنسيق آخر إلى RGB
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # تحويل HEIC إلى RGB وضغطها
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # تغيير حجم الصورة إذا كانت أكبر من الحد المسموح
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # حفظ الصورة المضغوطة
            img.save(image_path, 'JPEG', quality=quality, optimize=True)
            return True
    except Exception as e:
        current_app.logger.error(f"خطأ في ضغط الصورة: {str(e)}")
        return False


def send_supervisor_notification_email(safety_check):
    """
    تقوم ببناء وإرسال بريد إلكتروني لإشعار المشرف بوجود طلب فحص جديد.
    """
    # --- !! هام: قم بتعديل هذه المتغيرات !! ---
    # الخيار الأفضل: اقرأ هذا من إعدادات التطبيق (config file)
    # SUPERVISOR_EMAIL = current_app.config.get('SAFETY_CHECK_SUPERVISOR_EMAIL')
    # supervisor_email = "ferasswed2022@gmail.com"  # <--- ضع بريد المشرف هنا
    # company_name = "نُــظــم لإدارة الأساطيل"
    # ----------------------------------------------
    
    # توليد الرابط الخاص بمراجعة الطلب في لوحة التحكم
    # تأكد من أن اسم الـ blueprint والنقطة النهائية صحيحين. قد يكون 'admin.view_check' أو ما شابه
    logo_url = "https://i.postimg.cc/LXzD6b0N/logo.png" # <--- رابط الشعار العام
    try:
        review_url = url_for('external_safety_bp.admin_view_safety_check', # <--- تأكد من هذا المسار
                             check_id=safety_check.id, 
                             _external=True)
    except Exception as e:
        # حل احتياطي في حال حدوث خطأ، لكن يجب إصلاح المسار أعلاه
        review_url = f"http://127.0.0.1:4032//admin/external-safety-check/{safety_check.id}"
        current_app.logger.error(f"Failed to generate review URL, using fallback. Error: {e}")

    # بناء قالب HTML احترافي للإشعار

    email_html_content = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
            body {{
                margin: 0;
                padding: 0;
                background-color: #e9ecef; /* خلفية رمادية فاتحة جدا */
                font-family: 'Tajawal', sans-serif;
            }}
            .email-wrapper {{
                max-width: 680px;
                margin: 40px auto;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.07);
            }}
            .email-header {{
                background: linear-gradient(135deg, #182551 10%, #425359 100%);
                border-radius: 12px 12px 0 0;
                padding: 25px;
                text-align: center;
            }}
            .email-header img {{
                max-height: 50px; /* حجم مناسب للشعار */
                margin-bottom: 15px;
            }}
            .email-header h1 {{
                margin: 0;
                color: #ffffff;
                font-size: 26px;
                font-weight: 700;
            }}
            .email-body {{
                padding: 25px 35px;
                text-align: right;
            }}
            .greeting {{
                font-size: 20px;
                color: #2c3e50;
                font-weight: 700;
                margin-bottom: 10px;
            }}
            .main-message {{
                font-size: 16px;
                color: #555;
                line-height: 1.7;
            }}
            .details-card {{
                background-color: #f8f9fa;
                border: 1px dashed #ced4da;
                border-radius: 8px;
                padding: 20px;
                margin: 25px 0;
            }}
            .details-card h3 {{
                margin-top: 0;
                color: #343a40;
                border-bottom: 2px solid #dee2e6;
                padding-bottom: 10px;
                margin-bottom: 15px;
            }}
            .details-card p {{
                margin: 8px 0;
                font-size: 16px;
            }}
            .details-card p strong {{
                color: #495057;
                display: inline-block;
                width: 110px;
            }}
            .action-button-container {{
                text-align: center;
                margin: 30px 0;
            }}
            .action-button {{
                background: linear-gradient(135deg, #0d6efd 0%, #0a58ca 100%);
                color: #ffffff !important;
                padding: 14px 40px;
                text-decoration: none;
                border-radius: 50px;
                font-weight: 700;
                font-size: 18px;
                box-shadow: 0 5px 15px rgba(52,152,219,0.3);
                transition: all 0.3s ease;
            }}
            .action-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(52,152,219,0.4);
            }}
            .email-footer {{
                padding: 20px;
                text-align: center;
                font-size: 13px;
                color: #888;
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
            }}
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="email-header">
                <img src="{logo_url}" alt="{company_name} Logo">
                <h1>إشعار بفحص جديد</h1>
            </div>
            <div class="email-body">
                <p class="greeting">مرحباً أيها المشرف،</p>
                <p class="main-message">تم استلام طلب فحص سلامة جديد وهو في انتظار مراجعتكم لاتخاذ الإجراء المناسب. يرجى الاطلاع على التفاصيل أدناه.</p>
                
                <div class="details-card">
                    <h3>تفاصيل الطلب</h3>
                    <p><strong>رقم الطلب:</strong> #{safety_check.id}</p>
                    <p><strong>المركبة:</strong> {safety_check.vehicle_plate_number} ({safety_check.vehicle_make_model})</p>
                    <p><strong>السائق:</strong> {safety_check.driver_name}</p>
                    <p><strong>التاريخ:</strong> {safety_check.inspection_date.strftime('%d-%m-%Y %I:%M %p')}</p>
                </div>

                <p class="main-message">اضغط على الزر أدناه للانتقال مباشرة إلى صفحة المراجعة:</p>

                <div class="action-button-container">
                    <a href="{review_url}" class="action-button">مراجعة طلب الفحص</a>
                </div>
            </div>
            <div class="email-footer">
                <p>© {datetime.now().year} {company_name}. جميع الحقوق محفوظة.</p>
            </div>
        </div>
    </body>
    </html>
    """

    

    # إرسال البريد الإلكتروني عبر Resend
    try:
        params = {
            "from": f"{company_name} <notifications@resend.dev>",
            "to": [supervisor_email],
            "subject": f"طلب فحص جديد للمركبة {safety_check.vehicle_plate_number} بحاجة لمراجعة",
            "html": email_html_content,
        }
        resend.Emails.send(params)
        current_app.logger.info(f"تم إرسال إشعار للمشرف بنجاح بخصوص فحص ID: {safety_check.id}")
    except Exception as e:
        current_app.logger.error(f"فشل إرسال إشعار للمشرف بخصوص فحص ID: {safety_check.id}. الخطأ: {e}")





@external_safety_bp.route('/external-safety-check/<int:vehicle_id>', methods=['GET', 'POST'])
def external_safety_check_form(vehicle_id):
    """عرض نموذج فحص السلامة الخارجي للسيارة أو معالجة البيانات المرسلة"""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    if request.method == 'POST':
        return handle_safety_check_submission(vehicle)
    
    return render_template('external_safety_check.html', vehicle=vehicle)



def handle_safety_check_submission(vehicle):
    """معالجة إرسال بيانات فحص السلامة"""
    try:
        # الحصول على البيانات من النموذج
        driver_name = request.form.get('driver_name')
        driver_national_id = request.form.get('driver_national_id')
        driver_department = request.form.get('driver_department')
        driver_city = request.form.get('driver_city')
        vehicle_plate_number = request.form.get('vehicle_plate_number', vehicle.plate_number)
        vehicle_make_model = request.form.get('vehicle_make_model', f"{vehicle.make} {vehicle.model}")
        current_delegate = request.form.get('current_delegate')
        notes = request.form.get('notes')
        
        # التحقق من البيانات المطلوبة
        if not all([driver_name, driver_national_id, driver_department, driver_city]):
            return jsonify({'error': 'يرجى ملء جميع الحقول المطلوبة'}), 400
        
        # إنشاء سجل فحص السلامة
        safety_check = VehicleExternalSafetyCheck()
        safety_check.vehicle_id = vehicle.id
        safety_check.driver_name = driver_name
        safety_check.driver_national_id = driver_national_id
        safety_check.driver_department = driver_department
        safety_check.driver_city = driver_city
        safety_check.vehicle_plate_number = vehicle_plate_number
        safety_check.vehicle_make_model = vehicle_make_model
        safety_check.current_delegate = current_delegate
        safety_check.notes = notes
        safety_check.inspection_date = datetime.now()
        safety_check.approval_status = 'pending'
        
        db.session.add(safety_check)
        db.session.flush()  # للحصول على ID الجديد
        
        # معالجة الصور من الكاميرا
        camera_images = request.form.get('camera_images', '')
        image_notes = request.form.get('image_notes', '')
        
        if camera_images:
            # إنشاء مجلد الصور في جذر المشروع (مجلد دائم)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            upload_dir = os.path.join(project_root, 'uploads', 'safety_checks')
            os.makedirs(upload_dir, exist_ok=True)
            
            import base64
            
            # تقسيم الصور والملاحظات
            image_list = camera_images.split('|||') if camera_images else []
            notes_list = image_notes.split('|||') if image_notes else []
            
            for i, image_data in enumerate(image_list):
                if image_data and image_data.startswith('data:image'):
                    try:
                        # استخراج البيانات من base64
                        header, data = image_data.split(',', 1)
                        image_bytes = base64.b64decode(data)
                        
                        # تحديد التنسيق المصدر وتحويل إلى JPEG للتوافق
                        source_format = 'jpg'  # افتراضي
                        if 'png' in header:
                            source_format = 'png'
                        elif 'jpeg' in header or 'jpg' in header:
                            source_format = 'jpg'
                        elif 'heic' in header or 'heif' in header:
                            source_format = 'heic'
                        elif 'webp' in header:
                            source_format = 'webp'
                        
                        # دائماً حفظ كـ JPEG للتوافق مع جميع المتصفحات
                        ext = 'jpg'
                        
                        # إنشاء اسم ملف آمن
                        filename = f"{uuid.uuid4()}.{ext}"
                        image_path = os.path.join(upload_dir, filename)
                        
                        # حفظ الصورة
                        with open(image_path, 'wb') as f:
                            f.write(image_bytes)
                        
                        # ضغط الصورة وتحويلها إلى JPEG
                        success = compress_image(image_path)
                        if not success:
                            current_app.logger.warning(f"فشل ضغط الصورة {filename}")
                        else:
                            current_app.logger.info(f"تم تحويل صورة {source_format} إلى JPEG: {filename}")
                        
                        # حفظ معلومات الصورة في قاعدة البيانات
                        description = notes_list[i] if i < len(notes_list) else None
                        
                        safety_image = VehicleSafetyImage()
                        safety_image.safety_check_id = safety_check.id
                        safety_image.image_path = f'uploads/safety_checks/{filename}'
                        safety_image.image_description = description
                        
                        db.session.add(safety_image)
                        
                    except Exception as e:
                        current_app.logger.error(f"خطأ في معالجة الصورة {i}: {str(e)}")
                        continue
        
        # حفظ جميع التغييرات
        db.session.commit()

        send_supervisor_notification_email(safety_check)

        
        # تسجيل العملية في سجل المراجعة
        log_audit(
            user_id=current_user.id if current_user.is_authenticated else None,
            action='create',
            entity_type='VehicleExternalSafetyCheck',
            entity_id=safety_check.id,
            details=f'تم إنشاء طلب فحص السلامة الخارجي للسيارة {vehicle.plate_number} بواسطة {safety_check.driver_name}'
        )
        
        current_app.logger.info(f'تم إنشاء طلب فحص السلامة بنجاح: ID={safety_check.id}, Vehicle={vehicle.plate_number}')
        
        # توجيه المستخدم لصفحة التأكيد المميزة
        return redirect(url_for('external_safety.success_page', safety_check_id=safety_check.id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'خطأ في معالجة طلب فحص السلامة: {str(e)}')
        flash('حدث خطأ أثناء معالجة الطلب', 'danger')
        return redirect(url_for('external_safety.external_safety_check_form', vehicle_id=vehicle.id))

@external_safety_bp.route('/success/<int:safety_check_id>')
def success_page(safety_check_id):
    """صفحة تأكيد إرسال طلب فحص السلامة"""
    safety_check = VehicleExternalSafetyCheck.query.get_or_404(safety_check_id)
    return render_template('external_safety_success.html', safety_check=safety_check)

@external_safety_bp.route('/status/<int:safety_check_id>')
def check_status(safety_check_id):
    """التحقق من حالة طلب فحص السلامة - للإشعارات"""
    safety_check = VehicleExternalSafetyCheck.query.get_or_404(safety_check_id)
    
    # إنشاء رسالة حسب الحالة
    if safety_check.approval_status == 'approved':
        message = {
            'type': 'success',
            'title': 'تم اعتماد الطلب',
            'text': 'تم اعتماد طلب فحص السلامة بنجاح من قبل الإدارة.'
        }
    elif safety_check.approval_status == 'rejected':
        message = {
            'type': 'error',
            'title': 'تم رفض الطلب',
            'text': f'نرجو المحاولة مرة أخرى. تم رفض الطلب.\nسبب الرفض: {safety_check.rejection_reason or "لم يتم تحديد السبب"}'
        }
    else:
        message = {
            'type': 'pending',
            'title': 'قيد المراجعة',
            'text': 'طلبك قيد المراجعة من قبل الإدارة المختصة.'
        }
    
    return jsonify(message)





@external_safety_bp.route('/')
def external_safety_index():
    """الصفحة الرئيسية لنظام فحص السلامة الخارجية"""
    return redirect(url_for('external_safety.share_links'))

@external_safety_bp.route('/share-links')
def share_links():
    """صفحة مشاركة روابط النماذج الخارجية لجميع السيارات مع الفلاتر"""
    # الحصول على معاملات الفلترة من الطلب
    status_filter = request.args.get('status', '')
    make_filter = request.args.get('make', '')
    search_plate = request.args.get('search_plate', '')
    project_filter = request.args.get('project', '')

    
    # قاعدة الاستعلام الأساسية
    query = Vehicle.query
    
    # فلترة المركبات حسب القسم المحدد للمستخدم الحالي
    from flask_login import current_user
    from models import employee_departments, Department, Employee, VehicleHandover
    if current_user.is_authenticated and hasattr(current_user, 'assigned_department_id') and current_user.assigned_department_id:
        # الحصول على معرفات الموظفين في القسم المحدد
        dept_employee_ids = db.session.query(Employee.id).join(
            employee_departments
        ).join(Department).filter(
            Department.id == current_user.assigned_department_id
        ).all()
        dept_employee_ids = [emp.id for emp in dept_employee_ids]
        
        if dept_employee_ids:
            # فلترة المركبات التي لها تسليم لموظف في القسم المحدد
            vehicle_ids_with_handovers = db.session.query(
                VehicleHandover.vehicle_id
            ).filter(
                VehicleHandover.handover_type == 'delivery',
                VehicleHandover.employee_id.in_(dept_employee_ids)
            ).distinct().all()
            
            vehicle_ids = [h.vehicle_id for h in vehicle_ids_with_handovers]
            if vehicle_ids:
                query = query.filter(Vehicle.id.in_(vehicle_ids))
            else:
                query = query.filter(Vehicle.id == -1)  # قائمة فارغة
        else:
            query = query.filter(Vehicle.id == -1)  # قائمة فارغة
    
    # إضافة التصفية حسب الحالة إذا تم تحديدها
    if status_filter:
        query = query.filter(Vehicle.status == status_filter)
    
    # إضافة التصفية حسب الشركة المصنعة إذا تم تحديدها
    if make_filter:
        query = query.filter(Vehicle.make == make_filter)
    
    # إضافة التصفية حسب المشروع إذا تم تحديده
    if project_filter:
        query = query.filter(Vehicle.project == project_filter)
    
    # إضافة البحث برقم السيارة إذا تم تحديده
    if search_plate:
        query = query.filter(Vehicle.plate_number.contains(search_plate))
    
    # الحصول على قائمة بالشركات المصنعة لقائمة التصفية
    makes = db.session.query(Vehicle.make).distinct().all()
    makes = [make[0] for make in makes]
    
    # الحصول على قائمة بالمشاريع لقائمة التصفية
    projects = db.session.query(Vehicle.project).filter(Vehicle.project.isnot(None)).distinct().all()
    projects = [project[0] for project in projects]
    
    # الحصول على قائمة السيارات
    vehicles = query.order_by(Vehicle.status, Vehicle.plate_number).all()
    all_current_drivers = get_all_current_drivers()
    all_current_drivers_with_emil = get_all_current_driversWithEmil()
    
    # قائمة حالات السيارات
    statuses = ['available', 'rented', 'in_project', 'in_workshop', 'accident']
    
    return render_template('external_safety_share_links.html', 
                           vehicles=vehicles,
                           status_filter=status_filter,
                           make_filter=make_filter,
                           search_plate=search_plate,
                           project_filter=project_filter,
                           makes=makes,
                           projects=projects,
                           statuses=statuses,
                           all_current_drivers=all_current_drivers,
                           all_current_drivers_with_emil=all_current_drivers_with_emil
                           )

# في ملف الراوت الخاص بك (e.g., external_safety_bp.py)

@external_safety_bp.route('/api/send-email', methods=['POST'])
def send_vehicle_email():
    """
    نقطة نهاية (API endpoint) متكاملة لتلقي طلب إرسال بريد إلكتروني
    احترافي ومصمم لفحص المركبة عبر Resend.
    """
    # 1. استلام البيانات من الطلب القادم من JavaScript
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'الطلب فارغ أو ليس بصيغة JSON'}), 400

    driver_email = data.get('driver_email')
    driver_name = data.get('driver_name', 'زميلنا العزيز') # اسم افتراضي
    plate_number = data.get('plate_number')
    vehicle_model = data.get('vehicle_model')
    form_url = data.get('form_url')

    # التحقق من وجود جميع البيانات الضرورية
    if not all([driver_email, plate_number, vehicle_model, form_url]):
        error_message = "بيانات ناقصة في الطلب. تأكد من إرسال كل من: driver_email, plate_number, vehicle_model, form_url."
        return jsonify({'success': False, 'error': error_message}), 400

    # 2. إعداد المتغيرات الخاصة بالرسالة (الشعار والاسم)
    # ===== تم تطبيق الإصلاحات هنا =====
    company_name = os.environ.get("COMPANY_NAME", "نُــظــم لإدارة الأساطيل")
    logo_url = "https://i.postimg.cc/LXzD6b0N/logo.png" # رابط ثابت وآمن للشعار

    # 3. بناء قالب HTML الكامل للبريد الإلكتروني
    email_html_content = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
            body {{ margin: 0; padding: 0; background-color: #f4f7f6; font-family: 'Tajawal', sans-serif; }}
            .email-container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
            .email-header {{ background-color: #171e3f; color: #ffffff; padding: 20px; text-align: center; }}
            .email-header img {{ max-width: 150px; margin-bottom: 10px; }}
            .email-body {{ padding: 30px; color: #333333; line-height: 1.6; text-align: right; }}
            .email-body h2 {{ color: #2c3e50; font-size: 22px; }}
            .vehicle-info {{ background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 15px; margin: 20px 0; }}
            .button-container {{ text-align: center; margin: 30px 0; }}
            .button {{ background: linear-gradient(135deg, #3498db, #2980b9); color: #ffffff !important; padding: 12px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block; font-size: 16px; transition: transform 0.2s ease; }}
            .button:hover {{ transform: translateY(-2px); }}
            .instructions-section {{ margin-top: 25px; border-top: 1px solid #eeeeee; padding-top: 20px; }}
            .instructions-section h3 {{ color: #e67e22; font-size: 18px; }}
            .instructions-section ul {{ padding-right: 20px; list-style-type: '✔️  '; }}
            .email-footer {{ background-color: #2c3e50; color: #bdc3c7; padding: 20px; text-align: center; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="email-header">
                <img src="{logo_url}" alt="{company_name} Logo">
                <h1>{company_name}</h1>
            </div>
            <div class="email-body">
                <h2>إجراء مطلوب: فحص السلامة الخارجي للمركبة</h2>
                <p>مرحباً <strong>{driver_name}</strong> 👋،</p>
                <p>نرجو منك تعبئة نموذج فحص السلامة الخارجي للمركبة التالية بدقة وعناية.</p>
                <div class="vehicle-info">
                    🚗 <strong>المركبة:</strong> {plate_number} ({vehicle_model})
                </div>
                <p><strong>👇 الرابط المباشر للنموذج:</strong></p>
                <div class="button-container">
                    <a href="{form_url}" class="button">فتح نموذج الفحص</a>
                </div>
                <div class="instructions-section">
                    <h3>📋 التعليمات المطلوبة (مهم جدًا):</h3>
                    <h4>1️⃣ الصور الأساسية (إلزامية):</h4>
                    <ul>
                        <li>صورة من <strong>الأمام</strong> (تظهر كامل واجهة المركبة).</li>
                        <li>صورة من <strong>الخلف</strong> (تظهر كامل خلفية المركبة).</li>
                        <li>صورة من <strong>الجانب الأيمن والأيسر</strong> (بشكل واضح وكامل).</li>
                        <li>صورة <strong>لسقف</strong> المركبة.</li>
                        <li>صورة لـ <strong>أسفل المركبة من الأمام</strong>.</li>
                    </ul>
                    <h4>2️⃣ صور الملاحظات (إن وجدت):</h4>
                    <ul>
                        <li>إذا وجدت أي خدوش، صدمات، أو عيوب، قم بتصويرها عن قرب.</li>
                        <li><strong>هام:</strong> قم بالإشارة بإصبعك إلى مكان الملاحظة في الصورة.</li>
                        <li>اكتب وصفاً لكل ملاحظة أسفل الصورة المرفوعة.</li>
                    </ul>
                </div>
                <div class="instructions-section">
                    <h3>✅ ما بعد إرسال النموذج:</h3>
                    <ul>
                        <li><strong>في حال القبول:</strong> سيتم إعلامك وتفعيل إجراءات الوقود.</li>
                        <li><strong>في حال الرفض:</strong> ستصلك رسالة بالسبب. يرجى الدخول على نفس الرابط مجدداً وتصحيح الملاحظات.</li>
                    </ul>
                </div>
                <p>شكرًا لتعاونكم وحرصكم على السلامة.</p>
            </div>
            <div class="email-footer">
                <p>هذه رسالة آلية من {company_name}.</p>
                <p>© {datetime.now().year} جميع الحقوق محفوظة.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # 4. بناء طلب الإرسال واستدعاء Resend API
    try:
        params = {
            "from": f"{company_name} <onboarding@resend.dev>",
            "to": [driver_email],
            "subject": f"إجراء مطلوب: فحص السلامة للمركبة {plate_number}",
            "html": email_html_content,
        }
        sent_email = resend.Emails.send(params)

        # يمكنك تفعيل السطر التالي للتشخيص إذا لزم الأمر
        # current_app.logger.info(f"Email sent successfully. ID: {sent_email['id']}")

        return jsonify({'success': True, 'message': f"تم إرسال البريد الإلكتروني بنجاح إلى {driver_email}"})

    except Exception as e:
        # تسجيل الخطأ بالتفصيل في سجلات الخادم للمساعدة في التشخيص
        current_app.logger.error(f"Error sending email with Resend: {e}")
        # إرجاع رسالة خطأ واضحة
        return jsonify({'success': False, 'error': f"فشل في إرسال البريد عبر الخدمة الخارجية: {str(e)}"}), 500

# # # ----- أضف هذه الدالة الجديدة لمشروعك -----
# @external_safety_bp.route('/api/send-email', methods=['POST'])
# def send_vehicle_email():
#     """
#     نقطة نهاية (API endpoint) متكاملة لتلقي طلب إرسال بريد إلكتروني
#     احترافي ومصمم لفحص المركبة عبر Resend.
#     """
#     # 1. استلام البيانات من الطلب القادم من JavaScript
#     data = request.get_json()
#     if not data:
#         return jsonify({'success': False, 'error': 'الطلب فارغ أو ليس بصيغة JSON'}), 400

#     driver_email = data.get('driver_email')
#     driver_name = data.get('driver_name', 'زميلنا العزيز') # اسم افتراضي
#     plate_number = data.get('plate_number')
#     vehicle_model = data.get('vehicle_model')
#     form_url = data.get('form_url')

#     # التحقق من وجود جميع البيانات الضرورية
#     if not all([driver_email, plate_number, vehicle_model, form_url]):
#         error_message = "بيانات ناقصة في الطلب. تأكد من إرسال كل من: driver_email, plate_number, vehicle_model, form_url."
#         return jsonify({'success': False, 'error': error_message}), 400

#     # 2. إعداد المتغيرات الخاصة بالرسالة (الشعار والاسم)
#     # company_name = "شركة رأس السعودية المحدوده"  # <--- يمكنك تغيير هذا
#     # تأكد من أن مسار الشعار صحيح. _external=True ضروري لتوليد رابط كامل.
#     logo_path = 'images/logo.png' # <--- يمكنك تغيير هذا
#     try:
#         logo_url = url_for('static', filename=logo_path, _external=True)

#     except RuntimeError:
#         # هذا الحل الاحتياطي يعمل إذا تم استدعاء الدالة خارج سياق الطلب
#         # (على الرغم من أنه في حالتك لن يحدث ذلك مع استدعاء API)
#         logo_url = "https://your-fallback-domain.com" + url_for('static', filename=logo_path)


#     # 3. بناء قالب HTML الكامل للبريد الإلكتروني
#     email_html_content = f"""
#     <!DOCTYPE html>
#     <html lang="ar" dir="rtl">
#     <head>
#         <meta charset="UTF-8">
#         <meta name="viewport" content="width=device-width, initial-scale=1.0">
#         <style>
#             body {{ margin: 0; padding: 0; background-color: #f4f7f6; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }}
#             .email-container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
#             .email-header {{ background-color: #171e3f; color: #ffffff; padding: 20px; text-align: center; }}
#             .email-header img {{ max-width: 150px; margin-bottom: 10px; }}
#             .email-body {{ padding: 30px; color: #333333; line-height: 1.6; text-align: right; }}
#             .email-body h2 {{ color: #2c3e50; font-size: 22px; }}
#             .vehicle-info {{ background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 15px; margin: 20px 0; }}
#             .button-container {{ text-align: center; margin: 30px 0; }}
#             .button {{ background-color: #3498db; color: #ffffff !important; padding: 12px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block; font-size: 16px; }}
#             .instructions-section {{ margin-top: 25px; border-top: 1px solid #eeeeee; padding-top: 20px; }}
#             .instructions-section h3 {{ color: #e67e22; font-size: 18px; }}
#             .instructions-section ul {{ padding-right: 20px; list-style-type: '✔️ '; }}
#             .email-footer {{ background-color: #2c3e50; color: #bdc3c7; padding: 20px; text-align: center; font-size: 12px; }}
#         </style>
#     </head>
#     <body>
#         <div class="email-container">
#             <div class="email-header">
#                 <img src="https://i.postimg.cc/LXzD6b0N/logo.png" alt="نُــظــم  للحلول البرمجية">
#                 <h1>{company_name}</h1>
#             </div>
#             <div class="email-body">
#                 <h2>إجراء مطلوب: فحص السلامة الخارجي للمركبة</h2>
#                 <p>مرحباً <strong>{driver_name}</strong> 👋،</p>
#                 <p>نرجو منك تعبئة نموذج فحص السلامة الخارجي للمركبة التالية بدقة وعناية.</p>
#                 <div class="vehicle-info">
#                     🚗 <strong>المركبة:</strong> {plate_number} ({vehicle_model})
#                 </div>
#                 <p><strong>👇 الرابط المباشر للنموذج:</strong></p>
#                 <div class="button-container">
#                     <a href="{form_url}" class="button">فتح نموذج الفحص</a>
#                 </div>
#                 <div class="instructions-section">
#                     <h3>📋 التعليمات المطلوبة (مهم جدًا):</h3>
#                     <h4>1️⃣ الصور الأساسية (إلزامية):</h4>
#                     <ul>
#                         <li>صورة من <strong>الأمام</strong> (تظهر كامل واجهة المركبة).</li>
#                         <li>صورة من <strong>الخلف</strong> (تظهر كامل خلفية المركبة).</li>
#                         <li>صورة من <strong>الجانب الأيمن والأيسر</strong> (من الزاوية).</li>
#                         <li>صورة <strong>لسقف</strong> المركبة.</li>
#                         <li>صورة لـ <strong>أسفل المركبة من الأمام</strong>.</li>
#                     </ul>
#                     <h4>2️⃣ صور الملاحظات (إن وجدت):</h4>
#                     <ul>
#                         <li>إذا وجدت أي خدوش، صدمات، أو عيوب، قم بتصويرها عن قرب.</li>
#                         <li><strong>هام:</strong> قم بالإشارة بإصبعك إلى مكان الملاحظة في الصورة.</li>
#                         <li>اكتب وصفاً لكل ملاحظة أسفل الصورة المرفوعة.</li>
#                     </ul>
#                 </div>
#                 <div class="instructions-section">
#                     <h3>✅ ما بعد إرسال النموذج:</h3>
#                     <ul>
#                         <li><strong>في حال القبول:</strong> سيتم إعلامك وتفعيل إجراءات الوقود.</li>
#                         <li><strong>في حال الرفض:</strong> ستصلك رسالة بالسبب. يرجى الدخول على نفس الرابط مجدداً وتصحيح الملاحظات.</li>
#                     </ul>
#                 </div>
#                 <p>شكرًا لتعاونكم وحرصكم على السلامة.</p>
#             </div>
#             <div class="email-footer">
#                 <p>هذه رسالة آلية من {company_name}.</p>
#                 <p>© {datetime.now().year} جميع الحقوق محفوظة.</p>
#             </div>
#         </div>
#     </body>
#     </html>
#     """

#     # 4. بناء طلب الإرسال واستدعاء Resend API
#     try:
#         params = {
#             "from": f"{company_name} <onboarding@resend.dev>",
#             "to": [driver_email],
#             "subject": f"إجراء مطلوب: فحص السلامة للمركبة {plate_number}",
#             "html": email_html_content,
#         }
#         sent_email = resend.Emails.send(params)
        
#         # يمكنك تفعيل هذه للتشخيص
#         # print(f"Email sent successfully. ID: {sent_email['id']}")
        
#         return jsonify({'success': True, 'message': f"تم إرسال البريد الإلكتروني بنجاح إلى {driver_email}"})

#     except Exception as e:
#         # في حال حدوث خطأ من Resend أو غيره
#         print(f"Error sending email with Resend: {e}")
#         return jsonify({'success': False, 'error': str(e)}), 500



@external_safety_bp.route('/api/verify-employee/<national_id>')
def verify_employee(national_id):
    """التحقق من الموظف بواسطة رقم الهوية"""
    try:
        # البحث عن الموظف بواسطة رقم الهوية
        employee = Employee.query.filter_by(national_id=national_id).first()
        
        if not employee:
            return jsonify({'success': False, 'message': 'الموظف غير موجود'}), 404
        
        # الحصول على أسماء الأقسام
        department_names = [dept.name for dept in employee.departments] if employee.departments else []
        
        return jsonify({
            'success': True,
            'employee': {
                'id': employee.id,
                'name': employee.name,
                'department': ', '.join(department_names) if department_names else 'غير محدد',
                'city': employee.city if hasattr(employee, 'city') else 'الرياض',
                'national_id': employee.national_id
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"خطأ في التحقق من الموظف: {str(e)}")
        return jsonify({'success': False, 'message': 'حدث خطأ في التحقق من الموظف'}), 500

@external_safety_bp.route('/external-safety-check/success')
def external_safety_success():
    """صفحة نجاح إرسال طلب فحص السلامة"""
    return render_template('external_safety_success.html')

@external_safety_bp.route('/admin/external-safety-checks')
def admin_external_safety_checks():
    """عرض جميع طلبات فحص السلامة للإدارة مع الفلاتر"""
    from flask_login import current_user
    from models import employee_departments, Department, Employee, VehicleHandover, Vehicle
    
    # التحقق من تسجيل الدخول
    if not current_user.is_authenticated:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect('/login')
    
    # الحصول على معايير الفلترة من request
    vehicle_filter = request.args.get('vehicle_filter', '').strip()
    vehicle_search = request.args.get('vehicle_search', '').strip()
    department_filter = request.args.get('department_filter', '').strip()
    status_filter = request.args.get('status_filter', '').strip()
    
    # بناء الاستعلام مع الفلاتر
    query = VehicleExternalSafetyCheck.query
    
    # فلترة فحوصات السلامة حسب القسم المحدد للمستخدم الحالي
    if current_user.is_authenticated and hasattr(current_user, 'assigned_department_id') and current_user.assigned_department_id:
        # الحصول على معرفات الموظفين في القسم المحدد
        dept_employee_ids = db.session.query(Employee.id).join(
            employee_departments
        ).join(Department).filter(
            Department.id == current_user.assigned_department_id
        ).all()
        dept_employee_ids = [emp.id for emp in dept_employee_ids]
        
        if dept_employee_ids:
            # فلترة فحوصات السلامة للمركبات المسلمة لموظفي القسم المحدد
            dept_vehicle_plates = db.session.query(Vehicle.plate_number).join(
                VehicleHandover, Vehicle.id == VehicleHandover.vehicle_id
            ).filter(
                VehicleHandover.handover_type == 'delivery',
                VehicleHandover.employee_id.in_(dept_employee_ids)
            ).distinct().all()
            dept_vehicle_plates = [v.plate_number for v in dept_vehicle_plates]
            if dept_vehicle_plates:
                query = query.filter(VehicleExternalSafetyCheck.vehicle_plate_number.in_(dept_vehicle_plates))
            else:
                query = query.filter(VehicleExternalSafetyCheck.id == -1)  # قائمة فارغة
        else:
            query = query.filter(VehicleExternalSafetyCheck.id == -1)  # قائمة فارغة
    
    # فلترة حسب رقم السيارة (من القائمة المنسدلة)
    if vehicle_filter:
        query = query.filter(VehicleExternalSafetyCheck.vehicle_plate_number.contains(vehicle_filter))
    
    # البحث في السيارة (من حقل البحث)
    if vehicle_search:
        query = query.filter(VehicleExternalSafetyCheck.vehicle_plate_number.contains(vehicle_search))
    
    # فلترة حسب القسم
    if department_filter:
        query = query.filter(VehicleExternalSafetyCheck.driver_department.contains(department_filter))
    
    # فلترة حسب الحالة
    if status_filter:
        query = query.filter(VehicleExternalSafetyCheck.approval_status == status_filter)
    
    # جلب النتائج مرتبة حسب التاريخ
    safety_checks = query.order_by(VehicleExternalSafetyCheck.created_at.desc()).all()
    
    # إحصائيات للفلاتر
    total_checks = VehicleExternalSafetyCheck.query.count()
    pending_checks = VehicleExternalSafetyCheck.query.filter_by(approval_status='pending').count()
    approved_checks = VehicleExternalSafetyCheck.query.filter_by(approval_status='approved').count()
    rejected_checks = VehicleExternalSafetyCheck.query.filter_by(approval_status='rejected').count()
    
    # جلب قائمة السيارات والأقسام للفلاتر
    vehicles_list = db.session.query(VehicleExternalSafetyCheck.vehicle_plate_number).distinct().all()
    vehicles_list = [v[0] for v in vehicles_list if v[0]]
    
    departments_list = db.session.query(VehicleExternalSafetyCheck.driver_department).distinct().all()
    departments_list = [d[0] for d in departments_list if d[0]]
    
    return render_template('admin_external_safety_checks.html', 
                         safety_checks=safety_checks,
                         vehicle_filter=vehicle_filter,
                         vehicle_search=vehicle_search,
                         department_filter=department_filter,
                         status_filter=status_filter,
                         vehicles_list=vehicles_list,
                         departments_list=departments_list,
                         total_checks=total_checks,
                         pending_checks=pending_checks,
                         approved_checks=approved_checks,
                         rejected_checks=rejected_checks)

@external_safety_bp.route('/admin/external-safety-check/<int:check_id>')
def admin_view_safety_check(check_id):
    """عرض تفاصيل طلب فحص السلامة"""
    if not current_user.is_authenticated:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect('/login')
    
    # استخدام العلاقة المحددة مسبقاً لجلب الصور مع فحص السلامة
    safety_check = VehicleExternalSafetyCheck.query.options(
        db.selectinload(VehicleExternalSafetyCheck.safety_images)
    ).get_or_404(check_id)
    
    current_app.logger.info(f'تم جلب فحص السلامة ID={check_id} مع {len(safety_check.safety_images)} صور')
    
    # تحديث مسار الصور المحفوظة في قاعدة البيانات إذا لزم الأمر
    if safety_check.safety_images:
        for img in safety_check.safety_images:
            # التأكد من أن المسار يحتوي على static/
            if img.image_path and not img.image_path.startswith('static/'):
                img.image_path = 'static/' + img.image_path
                current_app.logger.info(f'تم تحديث مسار الصورة: {img.image_path}')
            # تحديث مسارات قديمة قد تكون مكررة
            elif img.image_path and img.image_path.startswith('static/static/'):
                img.image_path = img.image_path.replace('static/static/', 'static/')
                current_app.logger.info(f'تم إصلاح مسار مكرر: {img.image_path}')
    
    db.session.commit()
    
    return render_template('admin_view_safety_check.html', safety_check=safety_check)

@external_safety_bp.route('/admin/external-safety-check/<int:check_id>/reject', methods=['GET', 'POST'])
def reject_safety_check_page(check_id):
    """صفحة رفض طلب فحص السلامة"""
    if not current_user.is_authenticated:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect('/login')
    
    safety_check = VehicleExternalSafetyCheck.query.get_or_404(check_id)
    
    if request.method == 'POST':
        # معالجة رفض الطلب
        rejection_reason = request.form.get('rejection_reason')
        
        if not rejection_reason or not rejection_reason.strip():
            flash('يرجى كتابة سبب الرفض', 'error')
            return render_template('admin_reject_safety_check.html', safety_check=safety_check)
        
        # تحديث حالة الطلب
        safety_check.approval_status = 'rejected'
        safety_check.rejection_reason = rejection_reason.strip()
        safety_check.approved_by = current_user.id
        safety_check.approved_at = datetime.now()
        
        db.session.commit()
        
        # تسجيل العملية
        log_audit(
            user_id=current_user.id,
            action='reject',
            entity_type='VehicleExternalSafetyCheck',
            entity_id=safety_check.id,
            details=f'تم رفض طلب فحص السلامة للسيارة {safety_check.vehicle_plate_number}. السبب: {rejection_reason}'
        )
        
        current_app.logger.info(f'تم رفض طلب فحص السلامة ID={safety_check.id} بواسطة {current_user.name}')
        
        flash('تم رفض الطلب بنجاح', 'success')
        return redirect(url_for('external_safety.admin_view_safety_check', check_id=check_id))
    
    return render_template('admin_reject_safety_check.html', safety_check=safety_check)
    return render_template('admin_view_safety_check.html', safety_check=safety_check)

@external_safety_bp.route('/admin/external-safety-check/<int:check_id>/approve', methods=['POST'])
def approve_safety_check(check_id):
    """اعتماد طلب فحص السلامة"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'غير مصرح لك'}), 403
    
    try:
        safety_check = VehicleExternalSafetyCheck.query.get_or_404(check_id)
        
        safety_check.approval_status = 'approved'
        safety_check.approved_by = current_user.id
        safety_check.approved_at = datetime.now()
        
        db.session.commit()
        
        # تسجيل العملية
        log_audit(
            user_id=current_user.id,
            action='approve',
            entity_type='VehicleExternalSafetyCheck',
            entity_id=safety_check.id,
            details=f'تم اعتماد طلب فحص السلامة للسيارة {safety_check.vehicle_plate_number}'
        )
        
        flash('تم اعتماد طلب فحص السلامة بنجاح', 'success')
        return redirect(url_for('external_safety.admin_view_safety_check', check_id=check_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"خطأ في اعتماد طلب فحص السلامة: {str(e)}")
        flash('حدث خطأ في اعتماد الطلب', 'error')
        return redirect(url_for('external_safety.admin_view_safety_check', check_id=check_id))

@external_safety_bp.route('/admin/external-safety-check/<int:check_id>/reject', methods=['POST'])
def reject_safety_check(check_id):
    """رفض طلب فحص السلامة"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'غير مصرح لك'}), 403
    
    try:
        safety_check = VehicleExternalSafetyCheck.query.get_or_404(check_id)
        
        safety_check.approval_status = 'rejected'
        safety_check.approved_by = current_user.id
        safety_check.approved_at = datetime.now()
        safety_check.rejection_reason = request.form.get('rejection_reason', '')
        
        db.session.commit()
        
        # تسجيل العملية
        log_audit(
            user_id=current_user.id,
            action='reject',
            entity_type='VehicleExternalSafetyCheck',
            entity_id=safety_check.id,
            details=f'تم رفض طلب فحص السلامة للسيارة {safety_check.vehicle_plate_number}. السبب: {safety_check.rejection_reason}'
        )
        
        flash('تم رفض طلب فحص السلامة', 'success')
        return redirect(url_for('external_safety.admin_view_safety_check', check_id=check_id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"خطأ في رفض طلب فحص السلامة: {str(e)}")
        flash('حدث خطأ في رفض الطلب', 'error')
        return redirect(url_for('external_safety.admin_view_safety_check', check_id=check_id))

@external_safety_bp.route('/admin/external-safety-check/<int:check_id>/delete', methods=['GET', 'POST'])
def delete_external_safety_check(check_id):
    """حذف طلب فحص السلامة"""
    if not current_user.is_authenticated:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect('/login')
    
    safety_check = VehicleExternalSafetyCheck.query.get_or_404(check_id)
    
    if request.method == 'GET':
        # عرض صفحة تأكيد الحذف
        return render_template('admin_delete_safety_check.html', safety_check=safety_check)
    
    if request.method == 'POST':
        try:
            # حذف الصور المرتبطة من الخادم
            import os
            for image in safety_check.safety_images:
                if image.image_path:
                    image_full_path = os.path.join(current_app.root_path, image.image_path)
                    if os.path.exists(image_full_path):
                        os.remove(image_full_path)
                        current_app.logger.info(f"تم حذف الصورة: {image_full_path}")
            
            # تسجيل العملية قبل الحذف
            log_audit(
                user_id=current_user.id,
                action='delete',
                entity_type='VehicleExternalSafetyCheck',
                entity_id=safety_check.id,
                details=f'تم حذف طلب فحص السلامة للسيارة {safety_check.vehicle_plate_number} - السائق: {safety_check.driver_name}'
            )
            
            # حذف السجل من قاعدة البيانات
            db.session.delete(safety_check)
            db.session.commit()
            
            flash('تم حذف طلب فحص السلامة بنجاح', 'success')
            return redirect(url_for('external_safety.admin_external_safety_checks'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"خطأ في حذف طلب فحص السلامة: {str(e)}")
            flash('حدث خطأ في حذف الطلب', 'error')
            return redirect(url_for('external_safety.admin_view_safety_check', check_id=check_id))

@external_safety_bp.route('/admin/external-safety-check/<int:check_id>/edit', methods=['GET', 'POST'])
def edit_safety_check(check_id):
    """تعديل طلب فحص السلامة"""
    if not current_user.is_authenticated:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('external_safety.admin_external_safety_checks'))
    
    safety_check = VehicleExternalSafetyCheck.query.get_or_404(check_id)
    
    if request.method == 'POST':
        try:
            # تحديث البيانات
            safety_check.current_delegate = request.form.get('current_delegate', '')
            inspection_date_str = request.form.get('inspection_date')
            safety_check.inspection_date = datetime.fromisoformat(inspection_date_str) if inspection_date_str else datetime.now()
            safety_check.driver_name = request.form.get('driver_name', '')
            safety_check.driver_national_id = request.form.get('driver_national_id', '')
            safety_check.driver_department = request.form.get('driver_department', '')
            safety_check.driver_city = request.form.get('driver_city', '')
            safety_check.notes = request.form.get('notes', '')
            
            # تحديث أوصاف الصور
            for image in safety_check.safety_images:
                description_field = f'image_description_{image.id}'
                if description_field in request.form:
                    image.image_description = request.form.get(description_field, '')
            
            # تحديث تاريخ التعديل
            safety_check.updated_at = datetime.now()
            
            db.session.commit()
            
            # تسجيل العملية
            log_audit(
                user_id=current_user.id,
                action='update',
                entity_type='VehicleExternalSafetyCheck',
                entity_id=safety_check.id,
                details=f'تم تحديث طلب فحص السلامة للسيارة {safety_check.vehicle_plate_number}'
            )
            
            flash('تم تحديث طلب فحص السلامة بنجاح', 'success')
            return redirect(url_for('external_safety.admin_view_safety_check', check_id=check_id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"خطأ في تحديث طلب فحص السلامة: {str(e)}")
            flash('حدث خطأ في تحديث الطلب', 'error')
    
    return render_template('admin_edit_safety_check.html', safety_check=safety_check)

@external_safety_bp.route('/admin/external-safety-check/<int:check_id>/delete', methods=['POST'])
def delete_safety_check(check_id):
    """حذف طلب فحص السلامة"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'غير مصرح لك'}), 403
    
    try:
        safety_check = VehicleExternalSafetyCheck.query.get_or_404(check_id)
        
        # حذف الصور المرفقة
        for image in safety_check.safety_images:
            try:
                if os.path.exists(image.image_path):
                    os.remove(image.image_path)
            except Exception as e:
                current_app.logger.error(f"خطأ في حذف الصورة: {str(e)}")
        
        # تسجيل العملية قبل الحذف
        log_audit(
            user_id=current_user.id,
            action='delete',
            entity_type='VehicleExternalSafetyCheck',
            entity_id=safety_check.id,
            details=f'تم حذف طلب فحص السلامة للسيارة {safety_check.vehicle_plate_number}'
        )
        
        db.session.delete(safety_check)
        db.session.commit()
        
        flash('تم حذف طلب فحص السلامة بنجاح', 'success')
        return redirect(url_for('external_safety.admin_external_safety_checks'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"خطأ في حذف طلب فحص السلامة: {str(e)}")
        flash('حدث خطأ في حذف الطلب', 'error')
        return redirect(url_for('external_safety.admin_view_safety_check', check_id=check_id))

@external_safety_bp.route('/admin/external-safety-check/<int:check_id>/pdf')
def export_safety_check_pdf(check_id):
    """تصدير طلب فحص السلامة كملف PDF"""
    if not current_user.is_authenticated:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('external_safety.admin_external_safety_checks'))
    
    try:
        safety_check = VehicleExternalSafetyCheck.query.get_or_404(check_id)
        
        # استيراد مكتبات ReportLab المطلوبة
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, mm, cm
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
        import io
        import os
        
        # استيراد مكتبات معالجة النصوص العربية
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display
            arabic_support = True
        except ImportError:
            arabic_support = False
        
        # دالة لمعالجة النصوص العربية
        def process_arabic_text(text):
            if not text or not arabic_support:
                return text
            try:
                # تشكيل النص العربي
                reshaped_text = arabic_reshaper.reshape(text)
                # تطبيق خوارزمية الـ bidi للاتجاه الصحيح
                display_text = get_display(reshaped_text)
                return display_text
            except Exception as e:
                current_app.logger.error(f"خطأ في معالجة النص العربي: {str(e)}")
                return text
        
        # إنشاء buffer للـ PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm,
            title=f"تقرير فحص السلامة رقم {safety_check.id}"
        )
        
        # تسجيل خط عربي بترتيب أولوية
        arabic_font = 'Helvetica'  # قيمة افتراضية
        font_paths = [
            ('static/fonts/beIN-Normal.ttf', 'خط beIN-Normal.ttf'),
            ('static/fonts/beIN Normal .ttf', 'خط beIN Normal .ttf'),
            ('utils/beIN-Normal.ttf', 'خط beIN-Normal.ttf من utils'),
            ('Cairo.ttf', 'خط Cairo.ttf'),
            ('static/fonts/NotoSansArabic-Regular.ttf', 'خط NotoSansArabic'),
        ]
        
        for font_path, font_name in font_paths:
            try:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('Arabic', font_path))
                    arabic_font = 'Arabic'
                    current_app.logger.info(f"تم تحميل {font_name} بنجاح من {font_path}")
                    break
                else:
                    current_app.logger.warning(f"الخط غير موجود: {font_path}")
            except Exception as e:
                current_app.logger.error(f"فشل في تحميل {font_name}: {str(e)}")
                continue
        
        if arabic_font == 'Helvetica':
            current_app.logger.warning("لم يتم العثور على أي خط عربي، سيتم استخدام Helvetica")
        
        current_app.logger.info(f"الخط المستخدم في PDF: {arabic_font}")
        
        # تعريف الأنماط
        styles = getSampleStyleSheet()
        
        # نمط العنوان الرئيسي
        title_style = ParagraphStyle(
            'CustomTitle',
            fontName=arabic_font,
            fontSize=20,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2C3E50'),
            borderWidth=2,
            borderColor=colors.HexColor('#3498DB'),
            borderPadding=10,
            backColor=colors.HexColor('#ECF0F1')
        )
        
        # نمط العناوين الفرعية
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            fontName=arabic_font,
            fontSize=14,
            spaceAfter=15,
            alignment=TA_RIGHT,
            textColor=colors.HexColor('#2C3E50'),
            borderWidth=1,
            borderColor=colors.HexColor('#BDC3C7'),
            borderPadding=5,
            backColor=colors.HexColor('#F8F9FA')
        )
        
        # نمط النص العادي
        normal_style = ParagraphStyle(
            'CustomNormal',
            fontName=arabic_font,
            fontSize=11,
            spaceAfter=8,
            alignment=TA_RIGHT,
            textColor=colors.HexColor('#34495E')
        )
        
        # نمط وصف الصور
        image_desc_style = ParagraphStyle(
            'ImageDesc',
            fontName=arabic_font,
            fontSize=10,
            spaceAfter=5,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#7F8C8D'),
            backColor=colors.HexColor('#F8F9FA')
        )
        
        # محتوى الـ PDF
        story = []
        
        # العنوان الرئيسي مع شعار
        title_text = process_arabic_text(f"تقرير فحص السلامة الخارجي رقم {safety_check.id}")
        story.append(Paragraph(title_text, title_style))
        story.append(Spacer(1, 20))
        
        # معلومات السيارة
        vehicle_section_title = process_arabic_text("معلومات السيارة")
        story.append(Paragraph(vehicle_section_title, subtitle_style))
        
        vehicle_data = [
            [process_arabic_text('البيان'), process_arabic_text('القيمة')],
            [process_arabic_text('رقم اللوحة'), process_arabic_text(safety_check.vehicle_plate_number)],
            [process_arabic_text('نوع السيارة'), process_arabic_text(safety_check.vehicle_make_model)],
            [process_arabic_text('المفوض الحالي'), process_arabic_text(safety_check.current_delegate or 'غير محدد')],
            [process_arabic_text('تاريخ الفحص'), safety_check.inspection_date.strftime('%Y-%m-%d %H:%M')]
        ]
        
        vehicle_table = Table(vehicle_data, colWidths=[6*cm, 8*cm])
        vehicle_table.setStyle(TableStyle([
            # نمط الرأس
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), arabic_font),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            # نمط الصفوف
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ECF0F1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
        ]))
        
        story.append(vehicle_table)
        story.append(Spacer(1, 20))
        
        # معلومات السائق
        driver_section_title = process_arabic_text("معلومات السائق")
        story.append(Paragraph(driver_section_title, subtitle_style))
        
        driver_data = [
            [process_arabic_text('البيان'), process_arabic_text('القيمة')],
            [process_arabic_text('اسم السائق'), process_arabic_text(safety_check.driver_name)],
            [process_arabic_text('رقم الهوية'), process_arabic_text(safety_check.driver_national_id)],
            [process_arabic_text('القسم'), process_arabic_text(safety_check.driver_department)],
            [process_arabic_text('المدينة'), process_arabic_text(safety_check.driver_city)]
        ]
        
        driver_table = Table(driver_data, colWidths=[6*cm, 8*cm])
        driver_table.setStyle(TableStyle([
            # نمط الرأس
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27AE60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), arabic_font),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            # نمط الصفوف
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ECF0F1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
        ]))
        
        story.append(driver_table)
        story.append(Spacer(1, 20))
        
        # الملاحظات
        if safety_check.notes:
            notes_title = process_arabic_text("الملاحظات والتوصيات")
            story.append(Paragraph(notes_title, subtitle_style))
            notes_text = process_arabic_text(safety_check.notes)
            notes_para = Paragraph(notes_text, normal_style)
            story.append(notes_para)
            story.append(Spacer(1, 20))
        
        # معلومات الحالة
        if safety_check.approved_by:
            status_text = process_arabic_text("معتمدة ✅" if safety_check.is_approved else "مرفوضة ❌")
            status_color = colors.HexColor('#27AE60') if safety_check.is_approved else colors.HexColor('#E74C3C')
            
            status_style = ParagraphStyle(
                'StatusStyle',
                fontName=arabic_font,
                fontSize=14,
                spaceAfter=10,
                alignment=TA_CENTER,
                textColor=status_color,
                borderWidth=2,
                borderColor=status_color,
                borderPadding=8,
                backColor=colors.HexColor('#F8F9FA')
            )
            
            status_label = process_arabic_text(f"حالة الطلب: {status_text}")
            story.append(Paragraph(status_label, status_style))
            
            approval_date = process_arabic_text(f"تاريخ الاعتماد: {safety_check.approved_at.strftime('%Y-%m-%d %H:%M')}")
            story.append(Paragraph(approval_date, normal_style))
            
            approved_by = process_arabic_text(f"تم بواسطة: {safety_check.approver.name if safety_check.approver else 'غير محدد'}")
            story.append(Paragraph(approved_by, normal_style))
            
            if safety_check.rejection_reason:
                rejection_reason = process_arabic_text(f"سبب الرفض: {safety_check.rejection_reason}")
                story.append(Paragraph(rejection_reason, normal_style))
            
            story.append(Spacer(1, 20))
        
        # صور فحص السلامة
        if safety_check.safety_images:
            images_title = process_arabic_text(f"صور فحص السلامة ({len(safety_check.safety_images)} صورة)")
            story.append(Paragraph(images_title, subtitle_style))
            story.append(Spacer(1, 10))
            
            # تنظيم الصور في صفوف (صورتين في كل صف)
            images_per_row = 2
            current_row = []
            
            for i, image in enumerate(safety_check.safety_images):
                try:
                    # التحقق من وجود الصورة مع المسار الكامل
                    image_path = image.image_path
                    if not image_path.startswith('/'):
                        # إضافة المسار المطلق إذا لم يكن موجوداً
                        image_path = os.path.join(os.getcwd(), image_path)
                    
                    # التحقق من وجود الصورة
                    if not os.path.exists(image_path):
                        current_app.logger.warning(f"الصورة غير موجودة: {image_path}")
                        continue
                    
                    # إنشاء كائن الصورة
                    img = RLImage(image_path)
                    
                    # تحديد حجم الصورة (الحد الأقصى)
                    max_width = 7*cm
                    max_height = 5*cm
                    
                    # حساب النسبة للحفاظ على أبعاد الصورة
                    img_width = img.imageWidth
                    img_height = img.imageHeight
                    
                    ratio = min(max_width/img_width, max_height/img_height)
                    img.drawWidth = img_width * ratio
                    img.drawHeight = img_height * ratio
                    
                    # إضافة الصورة مع الوصف
                    description = process_arabic_text(image.image_description or f'صورة رقم {i+1}')
                    img_data = [
                        [img],
                        [Paragraph(description, image_desc_style)]
                    ]
                    
                    img_table = Table(img_data, colWidths=[max_width])
                    img_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
                        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#F8F9FA')),
                        ('TOPPADDING', (0, 0), (-1, -1), 5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5)
                    ]))
                    
                    current_row.append(img_table)
                    
                    # إذا امتلأ الصف أو كانت هذه آخر صورة
                    if len(current_row) == images_per_row or i == len(safety_check.safety_images) - 1:
                        # إضافة خلايا فارغة لإكمال الصف
                        while len(current_row) < images_per_row:
                            current_row.append('')
                        
                        # إنشاء جدول للصف
                        row_table = Table([current_row], colWidths=[max_width + 1*cm] * images_per_row)
                        row_table.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 5),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                            ('TOPPADDING', (0, 0), (-1, -1), 5),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 5)
                        ]))
                        
                        story.append(row_table)
                        story.append(Spacer(1, 15))
                        current_row = []
                
                except Exception as e:
                    current_app.logger.error(f"خطأ في إضافة الصورة للـ PDF: {str(e)}")
                    continue
        
        # تذييل التقرير
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'FooterStyle',
            fontName=arabic_font,
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#7F8C8D'),
            borderWidth=1,
            borderColor=colors.HexColor('#BDC3C7'),
            borderPadding=5,
            backColor=colors.HexColor('#F8F9FA')
        )
        
        footer_text1 = process_arabic_text(f"تم إنشاء هذا التقرير في: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        footer_text2 = process_arabic_text("نُظم - نظام إدارة المركبات والموظفين")
        story.append(Paragraph(footer_text1, footer_style))
        story.append(Paragraph(footer_text2, footer_style))
        
        # بناء الـ PDF
        doc.build(story)
        buffer.seek(0)
        
        # تسجيل العملية
        log_audit(
            user_id=current_user.id,
            action='export_pdf',
            entity_type='VehicleExternalSafetyCheck',
            entity_id=safety_check.id,
            details=f'تم تصدير طلب فحص السلامة للسيارة {safety_check.vehicle_plate_number} كملف PDF'
        )
        
        # إرسال الـ PDF
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'safety_check_{safety_check.id}_{safety_check.vehicle_plate_number}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        current_app.logger.error(f"خطأ في تصدير طلب فحص السلامة كـ PDF: {str(e)}")
        flash('حدث خطأ في تصدير الطلب', 'error')
        return redirect(url_for('external_safety.admin_view_safety_check', check_id=check_id))

@external_safety_bp.route('/admin/bulk-delete-safety-checks', methods=['POST'])
def bulk_delete_safety_checks():
    """حذف عدة طلبات فحص سلامة جماعياً"""
    if not current_user.is_authenticated:
        flash('يرجى تسجيل الدخول أولاً', 'error')
        return redirect(url_for('external_safety.admin_external_safety_checks'))
    
    try:
        # الحصول على معرفات الطلبات المحددة
        check_ids = request.form.getlist('check_ids')
        
        if not check_ids:
            flash('لم يتم تحديد أي طلبات للحذف', 'warning')
            return redirect(url_for('external_safety.admin_external_safety_checks'))
        
        # تحويل المعرفات إلى أرقام صحيحة
        try:
            check_ids = [int(check_id) for check_id in check_ids]
        except ValueError:
            flash('معرفات الطلبات غير صحيحة', 'error')
            return redirect(url_for('external_safety.admin_external_safety_checks'))
        
        # جلب جميع الطلبات المحددة
        safety_checks = VehicleExternalSafetyCheck.query.filter(
            VehicleExternalSafetyCheck.id.in_(check_ids)
        ).all()
        
        if not safety_checks:
            flash('لم يتم العثور على الطلبات المحددة', 'warning')
            return redirect(url_for('external_safety.admin_external_safety_checks'))
        
        deleted_count = 0
        deleted_plates = []
        
        # حذف كل طلب مع صوره
        for safety_check in safety_checks:
            try:
                # حذف الصور المرفقة من الخادم
                images_deleted = 0
                for image in safety_check.safety_images:
                    if image.image_path:
                        image_full_path = os.path.join(current_app.root_path, image.image_path)
                        if os.path.exists(image_full_path):
                            os.remove(image_full_path)
                            images_deleted += 1
                            current_app.logger.info(f"تم حذف الصورة: {image_full_path}")
                
                # تسجيل العملية قبل الحذف
                log_audit(
                    user_id=current_user.id,
                    action='bulk_delete',
                    entity_type='VehicleExternalSafetyCheck',
                    entity_id=safety_check.id,
                    details=f'تم حذف طلب فحص السلامة للسيارة {safety_check.vehicle_plate_number} - السائق: {safety_check.driver_name} (ضمن حذف جماعي لـ {len(check_ids)} طلب)'
                )
                
                # حذف السجل من قاعدة البيانات
                plate_number = safety_check.vehicle_plate_number
                deleted_plates.append(plate_number)
                db.session.delete(safety_check)
                deleted_count += 1
                
                current_app.logger.info(f"تم حذف طلب فحص السلامة رقم {safety_check.id} للسيارة {plate_number} مع {images_deleted} صورة")
                
            except Exception as e:
                current_app.logger.error(f"خطأ في حذف طلب فحص السلامة رقم {safety_check.id}: {str(e)}")
                continue
        
        # حفظ التغييرات
        db.session.commit()
        
        # تسجيل العملية الجماعية
        log_audit(
            user_id=current_user.id,
            action='bulk_delete_completed',
            entity_type='VehicleExternalSafetyCheck',
            entity_id=0,  # للحذف الجماعي
            details=f'تم حذف {deleted_count} طلب فحص سلامة بنجاح من أصل {len(check_ids)} طلب محدد. السيارات: {", ".join(deleted_plates[:5])}{"..." if len(deleted_plates) > 5 else ""}'
        )
        
        if deleted_count > 0:
            flash(f'تم حذف {deleted_count} طلب فحص سلامة بنجاح مع جميع الصور المرفقة', 'success')
        else:
            flash('لم يتم حذف أي طلبات. قد تكون هناك مشكلة في البيانات المحددة', 'warning')
        
        return redirect(url_for('external_safety.admin_external_safety_checks'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"خطأ في الحذف الجماعي لطلبات فحص السلامة: {str(e)}")
        flash('حدث خطأ في عملية الحذف الجماعي. يرجى المحاولة مرة أخرى', 'error')
        return redirect(url_for('external_safety.admin_external_safety_checks'))