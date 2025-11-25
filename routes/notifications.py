from flask import Blueprint, render_template, jsonify, request, url_for, redirect
from flask_login import login_required, current_user
from datetime import datetime
from models import Notification, User, db

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/', methods=['GET'])
@login_required
def index():
    """صفحة عرض جميع الإشعارات"""
    page = request.args.get('page', 1, type=int)
    notification_type = request.args.get('type', None)
    
    # بناء الاستعلام مع فلترة النوع
    query = Notification.query.filter_by(user_id=current_user.id)
    
    # تطبيق فلتر النوع إذا تم تحديده
    if notification_type:
        query = query.filter_by(notification_type=notification_type)
    
    notifications = query.order_by(
        Notification.created_at.desc()
    ).paginate(page=page, per_page=20)
    
    # تحديث حالة قراءة الإشعارات المعروضة
    unread_ids = [n.id for n in notifications.items if not n.is_read]
    if unread_ids:
        Notification.query.filter(Notification.id.in_(unread_ids)).update(
            {'is_read': True, 'read_at': datetime.utcnow()}, synchronize_session=False
        )
        db.session.commit()
    
    return render_template('notifications/index.html', notifications=notifications)


@notifications_bp.route('/<int:notification_id>', methods=['GET'])
@login_required
def view_detail(notification_id):
    """عرض تفاصيل إشعار محدد"""
    notification = Notification.query.filter_by(
        id=notification_id, user_id=current_user.id
    ).first_or_404()
    
    # تحديث حالة القراءة
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        db.session.commit()
    
    # عرض صفحة التفاصيل أولاً مع رابط للصفحة المرتبطة
    return render_template('notifications/detail.html', notification=notification)


@notifications_bp.route('/unread-count', methods=['GET'])
def unread_count():
    """الحصول على عدد الإشعارات غير المقروءة"""
    # إذا كان المستخدم مسجل دخول
    if current_user.is_authenticated:
        count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        return jsonify({'unread_count': count})
    else:
        # الحصول على أول مستخدم (للاختبار)
        from models import User
        first_user = User.query.first()
        if first_user:
            count = Notification.query.filter_by(user_id=first_user.id, is_read=False).count()
            return jsonify({'unread_count': count})
        return jsonify({'unread_count': 0})


@notifications_bp.route('/<int:notification_id>/mark-as-read', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """تحديث إشعار كمقروء"""
    notification = Notification.query.filter_by(
        id=notification_id, user_id=current_user.id
    ).first_or_404()
    
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        db.session.commit()
    
    return jsonify({'success': True})


@notifications_bp.route('/mark-all-as-read', methods=['POST'])
@login_required
def mark_all_as_read():
    """تحديث جميع الإشعارات كمقروءة"""
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update(
        {'is_read': True, 'read_at': datetime.utcnow()}, synchronize_session=False
    )
    db.session.commit()
    return jsonify({'success': True})


@notifications_bp.route('/<int:notification_id>/delete', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """حذف إشعار"""
    notification = Notification.query.filter_by(
        id=notification_id, user_id=current_user.id
    ).first_or_404()
    
    db.session.delete(notification)
    db.session.commit()
    return jsonify({'success': True})


def create_notification(user_id, notification_type, title, description, 
                       related_entity_type=None, related_entity_id=None, 
                       priority='normal', action_url=None):
    """دالة مساعدة لإنشاء إشعار جديد"""
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        description=description,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        priority=priority,
        action_url=action_url
    )
    db.session.add(notification)
    db.session.commit()
    return notification


def create_absence_notification(user_id, employee_name, department_name):
    """إشعار غياب موظف"""
    action_url = url_for('attendance.index')
    return create_notification(
        user_id=user_id,
        notification_type='absence',
        title=f'غياب موظف - {employee_name}',
        description=f'الموظف {employee_name} لم يتم تسجيل حضوره في قسم {department_name}',
        related_entity_type='employee',
        priority='high',
        action_url=action_url
    )


def create_document_expiry_notification(user_id, employee_name, doc_type, days_left):
    """إشعار انتهاء صلاحية وثيقة"""
    action_url = url_for('documents.index')
    priority = 'critical' if days_left <= 7 else 'high'
    return create_notification(
        user_id=user_id,
        notification_type='document_expiry',
        title=f'انتهاء صلاحية {doc_type} - {employee_name}',
        description=f'صلاحية {doc_type} للموظف {employee_name} ستنتهي خلال {days_left} أيام',
        related_entity_type='document',
        priority=priority,
        action_url=action_url
    )


def create_operations_notification(user_id, operation_title, operation_description, entity_type, entity_id):
    """إشعار من إدارة العمليات"""
    action_urls = {
        'vehicle': url_for('vehicles.index'),
        'accident': url_for('vehicle_operations.vehicle_operations_list'),
        'employee_request': url_for('employee_requests.index'),
        'safety_check': url_for('external_safety.admin_external_safety_checks')
    }
    
    return create_notification(
        user_id=user_id,
        notification_type='operations',
        title=f'عملية جديدة - {operation_title}',
        description=operation_description,
        related_entity_type=entity_type,
        related_entity_id=entity_id,
        priority='normal',
        action_url=action_urls.get(entity_type, '/')
    )


def create_safety_check_notification(user_id, vehicle_plate, supervisor_name, check_status, check_id):
    """إشعار فحص السلامة الخارجية"""
    status_labels = {
        'pending': 'قيد الانتظار',
        'under_review': 'قيد المراجعة',
        'approved': 'موافق عليه',
        'rejected': 'مرفوض'
    }
    
    priority_map = {
        'pending': 'high',
        'under_review': 'normal',
        'approved': 'normal',
        'rejected': 'critical'
    }
    
    status_label = status_labels.get(check_status, check_status)
    
    return create_notification(
        user_id=user_id,
        notification_type='safety_check',
        title=f'فحص السلامة - السيارة {vehicle_plate}',
        description=f'طلب فحص السلامة الخارجية للسيارة {vehicle_plate} من قبل {supervisor_name} - الحالة: {status_label}',
        related_entity_type='safety_check',
        related_entity_id=check_id,
        priority=priority_map.get(check_status, 'normal'),
        action_url=url_for('external_safety.admin_external_safety_checks')
    )


def create_safety_check_review_notification(user_id, vehicle_plate, action, reviewer_name, check_id):
    """إشعار بمراجعة/موافقة فحص السلامة"""
    action_labels = {
        'approved': 'تمت الموافقة على',
        'rejected': 'تم رفض',
        'under_review': 'قيد المراجعة'
    }
    
    priority = 'high' if action in ['rejected'] else 'normal'
    action_label = action_labels.get(action, action)
    
    return create_notification(
        user_id=user_id,
        notification_type='safety_check_review',
        title=f'{action_label} فحص السلامة - {vehicle_plate}',
        description=f'تمت مراجعة فحص السلامة للسيارة {vehicle_plate} بواسطة {reviewer_name}: {action_label}',
        related_entity_type='safety_check',
        related_entity_id=check_id,
        priority=priority,
        action_url=url_for('external_safety.admin_external_safety_checks')
    )


def create_accident_notification(user_id, vehicle_plate, driver_name, accident_type, accident_id, severity='normal'):
    """إشعار حادثة سير جديدة"""
    severity_labels = {
        'minor': 'بسيطة',
        'moderate': 'متوسطة',
        'severe': 'حادة',
        'critical': 'حرجة'
    }
    
    severity_priority = {
        'minor': 'low',
        'moderate': 'normal',
        'severe': 'high',
        'critical': 'critical'
    }
    
    severity_label = severity_labels.get(accident_type, accident_type)
    
    return create_notification(
        user_id=user_id,
        notification_type='accident',
        title=f'حادثة سير - السيارة {vehicle_plate}',
        description=f'تم تسجيل حادثة سير {severity_label} للسيارة {vehicle_plate} من قبل السائق {driver_name}. يرجى المراجعة والموافقة.',
        related_entity_type='accident',
        related_entity_id=accident_id,
        priority=severity_priority.get(severity, 'normal'),
        action_url=url_for('vehicle_operations.vehicle_operations_list')
    )


def get_all_admin_users():
    """الحصول على جميع المستخدمين الإداريين"""
    from models import User
    return User.query.all()


@notifications_bp.route('/test/create-demo-notifications', methods=['GET', 'POST'])
def create_demo_notifications():
    """إنشاء إشعارات تجريبية لاختبار النظام - لجميع المستخدمين"""
    from models import User
    
    # الحصول على جميع المستخدمين
    admin_users = get_all_admin_users()
    if not admin_users:
        return jsonify({'error': 'لا يوجد مستخدمين في النظام', 'redirect_url': url_for('auth.login')}), 404
    
    notification_count = 0
    
    # إنشاء الإشعارات لجميع المستخدمين الإداريين
    for admin_user in admin_users:
        user_id = admin_user.id
        
        # 1. إشعار غياب موظف
        create_absence_notification(
            user_id=user_id,
            employee_name='محمد علي',
            department_name='قسم التسويق'
        )
        notification_count += 1
        
        # 2. إشعار انتهاء إقامة
        create_document_expiry_notification(
            user_id=user_id,
            employee_name='أحمد محمود',
            doc_type='الإقامة',
            days_left=5
        )
        notification_count += 1
        
        # 3. إشعار انتهاء تفويض
        create_document_expiry_notification(
            user_id=user_id,
            employee_name='فاطمة عبدالرحمن',
            doc_type='التفويض',
            days_left=3
        )
        notification_count += 1
        
        # 4. إشعار انتهاء فحص دوري
        create_document_expiry_notification(
            user_id=user_id,
            employee_name='سيارة رقم 123',
            doc_type='الفحص الدوري',
            days_left=10
        )
        notification_count += 1
        
        # 5. إشعارات عمليات متنوعة
        create_operations_notification(
            user_id=user_id,
            operation_title='حادثة سير جديدة',
            operation_description='تم تسجيل حادثة سير جديدة للسيارة رقم ABC-1234. يرجى المراجعة والموافقة.',
            entity_type='accident',
            entity_id=1
        )
        notification_count += 1
        
        create_operations_notification(
            user_id=user_id,
            operation_title='طلب سيارة جديد',
            operation_description='تم استلام طلب تخصيص سيارة جديد من قسم العمليات.',
            entity_type='vehicle',
            entity_id=5
        )
        notification_count += 1
        
        create_operations_notification(
            user_id=user_id,
            operation_title='طلب سلفة مالية',
            operation_description='تم تقديم طلب سلفة مالية جديد من الموظف أحمد محمود بقيمة 5000 ريال.',
            entity_type='employee_request',
            entity_id=3
        )
        notification_count += 1
        
        # 6. إشعار غياب آخر
        create_absence_notification(
            user_id=user_id,
            employee_name='سارة إبراهيم',
            department_name='قسم الموارد البشرية'
        )
        notification_count += 1
        
        create_document_expiry_notification(
            user_id=user_id,
            employee_name='عمر خالد',
            doc_type='جواز السفر',
            days_left=15
        )
        notification_count += 1
        
        # 7. إشعارات فحص السلامة الخارجية
        create_safety_check_notification(
            user_id=user_id,
            vehicle_plate='ABC-1234',
            supervisor_name='أحمد محمد',
            check_status='pending',
            check_id=1
        )
        notification_count += 1
        
        create_safety_check_notification(
            user_id=user_id,
            vehicle_plate='XYZ-5678',
            supervisor_name='فاطمة علي',
            check_status='under_review',
            check_id=2
        )
        notification_count += 1
        
        create_safety_check_review_notification(
            user_id=user_id,
            vehicle_plate='DEF-9012',
            action='approved',
            reviewer_name='سلمان الدعيع',
            check_id=3
        )
        notification_count += 1
        
        # 8. إشعارات الحوادث
        create_accident_notification(
            user_id=user_id,
            vehicle_plate='ABC-1234',
            driver_name='محمد عبدالله',
            accident_type='moderate',
            accident_id=10,
            severity='moderate'
        )
        notification_count += 1
        
        create_accident_notification(
            user_id=user_id,
            vehicle_plate='XYZ-5678',
            driver_name='فاطمة احمد',
            accident_type='severe',
            accident_id=11,
            severity='severe'
        )
        notification_count += 1
    
    return jsonify({
        'success': True,
        'message': f'تم إنشاء {notification_count} إشعار تجريبي لـ {len(admin_users)} مستخدم',
        'redirect_url': url_for('notifications.index')
    })
