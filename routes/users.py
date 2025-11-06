from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from models import User, Department, UserRole, Module, Permission, AuditLog, UserPermission
from functools import wraps
from sqlalchemy.orm import joinedload # <<<<<--- أضف هذا السطر

users_bp = Blueprint('users', __name__, url_prefix='/users')

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('attendance.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# @users_bp.route('/')
# @login_required
# @admin_required
# def index():
#     """قائمة المستخدمين"""
#     users = User.query.all()
#     departments = Department.query.all()
#     return render_template('users/index.html', users=users, departments=departments)
# # في ملف routes/users.py
# from sqlalchemy.orm import joinedload
# # تأكد من استيراد النماذج (User, Department) ومكتبة SQLAlchemy (db)

@users_bp.route('/')
@login_required
@admin_required
def index():
    """
    يعرض قائمة المستخدمين مع تحسين أداء جلب بيانات الأقسام المرتبطة.
    """
    try:
        # 1. جلب كل الأقسام مرة واحدة (هذا يبقى كما هو)
        # سيتم استخدامها في كل النوافذ المنبثقة
        all_departments = Department.query.order_by(Department.name).all()
        
        # 2. جلب المستخدمين مع فلترة حسب القسم المحدد للمستخدم الحالي
        user_query = User.query.options(
            joinedload(User.departments)
        )
        
        # فلترة المستخدمين حسب القسم المحدد للمستخدم الحالي
        if current_user.assigned_department_id:
            # إذا كان المستخدم مرتبط بقسم محدد، عرض المستخدمين المرتبطين بنفس القسم فقط
            user_query = user_query.filter(User.assigned_department_id == current_user.assigned_department_id)
        
        all_users = user_query.order_by(User.name).all()
        
    except Exception as e:
        flash('حدث خطأ أثناء جلب البيانات من قاعدة البيانات.', 'danger')
        print(f"Error fetching user list: {e}")
        all_users = []
        all_departments = []

    # 3. عرض القالب وتمرير البيانات إليه
    return render_template(
        'users/index.html',
        users=all_users,
        departments=all_departments
        # لا حاجة لتمرير current_user، فهو متاح عالمياً في القوالب بفضل Flask-Login
    )


# في ملف routes/users.py

# قم بتغيير مسار واسم الدالة ليعكس الوظيفة الجديدة
@users_bp.route('/assign_departments/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def assign_departments(user_id):
    """تحديد عدة أقسام للمستخدم."""
    user = User.query.get_or_404(user_id)
    
    # 1. استلام قائمة بكل معرفات الأقسام المحددة من النموذج
    # request.form.getlist() هي الطريقة الصحيحة للتعامل مع عدة مربعات اختيار بنفس الاسم
    selected_dept_ids = request.form.getlist('department_ids')
    
    # تحويل قائمة السلاسل النصية إلى قائمة أرقام صحيحة
    selected_dept_ids = [int(id) for id in selected_dept_ids]
    
    try:
        # 2. جلب كائنات الأقسام الفعلية من قاعدة البيانات بناءً على المعرفات
        selected_departments = Department.query.filter(Department.id.in_(selected_dept_ids)).all()
        
        # 3. تحديث قائمة أقسام المستخدم
        # هذه هي الطريقة الأبسط في SQLAlchemy لتحديث علاقة متعدد إلى متعدد
        user.departments = selected_departments

        
        db.session.commit()
        
        if selected_departments:
            flash(f'تم تحديث أقسام المستخدم {user.name} بنجاح.', 'success')
        else:
            flash(f'تم إزالة كل الأقسام من المستخدم {user.name}.', 'info')
            
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تحديث الأقسام: {e}', 'danger')

    return redirect(url_for('users.index'))
@users_bp.route('/assign_department/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def assign_department(user_id):
    """تحديد قسم للمستخدم"""
    user = User.query.get_or_404(user_id)
    department_id = request.form.get('department_id')
    
    if department_id and department_id != '':
        department_id = int(department_id)
        department = Department.query.get(department_id)
        if not department:
            flash('القسم غير موجود', 'error')
            return redirect(url_for('users.index'))
        
        user.assigned_department_id = department_id
        flash(f'تم تحديد قسم "{department.name}" للمستخدم {user.name}', 'success')
    else:
        user.assigned_department_id = None
        flash(f'تم إلغاء تحديد القسم للمستخدم {user.name}', 'info')
    
    db.session.commit()
    return redirect(url_for('users.index'))

@users_bp.route('/edit_role/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def edit_role(user_id):
    """تحديث دور المستخدم"""
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    
    if new_role in [role.value for role in UserRole]:
        user.role = UserRole(new_role)
        db.session.commit()
        flash(f'تم تحديث دور المستخدم {user.name} إلى {new_role}', 'success')
    else:
        flash('الدور المحدد غير صالح', 'error')
    
    return redirect(url_for('users.index'))

@users_bp.route('/permissions/<int:user_id>')
@login_required
@admin_required
def user_permissions(user_id):
    """إدارة صلاحيات المستخدم التفصيلية"""
    user = User.query.get_or_404(user_id)
    modules = list(Module)
    return render_template('users/permissions.html', user=user, modules=modules)

@users_bp.route('/toggle_active/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_active(user_id):
    """تفعيل/إلغاء تفعيل المستخدم"""
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    status = "تفعيل" if user.is_active else "إلغاء تفعيل"
    flash(f'تم {status} المستخدم {user.name}', 'success')
    return redirect(url_for('users.index'))

@users_bp.route('/department_users/<int:department_id>')
@login_required
@admin_required
def department_users(department_id):
    """عرض جميع المستخدمين المخصصين لقسم معين"""
    department = Department.query.get_or_404(department_id)
    users = User.query.filter_by(assigned_department_id=department_id).all()
    return jsonify({
        'department': department.name,
        'users': [{'id': u.id, 'name': u.name, 'email': u.email, 'role': u.role.value} for u in users]
    })

@users_bp.route('/view/<int:id>')
@login_required
@admin_required
def view(id):
    """عرض تفاصيل مستخدم"""
    user = User.query.get_or_404(id)
    
    # جلب آخر 10 أنشطة للمستخدم
    recent_activities = AuditLog.query.filter_by(user_id=id).order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    return render_template('users/view.html', user=user, recent_activities=recent_activities)

@users_bp.route('/activity_logs')
@login_required
@admin_required
def activity_logs():
    """عرض قائمة المستخدمين لاختيار سجل النشاط"""
    users = User.query.all()
    return render_template('users/activity_logs.html', users=users)

@users_bp.route('/activity_log/<int:id>')
@login_required
@admin_required
def activity_log(id):
    """عرض سجل النشاط الكامل للمستخدم من جميع مصادر السجلات"""
    from models import SystemAudit
    from datetime import datetime
    user = User.query.get_or_404(id)
    
    # معاملات التصفية
    action_filter = request.args.get('action', '')
    entity_filter = request.args.get('entity_type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # جلب النشاط من كلا الجدولين بشكل منفصل ثم دمجهما
    activities_list = []
    
    # جلب من AuditLog
    audit_query = AuditLog.query.filter_by(user_id=id)
    if action_filter:
        audit_query = audit_query.filter(AuditLog.action == action_filter)
    if entity_filter:
        audit_query = audit_query.filter(AuditLog.entity_type == entity_filter)
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            audit_query = audit_query.filter(AuditLog.timestamp >= date_from_obj)
        except ValueError:
            pass
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            audit_query = audit_query.filter(AuditLog.timestamp <= date_to_obj)
        except ValueError:
            pass
    
    audit_logs = audit_query.all()
    for log in audit_logs:
        activities_list.append({
            'id': log.id,
            'action': log.action,
            'entity_type': log.entity_type,
            'entity_id': log.entity_id,
            'details': log.details,
            'timestamp': log.timestamp,
            'source': 'AuditLog'
        })
    
    # جلب من SystemAudit
    system_query = SystemAudit.query.filter_by(user_id=id)
    if action_filter:
        system_query = system_query.filter(SystemAudit.action == action_filter)
    if entity_filter:
        system_query = system_query.filter(SystemAudit.entity_type == entity_filter)
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            system_query = system_query.filter(SystemAudit.timestamp >= date_from_obj)
        except ValueError:
            pass
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            system_query = system_query.filter(SystemAudit.timestamp <= date_to_obj)
        except ValueError:
            pass
    
    system_logs = system_query.all()
    for log in system_logs:
        activities_list.append({
            'id': log.id,
            'action': log.action,
            'entity_type': log.entity_type,
            'entity_id': log.entity_id,
            'details': log.details,
            'timestamp': log.timestamp,
            'source': 'SystemAudit'
        })
    
    # ترتيب النتائج حسب التاريخ
    activities_list.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # حساب معلومات التصفح
    total_count = len(activities_list)
    start = (page - 1) * per_page
    end = start + per_page
    activities_page = activities_list[start:end]
    
    has_prev = page > 1
    has_next = end < total_count
    prev_num = page - 1 if has_prev else None
    next_num = page + 1 if has_next else None
    
    # إنشاء كائن pagination
    class PaginationObj:
        def __init__(self, items, page, per_page, total, has_prev, has_next, prev_num, next_num):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.has_prev = has_prev
            self.has_next = has_next
            self.prev_num = prev_num
            self.next_num = next_num
            self.pages = (total + per_page - 1) // per_page
    
    activities = PaginationObj(activities_page, page, per_page, total_count, has_prev, has_next, prev_num, next_num)
    
    print(f"إجمالي سجلات النشاط للمستخدم {id}: {total_count}")
    print(f"عدد السجلات في الصفحة الحالية: {len(activities_page)}")
    
    # جلب قائمة الإجراءات والكيانات الفريدة للفلتر
    audit_actions = db.session.query(AuditLog.action).filter_by(user_id=id).distinct().all()
    system_actions = db.session.query(SystemAudit.action).filter_by(user_id=id).distinct().all()
    all_actions = list(set([a[0] for a in audit_actions] + [a[0] for a in system_actions]))
    
    audit_entities = db.session.query(AuditLog.entity_type).filter_by(user_id=id).distinct().all()
    system_entities = db.session.query(SystemAudit.entity_type).filter_by(user_id=id).distinct().all()
    all_entities = list(set([e[0] for e in audit_entities] + [e[0] for e in system_entities]))
    
    return render_template('users/activity_log.html', 
                         user=user, 
                         activities=activities,
                         actions=sorted(all_actions),
                         entity_types=sorted(all_entities),
                         current_filters={
                             'action': action_filter,
                             'entity_type': entity_filter,
                             'date_from': date_from,
                             'date_to': date_to
                         })

@users_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add():
    """إضافة مستخدم جديد"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role', 'user')
            department_id = request.form.get('department_id')
            
            # التحقق من البيانات المطلوبة
            if not name or not email or not password:
                flash('جميع الحقول مطلوبة', 'error')
                return redirect(url_for('users.add'))
            
            # التحقق من عدم وجود مستخدم بنفس البريد الإلكتروني
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('يوجد مستخدم آخر بنفس البريد الإلكتروني', 'error')
                return redirect(url_for('users.add'))
            
            # إنشاء المستخدم الجديد
            new_user = User(
                name=name,
                email=email,
                role=UserRole(role),
                is_active=True
            )
            new_user.set_password(password)
            
            # تحديد القسم إذا تم اختياره
            if department_id and department_id != '':
                new_user.assigned_department_id = int(department_id)
            
            db.session.add(new_user)
            db.session.commit()
            
            flash(f'تم إضافة المستخدم {name} بنجاح', 'success')
            return redirect(url_for('users.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'error')
    
    departments = Department.query.all()
    return render_template('users/add.html', departments=departments)



@users_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(user_id):
    """تعديل بيانات المستخدم وأقسامه المخصصة."""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            # 1. تحديث البيانات الأساسية للمستخدم
            user.name = request.form.get('name')
            new_email = request.form.get('email')
            password = request.form.get('password')
            role_str = request.form.get('role')

            if not user.name or not new_email:
                flash('الاسم والبريد الإلكتروني حقول مطلوبة.', 'danger')
                return redirect(url_for('users.edit', user_id=user_id))

            # التحقق من أن البريد الإلكتروني الجديد غير مستخدم
            if new_email != user.email:
                existing_user = User.query.filter_by(email=new_email).first()
                if existing_user:
                    flash('هذا البريد الإلكتروني مستخدم بالفعل.', 'danger')
                    return redirect(url_for('users.edit', user_id=user_id))
            user.email = new_email
            
            # تحديث الدور
            if role_str:
                user.role = UserRole(role_str)
            
            # تحديث كلمة المرور (إذا تم إدخالها)
            if password:
                user.set_password(password)
                
            # 2. *** الجزء الجديد: تحديث الأقسام ***
            # استلام قائمة معرفات الأقسام المحددة
            selected_dept_ids = request.form.getlist('department_ids')
            # تحويلها إلى قائمة أرقام صحيحة
            selected_dept_ids = [int(id) for id in selected_dept_ids]

            # جلب كائنات الأقسام من قاعدة البيانات
            selected_departments = Department.query.filter(Department.id.in_(selected_dept_ids)).all()
            
            # تعيين القائمة الجديدة للمستخدم، وSQLAlchemy سيتولى الباقي
            user.departments = selected_departments
            
            # 3. حفظ كل التغييرات
            db.session.commit()
            
            flash(f'تم تحديث بيانات المستخدم {user.name} بنجاح.', 'success')
            return redirect(url_for('users.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء التحديث: {str(e)}', 'danger')

    # في حالة GET request، نحتاج لكل الأقسام لعرضها في النموذج
    departments = Department.query.order_by(Department.name).all()
    return render_template('users/edit.html', user=user, departments=departments)



# @users_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
# @login_required
# @admin_required
# def edit(user_id):
#     """تعديل مستخدم"""
#     user = User.query.get_or_404(user_id)
    
#     if request.method == 'POST':
#         try:
#             user.name = request.form.get('name')
#             email = request.form.get('email')
#             role = request.form.get('role')
#             department_id = request.form.get('department_id')
#             password = request.form.get('password')
            
#             # التحقق من البيانات المطلوبة
#             if not user.name or not email:
#                 flash('الاسم والبريد الإلكتروني مطلوبان', 'error')
#                 return redirect(url_for('users.edit', user_id=user_id))
            
#             # التحقق من عدم وجود مستخدم آخر بنفس البريد الإلكتروني
#             existing_user = User.query.filter_by(email=email).filter(User.id != user_id).first()
#             if existing_user:
#                 flash('يوجد مستخدم آخر بنفس البريد الإلكتروني', 'error')
#                 return redirect(url_for('users.edit', user_id=user_id))
            
#             user.email = email
#             user.role = UserRole(role)
            
#             # تحديد القسم
#             if department_id and department_id != '':
#                 user.assigned_department_id = int(department_id)
#             else:
#                 user.assigned_department_id = None
            
#             # تحديث كلمة المرور إذا تم إدخالها
#             if password:
#                 user.set_password(password)
            
#             db.session.commit()
#             flash(f'تم تحديث بيانات المستخدم {user.name} بنجاح', 'success')
#             return redirect(url_for('users.index'))
            
#         except Exception as e:
#             db.session.rollback()
#             flash(f'حدث خطأ: {str(e)}', 'error')
    
#     departments = Department.query.all()
#     return render_template('users/edit.html', user=user, departments=departments)

@users_bp.route('/confirm_delete/<int:user_id>')
@login_required
@admin_required
def confirm_delete(user_id):
    """صفحة تأكيد حذف المستخدم"""
    user = User.query.get_or_404(user_id)
    
    # منع المستخدم من حذف نفسه
    if user.id == current_user.id:
        flash('لا يمكنك حذف حسابك الخاص', 'error')
        return redirect(url_for('users.index'))
    
    return render_template('users/confirm_delete.html', user=user)

@users_bp.route('/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete(user_id):
    """حذف مستخدم"""
    user = User.query.get_or_404(user_id)
    
    # منع المستخدم من حذف نفسه
    if user.id == current_user.id:
        flash('لا يمكنك حذف حسابك الخاص', 'error')
        return redirect(url_for('users.index'))
    
    try:
        user_name = user.name
        
        # حذف الإشعارات المرتبطة بهذا المستخدم أولاً
        from models import OperationNotification
        OperationNotification.query.filter_by(user_id=user_id).delete()
        
        # حذف المستخدم من قاعدة البيانات
        db.session.delete(user)
        db.session.commit()
        
        flash(f'تم حذف المستخدم {user_name} بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف المستخدم: {str(e)}', 'error')
    
    return redirect(url_for('users.index'))


# في ملف routes/users.py (أو ما شابه)

@users_bp.route('/<int:user_id>/permissions', methods=['POST'])
@login_required
@admin_required
def update_permissions(user_id):
    """
    تحديث صلاحيات مستخدم معين.
    """
    # 1. جلب المستخدم المطلوب أو إرجاع خطأ 404
    user_to_update = User.query.get_or_404(user_id)

    # لا يمكن تعديل صلاحيات مدير آخر أو صلاحيات نفسك
    if user_to_update.role == UserRole.ADMIN or user_to_update.id == current_user.id:
        flash('لا يمكن تعديل صلاحيات هذا المستخدم.', 'danger')
        return redirect(url_for('users.index'))

    try:
        # 2. استلام قائمة الصلاحيات المحددة من النموذج
        # request.form.getlist('permissions') هي الطريقة الصحيحة لقراءة كل قيم checkbox بنفس الـ name
        submitted_permissions = request.form.getlist('permissions')

        # 3. *** الجزء الحاسم: تجميع الصلاحيات ***
        # سنستخدم قاموساً لتجميع الصلاحيات لكل وحدة
        # المفتاح: اسم الوحدة (Module), القيمة: مجموع قيم الصلاحيات (Integer)
        # مثال: {'EMPLOYEES': 5, 'VEHICLES': 3}
        new_permissions_map = {}

        for perm_string in submitted_permissions:
            # مثال على perm_string: "EMPLOYEES_4"
            try:
                module_name_str, permission_value_str = perm_string.rsplit('_', 1)
                permission_value = int(permission_value_str)
                
                # تحويل اسم الوحدة من سلسلة نصية إلى كائن Enum
                module_enum = Module[module_name_str]

                # التجميع: إذا كانت الوحدة موجودة في القاموس، أضف القيمة الجديدة. وإلا، أنشئها.
                current_value = new_permissions_map.get(module_enum, 0)
                new_permissions_map[module_enum] = current_value | permission_value # استخدام OR बिटواي لتجميع الصلاحيات
            
            except (ValueError, KeyError):
                # تجاهل أي قيمة غير صالحة تم إرسالها
                continue

        # 4. حذف كل الصلاحيات القديمة للمستخدم
        # هذا هو الأسلوب الأنظف. نحذف القديم ونضيف الجديد.
        UserPermission.query.filter_by(user_id=user_to_update.id).delete()

        # 5. إضافة الصلاحيات الجديدة المجمعة
        for module, aggregated_permissions in new_permissions_map.items():
            new_permission_record = UserPermission(
                user_id=user_to_update.id,
                module=module,
                permissions=aggregated_permissions
            )
            db.session.add(new_permission_record)

        # 6. حفظ كل التغييرات في قاعدة البيانات
        db.session.commit()
        
        flash(f'تم تحديث صلاحيات المستخدم {user_to_update.name} بنجاح.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء تحديث الصلاحيات: {e}', 'danger')

    return redirect(url_for('users.user_permissions', user_id=user_id))






# @users_bp.route('/update_permissions/<int:user_id>', methods=['POST'])
# @login_required
# @admin_required
# def update_permissions(user_id):
#     id = user_id
#     """تحديث صلاحيات المستخدم التفصيلية"""
#     user = User.query.get_or_404(id)
    
#     # منع تعديل صلاحيات المديرين
#     if user.role == UserRole.ADMIN:
#         flash('لا يمكن تعديل صلاحيات المديرين', 'error')
#         return redirect(url_for('users.user_permissions', user_id=user_id))
    
#     try:
#         # جلب الصلاحيات المحددة
#         selected_permissions = request.form.getlist('permissions')
        
#         # حذف جميع صلاحيات المستخدم الحالية
#         UserPermission.query.filter_by(user_id=user_id).delete()
        
#         # إضافة الصلاحيات الجديدة
#         for permission_str in selected_permissions:
#             module_name, permission_value = permission_str.split('_')
#             module = Module[module_name]
#             permission_value = int(permission_value)
            
#             new_permission = UserPermission(
#                 user_id=user_id,
#                 module=module,
#                 permissions=permission_value
#             )
#             db.session.add(new_permission)
        
#         db.session.commit()
        
#         # تسجيل العملية في سجل النشاط
#         audit_log = AuditLog(
#             user_id=current_user.id,
#             action='تحديث الصلاحيات',
#             entity_type='مستخدم',
#             entity_id=user_id,
#             details=f'تم تحديث صلاحيات المستخدم {user.name}'
#         )
#         db.session.add(audit_log)
#         db.session.commit()
        
#         flash(f'تم تحديث صلاحيات المستخدم {user.name} بنجاح', 'success')
        
#     except Exception as e:
#         db.session.rollback()
#         flash(f'حدث خطأ أثناء تحديث الصلاحيات: {str(e)}', 'error')
    
#     return redirect(url_for('users.user_permissions', user_id=user_id))