import os
import io

# محاولة الاتصال بـ Object Storage مع معالجة الأخطاء
try:
    from replit.object_storage import Client
    client = Client()
    STORAGE_AVAILABLE = True
except Exception as e:
    print(f"Warning: Object Storage not available: {e}")
    client = None
    STORAGE_AVAILABLE = False

def upload_image(file_data, folder_name, filename):
    """
    رفع صورة وحفظها محلياً في static/uploads
    
    Args:
        file_data: البيانات الثنائية للملف (bytes أو file-like object)
        folder_name: اسم المجلد (مثل: safety_checks, properties, employees)
        filename: اسم الملف
    
    Returns:
        str: المسار الكامل للملف المحلي
    """
    # تحضير البيانات
    if hasattr(file_data, 'read'):
        file_bytes = file_data.read()
    else:
        file_bytes = file_data
    
    # الحفظ المحلي (الطريقة الأساسية الآن)
    local_path = os.path.join('static', 'uploads', folder_name, filename)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    with open(local_path, 'wb') as f:
        f.write(file_bytes)
    
    return f'static/uploads/{folder_name}/{filename}'

def download_image(object_key):
    """
    تحميل صورة من النظام المحلي أولاً، ثم Object Storage كبديل
    
    Args:
        object_key: المسار الكامل للملف (يدعم كلاً من المسارات المحلية و Object Storage)
    
    Returns:
        bytes: البيانات الثنائية للملف أو None
    """
    # إذا كان المسار يبدأ بـ static/uploads، فهو مسار محلي قديم
    if object_key.startswith('static/uploads/'):
        local_path = object_key
        if os.path.exists(local_path):
            try:
                with open(local_path, 'rb') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading local file {local_path}: {str(e)}")
                return None
        return None
    
    # إذا كان المسار يبدأ بـ uploads/ (بدون static/)، أضف static/ في البداية
    if object_key.startswith('uploads/'):
        local_path = os.path.join('static', object_key)
        if os.path.exists(local_path):
            try:
                with open(local_path, 'rb') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading local file {local_path}: {str(e)}")
                # استمر للبحث مع المسار الأصلي
    
    # محاولة البحث المحلي في static/uploads/
    local_path = os.path.join('static', 'uploads', object_key)
    if os.path.exists(local_path):
        try:
            with open(local_path, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading local file {local_path}: {str(e)}")
            # استمر للبحث في Object Storage كبديل
    
    # محاولة Object Storage كبديل فقط
    if not STORAGE_AVAILABLE or client is None:
        return None
    
    try:
        return client.download_as_bytes(object_key)
    except Exception:
        # فشل Object Storage، والملف المحلي غير موجود
        return None

def delete_image(object_key):
    """
    حذف صورة من Replit Object Storage أو من النظام المحلي
    
    Args:
        object_key: المسار الكامل للملف
    
    Returns:
        bool: True إذا نجح الحذف، False إذا فشل
    """
    # إذا كان المسار محلياً
    if object_key.startswith('static/uploads/'):
        if os.path.exists(object_key):
            try:
                os.remove(object_key)
                return True
            except Exception as e:
                print(f"Error deleting local file {object_key}: {str(e)}")
                return False
        return False
    
    # حذف من Object Storage
    if STORAGE_AVAILABLE and client is not None:
        try:
            client.delete(object_key)
            return True
        except Exception as e:
            print(f"Warning: Failed to delete from Object Storage ({e}), trying local fallback")
    
    # محاولة حذف من المسار المحلي كبديل
    local_path = os.path.join('static', 'uploads', object_key)
    if os.path.exists(local_path):
        try:
            os.remove(local_path)
            return True
        except Exception as e:
            print(f"Error deleting fallback file {local_path}: {str(e)}")
            return False
    
    return False

def list_images(folder_name):
    """
    عرض جميع الصور في مجلد معين
    
    Args:
        folder_name: اسم المجلد
    
    Returns:
        list: قائمة بأسماء الملفات
    """
    if not STORAGE_AVAILABLE or client is None:
        # قراءة من المجلد المحلي
        local_path = os.path.join('static', 'uploads', folder_name)
        if os.path.exists(local_path):
            try:
                return [f"{folder_name}/{f}" for f in os.listdir(local_path) if os.path.isfile(os.path.join(local_path, f))]
            except Exception as e:
                print(f"Error listing local images in {folder_name}: {str(e)}")
        return []
    
    try:
        objects = client.list(prefix=f"{folder_name}/")
        return [obj.name for obj in objects]
    except Exception as e:
        print(f"Error listing images in {folder_name}: {str(e)}")
        # محاولة قراءة محلية
        local_path = os.path.join('static', 'uploads', folder_name)
        if os.path.exists(local_path):
            try:
                return [f"{folder_name}/{f}" for f in os.listdir(local_path) if os.path.isfile(os.path.join(local_path, f))]
            except:
                pass
        return []

def migrate_existing_files():
    """
    نقل الملفات الموجودة من static/uploads إلى Object Storage
    """
    base_path = "static/uploads"
    folders = ["safety_checks", "properties", "employees", "vehicles", "housing_documents"]
    
    migrated_count = 0
    
    for folder in folders:
        folder_path = os.path.join(base_path, folder)
        if not os.path.exists(folder_path):
            continue
        
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        upload_image(f, folder, filename)
                    migrated_count += 1
                    print(f"Migrated: {folder}/{filename}")
                except Exception as e:
                    print(f"Error migrating {file_path}: {str(e)}")
    
    return migrated_count
