from flask import Blueprint, render_template
from models import Employee, Vehicle, Department, User, Salary

landing_bp = Blueprint('landing', __name__)

@landing_bp.route('/nuzum')
def index():
    """صفحة هبوط نظام نُظم - عرض المواصفات والإمكانيات"""
    
    # تحميل إعدادات صفحة الهبوط
    import os
    import json
    
    def load_landing_settings():
        settings_file = 'landing_settings.json'
        default_settings = {
            'hero_title': 'نُظم - نظام إدارة الموظفين والمركبات',
            'hero_subtitle': 'حل شامل ومتكامل لإدارة العمليات الداخلية للشركات والمؤسسات',
            'hero_primary_btn': 'جرب النظام مجاناً',
            'hero_secondary_btn': 'تعرف على المزايا',
            'company_info': {
                'name': 'نُظم للتقنية',
                'description': 'شركة رائدة في تطوير حلول إدارة الموارد البشرية والمركبات',
                'year': 2020,
                'location': 'الرياض، المملكة العربية السعودية'
            },
            'stats': {
                'companies': 5,
                'employees': 8,
                'vehicles': 3,
                'satisfaction': 9
            }
        }
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    return settings
        except Exception as e:
            print(f"خطأ في تحميل إعدادات صفحة الهبوط: {e}")
        
        return default_settings
    
    # تحميل الإعدادات المحفوظة
    settings = load_landing_settings()
    
    # إحصائيات النظام - استخدام الأرقام المحفوظة فقط (لا تأثير على قاعدة البيانات)
    stats = settings.get('stats', {
        'companies': 5,
        'employees': 8,
        'vehicles': 3,
        'satisfaction': 9
    })
    
    # ميزات النظام
    features = [
        {
            'title': 'إدارة الموظفين',
            'description': 'نظام شامل لإدارة بيانات الموظفين مع تتبع المستندات وانتهاء الصلاحيات',
            'icon': 'fas fa-users',
            'image': '/static/images/employee-management.svg',
            'capabilities': [
                'إضافة وتعديل بيانات الموظفين الشخصية والوظيفية',
                'إدارة المستندات مع تنبيهات انتهاء الصلاحية',
                'رفع صور الهوية والملف الشخصي',
                'استيراد وتصدير البيانات من/إلى Excel',
                'نظام بحث متقدم وفلترة',
                'تتبع تاريخ التوظيف والعقود'
            ]
        },
        {
            'title': 'إدارة المركبات',
            'description': 'نظام متكامل لإدارة أسطول المركبات وتتبع العمليات',
            'icon': 'fas fa-car',
            'image': '/static/images/vehicle-management.svg',
            'capabilities': [
                'تسجيل وإدارة بيانات المركبات',
                'نظام تسليم واستقبال المركبات',
                'تتبع مستندات المركبة (رخصة، تأمين، استمارة)',
                'إدارة ورش الصيانة والإصلاحات',
                'فحوصات السلامة الخارجية مع الصور',
                'تقارير تفصيلية للمركبات والعمليات'
            ]
        },
        {
            'title': 'نظام الحضور والانصراف',
            'description': 'تتبع دقيق لحضور الموظفين مع حساب الإضافي والخصم',
            'icon': 'fas fa-clock',
            'image': '/static/images/attendance-system.svg',
            'capabilities': [
                'تسجيل الحضور والانصراف اليومي',
                'حساب ساعات العمل الإضافية',
                'تقارير شهرية وأسبوعية مفصلة',
                'دعم التقويم الهجري والميلادي',
                'تتبع الغياب والإجازات',
                'إحصائيات متقدمة للأداء'
            ]
        },
        {
            'title': 'إدارة الرواتب',
            'description': 'نظام محاسبي متكامل لحساب ومعالجة رواتب الموظفين',
            'icon': 'fas fa-money-bill-wave',
            'image': '/static/images/salary-management.svg',
            'capabilities': [
                'حساب الراتب الأساسي والبدلات',
                'إدارة الخصومات والاستقطاعات',
                'معالجة دفعية للرواتب',
                'تقارير شهرية مفصلة',
                'تصدير كشوف الرواتب PDF',
                'تتبع تاريخ الدفع والمستحقات'
            ]
        },
        {
            'title': 'إدارة الأقسام',
            'description': 'تنظيم هيكلي للإدارات والأقسام المختلفة',
            'icon': 'fas fa-sitemap',
            'capabilities': [
                'إنشاء وإدارة الأقسام والإدارات',
                'تحديد المديرين والمسؤولين',
                'ربط الموظفين بالأقسام',
                'هيكل تنظيمي واضح',
                'تقارير على مستوى القسم',
                'إحصائيات الأداء الإداري'
            ]
        },
        {
            'title': 'إدارة المستخدمين والصلاحيات',
            'description': 'نظام أمان متقدم لإدارة المستخدمين والصلاحيات',
            'icon': 'fas fa-shield-alt',
            'capabilities': [
                'إنشاء حسابات مستخدمين متعددة',
                'نظام أدوار وصلاحيات مرن',
                'تسجيل نشاط المستخدمين',
                'تشفير كلمات المرور',
                'جلسات آمنة ومحمية',
                'تدقيق العمليات والتغييرات'
            ]
        },
        {
            'title': 'التقارير والإحصائيات',
            'description': 'تقارير شاملة ومرئيات بيانية للمساعدة في اتخاذ القرارات',
            'icon': 'fas fa-chart-bar',
            'capabilities': [
                'تقارير PDF احترافية',
                'تصدير Excel للبيانات',
                'رسوم بيانية تفاعلية',
                'تقارير مخصصة حسب الفترة',
                'إحصائيات الأداء الشاملة',
                'تحليل البيانات المتقدم'
            ]
        },
        {
            'title': 'إدارة الأجهزة المحمولة',
            'description': 'تتبع وإدارة الأجهزة المحمولة المخصصة للموظفين',
            'icon': 'fas fa-mobile-alt',
            'capabilities': [
                'تسجيل تفاصيل الأجهزة والـ IMEI',
                'ربط الأجهزة بالموظفين',
                'تتبع حالة الجهاز والصيانة',
                'إدارة أرقام الهواتف',
                'تقارير استخدام الأجهزة',
                'نظام بحث متقدم للأجهزة'
            ]
        }
    ]
    
    # المزايا التنافسية
    advantages = [
        {
            'title': 'واجهة عربية كاملة',
            'description': 'تصميم يدعم الكتابة من اليمين لليسار مع خطوط عربية واضحة',
            'icon': 'fas fa-language'
        },
        {
            'title': 'نظام أمان متقدم',
            'description': 'حماية البيانات بأعلى معايير الأمان مع تشفير المعلومات الحساسة',
            'icon': 'fas fa-lock'
        },
        {
            'title': 'تقارير احترافية',
            'description': 'تقارير PDF وExcel بتصميم احترافي يدعم الخطوط العربية',
            'icon': 'fas fa-file-pdf'
        },
        {
            'title': 'سهولة الاستخدام',
            'description': 'واجهة بديهية وسهلة التعلم لجميع مستويات المستخدمين',
            'icon': 'fas fa-mouse-pointer'
        },
        {
            'title': 'مرونة في التخصيص',
            'description': 'إمكانية تخصيص النظام حسب احتياجات كل مؤسسة',
            'icon': 'fas fa-cogs'
        },
        {
            'title': 'دعم فني مستمر',
            'description': 'فريق دعم فني متخصص لضمان استمرارية العمل',
            'icon': 'fas fa-headset'
        }
    ]
    
    return render_template('landing/index.html', 
                         stats=stats,
                         features=features, 
                         advantages=advantages,
                         settings=settings)

@landing_bp.route('/nuzum/features')
def features():
    """صفحة تفصيلية للميزات"""
    return render_template('landing/features.html')

@landing_bp.route('/nuzum/pricing') 
def pricing():
    """صفحة الأسعار والباقات"""
    return render_template('landing/pricing.html')

@landing_bp.route('/nuzum/contact')
def contact():
    """صفحة التواصل"""
    return render_template('landing/contact.html')

@landing_bp.route('/nuzum/about')
def about():
    """صفحة من نحن"""
    return render_template('landing/about.html')

@landing_bp.route('/nuzum/support')
def support():
    """صفحة الدعم"""
    return render_template('landing/support.html')

@landing_bp.route('/nuzum/help')
def help():
    """صفحة المساعدة"""
    return render_template('landing/help.html')

@landing_bp.route('/nuzum/guide')
def guide():
    """صفحة الدليل"""
    return render_template('landing/guide.html')

@landing_bp.route('/nuzum/company')
def company():
    """صفحة الشركة"""
    return render_template('landing/company.html')

@landing_bp.route('/nuzum/news')
def news():
    """صفحة الأخبار"""
    return render_template('landing/news.html')

@landing_bp.route('/nuzum/jobs')
def jobs():
    """صفحة الوظائف"""
    return render_template('landing/jobs.html')

@landing_bp.route('/nuzum/privacy')
def privacy():
    """صفحة سياسة الخصوصية"""
    return render_template('landing/privacy.html')

@landing_bp.route('/nuzum/terms')
def terms():
    """صفحة شروط الاستخدام"""
    return render_template('landing/terms.html')

@landing_bp.route('/nuzum/cookies')
def cookies():
    """صفحة ملفات تعريف الارتباط"""
    return render_template('landing/cookies.html')

@landing_bp.route('/about')
def about_old():
    """صفحة من نحن"""
    return render_template('landing/about.html')

@landing_bp.route('/privacy')
def privacy_old():
    """صفحة سياسة الخصوصية (قديمة)"""
    return render_template('landing/privacy.html')

@landing_bp.route('/contact')
def contact_page():
    """صفحة اتصل بنا"""
    return render_template('contact.html')

@landing_bp.route('/nuzum/demo')
def demo():
    """صفحة عرض توضيحي"""
    return render_template('landing/demo.html')

@landing_bp.route('/nuzum/login', methods=['GET', 'POST'])
def login():
    """صفحة تسجيل دخول خاصة بالتسويق"""
    from flask_login import login_user, current_user
    from werkzeug.security import check_password_hash
    from models import User
    from datetime import datetime
    from flask import flash, redirect, url_for, request, render_template
    
    # إذا كان المستخدم مسجل دخوله بالفعل، وجهه لصفحة العرض التوضيحي
    if current_user.is_authenticated:
        return redirect(url_for('landing_admin.demo_dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        
        if not email or not password:
            flash('يرجى إدخال البريد الإلكتروني وكلمة المرور', 'error')
            return render_template('landing/login.html')
        
        # البحث عن المستخدم
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            # تسجيل الدخول بنجاح
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            
            from core.database import db
            db.session.commit()
            
            flash('مرحباً بك! تم تسجيل الدخول بنجاح', 'success')
            
            # التوجيه للعرض التوضيحي أو النظام حسب الطلب
            next_page = request.args.get('next')
            if next_page and 'landing-admin' in next_page:
                return redirect(next_page)
            
            # التوجيه الافتراضي للعرض التوضيحي للتسويق
            return redirect(url_for('landing_admin.demo_dashboard'))
        else:
            flash('بيانات الدخول غير صحيحة. جرب بيانات التجربة المعروضة', 'error')
    
    return render_template('landing/login.html')

# روتات العروض التوضيحية المدمجة (iframe)
@landing_bp.route('/nuzum/demo-iframe/<demo_type>')
def demo_iframe(demo_type):
    """عرض iframe للنظام الحقيقي"""
    
    # تحديد الصفحة المطلوبة حسب النوع
    demo_routes = {
        'employees': '/dashboard/employees',
        'vehicles': '/dashboard/vehicles', 
        'attendance': '/dashboard/attendance',
        'reports': '/dashboard/reports'
    }
    
    target_route = demo_routes.get(demo_type, '/dashboard')
    
    return render_template('landing/demo_iframe.html', 
                         demo_type=demo_type,
                         target_route=target_route)