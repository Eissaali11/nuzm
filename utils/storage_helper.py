import os
import io
from replit.object_storage import Client

client = Client()

def upload_image(file_data, folder_name, filename):
    """
    رفع صورة إلى Replit Object Storage
    
    Args:
        file_data: البيانات الثنائية للملف (bytes أو file-like object)
        folder_name: اسم المجلد (مثل: safety_checks, properties, employees)
        filename: اسم الملف
    
    Returns:
        str: المسار الكامل للملف في Storage
    """
    object_key = f"{folder_name}/{filename}"
    
    if hasattr(file_data, 'read'):
        file_bytes = file_data.read()
    else:
        file_bytes = file_data
    
    client.upload_from_bytes(object_key, file_bytes)
    
    return object_key

def download_image(object_key):
    """
    تحميل صورة من Replit Object Storage
    
    Args:
        object_key: المسار الكامل للملف في Storage
    
    Returns:
        bytes: البيانات الثنائية للملف
    """
    try:
        return client.download_as_bytes(object_key)
    except Exception as e:
        print(f"Error downloading image {object_key}: {str(e)}")
        return None

def delete_image(object_key):
    """
    حذف صورة من Replit Object Storage
    
    Args:
        object_key: المسار الكامل للملف في Storage
    
    Returns:
        bool: True إذا نجح الحذف، False إذا فشل
    """
    try:
        client.delete(object_key)
        return True
    except Exception as e:
        print(f"Error deleting image {object_key}: {str(e)}")
        return False

def list_images(folder_name):
    """
    عرض جميع الصور في مجلد معين
    
    Args:
        folder_name: اسم المجلد
    
    Returns:
        list: قائمة بأسماء الملفات
    """
    try:
        objects = client.list(prefix=f"{folder_name}/")
        return [obj.key for obj in objects]
    except Exception as e:
        print(f"Error listing images in {folder_name}: {str(e)}")
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
