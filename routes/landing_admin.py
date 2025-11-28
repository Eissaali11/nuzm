from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session, current_app as app
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import check_password_hash
from datetime import datetime
from models import db, User, UserRole
import json
import os
import time

landing_admin_bp = Blueprint('landing_admin', __name__, url_prefix='/landing-admin')

def admin_required(f):
    """ديكوريتر للتحقق من صلاحيات المدير"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            flash('ليس لديك صلاحية للوصول لهذه الصفحة', 'error')
            return redirect(url_for('landing_admin.admin_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@landing_admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """صفحة تسجيل دخول المدير لإعدادات صفحة الهبوط"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        print(f"DEBUG: محاولة تسجيل دخول - المستخدم: '{username}', كلمة المرور: '{password[:3]}***'")
        
        if not username or not password:
            flash('يرجى إدخال اسم المستخدم وكلمة المرور', 'error')
            return render_template('landing_admin/login.html')
        
        # البحث عن المستخدم المدير
        user = User.query.filter_by(username=username).first()
        
        print(f"DEBUG: المستخدم الموجود: {user.username if user else 'لا يوجد'}")
        print(f"DEBUG: دور المستخدم: {user.role if user else 'لا يوجد'}")
        print(f"DEBUG: نشط: {user.is_active if user else 'لا يوجد'}")
        
        if user and user.role == UserRole.ADMIN and user.is_active:
            if check_password_hash(user.password_hash, password):
                print("DEBUG: كلمة المرور صحيحة - تسجيل الدخول")
                login_user(user)
                
                # التوجه إلى الصفحة المطلوبة أو لوحة التحكم
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('landing_admin.dashboard'))
            else:
                print("DEBUG: كلمة المرور خاطئة")
                flash('كلمة المرور غير صحيحة', 'error')
        else:
            print("DEBUG: المستخدم غير موجود أو ليس مديراً أو غير نشط")
            flash('اسم المستخدم غير صحيح أو ليس لديك صلاحيات إدارية', 'error')
    
    return render_template('landing_admin/login.html')

@landing_admin_bp.route('/logout')
def admin_logout():
    """تسجيل خروج المدير"""
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('landing_admin.admin_login'))

@landing_admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """الصفحة الرئيسية لإدارة صفحة الهبوط"""
    
    # قراءة إعدادات صفحة الهبوط
    landing_settings = load_landing_settings()
    
    # إحصائيات أساسية
    stats = {
        'total_sections': 5,  # الأقسام: الرئيسية، الميزات، الأسعار، التواصل، العرض
        'active_features': len(landing_settings.get('features', [])),
        'testimonials_count': len(landing_settings.get('testimonials', [])),
        'contact_methods': len(landing_settings.get('contact_info', {})),
    }
    
    return render_template('landing_admin/dashboard.html', 
                         settings=landing_settings,
                         stats=stats)

@landing_admin_bp.route('/demo-dashboard')
def demo_dashboard():
    """عرض توضيحي للوحة التحكم بدون حماية - للعرض التوضيحي فقط"""
    # إشعار المستخدم أن هذا عرض توضيحي فقط
    flash('هذا عرض توضيحي فقط. للوصول للنظام الرئيسي، يرجى تسجيل الدخول من الرابط أدناه.', 'info')
    
    # قراءة إعدادات صفحة الهبوط
    landing_settings = load_landing_settings()
    
    # إحصائيات أساسية للعرض التوضيحي
    stats = {
        'total_sections': 5,
        'active_features': len(landing_settings.get('features', [])),
        'testimonials_count': len(landing_settings.get('testimonials', [])),
        'contact_methods': len(landing_settings.get('contact_info', {})),
        'is_demo': True  # تمييز أن هذا عرض توضيحي
    }
    
    return render_template('landing_admin/demo_dashboard.html', 
                         settings=landing_settings,
                         stats=stats)

@landing_admin_bp.route('/content')
@login_required
@admin_required
def content_management():
    """إدارة محتوى صفحة الهبوط"""
    settings = load_landing_settings()
    return render_template('landing_admin/content.html', settings=settings)

@landing_admin_bp.route('/features')
@login_required
@admin_required
def features_management():
    """إدارة ميزات النظام"""
    settings = load_landing_settings()
    return render_template('landing_admin/features.html', settings=settings)

# API endpoints for features management
@landing_admin_bp.route('/api/features', methods=['POST'])
@login_required
@admin_required
def add_feature():
    """إضافة ميزة جديدة"""
    try:
        settings = load_landing_settings()
        
        new_feature = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'category': request.form.get('category', 'إدارة'),
            'order': int(request.form.get('order', 1)),
            'active': request.form.get('active') == 'true',
            'icon_type': request.form.get('icon_type', 'icon')
        }
        
        if new_feature['icon_type'] == 'icon':
            new_feature['icon'] = request.form.get('icon')
        else:
            # رفع الصورة
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file.filename != '':
                    # حفظ الصورة في مجلد uploads
                    import os
                    from werkzeug.utils import secure_filename
                    
                    filename = secure_filename(image_file.filename)
                    timestamp = str(int(time.time()))
                    filename = f"feature_{timestamp}_{filename}"
                    
                    upload_path = os.path.join('static', 'uploads', 'features')
                    os.makedirs(upload_path, exist_ok=True)
                    
                    file_path = os.path.join(upload_path, filename)
                    image_file.save(file_path)
                    
                    new_feature['image'] = f"/static/uploads/features/{filename}"
        
        if 'features' not in settings:
            settings['features'] = []
        
        settings['features'].append(new_feature)
        
        # ترتيب الميزات حسب order
        settings['features'].sort(key=lambda x: x.get('order', 1))
        
        save_landing_settings(settings)
        
        return jsonify({'success': True})
        
    except Exception as e:
        app.logger.error(f"Error adding feature: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@landing_admin_bp.route('/api/features/<int:index>', methods=['GET'])
@login_required
@admin_required
def get_feature(index):
    """جلب ميزة محددة"""
    settings = load_landing_settings()
    features = settings.get('features', [])
    
    if 0 <= index < len(features):
        return jsonify(features[index])
    
    return jsonify({'error': 'Feature not found'}), 404

@landing_admin_bp.route('/api/features/<int:index>', methods=['PUT'])
@login_required
@admin_required
def update_feature(index):
    """تحديث ميزة"""
    try:
        settings = load_landing_settings()
        features = settings.get('features', [])
        
        if 0 <= index < len(features):
            existing_feature = features[index].copy()
            
            # تحديث البيانات الأساسية
            features[index].update({
                'title': request.form.get('title'),
                'description': request.form.get('description'),
                'category': request.form.get('category', 'إدارة'),
                'order': int(request.form.get('order', 1)),
                'active': request.form.get('active') == 'true',
                'icon_type': request.form.get('icon_type', 'icon')
            })
            
            if features[index]['icon_type'] == 'icon':
                features[index]['icon'] = request.form.get('icon')
                # إزالة الصورة إذا كانت موجودة
                if 'image' in features[index]:
                    del features[index]['image']
            else:
                # رفع صورة جديدة إذا تم اختيارها
                if 'image' in request.files and request.files['image'].filename != '':
                    image_file = request.files['image']
                    
                    import os
                    from werkzeug.utils import secure_filename
                    
                    filename = secure_filename(image_file.filename)
                    timestamp = str(int(time.time()))
                    filename = f"feature_{timestamp}_{filename}"
                    
                    upload_path = os.path.join('static', 'uploads', 'features')
                    os.makedirs(upload_path, exist_ok=True)
                    
                    file_path = os.path.join(upload_path, filename)
                    image_file.save(file_path)
                    
                    # 💾 لا حذف للصور القديمة - الاحتفاظ بجميع النسخ للأمان
                    features[index]['image'] = f"/static/uploads/features/{filename}"
                
                # إزالة الأيقونة إذا كانت موجودة
                if 'icon' in features[index]:
                    del features[index]['icon']
            
            # ترتيب الميزات حسب order
            settings['features'].sort(key=lambda x: x.get('order', 1))
            
            save_landing_settings(settings)
            return jsonify({'success': True})
        
        return jsonify({'error': 'Feature not found'}), 404
        
    except Exception as e:
        app.logger.error(f"Error updating feature: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@landing_admin_bp.route('/api/features/<int:index>', methods=['DELETE'])
@login_required
@admin_required
def delete_feature(index):
    """حذف ميزة"""
    settings = load_landing_settings()
    features = settings.get('features', [])
    
    if 0 <= index < len(features):
        features.pop(index)
        save_landing_settings(settings)
        return jsonify({'success': True})
    
    return jsonify({'error': 'Feature not found'}), 404

@landing_admin_bp.route('/testimonials')
@login_required
@admin_required
def testimonials_management():
    """إدارة آراء العملاء"""
    settings = load_landing_settings()
    return render_template('landing_admin/testimonials.html', settings=settings)

@landing_admin_bp.route('/pricing')
@login_required
@admin_required
def pricing_management():
    """إدارة خطط الأسعار"""
    settings = load_landing_settings()
    return render_template('landing_admin/pricing.html', settings=settings)

@landing_admin_bp.route('/contact-info')
@login_required
@admin_required
def contact_management():
    """إدارة معلومات التواصل"""
    settings = load_landing_settings()
    return render_template('landing_admin/contact.html', settings=settings)

# API Endpoints

@landing_admin_bp.route('/api/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def api_settings():
    """API لقراءة وحفظ الإعدادات"""
    if request.method == 'GET':
        return jsonify(load_landing_settings())
    
    if request.method == 'POST':
        try:
            new_settings = request.get_json()
            save_landing_settings(new_settings)
            return jsonify({'success': True, 'message': 'تم حفظ الإعدادات بنجاح'})
        except Exception as e:
            return jsonify({'success': False, 'message': 'حدث خطأ في حفظ الإعدادات'}), 500

@landing_admin_bp.route('/api/feature', methods=['POST', 'PUT', 'DELETE'])
@login_required
@admin_required
def api_feature():
    """API لإدارة الميزات"""
    settings = load_landing_settings()
    
    if request.method == 'POST':
        feature = request.get_json()
        if 'features' not in settings:
            settings['features'] = []
        feature['id'] = len(settings['features']) + 1
        settings['features'].append(feature)
        save_landing_settings(settings)
        return jsonify({'success': True, 'message': 'تم إضافة الميزة بنجاح'})
    
    elif request.method == 'PUT':
        feature_id = request.args.get('id', type=int)
        feature_data = request.get_json()
        
        for i, feature in enumerate(settings.get('features', [])):
            if feature.get('id') == feature_id:
                settings['features'][i] = {**feature, **feature_data}
                save_landing_settings(settings)
                return jsonify({'success': True, 'message': 'تم تحديث الميزة بنجاح'})
        
        return jsonify({'success': False, 'message': 'الميزة غير موجودة'}), 404
    
    elif request.method == 'DELETE':
        feature_id = request.args.get('id', type=int)
        settings['features'] = [f for f in settings.get('features', []) if f.get('id') != feature_id]
        save_landing_settings(settings)
        return jsonify({'success': True, 'message': 'تم حذف الميزة بنجاح'})

@landing_admin_bp.route('/api/testimonial', methods=['POST', 'PUT', 'DELETE'])
@login_required
@admin_required
def api_testimonial():
    """API لإدارة آراء العملاء"""
    settings = load_landing_settings()
    
    if request.method == 'POST':
        testimonial = request.get_json()
        if 'testimonials' not in settings:
            settings['testimonials'] = []
        testimonial['id'] = len(settings['testimonials']) + 1
        testimonial['date'] = datetime.now().isoformat()
        settings['testimonials'].append(testimonial)
        save_landing_settings(settings)
        return jsonify({'success': True, 'message': 'تم إضافة الرأي بنجاح'})
    
    elif request.method == 'PUT':
        testimonial_id = request.args.get('id', type=int)
        testimonial_data = request.get_json()
        
        for i, testimonial in enumerate(settings.get('testimonials', [])):
            if testimonial.get('id') == testimonial_id:
                settings['testimonials'][i] = {**testimonial, **testimonial_data}
                save_landing_settings(settings)
                return jsonify({'success': True, 'message': 'تم تحديث الرأي بنجاح'})
        
        return jsonify({'success': False, 'message': 'الرأي غير موجود'}), 404
    
    elif request.method == 'DELETE':
        testimonial_id = request.args.get('id', type=int)
        settings['testimonials'] = [t for t in settings.get('testimonials', []) if t.get('id') != testimonial_id]
        save_landing_settings(settings)
        return jsonify({'success': True, 'message': 'تم حذف الرأي بنجاح'})

@landing_admin_bp.route('/api/pricing-plan', methods=['POST', 'PUT', 'DELETE'])
@login_required
@admin_required
def api_pricing_plan():
    """API لإدارة خطط الأسعار"""
    settings = load_landing_settings()
    
    if request.method == 'POST':
        plan = request.get_json()
        if 'pricing_plans' not in settings:
            settings['pricing_plans'] = []
        plan['id'] = len(settings['pricing_plans']) + 1
        settings['pricing_plans'].append(plan)
        save_landing_settings(settings)
        return jsonify({'success': True, 'message': 'تم إضافة الخطة بنجاح'})
    
    elif request.method == 'PUT':
        plan_id = request.args.get('id', type=int)
        plan_data = request.get_json()
        
        for i, plan in enumerate(settings.get('pricing_plans', [])):
            if plan.get('id') == plan_id:
                settings['pricing_plans'][i] = {**plan, **plan_data}
                save_landing_settings(settings)
                return jsonify({'success': True, 'message': 'تم تحديث الخطة بنجاح'})
        
        return jsonify({'success': False, 'message': 'الخطة غير موجودة'}), 404
    
    elif request.method == 'DELETE':
        plan_id = request.args.get('id', type=int)
        settings['pricing_plans'] = [p for p in settings.get('pricing_plans', []) if p.get('id') != plan_id]
        save_landing_settings(settings)
        return jsonify({'success': True, 'message': 'تم حذف الخطة بنجاح'})

def load_landing_settings():
    """تحميل إعدادات صفحة الهبوط"""
    settings_file = 'landing_settings.json'
    
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    
    # الإعدادات الافتراضية
    return {
        'site_title': 'نُظم - نظام إدارة الموظفين والمركبات',
        'hero_title': 'إدارة ذكية لمؤسستك',
        'hero_subtitle': 'نظام شامل لإدارة الموظفين والمركبات مع واجهة عربية متطورة',
        'company_info': {
            'name': 'نُظم',
            'description': 'نظام إدارة المؤسسات الرائد في المملكة العربية السعودية',
            'founded': '2024',
            'employees': '500+'
        },
        'contact_info': {
            'phone': '+966 11 123 4567',
            'email': 'info@nuzum.sa',
            'address': 'الرياض، المملكة العربية السعودية',
            'working_hours': 'الأحد - الخميس: 8:00 ص - 6:00 م'
        },
        'features': [
            {
                'id': 1,
                'title': 'إدارة الموظفين',
                'description': 'نظام شامل لإدارة بيانات الموظفين ومستنداتهم',
                'icon': 'fas fa-users',
                'color': 'primary'
            },
            {
                'id': 2,
                'title': 'إدارة المركبات',
                'description': 'تتبع وإدارة أسطول المركبات بكفاءة عالية',
                'icon': 'fas fa-car',
                'color': 'success'
            },
            {
                'id': 3,
                'title': 'التقارير المتقدمة',
                'description': 'تقارير احترافية وتحليلات ذكية',
                'icon': 'fas fa-chart-bar',
                'color': 'info'
            }
        ],
        'testimonials': [
            {
                'id': 1,
                'name': 'أحمد محمد',
                'position': 'مدير الموارد البشرية',
                'company': 'شركة التقنية المتطورة',
                'content': 'نُظم غيّر طريقة عملنا بالكامل. وفرنا أكثر من 20 ساعة أسبوعياً',
                'rating': 5
            }
        ],
        'stats': {
            'companies': 500,
            'employees': 50000,
            'vehicles': 10000,
            'satisfaction': 99
        }
    }

def save_landing_settings(settings):
    """حفظ إعدادات صفحة الهبوط"""
    settings_file = 'landing_settings.json'
    try:
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

# مسارات API لحفظ المحتوى
@landing_admin_bp.route('/api/save-hero', methods=['POST'])
@login_required
@admin_required
def api_save_hero():
    """حفظ إعدادات القسم الرئيسي"""
    try:
        data = request.get_json()
        settings = load_landing_settings()
        
        # تحديث إعدادات القسم الرئيسي
        settings['hero_title'] = data.get('hero_title', settings.get('hero_title'))
        settings['hero_subtitle'] = data.get('hero_subtitle', settings.get('hero_subtitle'))
        settings['hero_primary_btn'] = data.get('hero_primary_btn', settings.get('hero_primary_btn'))
        settings['hero_secondary_btn'] = data.get('hero_secondary_btn', settings.get('hero_secondary_btn'))
        
        if save_landing_settings(settings):
            return jsonify({'success': True, 'message': 'تم حفظ القسم الرئيسي بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'حدث خطأ في الحفظ'})
    
    except Exception as e:
        print(f"خطأ في حفظ القسم الرئيسي: {e}")
        return jsonify({'success': False, 'message': 'حدث خطأ في معالجة البيانات'})

@landing_admin_bp.route('/api/save-stats', methods=['POST'])
@login_required
@admin_required
def api_save_stats():
    """حفظ إعدادات الإحصائيات"""
    try:
        data = request.get_json()
        settings = load_landing_settings()
        
        # تحديث الإحصائيات
        settings['stats']['companies'] = int(data.get('stats_companies', settings['stats']['companies']))
        settings['stats']['employees'] = int(data.get('stats_employees', settings['stats']['employees']))
        settings['stats']['vehicles'] = int(data.get('stats_vehicles', settings['stats']['vehicles']))
        settings['stats']['satisfaction'] = int(data.get('stats_satisfaction', settings['stats']['satisfaction']))
        
        if save_landing_settings(settings):
            return jsonify({'success': True, 'message': 'تم حفظ الإحصائيات بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'حدث خطأ في الحفظ'})
    
    except Exception as e:
        print(f"خطأ في حفظ الإحصائيات: {e}")
        return jsonify({'success': False, 'message': 'حدث خطأ في معالجة البيانات'})

@landing_admin_bp.route('/api/save-company', methods=['POST'])
@login_required
@admin_required
def api_save_company():
    """حفظ معلومات الشركة"""
    try:
        data = request.get_json()
        settings = load_landing_settings()
        
        # تحديث معلومات الشركة
        if 'company_info' not in settings:
            settings['company_info'] = {}
        
        settings['company_info']['name'] = data.get('company_name', settings['company_info'].get('name', ''))
        settings['company_info']['description'] = data.get('company_description', settings['company_info'].get('description', ''))
        settings['company_info']['year'] = int(data.get('company_year', settings['company_info'].get('year', 2020)))
        settings['company_info']['location'] = data.get('company_location', settings['company_info'].get('location', ''))
        
        if save_landing_settings(settings):
            return jsonify({'success': True, 'message': 'تم حفظ معلومات الشركة بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'حدث خطأ في الحفظ'})
    
    except Exception as e:
        print(f"خطأ في حفظ معلومات الشركة: {e}")
        return jsonify({'success': False, 'message': 'حدث خطأ في معالجة البيانات'})