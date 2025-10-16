import os
import logging
from datetime import datetime

from flask import Flask, session, redirect, url_for, render_template, request, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager, current_user, login_required
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate  # أضف هذا الاستيراد في الأعلى

# استيراد مكتبة dotenv لقراءة ملف .env
from dotenv import load_dotenv
load_dotenv()  # تحميل المتغيرات البيئية من ملف .env


# app.py
from whatsapp_client import WhatsAppWrapper
# ... استيراد مكتبات أخرى ...

# إنشاء كائن واتساب واحد عند بدء تشغيل التطبيق
# سيقوم الكلاس تلقائياً بقراءة المتغيرات من ملف .env
whatsapp_service = WhatsAppWrapper()

# ... بقية كود التطبيق الخاص بك ...


# في ملف manage.py أو app.py


# إعدادات اللغة العربية
ARABIC_CONFIG = {
    'language': 'Arabic',
    'delete_harakat': True,
    'delete_tatweel': False,
    'support_zwj': True,
    'support_ligatures': True
}

# استيراد مكتبة SQLAlchemy للتعامل مع MySQL
import pymysql
pymysql.install_as_MySQLdb()  # استخدام PyMySQL كبديل لـ MySQLdb

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Initialize Flask-Login
login_manager = LoginManager()




# Initialize CSRF Protection
csrf = CSRFProtect()

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "employee_management_secret")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# إعفاء بعض المسارات من حماية CSRF
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_CHECK_DEFAULT'] = False  # تعطيل التحقق التلقائي من CSRF

# Configure database connection with flexible support for different databases
database_url = os.environ.get("DATABASE_URL")



# If no DATABASE_URL is provided, use SQLite as fallback
if not database_url:
    # إنشاء مجلد database إذا لم يكن موجوداً
    os.makedirs('database', exist_ok=True)
    database_url = "sqlite:///database/nuzum.db"
    logger.info("Using SQLite database: database/nuzum.db")
else:
    logger.info(f"Using database: {database_url.split('@')[0]}@***")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url

# Configure engine options based on database type
if database_url.startswith("postgresql://") or database_url.startswith("postgres://"):
    # PostgreSQL optimized settings
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_timeout": 30,
        "pool_size": 10,
        "max_overflow": 5,
        "pool_reset_on_return": "rollback",
        "connect_args": {
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        }
    }
elif database_url.startswith("mysql://"):
    # MySQL optimized settings
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_timeout": 30,
        "pool_size": 5,
        "max_overflow": 3,
        "connect_args": {
            "connect_timeout": 10,
            "charset": "utf8mb4",
        }
    }
else:
    # SQLite settings (minimal connection pooling)
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_timeout": 20,
        "pool_recycle": -1,
        "pool_pre_ping": True,
        "connect_args": {
            "check_same_thread": False,
            "timeout": 20,
        }
    }
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# إعدادات لحجم الطلبات والملفات المرفوعة
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB - لدعم رفع عدد كبير من الصور
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Add execution options only for PostgreSQL/MySQL
if not database_url.startswith("sqlite"):
    if "execution_options" not in app.config["SQLALCHEMY_ENGINE_OPTIONS"]:
        app.config["SQLALCHEMY_ENGINE_OPTIONS"]["execution_options"] = {}
    app.config["SQLALCHEMY_ENGINE_OPTIONS"]["execution_options"]["isolation_level"] = "READ COMMITTED"

# Provide default values for uploads and other configurations
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB - لدعم رفع عدد كبير من الصور
app.config["UPLOAD_FOLDER"] = "uploads"

# Initialize SQLAlchemy with the app
db.init_app(app)

# Initialize Flask-Login
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'الرجاء تسجيل الدخول للوصول إلى هذه الصفحة'
login_manager.login_message_category = 'warning'

# التعامل بشكل مخصص مع المسارات المحمولة عند عدم تسجيل الدخول
@login_manager.unauthorized_handler
def unauthorized_handler():
    if request.path.startswith('/mobile'):
        # إعادة توجيه المستخدم إلى صفحة تسجيل الدخول المحمولة
        return redirect(url_for('mobile.login', next=request.path))
    # استخدام المسار الافتراضي لتسجيل الدخول
    return redirect(url_for('auth.login', next=request.path))

# Initialize CSRF Protection
csrf.init_app(app)

# ... بعد تعريف db = SQLAlchemy(app)
migrate = Migrate(app, db)

# إعداد Firebase
app.config['FIREBASE_API_KEY'] = os.environ.get('FIREBASE_API_KEY')
app.config['FIREBASE_PROJECT_ID'] = os.environ.get('FIREBASE_PROJECT_ID')
app.config['FIREBASE_APP_ID'] = os.environ.get('FIREBASE_APP_ID')

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# إضافة فلتر nl2br لتحويل السطور الجديدة إلى وسوم HTML <br>
from markupsafe import Markup

@app.template_filter('nl2br')
def nl2br_filter(s):
    if s:
        return Markup(s.replace('\n', '<br>'))
    return s

# إضافة فلتر لتنسيق التاريخ بشكل آمن
@app.template_filter('format_date')
def format_date_filter(date, format='%Y-%m-%d'):
    """
    فلتر آمن لتنسيق التواريخ مع التعامل مع القيم الفارغة

    :param date: كائن التاريخ (يمكن أن يكون None)
    :param format: صيغة التنسيق (افتراضياً YYYY-MM-DD)
    :return: التاريخ المنسق أو نص بديل
    """
    if date:
        return date.strftime(format)
    return ""

# إضافة فلتر لعرض التاريخ مع نص بديل
@app.template_filter('display_date')
def display_date_filter(date, format='%Y-%m-%d', default="غير محدد"):
    """
    عرض التاريخ بشكل منسق أو نص بديل إذا كان التاريخ فارغاً

    :param date: كائن التاريخ (يمكن أن يكون None)
    :param format: صيغة التنسيق (افتراضياً YYYY-MM-DD)
    :param default: النص البديل للعرض
    :return: التاريخ المنسق أو النص البديل
    """
    if date:
        return date.strftime(format)
    return default

# إضافة فلتر لحساب الأيام المتبقية من تاريخ معين
@app.template_filter('days_remaining')
def days_remaining_filter(date, from_date=None):
    """
    حساب عدد الأيام المتبقية من التاريخ المحدد حتى اليوم

    :param date: تاريخ الانتهاء (يمكن أن يكون None)
    :param from_date: تاريخ البداية (افتراضياً اليوم)
    :return: عدد الأيام المتبقية أو None إذا كان التاريخ غير محدد
    """
    if not date:
        return None

    if not from_date:
        from_date = datetime.now().date()
    elif hasattr(from_date, 'date'):
        from_date = from_date.date()

    if hasattr(date, 'date'):
        date = date.date()

    return (date - from_date).days

# Context processor to add variables to all templates
@app.context_processor
def inject_now():
    return {
        'now': datetime.now(),
        'firebase_api_key': app.config['FIREBASE_API_KEY'],
        'firebase_project_id': app.config['FIREBASE_PROJECT_ID'],
        'firebase_app_id': app.config['FIREBASE_APP_ID']
    }

# تصحيح مشكلة CSRF token في القوالب
@app.context_processor
def inject_csrf_token():
    """إضافة csrf_token إلى جميع القوالب"""
    def get_csrf_token():
        return csrf._get_csrf_token()

    return {'csrf_token': get_csrf_token}

# مسار الجذر الرئيسي للتطبيق مع توجيه تلقائي حسب نوع الجهاز
@app.route('/')
def root():
    from flask import request
    from models import Module, UserRole 

    user_agent = request.headers.get('User-Agent', '').lower()
    mobile_devices = ['android', 'iphone', 'ipad', 'mobile']

    # التحقق مما إذا كان الطلب يتضمن معلمة m=1 للوصول المباشر إلى نسخة الجوال
    mobile_param = request.args.get('m', '0')

    # إذا كان المستخدم يستخدم جهازاً محمولاً أو طلب نسخة الجوال صراحةً
    if any(device in user_agent for device in mobile_devices) or mobile_param == '1':
        if current_user.is_authenticated:
            return redirect(url_for('mobile.index'))
        else:
            return redirect(url_for('mobile.login'))

    # إذا كان المستخدم يستخدم جهاز كمبيوتر
    if current_user.is_authenticated:
        # التحقق من صلاحيات المستخدم للوصول إلى لوحة التحكم
        if current_user.role == UserRole.ADMIN or current_user.has_module_access(Module.DASHBOARD):
            return redirect(url_for('dashboard.index'))

        # توجيه المستخدم إلى أول وحدة مصرح له بالوصول إليها
        if current_user.has_module_access(Module.EMPLOYEES):
            return redirect(url_for('employees.index'))
        elif current_user.has_module_access(Module.DEPARTMENTS):
            return redirect(url_for('departments.index'))
        elif current_user.has_module_access(Module.ATTENDANCE):
            return redirect(url_for('attendance.index'))
        elif current_user.has_module_access(Module.SALARIES):
            return redirect(url_for('salaries.index'))
        elif current_user.has_module_access(Module.DOCUMENTS):
            return redirect(url_for('documents.index'))
        elif current_user.has_module_access(Module.VEHICLES):
            return redirect(url_for('vehicles.index'))
        elif current_user.has_module_access(Module.REPORTS):
            return redirect(url_for('reports.index'))
        elif current_user.has_module_access(Module.FEES):
            return redirect(url_for('fees_costs.index'))
        elif current_user.has_module_access(Module.USERS):
            return redirect(url_for('users.index'))
        else:
            # إذا لم يكن له أي صلاحية، عرض الصفحة المقيدة
            return render_template('restricted.html')
    else:
        return redirect(url_for('auth.login'))

# إضافة route مختصر للتوافق مع الروابط القديمة
@app.route('/login')
def login_redirect():
    """إعادة توجيه من /login إلى /auth/login للتوافق"""
    return redirect(url_for('auth.login'))

# معالج أخطاء الطلبات الكبيرة
@app.errorhandler(413)
def request_entity_too_large(error):
    """معالجة خطأ الطلب الكبير"""
    if request.endpoint and 'mobile' in request.endpoint:
        # للجوال: عرض رسالة خطأ مناسبة
        from flask import flash, redirect, url_for
        flash('حجم البيانات المرسلة كبير جداً. يرجى تقليل عدد الصور أو حجمها.', 'danger')
        return redirect(url_for('mobile.index'))
    else:
        # للويب: عرض صفحة خطأ
        return render_template('error.html', 
                             error_code=413,
                             error_message='حجم الطلب كبير جداً. يرجى تقليل حجم البيانات المرسلة.'), 413

# تعطيل استخدام WeasyPrint مؤقتاً
WEASYPRINT_ENABLED = False

# Register blueprints for different modules
with app.app_context():
    # Import models before creating tables
    import models  # noqa: F401
    import models_accounting  # noqa: F401

    # Import and register route blueprints
    from routes.dashboard import dashboard_bp
    from routes.employees import employees_bp
    from routes.departments import departments_bp
    from routes.attendance import attendance_bp
    from routes.salaries import salaries_bp
    from routes.documents import documents_bp
    from routes.reports import reports_bp
    from routes.auth import auth_bp
    from routes.vehicles import vehicles_bp
    from routes.fees_costs import fees_costs_bp
    from routes.api import api_bp
    from routes.enhanced_reports import enhanced_reports_bp
    from routes.mobile import mobile_bp
    from routes.users import users_bp
    from routes.mass_attendance import mass_attendance_bp
    from routes.attendance_dashboard import attendance_dashboard_bp


    # تعطيل تقارير الورشة مؤقتاً حتى يتم حل مشكلة WeasyPrint
    # from routes.workshop_reports import workshop_reports_bp

    from routes.employee_portal import employee_portal_bp
    from routes.insights import insights_bp
    from routes.external_safety import external_safety_bp
    from routes.mobile_devices import mobile_devices_bp
    from routes.operations import operations_bp
    from routes.sim_management import sim_management_bp
    from routes.device_management import device_management_bp
    from routes.device_assignment import device_assignment_bp
    from routes.accounting import accounting_bp
    from routes.accounting_extended import accounting_ext_bp
    from routes.analytics_simple import analytics_simple_bp
    from routes.vehicle_operations import vehicle_operations_bp
    from routes.integrated_simple import integrated_bp
    from routes.ai_services_simple import ai_services_bp
    from routes.email_queue import email_queue_bp
    from routes.voicehub import voicehub_bp
    from routes.properties import properties_bp

    # تعطيل حماية CSRF لطرق معينة
    csrf.exempt(voicehub_bp)
    csrf.exempt(auth_bp)

    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(employees_bp, url_prefix='/employees')
    app.register_blueprint(departments_bp, url_prefix='/departments')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(salaries_bp, url_prefix='/salaries')
    app.register_blueprint(documents_bp, url_prefix='/documents')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(vehicles_bp, url_prefix='/vehicles')
    app.register_blueprint(fees_costs_bp, url_prefix='/fees-costs')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(enhanced_reports_bp, url_prefix='/enhanced-reports')
    app.register_blueprint(mobile_bp, url_prefix='/mobile')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(mass_attendance_bp, url_prefix='/mass-attendance')
    app.register_blueprint(attendance_dashboard_bp, url_prefix='/attendance-dashboard')
    # app.register_blueprint(workshop_reports_bp, url_prefix='/workshop-reports')
    app.register_blueprint(employee_portal_bp, url_prefix='/employee-portal')
    app.register_blueprint(insights_bp, url_prefix='/insights')
    app.register_blueprint(external_safety_bp, url_prefix='/external-safety')
    app.register_blueprint(mobile_devices_bp, url_prefix='/mobile-devices')
    app.register_blueprint(operations_bp, url_prefix='/operations')
    app.register_blueprint(sim_management_bp, url_prefix='/sim-management')
    app.register_blueprint(device_management_bp, url_prefix='/device-management')
    app.register_blueprint(device_assignment_bp, url_prefix='/device-assignment')
    app.register_blueprint(vehicle_operations_bp, url_prefix='/vehicle-operations')
    app.register_blueprint(accounting_bp, url_prefix="/accounting")
    app.register_blueprint(accounting_ext_bp, url_prefix="/accounting")
    app.register_blueprint(analytics_simple_bp)
    app.register_blueprint(integrated_bp, url_prefix='/integrated')
    app.register_blueprint(voicehub_bp, url_prefix="/voicehub")
    app.register_blueprint(ai_services_bp, url_prefix='/ai')
    app.register_blueprint(email_queue_bp)
    app.register_blueprint(properties_bp, url_prefix='/properties')
    
    # استيراد وتسجيل مسار صفحة الهبوط - مسار منفصل عن النظام
    from routes.landing import landing_bp
    app.register_blueprint(landing_bp)
    
    # استيراد وتسجيل لوحة التحكم الإدارية
    from routes.admin_dashboard import admin_dashboard_bp
    app.register_blueprint(admin_dashboard_bp, url_prefix='/admin')
    
    # استيراد وتسجيل إدارة صفحة الهبوط
    from routes.landing_admin import landing_admin_bp
    app.register_blueprint(landing_admin_bp, url_prefix='/landing-admin')

    # إضافة route لخدمة الصور من مجلد uploads
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        from flask import send_from_directory
        from flask import send_from_directory, abort
        import os
        
        # البحث أولاً في uploads
        file_path = os.path.join("uploads", filename)
        if os.path.exists(file_path):
            dir_parts = filename.split("/")
            if len(dir_parts) > 1:
                subdir = "/".join(dir_parts[:-1])
                file_name = dir_parts[-1]
                return send_from_directory(f"uploads/{subdir}", file_name)
            else:
                return send_from_directory("uploads", filename)
        
        # البحث في static/uploads كنسخة احتياطية
        static_file_path = os.path.join("static", "uploads", filename)
        if os.path.exists(static_file_path):
            dir_parts = filename.split("/")
            if len(dir_parts) > 1:
                subdir = "/".join(dir_parts[:-1])
                file_name = dir_parts[-1]
                return send_from_directory(f"static/uploads/{subdir}", file_name)
            else:
                return send_from_directory("static/uploads", filename)
        
        # في حالة عدم وجود الصورة، إرجاع صورة بديلة
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            return send_from_directory('static/images', 'image-not-found.svg')
        
        abort(404)

    # مسار إضافي لخدمة صور static/uploads مع معالجة الأخطاء
    @app.route('/static/uploads/<path:filename>')
    def static_uploaded_file(filename):
        from flask import send_from_directory, abort
        import os
        
        # البحث في static/uploads
        file_path = os.path.join('static', 'uploads', filename)
        if os.path.exists(file_path):
            # استخراج اسم الملف والمجلد
            dir_parts = filename.split('/')
            if len(dir_parts) > 1:
                subdir = '/'.join(dir_parts[:-1])
                file_name = dir_parts[-1]
                return send_from_directory(f'static/uploads/{subdir}', file_name)
            else:
                return send_from_directory('static/uploads', filename)
        
        # في حالة عدم وجود الصورة، إرجاع صورة بديلة
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            return send_from_directory('static/images', 'image-not-found.svg')
        
        abort(404)

    # إضافة دوال مساعدة لقوالب Jinja
    from utils.user_helpers import get_role_display_name, get_module_display_name, format_permissions, check_module_access

    # إضافة مرشح bitwise_and لاستخدامه في قوالب Jinja2
    @app.template_filter('bitwise_and')
    def bitwise_and_filter(value1, value2):
        """تنفيذ عملية bitwise AND بين قيمتين"""
        return value1 & value2

    # إضافة مرشح للتحقق من صلاحيات المستخدم
    @app.template_filter('check_module_access')
    def check_module_access_filter(user, module, permission=None):
        """
        مرشح للتحقق من صلاحيات المستخدم للوصول إلى وحدة معينة

        :param user: كائن المستخدم
        :param module: الوحدة المطلوب التحقق منها
        :param permission: الصلاحية المطلوبة (اختياري)
        :return: True إذا كان المستخدم لديه الصلاحية، False غير ذلك
        """
        from models import Permission
        return check_module_access(user, module, permission or Permission.VIEW)

    @app.context_processor
    def inject_global_template_vars():
        from models import Module, UserRole, Permission
        return {
            'get_role_display_name': get_role_display_name,
            'get_module_display_name': get_module_display_name,
            'format_permissions': format_permissions,
            'Module': Module,
            'UserRole': UserRole,
            'Permission': Permission
        }

    # ملاحظة: تم دمج هذا الكود مع مسار الجذر الرئيسي

    # Create database tables if they don't exist
    logger.info("Creating database tables...")
    db.create_all()
    logger.info("Database tables created successfully.")

@app.before_request
def before_request():
    # تعيين اللغة الافتراضية للعربية
    g.language = 'ar'
    g.rtl = True
    g.arabic_config = ARABIC_CONFIG








# في ملف manage.py أو app.py

from models import User, UserRole # استيراد النماذج اللازمة
import click

@app.cli.command("make-all-admins")
def make_all_users_admins_command():
    """
    يقوم بتحويل دور كل المستخدمين المسجلين في النظام إلى مدير (ADMIN).
    """
    try:
        # 1. جلب كل المستخدمين من قاعدة البيانات
        users_to_update = User.query.all()

        if not users_to_update:
            print("لا يوجد مستخدمين في قاعدة البيانات لتحديثهم.")
            return

        count = 0
        # 2. المرور على كل مستخدم وتغيير دوره
        for user in users_to_update:
            if user.role != UserRole.ADMIN:
                user.role = UserRole.ADMIN
                count += 1

        # 3. حفظ كل التغييرات في قاعدة البيانات دفعة واحدة
        db.session.commit()

        print(f"نجاح! تم تحديث دور {count} مستخدم إلى 'admin'.")
        print(f"إجمالي عدد المستخدمين الآن: {len(users_to_update)}.")

    except Exception as e:
        db.session.rollback()
        print(f"حدث خطأ أثناء تحديث الأدوار: {e}")
        print("تم التراجع عن كل التغييرات.")
    """
    يقوم بتحويل دور كل المستخدمين المسجلين في النظام إلى مدير (ADMIN).
    """
    try:
        # 1. جلب كل المستخدمين من قاعدة البيانات
        users_to_update = User.query.all()

        if not users_to_update:
            print("لا يوجد مستخدمين في قاعدة البيانات لتحديثهم.")
            return

        count = 0
        # 2. المرور على كل مستخدم وتغيير دوره
        for user in users_to_update:
            if user.role != UserRole.ADMIN:
                user.role = UserRole.ADMIN
                count += 1

        # 3. حفظ كل التغييرات في قاعدة البيانات دفعة واحدة
        db.session.commit()

        print(f"نجاح! تم تحديث دور {count} مستخدم إلى 'admin'.")
        print(f"إجمالي عدد المستخدمين الآن: {len(users_to_update)}.")

    except Exception as e:
        db.session.rollback()
        print(f"حدث خطأ أثناء تحديث الأدوار: {e}")
        print("تم التراجع عن كل التغييرات.")

