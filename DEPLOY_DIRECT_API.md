# ربط مباشر بـ Hostinger API من المحرر

## ✅ لديك API Token: `5om43f07eSdSuSDBnXS3X53O17BviwydAd9myIEY5eb1e381`

## 🚀 الطرق المتاحة

### الطريقة 1: استخدام Hostinger API MCP (موصى بها)

#### إعداد MCP في Cursor:

1. **افتح إعدادات Cursor**:
   - `File` → `Preferences` → `Settings`
   - ابحث عن `MCP` أو `Model Context Protocol`

2. **أضف إعدادات Hostinger MCP**:
   - افتح ملف الإعدادات (عادة `settings.json` أو `mcp.json`)
   - أضف محتوى `hostinger_mcp_config.json`

3. **أعد تشغيل Cursor**

4. **استخدم MCP**:
   - الآن يمكنك استخدام أوامر Hostinger مباشرة من Cursor!

---

### الطريقة 2: سكريبت PowerShell مباشر

شغّل:

```powershell
.\hostinger_api_deploy.ps1 -ApiToken "5om43f07eSdSuSDBnXS3X53O17BviwydAd9myIEY5eb1e381"
```

---

### الطريقة 3: استخدام cURL مباشرة

```powershell
# اختبار الاتصال
curl -X GET "https://developers.hostinger.com/api/vps/v1/virtual-machines" `
  -H "Authorization: Bearer 5om43f07eSdSuSDBnXS3X53O17BviwydAd9myIEY5eb1e381" `
  -H "Content-Type: application/json"
```

---

## 📋 ما يمكنك فعله بـ Hostinger API

### 1. إدارة VPS
- عرض قائمة VPS
- إدارة VPS
- مراقبة الأداء

### 2. إدارة Domains
- عرض Domains
- إدارة DNS
- إدارة SSL

### 3. إدارة Databases
- عرض قواعد البيانات
- إنشاء/حذف قواعد البيانات

### 4. رفع الملفات
- ⚠️ **ملاحظة**: API لا يدعم رفع الملفات مباشرة
- استخدم **Git** أو **FTP** للرفع

---

## 🎯 الطريقة الموصى بها

**للرفع المباشر**: استخدم **Git** (الأسهل والأسرع)

```powershell
git push origin main
```

**للمراقبة والإدارة**: استخدم **Hostinger API**

---

## ⚠️ ملاحظات أمنية

1. **لا تشارك API Token** مع أحد
2. **احفظه في ملف آمن** (مثل `.env`)
3. **استخدم Environment Variables** في الإنتاج

---

## 📝 ملفات مساعدة

- `hostinger_api_deploy.ps1` - سكريبت PowerShell للـ API
- `hostinger_mcp_config.json` - إعدادات MCP
- `DEPLOY_DIRECT_API.md` - هذا الملف

---

**للرفع المباشر: استخدم Git! 🚀**

