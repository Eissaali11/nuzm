"""
خدمة الإشعارات لنظام طلبات الموظفين
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict
from app import db
from models import RequestNotification, EmployeeRequest, Employee

logger = logging.getLogger(__name__)


class RequestNotificationService:
    """خدمة إدارة إشعارات الطلبات"""
    
    # قوالب الرسائل
    NOTIFICATION_TEMPLATES = {
        'request_received': {
            'title': 'تم استلام طلبك',
            'message': 'تم استلام {request_type} رقم #{request_id} بنجاح. سيتم مراجعته قريباً.'
        },
        'approved': {
            'title': 'تمت الموافقة على طلبك',
            'message': 'تمت الموافقة على {request_type} رقم #{request_id}.'
        },
        'rejected': {
            'title': 'تم رفض طلبك',
            'message': 'تم رفض {request_type} رقم #{request_id}. السبب: {reason}'
        },
        'completed': {
            'title': 'تم إكمال طلبك',
            'message': 'تم إكمال {request_type} رقم #{request_id} بنجاح.'
        },
        'advance_disbursed': {
            'title': 'تم صرف السلفة',
            'message': 'تم صرف مبلغ {amount} ريال من السلفة رقم #{request_id} بنجاح.'
        },
        'invoice_paid': {
            'title': 'تم سداد الفاتورة',
            'message': 'تم سداد فاتورتك رقم #{request_id} بمبلغ {amount} ريال عبر {payment_method}.'
        },
        'liability_added': {
            'title': 'تم إضافة التزام مالي',
            'message': 'تم إضافة التزام مالي بمبلغ {amount} ريال. الوصف: {description}'
        },
        'payment_recorded': {
            'title': 'تم تسجيل دفعة',
            'message': 'تم تسجيل دفعة بمبلغ {amount} ريال على التزامك المالي. المبلغ المتبقي: {remaining} ريال.'
        },
        'uploaded': {
            'title': 'تم رفع الملفات',
            'message': 'تم رفع ملفات الطلب رقم #{request_id} إلى Google Drive بنجاح.'
        }
    }
    
    # ترجمة أنواع الطلبات
    REQUEST_TYPE_NAMES = {
        'invoice': 'الفاتورة',
        'car_wash': 'طلب غسيل السيارة',
        'car_inspection': 'طلب فحص السيارة',
        'advance_payment': 'طلب السلفة'
    }
    
    @staticmethod
    def create_notification(
        request_id: int,
        employee_id: int,
        notification_type: str,
        custom_title: str = None,
        custom_message: str = None,
        **kwargs
    ) -> Optional[RequestNotification]:
        """
        إنشاء إشعار جديد
        
        Args:
            request_id: رقم الطلب
            employee_id: رقم الموظف
            notification_type: نوع الإشعار
            custom_title: عنوان مخصص (اختياري)
            custom_message: رسالة مخصصة (اختياري)
            **kwargs: بيانات إضافية للقالب (amount, reason, etc.)
        
        Returns:
            كائن RequestNotification أو None
        """
        try:
            # جلب بيانات الطلب
            request = EmployeeRequest.query.get(request_id)
            if not request:
                logger.error(f"الطلب غير موجود: {request_id}")
                return None
            
            # تحديد العنوان والرسالة
            if custom_title and custom_message:
                title = custom_title
                message = custom_message
            else:
                template = RequestNotificationService.NOTIFICATION_TEMPLATES.get(notification_type)
                if not template:
                    logger.error(f"نوع إشعار غير معروف: {notification_type}")
                    return None
                
                title = template['title']
                message = template['message']
                
                # تطبيق القالب
                request_type_ar = RequestNotificationService.REQUEST_TYPE_NAMES.get(
                    request.request_type.value,
                    'الطلب'
                )
                
                format_data = {
                    'request_type': request_type_ar,
                    'request_id': request_id,
                    **kwargs
                }
                
                message = message.format(**format_data)
            
            # إنشاء الإشعار
            notification = RequestNotification(
                request_id=request_id,
                employee_id=employee_id,
                notification_type=notification_type,
                title_ar=title,
                message_ar=message,
                is_read=False,
                is_sent_to_app=False
            )
            
            db.session.add(notification)
            db.session.commit()
            
            logger.info(f"تم إنشاء إشعار: {notification_type} للموظف {employee_id}")
            
            # TODO: إرسال الإشعار للتطبيق عبر FCM
            
            return notification
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء الإشعار: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_employee_unread_notifications(employee_id: int) -> List[RequestNotification]:
        """
        جلب الإشعارات غير المقروءة للموظف
        
        Args:
            employee_id: رقم الموظف
        
        Returns:
            قائمة بالإشعارات غير المقروءة
        """
        try:
            notifications = RequestNotification.query.filter_by(
                employee_id=employee_id,
                is_read=False
            ).order_by(RequestNotification.created_at.desc()).all()
            
            return notifications
            
        except Exception as e:
            logger.error(f"خطأ في جلب الإشعارات غير المقروءة: {e}")
            return []
    
    @staticmethod
    def get_employee_notifications(
        employee_id: int,
        read_status: Optional[bool] = None,
        limit: int = 50
    ) -> List[RequestNotification]:
        """
        جلب إشعارات الموظف
        
        Args:
            employee_id: رقم الموظف
            read_status: حالة القراءة (True/False/None للكل)
            limit: عدد الإشعارات (افتراضياً 50)
        
        Returns:
            قائمة بالإشعارات
        """
        try:
            query = RequestNotification.query.filter_by(employee_id=employee_id)
            
            if read_status is not None:
                query = query.filter_by(is_read=read_status)
            
            notifications = query.order_by(
                RequestNotification.created_at.desc()
            ).limit(limit).all()
            
            return notifications
            
        except Exception as e:
            logger.error(f"خطأ في جلب الإشعارات: {e}")
            return []
    
    @staticmethod
    def mark_notification_as_read(notification_id: int) -> bool:
        """
        تحديد إشعار كمقروء
        
        Args:
            notification_id: رقم الإشعار
        
        Returns:
            True إذا نجحت العملية
        """
        try:
            notification = RequestNotification.query.get(notification_id)
            if not notification:
                logger.error(f"الإشعار غير موجود: {notification_id}")
                return False
            
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"تم تحديد الإشعار {notification_id} كمقروء")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تحديد الإشعار كمقروء: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def mark_all_as_read(employee_id: int) -> bool:
        """
        تحديد جميع إشعارات الموظف كمقروءة
        
        Args:
            employee_id: رقم الموظف
        
        Returns:
            True إذا نجحت العملية
        """
        try:
            RequestNotification.query.filter_by(
                employee_id=employee_id,
                is_read=False
            ).update({
                'is_read': True,
                'read_at': datetime.utcnow()
            })
            
            db.session.commit()
            
            logger.info(f"تم تحديد جميع إشعارات الموظف {employee_id} كمقروءة")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تحديد جميع الإشعارات كمقروءة: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def send_notification_to_app(notification_id: int) -> bool:
        """
        إرسال الإشعار للتطبيق (عبر FCM)
        
        Args:
            notification_id: رقم الإشعار
        
        Returns:
            True إذا نجح الإرسال
        """
        try:
            notification = RequestNotification.query.get(notification_id)
            if not notification:
                logger.error(f"الإشعار غير موجود: {notification_id}")
                return False
            
            # TODO: تطبيق FCM لإرسال الإشعار للتطبيق
            # من خلال Firebase Cloud Messaging
            
            notification.is_sent_to_app = True
            notification.sent_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"تم إرسال الإشعار {notification_id} للتطبيق")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في إرسال الإشعار للتطبيق: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def get_unread_count(employee_id: int) -> int:
        """
        الحصول على عدد الإشعارات غير المقروءة
        
        Args:
            employee_id: رقم الموظف
        
        Returns:
            عدد الإشعارات غير المقروءة
        """
        try:
            count = RequestNotification.query.filter_by(
                employee_id=employee_id,
                is_read=False
            ).count()
            
            return count
            
        except Exception as e:
            logger.error(f"خطأ في حساب الإشعارات غير المقروءة: {e}")
            return 0
    
    @staticmethod
    def delete_notification(notification_id: int) -> bool:
        """
        حذف إشعار
        
        Args:
            notification_id: رقم الإشعار
        
        Returns:
            True إذا نجح الحذف
        """
        try:
            notification = RequestNotification.query.get(notification_id)
            if not notification:
                return False
            
            db.session.delete(notification)
            db.session.commit()
            
            logger.info(f"تم حذف الإشعار {notification_id}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في حذف الإشعار: {e}")
            db.session.rollback()
            return False


# Instance للاستخدام المباشر
notification_service = RequestNotificationService()
