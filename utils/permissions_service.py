"""
نظام الصلاحيات المركزي
====================
يوفر خدمات التحقق من الصلاحيات مع caching على مستوى request
"""

from functools import wraps
from flask import g, abort, jsonify, request, flash, redirect, url_for
from flask_login import current_user
import logging

from models import Module, Permission, UserRole

logger = logging.getLogger(__name__)


# ========================================
# Permission Caching (Request-scoped)
# ========================================

def get_user_permissions():
    """
    الحصول على صلاحيات المستخدم الحالي مع caching على مستوى request
    Returns: dict {Module: permissions_value}
    """
    # التحقق من الـ cache في g
    if hasattr(g, '_user_permissions_cache'):
        return g._user_permissions_cache
    
    if not current_user.is_authenticated:
        g._user_permissions_cache = {}
        return g._user_permissions_cache
    
    # المديرون لديهم كل الصلاحيات
    if current_user.role == UserRole.ADMIN:
        # إعطاء صلاحيات كاملة لجميع الأقسام
        g._user_permissions_cache = {
            module: Permission.ADMIN 
            for module in Module
        }
        return g._user_permissions_cache
    
    # جلب صلاحيات المستخدم من قاعدة البيانات
    permissions_dict = {}
    for user_perm in current_user.permissions:
        permissions_dict[user_perm.module] = user_perm.permissions
    
    g._user_permissions_cache = permissions_dict
    return g._user_permissions_cache


def clear_permissions_cache():
    """مسح الـ cache (يُستدعى بعد تحديث الصلاحيات)"""
    if hasattr(g, '_user_permissions_cache'):
        delattr(g, '_user_permissions_cache')


def has_permission(module, permission):
    """
    التحقق من امتلاك المستخدم لصلاحية معينة
    
    Args:
        module: Module enum
        permission: Permission value (VIEW, CREATE, EDIT, DELETE, etc.)
    
    Returns:
        bool: True إذا كانت الصلاحية موجودة
    """
    if not current_user.is_authenticated:
        return False
    
    # المديرون لديهم كل الصلاحيات
    if current_user.role == UserRole.ADMIN:
        return True
    
    # الحصول على صلاحيات المستخدم (من cache)
    user_permissions = get_user_permissions()
    
    # التحقق من وجود الصلاحية
    module_permissions = user_permissions.get(module, 0)
    return bool(module_permissions & permission)


def has_module_access(module):
    """التحقق من وصول المستخدم إلى القسم"""
    if not current_user.is_authenticated:
        return False
    
    if current_user.role == UserRole.ADMIN:
        return True
    
    user_permissions = get_user_permissions()
    return module in user_permissions


# ========================================
# Permission Decorators
# ========================================

def require_permission(module, permission, return_json=False):
    """
    Decorator للتحقق من صلاحية معينة
    
    Args:
        module: Module enum
        permission: Permission value
        return_json: إذا كان True، يرجع JSON 403 بدلاً من HTML
    
    Usage:
        @require_permission(Module.EMPLOYEES, Permission.EDIT)
        def edit_employee(id):
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # التحقق من تسجيل الدخول
            if not current_user.is_authenticated:
                if return_json or request.is_json:
                    return jsonify({
                        'success': False,
                        'error': 'يجب تسجيل الدخول أولاً',
                        'code': 'UNAUTHORIZED'
                    }), 401
                flash('يجب تسجيل الدخول أولاً', 'warning')
                return redirect(url_for('auth.login'))
            
            # التحقق من الصلاحية
            if not has_permission(module, permission):
                # Logging للمحاولات المرفوضة
                logger.warning(
                    f"Permission denied: {current_user.username} tried to access "
                    f"{f.__name__} requiring {module.value} - {permission}"
                )
                
                if return_json or request.is_json:
                    return jsonify({
                        'success': False,
                        'error': 'ليس لديك صلاحية لهذا الإجراء',
                        'code': 'FORBIDDEN',
                        'required_permission': f"{module.name}_{permission}"
                    }), 403
                
                flash('ليس لديك صلاحية لهذا الإجراء', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_module_access(module, return_json=False):
    """
    Decorator للتحقق من الوصول إلى قسم معين
    
    Args:
        module: Module enum
        return_json: إذا كان True، يرجع JSON 403
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if return_json or request.is_json:
                    return jsonify({
                        'success': False,
                        'error': 'يجب تسجيل الدخول أولاً',
                        'code': 'UNAUTHORIZED'
                    }), 401
                flash('يجب تسجيل الدخول أولاً', 'warning')
                return redirect(url_for('auth.login'))
            
            if not has_module_access(module):
                logger.warning(
                    f"Module access denied: {current_user.username} tried to access "
                    f"{module.value}"
                )
                
                if return_json or request.is_json:
                    return jsonify({
                        'success': False,
                        'error': 'ليس لديك صلاحية للوصول إلى هذا القسم',
                        'code': 'FORBIDDEN',
                        'required_module': module.name
                    }), 403
                
                flash('ليس لديك صلاحية للوصول إلى هذا القسم', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ========================================
# Template Helpers
# ========================================

def can_view(module):
    """هل يمكن للمستخدم عرض القسم؟"""
    return has_permission(module, Permission.VIEW)


def can_create(module):
    """هل يمكن للمستخدم الإنشاء في القسم؟"""
    return has_permission(module, Permission.CREATE)


def can_edit(module):
    """هل يمكن للمستخدم التعديل في القسم؟"""
    return has_permission(module, Permission.EDIT)


def can_delete(module):
    """هل يمكن للمستخدم الحذف من القسم؟"""
    return has_permission(module, Permission.DELETE)


def can_manage(module):
    """هل يمكن للمستخدم إدارة القسم؟"""
    return has_permission(module, Permission.MANAGE)


def get_permissions_context():
    """
    Context processor للـ Jinja templates
    يُضاف في app.py
    """
    return {
        'Module': Module,
        'can_view': can_view,
        'can_create': can_create,
        'can_edit': can_edit,
        'can_delete': can_delete,
        'can_manage': can_manage,
        'has_module_access': has_module_access,
        'has_permission': has_permission
    }
