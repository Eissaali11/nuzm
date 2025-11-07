# 📍 توثيق API لتتبع مواقع الموظفين

> نظام تتبع مواقع الموظفين من تطبيق الأندرويد إلى واجهة الويب

---

## 📌 نظرة عامة

هذا API يستقبل مواقع GPS من تطبيق الأندرويد ويحفظها في قاعدة البيانات لعرضها على الخريطة التفاعلية في واجهة الويب.

---

## 🔗 معلومات نقطة النهاية

| المعلومة | القيمة |
|---------|--------|
| **الرابط** | `https://YOUR_DOMAIN.replit.app/api/external/employee-location` |
| **الطريقة** | `POST` |
| **نوع المحتوى** | `application/json` |
| **المصادقة** | مفتاح API ثابت |

⚠️ **مهم**: استبدل `YOUR_DOMAIN` برابط تطبيقك الفعلي على Replit.

---

## 🔑 المصادقة

يتطلب API إرسال مفتاح API مع كل طلب:

```json
{
  "api_key": "test_location_key_2025"
}
```

⚠️ **ملاحظة**: هذا مفتاح تجريبي. سيتم تحديثه في الإنتاج.

---

## 📤 البيانات المطلوبة

### الحقول الإلزامية ✅

| الحقل | النوع | الوصف | مثال |
|-------|------|-------|------|
| `api_key` | String | مفتاح API للمصادقة | `"test_location_key_2025"` |
| `job_number` | String | الرقم الوظيفي للموظف | `"EMP001"` |
| `latitude` | Number | خط العرض (-90 إلى 90) | `24.7136` |
| `longitude` | Number | خط الطول (-180 إلى 180) | `46.6753` |

### الحقول الاختيارية ⭕

| الحقل | النوع | الوصف | مثال |
|-------|------|-------|------|
| `accuracy` | Number | دقة الموقع بالأمتار | `10.5` |
| `recorded_at` | String (ISO 8601) | وقت التسجيل | `"2025-11-07T10:30:00Z"` |
| `notes` | String | ملاحظات إضافية | `"موقع تلقائي"` |

### مثال كامل للطلب

```json
{
  "api_key": "test_location_key_2025",
  "job_number": "EMP001",
  "latitude": 24.7136,
  "longitude": 46.6753,
  "accuracy": 10.5,
  "recorded_at": "2025-11-07T10:30:00Z",
  "notes": "تحديث تلقائي كل 15 دقيقة"
}
```

---

## 📥 الاستجابات

### ✅ نجاح العملية (200 OK)

```json
{
  "success": true,
  "message": "تم حفظ الموقع بنجاح",
  "data": {
    "employee_name": "محمد أحمد",
    "location_id": 123,
    "recorded_at": "2025-11-07T10:30:00",
    "received_at": "2025-11-07T10:30:05"
  }
}
```

### ❌ أخطاء محتملة

#### 400 Bad Request - بيانات ناقصة أو خاطئة

```json
{
  "success": false,
  "error": "الإحداثيات (latitude, longitude) مطلوبة"
}
```

**أمثلة على رسائل الخطأ:**
- `"لا توجد بيانات في الطلب"`
- `"الرقم الوظيفي مطلوب"`
- `"latitude يجب أن يكون بين -90 و 90"`
- `"الإحداثيات يجب أن تكون أرقام صحيحة"`

#### 401 Unauthorized - مفتاح خاطئ

```json
{
  "success": false,
  "error": "مفتاح API غير صحيح"
}
```

#### 404 Not Found - موظف غير موجود

```json
{
  "success": false,
  "error": "لم يتم العثور على موظف بالرقم الوظيفي: EMP999"
}
```

#### 500 Internal Server Error - خطأ في الخادم

```json
{
  "success": false,
  "error": "حدث خطأ في الخادم"
}
```

---

## 💻 أمثلة عملية

### 📱 Android - Kotlin مع Retrofit

#### 1. إضافة المكتبات في `build.gradle`

```gradle
dependencies {
    implementation 'com.squareup.retrofit2:retrofit:2.9.0'
    implementation 'com.squareup.retrofit2:converter-gson:2.9.0'
    implementation 'com.google.android.gms:play-services-location:21.0.1'
}
```

#### 2. تعريف نموذج البيانات

```kotlin
data class LocationRequest(
    val api_key: String,
    val job_number: String,
    val latitude: Double,
    val longitude: Double,
    val accuracy: Double? = null,
    val recorded_at: String? = null,
    val notes: String? = null
)

data class LocationResponse(
    val success: Boolean,
    val message: String? = null,
    val error: String? = null,
    val data: LocationData? = null
)

data class LocationData(
    val employee_name: String,
    val location_id: Int,
    val recorded_at: String,
    val received_at: String
)
```

#### 3. تعريف واجهة API

```kotlin
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

interface LocationApiService {
    @POST("api/external/employee-location")
    suspend fun sendLocation(@Body request: LocationRequest): Response<LocationResponse>
}
```

#### 4. إنشاء مدير API

```kotlin
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object LocationApiManager {
    private const val BASE_URL = "https://YOUR_DOMAIN.replit.app/"
    private const val API_KEY = "test_location_key_2025"
    
    private val retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    private val api = retrofit.create(LocationApiService::class.java)
    
    suspend fun sendEmployeeLocation(
        jobNumber: String,
        latitude: Double,
        longitude: Double,
        accuracy: Float? = null
    ): Result<LocationResponse> {
        return try {
            val request = LocationRequest(
                api_key = API_KEY,
                job_number = jobNumber,
                latitude = latitude,
                longitude = longitude,
                accuracy = accuracy?.toDouble(),
                recorded_at = java.time.Instant.now().toString()
            )
            
            val response = api.sendLocation(request)
            
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("خطأ: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
```

#### 5. الاستخدام في Activity/Fragment

```kotlin
import android.Manifest
import android.content.pm.PackageManager
import androidx.core.app.ActivityCompat
import androidx.lifecycle.lifecycleScope
import com.google.android.gms.location.*
import kotlinx.coroutines.launch

class LocationTrackingActivity : AppCompatActivity() {
    
    private lateinit var fusedLocationClient: FusedLocationProviderClient
    private val jobNumber = "EMP001" // رقم الموظف
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)
        
        // طلب الأذونات
        if (checkLocationPermission()) {
            startLocationTracking()
        } else {
            requestLocationPermission()
        }
    }
    
    private fun startLocationTracking() {
        val locationRequest = LocationRequest.create().apply {
            interval = 15 * 60 * 1000 // كل 15 دقيقة
            fastestInterval = 5 * 60 * 1000 // أسرع تحديث: 5 دقائق
            priority = LocationRequest.PRIORITY_BALANCED_POWER_ACCURACY
        }
        
        val locationCallback = object : LocationCallback() {
            override fun onLocationResult(result: LocationResult) {
                result.lastLocation?.let { location ->
                    sendLocationToServer(
                        latitude = location.latitude,
                        longitude = location.longitude,
                        accuracy = location.accuracy
                    )
                }
            }
        }
        
        if (ActivityCompat.checkSelfPermission(
                this,
                Manifest.permission.ACCESS_FINE_LOCATION
            ) == PackageManager.PERMISSION_GRANTED
        ) {
            fusedLocationClient.requestLocationUpdates(
                locationRequest,
                locationCallback,
                null
            )
        }
    }
    
    private fun sendLocationToServer(
        latitude: Double,
        longitude: Double,
        accuracy: Float
    ) {
        lifecycleScope.launch {
            val result = LocationApiManager.sendEmployeeLocation(
                jobNumber = jobNumber,
                latitude = latitude,
                longitude = longitude,
                accuracy = accuracy
            )
            
            result.onSuccess { response ->
                println("✅ تم إرسال الموقع: ${response.message}")
            }
            
            result.onFailure { error ->
                println("❌ خطأ في الإرسال: ${error.message}")
            }
        }
    }
    
    private fun checkLocationPermission(): Boolean {
        return ActivityCompat.checkSelfPermission(
            this,
            Manifest.permission.ACCESS_FINE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED
    }
    
    private fun requestLocationPermission() {
        ActivityCompat.requestPermissions(
            this,
            arrayOf(Manifest.permission.ACCESS_FINE_LOCATION),
            1001
        )
    }
}
```

---

### 🌐 cURL - للاختبار السريع

```bash
curl -X POST \
  https://YOUR_DOMAIN.replit.app/api/external/employee-location \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "test_location_key_2025",
    "job_number": "EMP001",
    "latitude": 24.7136,
    "longitude": 46.6753,
    "accuracy": 10.5,
    "recorded_at": "2025-11-07T10:30:00Z"
  }'
```

---

### 🐍 Python - للاختبار

```python
import requests
from datetime import datetime

def send_location(job_number, latitude, longitude, accuracy=None):
    url = "https://YOUR_DOMAIN.replit.app/api/external/employee-location"
    
    data = {
        "api_key": "test_location_key_2025",
        "job_number": job_number,
        "latitude": latitude,
        "longitude": longitude,
        "recorded_at": datetime.utcnow().isoformat() + "Z"
    }
    
    if accuracy:
        data["accuracy"] = accuracy
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        print("✅ نجح:", response.json())
    else:
        print("❌ فشل:", response.json())

# الاستخدام
send_location("EMP001", 24.7136, 46.6753, 10.5)
```

---

## 🔧 نقطة اختبار

للتحقق من أن API يعمل:

```bash
curl https://YOUR_DOMAIN.replit.app/api/external/test
```

**الاستجابة المتوقعة:**

```json
{
  "success": true,
  "message": "External API is working!",
  "endpoints": {
    "employee_location": "/api/external/employee-location [POST]"
  }
}
```

---

## ⚙️ توصيات للتطوير

### 1️⃣ تكرار الإرسال
- ✅ أرسل الموقع كل 15-30 دقيقة (لتوفير البطارية)
- ✅ استخدم `WorkManager` للإرسال في الخلفية
- ✅ أوقف التتبع عند بطارية منخفضة (< 15%)

### 2️⃣ معالجة الأخطاء
- ✅ احفظ المواقع محلياً في قاعدة بيانات (Room)
- ✅ أعد المحاولة عند فشل الإرسال
- ✅ استخدم `ExponentialBackoff` للمحاولات المتكررة

### 3️⃣ تحسين الدقة
- ✅ استخدم `PRIORITY_BALANCED_POWER_ACCURACY`
- ✅ تجاهل المواقع ذات دقة ضعيفة (> 100 متر)
- ✅ لا ترسل إذا كان الموقع قديم (> 5 دقائق)

### 4️⃣ الأمان
- ✅ لا تحفظ مفتاح API في الكود مباشرة (استخدم BuildConfig)
- ✅ استخدم ProGuard/R8 لحماية الكود
- ✅ تحقق من شهادة SSL

### 5️⃣ تحسين الأداء
- ✅ استخدم Coroutines للعمليات غير المتزامنة
- ✅ قلل استهلاك البطارية بتقليل التحديثات
- ✅ أوقف التتبع عند عدم الحاجة

---

## 🔐 ملاحظات أمنية

> ⚠️ **تحذير**: هذا النظام للاستخدام التجريبي فقط

### التحسينات المطلوبة للإنتاج:

1. **تحديث مفتاح API** إلى مفتاح آمن ومشفر
2. **إضافة Rate Limiting** لمنع الإساءة
3. **IP Whitelisting** للأمان الإضافي
4. **Token-based Authentication** بدلاً من المفتاح الثابت
5. **SSL/TLS** للتشفير الكامل
6. **تسجيل محاولات الوصول** للمراقبة

---

## 📊 حالات الاستخدام

### 1. الإرسال التلقائي
يرسل التطبيق الموقع تلقائياً كل فترة محددة في الخلفية.

### 2. الإرسال عند الطلب  
الموظف يرسل موقعه يدوياً عند الحاجة (زر في التطبيق).

### 3. تتبع المسار
إرسال نقاط GPS متتالية لرسم مسار تحرك الموظف.

---

## 📞 استكشاف الأخطاء

### المشكلة: لا يعمل API

**الحلول:**
1. ✅ تحقق من صحة الرابط
2. ✅ تأكد من مفتاح API الصحيح
3. ✅ جرّب نقطة الاختبار `/api/external/test`

### المشكلة: خطأ 404 - موظف غير موجود

**الحلول:**
1. ✅ تأكد من أن الرقم الوظيفي موجود في قاعدة البيانات
2. ✅ تحقق من تطابق الرقم (حساس لحالة الأحرف)

### المشكلة: خطأ 401 - مفتاح خاطئ

**الحلول:**
1. ✅ تأكد من استخدام المفتاح الصحيح: `test_location_key_2025`
2. ✅ تحقق من إرسال `api_key` في JSON

---

## 📝 سجل التحديثات

| الإصدار | التاريخ | التغييرات |
|---------|---------|-----------|
| 1.0 | 07/11/2025 | الإصدار الأول - نظام تتبع أساسي |

---

## 📧 الدعم

للأسئلة والمساعدة، راجع الوثائق أو اتصل بفريق الدعم الفني.

---

**تم بواسطة**: نظام نُظم - إدارة شاملة للشركات السعودية 🇸🇦
