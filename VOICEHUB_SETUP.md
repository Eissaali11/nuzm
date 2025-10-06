# دليل إعداد تكامل VoiceHub

## نظرة عامة
تم تكامل نظام نُظم مع منصة VoiceHub للذكاء الاصطناعي الصوتي لتسجيل وتحليل المكالمات الصوتية تلقائياً.

## المتطلبات
1. حساب على منصة VoiceHub: https://voicehub.dataqueue.ai/
2. مفتاح API من VoiceHub
3. إعداد Webhook في لوحة تحكم VoiceHub

## خطوات الإعداد

### 1. الحصول على مفتاح API
1. سجل دخول إلى لوحة تحكم VoiceHub
2. اذهب إلى الإعدادات (Settings)
3. انسخ مفتاح API الخاص بك
4. أضفه في متغيرات البيئة:
   - المفتاح: `VOICEHUB_API_KEY`
   - القيمة: مفتاح API الخاص بك

### 2. إعداد Webhook في VoiceHub

في لوحة تحكم VoiceHub، اذهب إلى قسم API واضبط الإعدادات التالية:

#### Webhook URL
```
https://YOUR_REPLIT_APP_URL/voicehub/webhook
```
مثال:
```
https://eissahr.replit.app/voicehub/webhook
```

#### Webhook Secret
أنشئ مفتاح سري قوي وأضفه في متغيرات البيئة:
- المفتاح: `VOICEHUB_WEBHOOK_SECRET`
- القيمة: المفتاح السري الخاص بك

⚠️ **مهم**: استخدم نفس المفتاح في كلا المكانين (VoiceHub و Replit)

#### إعدادات إضافية
- **Retry Attempts**: 3 محاولات
- **Retry Delay**: 5000 milliseconds (5 ثواني)
- **Request Timeout**: 30000 milliseconds (30 ثانية)

### 3. الأحداث المدعومة

سيستقبل النظام 3 أنواع من الأحداث:

#### 1. CallStatusChanged
يتم استقباله عند تغيير حالة المكالمة:
- `started` - بداية المكالمة
- `queued` - في الانتظار
- `in-progress` - جارية
- `completed` - مكتملة
- `failed` - فشلت
- `cancelled` - ملغاة

#### 2. RecordingsAvailable
يتم استقباله عند توفر تسجيلات المكالمة

#### 3. AnalysisResultReady
يتم استقباله عند جاهزية تحليل المكالمة، يشمل:
- النص الكامل للمحادثة
- التحليل العاطفي (إيجابي/سلبي/محايد)
- درجة التعاطف
- حالة الحل
- الكلمات المفتاحية
- مؤشرات الولاء

## استخدام النظام

### الوصول للوحة التحكم
```
https://YOUR_REPLIT_APP_URL/voicehub/dashboard
```

### عرض جميع المكالمات
```
https://YOUR_REPLIT_APP_URL/voicehub/calls
```

### عرض تفاصيل مكالمة معينة
```
https://YOUR_REPLIT_APP_URL/voicehub/calls/<CALL_ID>
```

## الميزات

### ✅ تسجيل تلقائي للمكالمات
- يتم حفظ جميع المكالمات تلقائياً في قاعدة البيانات
- تتبع حالة المكالمة في الوقت الفعلي

### ✅ تحليل ذكي
- تحليل عاطفي للمحادثة
- استخراج الكلمات المفتاحية
- قياس درجة التعاطف
- تحديد حالة الحل

### ✅ ربط بالموظفين والأقسام
- ربط المكالمات بموظفين محددين
- تصنيف حسب الأقسام
- إضافة ملاحظات

### ✅ فلترة حسب الصلاحيات
- المستخدمون يرون فقط مكالمات أقسامهم
- المديرون يرون جميع المكالمات

## اختبار التكامل

### اختبار Webhook يدوياً
```bash
curl -X POST https://YOUR_REPLIT_APP_URL/voicehub/webhook \
  -H "Content-Type: application/json" \
  -H "x-webhook-secret: YOUR_SECRET" \
  -d '{
    "eventType": "CallStatusChanged",
    "callId": "test-call-123",
    "status": "completed",
    "timestamp": "2025-01-01T12:00:00Z"
  }'
```

### التحقق من الاستجابة
إذا نجح الطلب، ستحصل على:
```json
{"success": true}
```

## استكشاف الأخطاء

### المشكلة: Webhook Secret غير صحيح
**الحل**: تأكد من أن المفتاح في VoiceHub مطابق للمفتاح في متغيرات البيئة

### المشكلة: لا تظهر المكالمات
**الحل**: 
1. تحقق من أن Webhook URL صحيح
2. راجع سجلات (logs) التطبيق
3. تأكد من أن Agent في VoiceHub مفعّل

### المشكلة: التحليل غير متوفر
**الحل**:
1. تحقق من صحة VOICEHUB_API_KEY
2. تأكد من أن VoiceHub أرسل حدث AnalysisResultReady

## قاعدة البيانات

### جداول جديدة
1. `voicehub_calls` - تخزين معلومات المكالمات
2. `voicehub_analysis` - تخزين تحليلات المكالمات

### العلاقات
- `voicehub_calls.employee_id` → `employee.id`
- `voicehub_calls.department_id` → `department.id`
- `voicehub_analysis.call_id` → `voicehub_calls.id`

## الأمان

### ✅ التحقق من المصدر
- كل طلب webhook يتم التحقق من سره
- الطلبات غير الموثوقة يتم رفضها تلقائياً

### ✅ فلترة البيانات
- المستخدمون يرون فقط بيانات أقسامهم
- حماية الخصوصية مضمونة

### ✅ تشفير الاتصال
- جميع الاتصالات عبر HTTPS
- البيانات الحساسة في متغيرات البيئة

## الدعم الفني
للمساعدة أو الاستفسارات:
- الوثائق: https://voicehub.dataqueue.ai/docs
- الدعم الفني: support@dataqueue.ai
