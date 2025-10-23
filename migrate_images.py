#!/usr/bin/env python3
"""
سكريبت لنقل الصور من Object Storage إلى التخزين المحلي
"""
import os
import sys
from app import app, db
from models import VehicleSafetyImage
from utils.storage_helper import download_image, upload_image

def migrate_safety_images():
    """نقل صور فحوصات السلامة"""
    print("بدء نقل صور فحوصات السلامة...")
    
    with app.app_context():
        images = VehicleSafetyImage.query.all()
        migrated = 0
        failed = 0
        
        for img in images:
            # تخطي الصور المحفوظة محلياً بالفعل
            if img.image_path.startswith('static/uploads/'):
                continue
            
            print(f"معالجة صورة {img.id}: {img.image_path}")
            
            try:
                # محاولة تحميل الصورة
                image_data = download_image(img.image_path)
                
                if image_data:
                    # استخراج اسم الملف
                    filename = os.path.basename(img.image_path)
                    
                    # رفع الصورة للتخزين المحلي
                    new_path = upload_image(image_data, 'safety_checks', filename)
                    
                    # تحديث المسار في قاعدة البيانات
                    img.image_path = new_path
                    db.session.commit()
                    
                    migrated += 1
                    print(f"  ✓ تم النقل: {new_path}")
                else:
                    failed += 1
                    print(f"  ✗ فشل: لم يتم العثور على الصورة")
                    
            except Exception as e:
                failed += 1
                print(f"  ✗ خطأ: {str(e)}")
                db.session.rollback()
        
        print(f"\nالنتائج:")
        print(f"  تم النقل بنجاح: {migrated}")
        print(f"  فشل: {failed}")
        print(f"  إجمالي: {len(images)}")


if __name__ == '__main__':
    print("=" * 50)
    print("سكريبت نقل الصور من Object Storage إلى التخزين المحلي")
    print("=" * 50)
    
    migrate_safety_images()
    
    print("\nتم الانتهاء!")
