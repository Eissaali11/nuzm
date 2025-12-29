# تثبيت Python الآن

## ⚠️ Python غير مثبت - يجب تثبيته أولاً

## الطريقة الأسرع: Microsoft Store

1. **افتح Microsoft Store** (يمكنك البحث عنه في قائمة ابدأ)
2. **ابحث عن**: `Python 3.12`
3. **اضغط Install**

أو افتح هذا الرابط مباشرة:
```
ms-windows-store://pdp/?ProductId=9NRWMJP3717K
```

## بعد التثبيت

بعد تثبيت Python من Microsoft Store:

1. **أعد تشغيل PowerShell**
2. **شغّل**:
   ```powershell
   python --version
   ```
3. **ثم شغّل**:
   ```powershell
   .\install_and_run.ps1
   ```

## طريقة بديلة: التحميل من الموقع الرسمي

1. افتح: https://www.python.org/downloads/
2. حمّل Python 3.12
3. **مهم جداً**: أثناء التثبيت، حدد ✅ **"Add Python to PATH"**
4. بعد التثبيت، أعد تشغيل PowerShell

## بعد التثبيت - تشغيل المشروع

```powershell
# الطريقة السريعة
.\install_and_run.ps1

# أو يدوياً
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

---

**ملاحظة**: بدون Python، لا يمكن تشغيل المشروع. يرجى تثبيته أولاً.

