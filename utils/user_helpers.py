import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

from app import db
from flask import abort, flash, g
from models import Module, Permission, User, UserPermission, UserRole, Employee
from utils.audit_helpers import log_create, log_update, log_delete

# إعداد التسجيل
logger = logging.getLogger(__name__)

# تعريف الصلاحيات الافتراضية حسب الدور
DEFAULT_PERMISSIONS = {
    UserRole.ADMIN: {
        Module.EMPLOYEES: Permission.ADMIN,
        Module.DEPARTMENTS: Permission.ADMIN,
        Module.ATTENDANCE: Permission.ADMIN,
        Module.SALARIES: Permission.ADMIN,
        Module.DOCUMENTS: Permission.ADMIN,
        Module.VEHICLES: Permission.ADMIN,
        Module.USERS: Permission.ADMIN,
        Module.REPORTS: Permission.ADMIN,
        Module.FEES: Permission.ADMIN
    },
    UserRole.MANAGER: {
        Module.EMPLOYEES: Permission.MANAGE,
        Module.DEPARTMENTS: Permission.MANAGE,
        Module.ATTENDANCE: Permission.MANAGE,
        Module.SALARIES: Permission.MANAGE,
        Module.DOCUMENTS: Permission.MANAGE,
        Module.VEHICLES: Permission.MANAGE,
        Module.REPORTS: Permission.MANAGE,
        Module.FEES: Permission.MANAGE
    },
    UserRole.HR: {
        Module.EMPLOYEES: Permission.MANAGE,
        Module.DEPARTMENTS: Permission.MANAGE,
        Module.ATTENDANCE: Permission.MANAGE,
        Module.DOCUMENTS: Permission.MANAGE,
        Module.REPORTS: Permission.VIEW
    },
    UserRole.FINANCE: {
        Module.EMPLOYEES: Permission.VIEW,
        Module.SALARIES: Permission.MANAGE,
        Module.FEES: Permission.MANAGE,
        Module.REPORTS: Permission.VIEW
    },
    UserRole.FLEET: {
        Module.VEHICLES: Permission.MANAGE,
        Module.REPORTS: Permission.VIEW
    },
    UserRole.USER: {
        Module.EMPLOYEES: Permission.VIEW,
        Module.DEPARTMENTS: Permission.VIEW,
        Module.REPORTS: Permission.VIEW
    }
}

# تعريف أسماء عرض الأدوار
ROLE_DISPLAY_NAMES = {
    UserRole.ADMIN: 'مدير النظام',
    UserRole.MANAGER: 'مدير',
    UserRole.HR: 'موارد بشرية',
    UserRole.FINANCE: 'مالية',
    UserRole.FLEET: 'أسطول',
    UserRole.USER: 'مستخدم عادي'
}

# تعريف أسماء عرض الوحدات
MODULE_DISPLAY_NAMES = {
    Module.EMPLOYEES: 'الموظفين',
    Module.DEPARTMENTS: 'الأقسام',
    Module.ATTENDANCE: 'الحضور والغياب',
    Module.SALARIES: 'الرواتب',
    Module.DOCUMENTS: 'المستندات',
    Module.VEHICLES: 'المركبات',
    Module.USERS: 'المستخدمين',
    Module.REPORTS: 'التقارير',
    Module.FEES: 'الرسوم والتكاليف'
}

# تعريف أسماء عرض الصلاحيات
PERMISSION_DISPLAY_NAMES = {
    Permission.VIEW: 'عرض',
    Permission.CREATE: 'إنشاء',
    Permission.EDIT: 'تعديل',
    Permission.DELETE: 'حذف',
    Permission.MANAGE: 'إدارة',
    Permission.ADMIN: 'إدارة كاملة'
}

def get_role_display_name(role: UserRole) -> str:
    """
    الحصول على الاسم المعروض للدور
    
    :param role: دور المستخدم
    :return: الاسم المعروض للدور
    """
    if not role:
        return 'غير محدد'
        
    return ROLE_DISPLAY_NAMES.get(role, str(role.value))

def get_module_display_name(module: Module) -> str:
    """
    الحصول على الاسم المعروض للوحدة
    
    :param module: الوحدة
    :return: الاسم المعروض للوحدة
    """
    if not module:
        return 'غير محدد'
        
    return MODULE_DISPLAY_NAMES.get(module, str(module.value))

def format_permissions(permissions_bit: int) -> List[str]:
    """
    تحويل بتات الصلاحيات إلى قائمة بالصلاحيات المقروءة
    
    :param permissions_bit: بتات الصلاحيات
    :return: قائمة بأسماء الصلاحيات
    """
    result = []
    
    # التحقق من الصلاحيات الفردية
    if permissions_bit & Permission.VIEW:
        result.append(PERMISSION_DISPLAY_NAMES[Permission.VIEW])
    
    if permissions_bit & Permission.CREATE:
        result.append(PERMISSION_DISPLAY_NAMES[Permission.CREATE])
    
    if permissions_bit & Permission.EDIT:
        result.append(PERMISSION_DISPLAY_NAMES[Permission.EDIT])
    
    if permissions_bit & Permission.DELETE:
        result.append(PERMISSION_DISPLAY_NAMES[Permission.DELETE])
    
    # التحقق من الصلاحيات المركبة
    if permissions_bit & Permission.MANAGE:
        result.append(PERMISSION_DISPLAY_NAMES[Permission.MANAGE])
    
    if permissions_bit == Permission.ADMIN:
        # استبدال كل الصلاحيات بصلاحية "إدارة كاملة"
        return [PERMISSION_DISPLAY_NAMES[Permission.ADMIN]]
    
    return result

def create_user(
    name: str,
    email: str,
    role: Union[UserRole, str],
    password: Optional[str] = None,
    is_active: bool = True,
    employee_id: Optional[int] = None,
    firebase_uid: Optional[str] = None,
    profile_picture: Optional[str] = None,
    auth_type: str = 'local',
    auto_create_permissions: bool = True
) -> User:
    """
    إنشاء مستخدم جديد
    
    :param name: اسم المستخدم
    :param email: البريد الإلكتروني
    :param role: دور المستخدم
    :param password: كلمة المرور (اختيارية إذا كان auth_type هو 'firebase')
    :param is_active: هل المستخدم نشط
    :param employee_id: معرف الموظف المرتبط (اختياري)
    :param firebase_uid: معرف Firebase (اختياري)
    :param profile_picture: رابط صورة الملف الشخصي (اختياري)
    :param auth_type: نوع المصادقة ('local' أو 'firebase')
    :param auto_create_permissions: هل يتم إنشاء الصلاحيات تلقائيًا حسب الدور
    :return: كائن المستخدم الجديد
    """
    # تحويل النص إلى تعداد إذا لزم الأمر
    if isinstance(role, str):
        try:
            role = UserRole(role)
        except ValueError:
            role = UserRole.USER  # استخدام القيمة الافتراضية في حالة وجود خطأ
    
    # إنشاء كائن المستخدم
    user = User(
        name=name,
        email=email,
        role=role,
        is_active=is_active,
        employee_id=employee_id if employee_id and employee_id != -1 else None,
        firebase_uid=firebase_uid,
        profile_picture=profile_picture,
        auth_type=auth_type,
        created_at=datetime.utcnow()
    )
    
    # تعيين كلمة المرور إذا تم توفيرها وكان نوع المصادقة محلي
    if password and auth_type == 'local':
        user.set_password(password)
    
    # حفظ المستخدم في قاعدة البيانات
    db.session.add(user)
    db.session.commit()
    
    # إنشاء الصلاحيات التلقائية إذا تم طلب ذلك
    if auto_create_permissions and role != UserRole.ADMIN:  # لا داعي لإنشاء صلاحيات للمدير
        create_default_permissions(user)
    
    # تسجيل العملية
    log_create('user', user)
    
    return user

def update_user(
    user_id: int,
    name: Optional[str] = None,
    email: Optional[str] = None,
    role: Optional[Union[UserRole, str]] = None,
    password: Optional[str] = None,
    is_active: Optional[bool] = None,
    employee_id: Optional[int] = None,
    profile_picture: Optional[str] = None,
    update_permissions: bool = False
) -> User:
    """
    تحديث معلومات مستخدم
    
    :param user_id: معرف المستخدم
    :param name: اسم المستخدم (اختياري)
    :param email: البريد الإلكتروني (اختياري)
    :param role: دور المستخدم (اختياري)
    :param password: كلمة المرور الجديدة (اختيارية)
    :param is_active: هل المستخدم نشط (اختياري)
    :param employee_id: معرف الموظف المرتبط (اختياري)
    :param profile_picture: رابط صورة الملف الشخصي (اختياري)
    :param update_permissions: هل يتم تحديث الصلاحيات آليًا عند تغيير الدور
    :return: كائن المستخدم بعد التحديث
    """
    # البحث عن المستخدم
    user = User.query.get(user_id)
    if not user:
        raise ValueError(f"لم يتم العثور على المستخدم بالمعرف {user_id}")
    
    # حفظ البيانات القديمة للتسجيل
    old_data = {
        'name': user.name,
        'email': user.email,
        'role': user.role.value if user.role else None,
        'is_active': user.is_active,
        'employee_id': user.employee_id
    }
    
    # تحديث البيانات إذا تم توفيرها
    if name is not None:
        user.name = name
    
    if email is not None and email != user.email:
        user.email = email
    
    if role is not None:
        # تحويل النص إلى تعداد إذا لزم الأمر
        if isinstance(role, str):
            try:
                role = UserRole(role)
            except ValueError:
                role = user.role  # الاحتفاظ بالدور الحالي في حالة وجود خطأ
        
        old_role = user.role
        user.role = role
        
        # تحديث الصلاحيات إذا تم تغيير الدور وطُلب التحديث
        if update_permissions and old_role != role:
            # حذف الصلاحيات الحالية
            UserPermission.query.filter_by(user_id=user.id).delete()
            db.session.commit()
            
            # إنشاء صلاحيات جديدة إذا لم يكن المستخدم مديرًا
            if role != UserRole.ADMIN:
                create_default_permissions(user)
    
    if password:
        user.set_password(password)
    
    if is_active is not None:
        user.is_active = is_active
    
    if employee_id is not None:
        if employee_id == -1:
            user.employee_id = None
        else:
            user.employee_id = employee_id
    
    if profile_picture is not None:
        user.profile_picture = profile_picture
    
    # حفظ التغييرات
    db.session.commit()
    
    # تسجيل العملية
    log_update('user', user, old_data)
    
    return user

def delete_user(user_id: int) -> bool:
    """
    حذف مستخدم
    
    :param user_id: معرف المستخدم
    :return: هل تم الحذف بنجاح
    """
    # البحث عن المستخدم
    user = User.query.get(user_id)
    if not user:
        raise ValueError(f"لم يتم العثور على المستخدم بالمعرف {user_id}")
    
    # لا يمكن حذف المستخدم الحالي
    if hasattr(g, 'user') and g.user and g.user.id == user_id:
        raise ValueError("لا يمكن حذف المستخدم الحالي")
    
    # تسجيل العملية قبل الحذف
    log_delete('user', user)
    
    # حذف المستخدم
    db.session.delete(user)
    db.session.commit()
    
    return True

def create_default_permissions(user: User) -> List[UserPermission]:
    """
    إنشاء الصلاحيات الافتراضية للمستخدم بناءً على دوره
    
    :param user: كائن المستخدم
    :return: قائمة بكائنات الصلاحيات المنشأة
    """
    permissions = []
    
    # الحصول على الصلاحيات الافتراضية للدور
    role_permissions = DEFAULT_PERMISSIONS.get(user.role, {})
    
    # إنشاء كائن صلاحية لكل وحدة
    for module, permission_bit in role_permissions.items():
        user_permission = UserPermission(
            user_id=user.id,
            module=module,
            permissions=permission_bit
        )
        permissions.append(user_permission)
        db.session.add(user_permission)
    
    db.session.commit()
    return permissions

def update_user_permissions(user_id: int, permissions_data: Dict[str, int]) -> List[UserPermission]:
    """
    تحديث صلاحيات المستخدم
    
    :param user_id: معرف المستخدم
    :param permissions_data: بيانات الصلاحيات (معرف الوحدة: بتات الصلاحيات)
    :return: قائمة بكائنات الصلاحيات المحدثة
    """
    # البحث عن المستخدم
    user = User.query.get(user_id)
    if not user:
        raise ValueError(f"لم يتم العثور على المستخدم بالمعرف {user_id}")
    
    # المدير لديه كل الصلاحيات دائمًا
    if user.role == UserRole.ADMIN:
        raise ValueError("لا يمكن تعديل صلاحيات مدير النظام")
    
    # حذف الصلاحيات الحالية
    UserPermission.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    
    permissions = []
    
    # إنشاء صلاحيات جديدة
    for module_name, permission_bit in permissions_data.items():
        try:
            module = Module(module_name)
            user_permission = UserPermission(
                user_id=user.id,
                module=module,
                permissions=permission_bit
            )
            permissions.append(user_permission)
            db.session.add(user_permission)
        except ValueError:
            # تجاهل الوحدات غير الصالحة
            continue
    
    db.session.commit()
    
    # تسجيل العملية
    log_update('user_permissions', user, {'user_id': user.id})
    
    return permissions

def get_available_employees() -> List[Tuple[int, str]]:
    """
    الحصول على قائمة بالموظفين المتاحين للربط بمستخدمين
    
    :return: قائمة بمعرفات وأسماء الموظفين
    """
    employees = Employee.query.all()
    
    # ترتيب الموظفين حسب الاسم
    employees.sort(key=lambda emp: emp.name)
    
    return [(emp.id, f"{emp.name} ({emp.employee_id})") for emp in employees]

def check_module_access(user: User, module: Module, permission: int = Permission.VIEW) -> bool:
    """
    التحقق مما إذا كان المستخدم لديه صلاحية معينة على وحدة معينة
    
    :param user: كائن المستخدم
    :param module: الوحدة المطلوب التحقق منها
    :param permission: الصلاحية المطلوبة (القيمة الافتراضية هي العرض)
    :return: هل المستخدم لديه الصلاحية
    """
    # التحقق من أن المستخدم نشط
    if not user.is_active:
        return False
    
    # المدير لديه كل الصلاحيات
    if user.role == UserRole.ADMIN:
        return True
    
    # البحث عن صلاحيات الوحدة
    for user_permission in user.permissions:
        if user_permission.module == module:
            return bool(user_permission.permissions & permission)
    
    return False

def require_module_access(module: Module, permission: int = Permission.VIEW):
    """
    زخرفة للتحقق من صلاحية الوصول إلى وحدة معينة
    (Legacy wrapper - يستخدم النظام المركزي الجديد)
    
    :param module: الوحدة المطلوب التحقق منها
    :param permission: الصلاحية المطلوبة (القيمة الافتراضية هي العرض)
    """
    from utils.permissions_service import require_permission
    return require_permission(module, permission, return_json=False)