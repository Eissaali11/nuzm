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
    
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(
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
    
    # التوجيه إلى الصفحة المرتبطة إن وجدت
    if notification.action_url:
        return redirect(notification.action_url)
    
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
