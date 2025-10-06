def save_file(file, folder):
    """حفظ الملف (صورة أو PDF) في المجلد المحدد وإرجاع المسار ونوع الملف - مع دعم HEIC"""
    if not file:
        return None, None
    if not file.filename:
        return None, None

    from werkzeug.utils import secure_filename
    from flask import current_app
    import uuid
    import os
    
    # إنشاء اسم فريد للملف
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"

    # التأكد من وجود المجلد
    upload_folder = os.path.join(current_app.static_folder, 'uploads', folder)
    os.makedirs(upload_folder, exist_ok=True)

    # حفظ الملف
    file_path = os.path.join(upload_folder, unique_filename)
    
    try:
        file.save(file_path)
        
        # تحويل HEIC/HEIF إلى JPEG للتوافق مع المتصفحات
        filename_lower = filename.lower()
        if filename_lower.endswith(('.heic', '.heif')):
            try:
                from PIL import Image
                # فتح الصورة HEIC
                img = Image.open(file_path)
                # تحويلها إلى RGB (HEIC قد يكون RGBA)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                # حفظها كـ JPEG
                jpeg_filename = unique_filename.rsplit('.', 1)[0] + '.jpg'
                jpeg_path = os.path.join(upload_folder, jpeg_filename)
                img.save(jpeg_path, 'JPEG', quality=90)
                # حذف الملف الأصلي
                os.remove(file_path)
                # تحديث المتغيرات
                unique_filename = jpeg_filename
            except Exception as convert_error:
                print(f"تحذير: فشل تحويل HEIC إلى JPEG: {convert_error}")
                # الاحتفاظ بالملف الأصلي في حالة فشل التحويل
        
        # تحديد نوع الملف (صورة أو PDF)
        file_type = 'pdf' if filename.lower().endswith('.pdf') else 'image'

        # إرجاع المسار النسبي للملف ونوعه
        return f"uploads/{folder}/{unique_filename}", file_type
        
    except Exception as e:
        print(f"خطأ في حفظ الملف: {e}")
        import traceback
        traceback.print_exc()
        return None, None
