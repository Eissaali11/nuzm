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
@login_required
def unread_count():
    """الحصول على عدد الإشعارات غير المقروءة"""
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'unread_count': count})


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
        'employee_request': url_for('employee_requests.index')
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


@notifications_bp.route('/test/create-demo-notifications', methods=['GET', 'POST'])
def create_demo_notifications():
    """إنشاء إشعارات تجريبية لاختبار النظام"""
    from models import User
    
    # الحصول على معرف المستخدم - استخدام المستخدم الحالي أو أول مستخدم
    if current_user.is_authenticated:
        user_id = current_user.id
    else:
        # استخدام أول مستخدم موجود
        first_user = User.query.first()
        if not first_user:
            return jsonify({'error': 'لا يوجد مستخدمين في النظام', 'redirect_url': url_for('auth.login')}), 404
        user_id = first_user.id
    
    # حذف الإشعارات التجريبية القديمة (اختياري)
    # Notification.query.filter_by(user_id=user_id).delete()
    # db.session.commit()
    
    # 1. إنشاء إشعار غياب موظف
    create_absence_notification(
        user_id=user_id,
        employee_name='محمد علي',
        department_name='قسم التسويق'
    )
    
    # 2. إنشاء إشعار انتهاء إقامة
    create_document_expiry_notification(
        user_id=user_id,
        employee_name='أحمد محمود',
        doc_type='الإقامة',
        days_left=5
    )
    
    # 3. إنشاء إشعار انتهاء تفويض
    create_document_expiry_notification(
        user_id=user_id,
        employee_name='فاطمة عبدالرحمن',
        doc_type='التفويض',
        days_left=3
    )
    
    # 4. إنشاء إشعار انتهاء فحص دوري
    create_document_expiry_notification(
        user_id=user_id,
        employee_name='سيارة رقم 123',
        doc_type='الفحص الدوري',
        days_left=10
    )
    
    # 5. إنشاء إشعارات عمليات متنوعة
    create_operations_notification(
        user_id=user_id,
        operation_title='حادثة سير جديدة',
        operation_description='تم تسجيل حادثة سير جديدة للسيارة رقم ABC-1234. يرجى المراجعة والموافقة.',
        entity_type='accident',
        entity_id=1
    )
    
    create_operations_notification(
        user_id=user_id,
        operation_title='طلب سيارة جديد',
        operation_description='تم استلام طلب تخصيص سيارة جديد من قسم العمليات.',
        entity_type='vehicle',
        entity_id=5
    )
    
    create_operations_notification(
        user_id=user_id,
        operation_title='طلب سلفة مالية',
        operation_description='تم تقديم طلب سلفة مالية جديد من الموظف أحمد محمود بقيمة 5000 ريال.',
        entity_type='employee_request',
        entity_id=3
    )
    
    # 6. إشعارات إضافية
    create_absence_notification(
        user_id=user_id,
        employee_name='سارة إبراهيم',
        department_name='قسم الموارد البشرية'
    )
    
    create_document_expiry_notification(
        user_id=user_id,
        employee_name='عمر خالد',
        doc_type='جواز السفر',
        days_left=15
    )
    
    return jsonify({
        'success': True,
        'message': 'تم إنشاء 8 إشعارات تجريبية بنجاح',
        'redirect_url': url_for('notifications.index')
    })
