"""
إعدادات Google Drive للأرشفة التلقائية
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
from utils.google_drive_service import drive_service
from models import UserRole

google_drive_settings_bp = Blueprint('google_drive_settings', __name__)


@google_drive_settings_bp.route('/settings/google-drive', methods=['GET', 'POST'])
@login_required
def google_drive():
    """صفحة إعدادات Google Drive"""
    
    # التحقق من أن المستخدم admin
    if current_user.role != UserRole.ADMIN:
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        # التحقق من وجود ملف
        if 'credentials_file' not in request.files:
            flash('الرجاء اختيار ملف بيانات الاعتماد', 'warning')
            return redirect(request.url)
        
        file = request.files['credentials_file']
        
        if file.filename == '':
            flash('لم يتم اختيار أي ملف', 'warning')
            return redirect(request.url)
        
        if file and file.filename.endswith('.json'):
            try:
                # قراءة محتوى الملف
                credentials_content = file.read().decode('utf-8')
                credentials_dict = json.loads(credentials_content)
                
                # التحقق من صحة البيانات
                required_fields = ['type', 'project_id', 'private_key', 'client_email']
                if all(field in credentials_dict for field in required_fields):
                    # حفظ في ملف
                    credentials_path = os.path.join('utils', 'google_drive_credentials.json')
                    with open(credentials_path, 'w') as f:
                        json.dump(credentials_dict, f, indent=2)
                    
                    # حفظ أيضاً في متغير بيئي (للاستخدام المؤقت)
                    os.environ['GOOGLE_DRIVE_CREDENTIALS'] = json.dumps(credentials_dict)
                    
                    # إعادة تحميل بيانات الاعتماد
                    drive_service.credentials = credentials_dict
                    
                    # محاولة المصادقة
                    if drive_service.authenticate():
                        flash('تم حفظ بيانات الاعتماد وتفعيل Google Drive بنجاح! ✓', 'success')
                    else:
                        flash('تم حفظ البيانات لكن فشلت المصادقة. تحقق من صحة البيانات.', 'warning')
                else:
                    flash('ملف بيانات الاعتماد غير صحيح. تأكد من أنه Service Account JSON.', 'danger')
                    
            except json.JSONDecodeError:
                flash('خطأ في قراءة ملف JSON. تأكد من صحة التنسيق.', 'danger')
            except Exception as e:
                flash(f'حدث خطأ: {str(e)}', 'danger')
        else:
            flash('الرجاء رفع ملف JSON فقط', 'warning')
        
        return redirect(request.url)
    
    # GET request
    is_configured = drive_service.is_configured()
    
    return render_template(
        'settings/google_drive.html',
        is_configured=is_configured
    )
