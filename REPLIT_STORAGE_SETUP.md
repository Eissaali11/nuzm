# إعداد Replit App Storage

## خطوات إنشاء Bucket للصور

### 1. فتح أداة App Storage
- اضغط على "All tools" من القائمة اليسرى
- ابحث عن "App Storage" واضغط عليه
- أو اكتب "App Storage" في شريط البحث

### 2. إنشاء Bucket جديد
- اضغط على "Create new bucket"
- أدخل اسم الـ bucket: **nuzum-uploads**
- اضغط على "Create bucket"

### 3. تعيينه كـ Default Bucket
- بعد إنشاء الـ bucket، سيتم تعيينه تلقائياً كـ default bucket
- للتحقق، اذهب إلى "Settings" في تبويب App Storage
- تأكد من أن Bucket ID موجود

### 4. اختبار النظام
بعد إنشاء الـ bucket، النظام سيبدأ تلقائياً في:
- رفع الصور الجديدة إلى Object Storage
- تخزينها بشكل دائم في السحابة
- عدم حذفها عند إعادة تشغيل Replit

### ملاحظات مهمة
- الصور الموجودة في `static/uploads/` ستبقى تعمل (للتوافق)
- الصور الجديدة ستُرفع مباشرة إلى Object Storage
- لن تُحذف الصور أبداً بعد إعادة التشغيل
- التخزين السحابي دائم ومتاح دائماً

### التحقق من نجاح الإعداد
```bash
# اختبر رفع صورة تجريبية
python3 -c "
from replit.object_storage import Client
client = Client()
client.upload_from_bytes('test.txt', b'Hello World')
print('✅ تم الإعداد بنجاح!')
"
```

إذا ظهرت رسالة النجاح، فالنظام جاهز للاستخدام!
