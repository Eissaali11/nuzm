"""
أداة تشفير وفك تشفير المعرفات للروابط
تستخدم لإخفاء المعرفات الرقمية المتسلسلة في الروابط
يتطلب وجود متغير البيئة SESSION_SECRET للعمل بشكل آمن
"""
import hashlib
import hmac
import os
from functools import lru_cache

# مفتاح سري للتشفير - مطلوب من متغيرات البيئة
SECRET_KEY = os.environ.get('SESSION_SECRET')
if not SECRET_KEY:
    raise RuntimeError("SESSION_SECRET environment variable is required for ID encoding security")

# الأحرف المستخدمة في التشفير (Base62)
ALPHABET = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
BASE = len(ALPHABET)

# Salt للتشفير باستخدام HMAC للمزيد من الأمان
SALT = hmac.new(SECRET_KEY.encode(), b'id_encoder_salt', hashlib.sha256).hexdigest()[:16]

def encode_id(id_value: int, prefix: str = '') -> str:
    """
    تشفير معرف رقمي إلى سلسلة نصية عشوائية المظهر
    
    Args:
        id_value: المعرف الرقمي
        prefix: بادئة اختيارية للتمييز بين أنواع الكيانات
    
    Returns:
        سلسلة مشفرة
    """
    if id_value < 0:
        raise ValueError("المعرف يجب أن يكون رقماً موجباً")
    
    # إضافة offset للمزيد من الأمان
    offset = int(SALT[:4], 16) % 10000
    encoded_value = id_value + offset
    
    # تحويل إلى Base62
    if encoded_value == 0:
        result = ALPHABET[0]
    else:
        result = ''
        while encoded_value > 0:
            result = ALPHABET[encoded_value % BASE] + result
            encoded_value //= BASE
    
    # إضافة checksum باستخدام HMAC (6 أحرف بدلاً من 2)
    checksum = _calculate_checksum(id_value, prefix)
    
    # دمج النتيجة مع checksum
    encoded = f"{checksum}{result}"
    
    return encoded

def decode_id(encoded_str: str, prefix: str = '') -> int:
    """
    فك تشفير سلسلة مشفرة إلى معرف رقمي
    
    Args:
        encoded_str: السلسلة المشفرة
        prefix: البادئة المستخدمة عند التشفير
    
    Returns:
        المعرف الرقمي الأصلي
    
    Raises:
        ValueError: إذا كانت السلسلة غير صالحة
    """
    if not encoded_str or len(encoded_str) < 7:
        raise ValueError("سلسلة التشفير غير صالحة")
    
    # فصل checksum عن الرقم المشفر (6 أحرف للـ checksum)
    checksum = encoded_str[:6]
    encoded_number = encoded_str[6:]
    
    # تحويل من Base62 إلى رقم
    decoded_value = 0
    for char in encoded_number:
        if char not in ALPHABET:
            raise ValueError(f"حرف غير صالح في السلسلة المشفرة: {char}")
        decoded_value = decoded_value * BASE + ALPHABET.index(char)
    
    # إزالة offset
    offset = int(SALT[:4], 16) % 10000
    original_id = decoded_value - offset
    
    if original_id < 0:
        raise ValueError("المعرف المفكك غير صالح")
    
    # التحقق من checksum
    expected_checksum = _calculate_checksum(original_id, prefix)
    if checksum != expected_checksum:
        raise ValueError("فشل التحقق من صحة المعرف")
    
    return original_id

def _calculate_checksum(id_value: int, prefix: str) -> str:
    """حساب checksum باستخدام HMAC للتحقق من صحة المعرف"""
    data = f"{prefix}{id_value}".encode()
    hash_result = hmac.new(SECRET_KEY.encode(), data, hashlib.sha256).hexdigest()
    return hash_result[:6]  # 6 أحرف = 2^24 احتمال (~16 مليون)

@lru_cache(maxsize=10000)
def encode_id_cached(id_value: int, prefix: str = '') -> str:
    """نسخة مع cache للتشفير المتكرر"""
    return encode_id(id_value, prefix)

@lru_cache(maxsize=10000)
def decode_id_cached(encoded_str: str, prefix: str = '') -> int:
    """نسخة مع cache لفك التشفير المتكرر"""
    return decode_id(encoded_str, prefix)

# دوال مساعدة لأنواع محددة من الكيانات
def encode_vehicle_id(id_value: int) -> str:
    """تشفير معرف سيارة"""
    return encode_id(id_value, 'vehicle')

def decode_vehicle_id(encoded_str: str) -> int:
    """فك تشفير معرف سيارة"""
    return decode_id(encoded_str, 'vehicle')

def encode_employee_id(id_value: int) -> str:
    """تشفير معرف موظف"""
    return encode_id(id_value, 'employee')

def decode_employee_id(encoded_str: str) -> int:
    """فك تشفير معرف موظف"""
    return decode_id(encoded_str, 'employee')

def encode_safety_check_id(id_value: int) -> str:
    """تشفير معرف فحص سلامة"""
    return encode_id(id_value, 'safety')

def decode_safety_check_id(encoded_str: str) -> int:
    """فك تشفير معرف فحص سلامة"""
    return decode_id(encoded_str, 'safety')

# Jinja2 filter للاستخدام في القوالب
def register_template_filters(app):
    """تسجيل الفلاتر في تطبيق Flask"""
    @app.template_filter('encode_id')
    def encode_id_filter(id_value, prefix=''):
        try:
            return encode_id(int(id_value), prefix)
        except (ValueError, TypeError):
            return str(id_value)
    
    @app.template_filter('encode_vehicle_id')
    def encode_vehicle_id_filter(id_value):
        try:
            return encode_vehicle_id(int(id_value))
        except (ValueError, TypeError):
            return str(id_value)
    
    @app.template_filter('encode_employee_id')
    def encode_employee_id_filter(id_value):
        try:
            return encode_employee_id(int(id_value))
        except (ValueError, TypeError):
            return str(id_value)
    
    @app.template_filter('encode_safety_id')
    def encode_safety_id_filter(id_value):
        try:
            return encode_safety_check_id(int(id_value))
        except (ValueError, TypeError):
            return str(id_value)
