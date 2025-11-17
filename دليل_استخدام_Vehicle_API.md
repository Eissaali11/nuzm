# 📘 دليل الاستخدام التفصيلي - Vehicle API

## 📌 نظرة عامة

هذا الدليل يشرح بالتفصيل كيفية استخدام Vehicle API في التطبيق الخارجي (Flutter Mobile App) للحصول على معلومات السيارات والموظفين.

---

## 🔗 معلومات الاتصال الأساسية

### الرابط الأساسي (Base URL)
```
http://nuzum.site
```

### النطاقات البديلة
```
https://eissahr.replit.app  (للنسخة التجريبية)
```

---

## 📍 نقاط الوصول (API Endpoints)

### 1️⃣ الحصول على سيارة موظف معين

**الرابط:**
```
GET http://nuzum.site/api/employees/{employee_id}/vehicle
```

**المعاملات:**
- `employee_id` (مطلوب): رقم الموظف في قاعدة البيانات (مثل: 180)

**مثال على الطلب:**
```
GET http://nuzum.site/api/employees/180/vehicle
```

**الاستجابة الناجحة (200):**
```json
{
  "success": true,
  "employee": { /* معلومات الموظف */ },
  "vehicle": { /* معلومات السيارة */ },
  "handover_records": [ /* سجلات التسليم */ ],
  "handover_count": 4
}
```

---

### 2️⃣ الحصول على تفاصيل سيارة معينة

**الرابط:**
```
GET http://nuzum.site/api/vehicles/{vehicle_id}/details
```

**المعاملات:**
- `vehicle_id` (مطلوب): رقم السيارة في قاعدة البيانات (مثل: 10)

**مثال على الطلب:**
```
GET http://nuzum.site/api/vehicles/10/details
```

---

## 📦 البيانات المُرجعة بالتفصيل

### أ) معلومات الموظف (Employee)

| الحقل | النوع | الوصف | مثال |
|------|------|-------|------|
| `id` | Integer | رقم الموظف في النظام | 180 |
| `employee_id` | String | رقم الموظف الوظيفي | "1910" |
| `name` | String | الاسم الكامل | "HUSSAM AL DAIN" |
| `mobile` | String | رقم الجوال | "966591014696" |
| `mobile_personal` | String | رقم الجوال الشخصي | "966563960177" |
| `job_title` | String | المسمى الوظيفي | "courier" |
| `department` | String | القسم | "Aramex Courier" |

**مثال JSON:**
```json
{
  "id": 180,
  "employee_id": "1910",
  "name": "HUSSAM AL DAIN",
  "mobile": "966591014696",
  "mobile_personal": "966563960177",
  "job_title": "courier",
  "department": "Aramex Courier"
}
```

---

### ب) معلومات السيارة (Vehicle)

#### المعلومات الأساسية:

| الحقل | النوع | الوصف | مثال |
|------|------|-------|------|
| `id` | Integer | رقم السيارة في النظام | 10 |
| `plate_number` | String | رقم اللوحة | "3189-ب س ن" |
| `make` | String | الشركة المصنعة | "نيسان" |
| `model` | String | الموديل | "ارفان" |
| `year` | Integer | سنة الصنع | 2021 |
| `color` | String | اللون | "برند ارامكس" |
| `type_of_car` | String | نوع السيارة | "باص" |
| `status` | String | الحالة (إنجليزي) | "in_project" |
| `status_arabic` | String | الحالة (عربي) | "نشطة مع سائق" |
| `driver_name` | String | اسم السائق الحالي | "HUSSAM AL DAIN" |
| `project` | String | المشروع | "Aramex Coruer" |

#### التواريخ المهمة (Expiry Dates):

| الحقل | النوع | الوصف | مثال |
|------|------|-------|------|
| `authorization_expiry_date` | String | **تاريخ انتهاء التفويض** | "2026-02-16" |
| `registration_expiry_date` | String | **تاريخ انتهاء الاستمارة** | "2026-10-07" |
| `inspection_expiry_date` | String | **تاريخ انتهاء الفحص الدوري** | "2026-07-10" |

#### الصور والمستندات:

| الحقل | النوع | الوصف |
|------|------|-------|
| `registration_form_image` | String (URL) | **رابط صورة الاستمارة** |
| `insurance_file` | String (URL) | **رابط ملف التأمين (PDF)** |
| `license_image` | String (URL) | رابط صورة الرخصة |
| `plate_image` | String (URL) | رابط صورة اللوحة |
| `drive_folder_link` | String (URL) | رابط مجلد Google Drive |

**مثال روابط الصور:**
```json
{
  "registration_form_image": "http://nuzum.site/static/uploads/vehicles/registration.jpg",
  "insurance_file": "http://nuzum.site/static/uploads/vehicles/insurance.pdf",
  "license_image": "http://nuzum.site/static/uploads/vehicles/license.jpg"
}
```

---

### ج) سجلات التسليم/الاستلام (Handover Records)

كل سجل يحتوي على:

#### المعلومات الأساسية:

| الحقل | النوع | الوصف | القيم الممكنة |
|------|------|-------|---------------|
| `id` | Integer | رقم السجل | 196 |
| `handover_type` | String | نوع العملية | "delivery" / "receipt" |
| `handover_type_arabic` | String | نوع العملية بالعربية | "تسليم" / "استلام" |
| `handover_date` | String | تاريخ العملية | "2025-10-15" |
| `handover_time` | String | وقت العملية | "14:02" |
| `mileage` | Integer | عداد الكيلومترات | 150000 |
| `fuel_level` | String | مستوى الوقود | "1/2", "ممتلئ", "فارغ" |

#### معلومات الأشخاص:

| الحقل | الوصف |
|------|-------|
| `person_name` | اسم المستلم/المسلم |
| `supervisor_name` | اسم المشرف |
| `city` | المدينة |
| `project_name` | اسم المشروع |

#### الروابط والمستندات:

| الحقل | النوع | الوصف | **مهم** |
|------|------|-------|---------|
| `form_link` | String (URL) | رابط نموذج Adobe للتعديل | ⭐ |
| `pdf_link` | String (URL) | **رابط PDF لعرض النموذج مباشرة** | ⭐⭐⭐ |
| `driver_signature` | String (URL) | رابط توقيع السائق | ✅ |
| `supervisor_signature` | String (URL) | رابط توقيع المشرف | ✅ |
| `damage_diagram` | String (URL) | رابط مخطط الأضرار | ✅ |

**مثال:**
```json
{
  "form_link": "https://acrobat.adobe.com/id/urn:aaid:sc:AP:41ee8126...",
  "pdf_link": "http://nuzum.site/vehicles/handover/196/pdf/public",
  "driver_signature": "http://nuzum.site/static/signatures/xxx.png",
  "supervisor_signature": "http://nuzum.site/static/signatures/yyy.png",
  "damage_diagram": "http://nuzum.site/static/diagrams/zzz.png"
}
```

#### قائمة الفحص (Checklist):

جميع الحقول من نوع Boolean (true/false):

**الأغراض المتوفرة** (يجب أن تكون true):
- `spare_tire` - إطار احتياطي ✓
- `fire_extinguisher` - طفاية حريق ✓
- `first_aid_kit` - حقيبة إسعافات أولية ✓
- `warning_triangle` - مثلث تحذير ✓
- `tools` - عدة أدوات ✓

**المشاكل الفنية** (يجب أن تكون false):
- `oil_leaks` - تسريب زيت ✗
- `gear_issue` - مشكلة في الجير ✗
- `clutch_issue` - مشكلة في الكلتش ✗
- `engine_issue` - مشكلة في المحرك ✗
- `windows_issue` - مشكلة في الشبابيك ✗
- `tires_issue` - مشكلة في الإطارات ✗
- `body_issue` - مشكلة في الهيكل ✗
- `electricity_issue` - مشكلة كهربائية ✗
- `lights_issue` - مشكلة في الإضاءة ✗
- `ac_issue` - مشكلة في المكيف ✗

**مثال JSON:**
```json
{
  "checklist": {
    "spare_tire": true,
    "fire_extinguisher": true,
    "first_aid_kit": true,
    "warning_triangle": true,
    "tools": true,
    "oil_leaks": false,
    "gear_issue": false,
    "engine_issue": false,
    "ac_issue": false
  }
}
```

#### صور السيارة (Images):

مصفوفة من الصور، كل صورة تحتوي على:

| الحقل | النوع | الوصف |
|------|------|-------|
| `id` | Integer | رقم الصورة |
| `url` | String (URL) | رابط الصورة الكامل |
| `uploaded_at` | String | تاريخ ووقت الرفع |

**مثال:**
```json
{
  "images": [
    {
      "id": 1768,
      "url": "http://nuzum.site/static/uploads/handover/image1.jpg",
      "uploaded_at": "2025-10-15 12:47:42"
    },
    {
      "id": 1769,
      "url": "http://nuzum.site/static/uploads/handover/image2.jpg",
      "uploaded_at": "2025-10-15 12:47:42"
    }
  ]
}
```

---

## 💻 أمثلة كود Flutter كاملة

### 1️⃣ إنشاء Service Class للتعامل مع API

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class VehicleApiService {
  // الرابط الأساسي
  static const String baseUrl = 'http://nuzum.site';
  
  /// جلب بيانات السيارة للموظف
  Future<Map<String, dynamic>> getEmployeeVehicle(int employeeId) async {
    try {
      final url = Uri.parse('$baseUrl/api/employees/$employeeId/vehicle');
      
      final response = await http.get(url);
      
      if (response.statusCode == 200) {
        // فك تشفير UTF-8 للنصوص العربية
        return json.decode(utf8.decode(response.bodyBytes));
      } else if (response.statusCode == 404) {
        throw Exception('الموظف غير موجود أو لا توجد سيارة مربوطة به');
      } else {
        throw Exception('خطأ في الاتصال بالخادم: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('فشل الاتصال بالخادم: $e');
    }
  }
  
  /// جلب تفاصيل السيارة بواسطة ID
  Future<Map<String, dynamic>> getVehicleDetails(int vehicleId) async {
    try {
      final url = Uri.parse('$baseUrl/api/vehicles/$vehicleId/details');
      
      final response = await http.get(url);
      
      if (response.statusCode == 200) {
        return json.decode(utf8.decode(response.bodyBytes));
      } else if (response.statusCode == 404) {
        throw Exception('السيارة غير موجودة');
      } else {
        throw Exception('خطأ في الاتصال بالخادم: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('فشل الاتصال بالخادم: $e');
    }
  }
}
```

---

### 2️⃣ إنشاء Model Classes

```dart
// نموذج الموظف
class Employee {
  final int id;
  final String employeeId;
  final String name;
  final String? mobile;
  final String? mobilePersonal;
  final String? jobTitle;
  final String? department;
  
  Employee({
    required this.id,
    required this.employeeId,
    required this.name,
    this.mobile,
    this.mobilePersonal,
    this.jobTitle,
    this.department,
  });
  
  factory Employee.fromJson(Map<String, dynamic> json) {
    return Employee(
      id: json['id'],
      employeeId: json['employee_id'],
      name: json['name'],
      mobile: json['mobile'],
      mobilePersonal: json['mobile_personal'],
      jobTitle: json['job_title'],
      department: json['department'],
    );
  }
}

// نموذج السيارة
class Vehicle {
  final int id;
  final String plateNumber;
  final String make;
  final String model;
  final int year;
  final String? color;
  final String? typeOfCar;
  final String status;
  final String statusArabic;
  final String? driverName;
  final String? project;
  
  // التواريخ المهمة
  final String? authorizationExpiryDate;
  final String? registrationExpiryDate;
  final String? inspectionExpiryDate;
  
  // الصور والمستندات
  final String? registrationFormImage;
  final String? insuranceFile;
  final String? licenseImage;
  final String? plateImage;
  
  Vehicle({
    required this.id,
    required this.plateNumber,
    required this.make,
    required this.model,
    required this.year,
    required this.status,
    required this.statusArabic,
    this.color,
    this.typeOfCar,
    this.driverName,
    this.project,
    this.authorizationExpiryDate,
    this.registrationExpiryDate,
    this.inspectionExpiryDate,
    this.registrationFormImage,
    this.insuranceFile,
    this.licenseImage,
    this.plateImage,
  });
  
  factory Vehicle.fromJson(Map<String, dynamic> json) {
    return Vehicle(
      id: json['id'],
      plateNumber: json['plate_number'],
      make: json['make'],
      model: json['model'],
      year: json['year'],
      status: json['status'],
      statusArabic: json['status_arabic'],
      color: json['color'],
      typeOfCar: json['type_of_car'],
      driverName: json['driver_name'],
      project: json['project'],
      authorizationExpiryDate: json['authorization_expiry_date'],
      registrationExpiryDate: json['registration_expiry_date'],
      inspectionExpiryDate: json['inspection_expiry_date'],
      registrationFormImage: json['registration_form_image'],
      insuranceFile: json['insurance_file'],
      licenseImage: json['license_image'],
      plateImage: json['plate_image'],
    );
  }
  
  // حساب الأيام المتبقية لتاريخ معين
  int? daysUntilExpiry(String? expiryDate) {
    if (expiryDate == null) return null;
    final expiry = DateTime.parse(expiryDate);
    final now = DateTime.now();
    return expiry.difference(now).inDays;
  }
}

// نموذج سجل التسليم/الاستلام
class HandoverRecord {
  final int id;
  final String handoverType;
  final String handoverTypeArabic;
  final String? handoverDate;
  final String? handoverTime;
  final int? mileage;
  final String? vehiclePlateNumber;
  final String? personName;
  final String? supervisorName;
  final String? fuelLevel;
  final String? formLink;
  final String? pdfLink;
  final String? driverSignature;
  final String? supervisorSignature;
  final String? damageDiagram;
  final Map<String, bool>? checklist;
  final List<HandoverImage> images;
  
  HandoverRecord({
    required this.id,
    required this.handoverType,
    required this.handoverTypeArabic,
    required this.images,
    this.handoverDate,
    this.handoverTime,
    this.mileage,
    this.vehiclePlateNumber,
    this.personName,
    this.supervisorName,
    this.fuelLevel,
    this.formLink,
    this.pdfLink,
    this.driverSignature,
    this.supervisorSignature,
    this.damageDiagram,
    this.checklist,
  });
  
  factory HandoverRecord.fromJson(Map<String, dynamic> json) {
    return HandoverRecord(
      id: json['id'],
      handoverType: json['handover_type'],
      handoverTypeArabic: json['handover_type_arabic'],
      handoverDate: json['handover_date'],
      handoverTime: json['handover_time'],
      mileage: json['mileage'],
      vehiclePlateNumber: json['vehicle_plate_number'],
      personName: json['person_name'],
      supervisorName: json['supervisor_name'],
      fuelLevel: json['fuel_level'],
      formLink: json['form_link'],
      pdfLink: json['pdf_link'],
      driverSignature: json['driver_signature'],
      supervisorSignature: json['supervisor_signature'],
      damageDiagram: json['damage_diagram'],
      checklist: json['checklist'] != null 
          ? Map<String, bool>.from(json['checklist'])
          : null,
      images: (json['images'] as List?)
          ?.map((img) => HandoverImage.fromJson(img))
          .toList() ?? [],
    );
  }
}

// نموذج صورة التسليم
class HandoverImage {
  final int id;
  final String url;
  final String? uploadedAt;
  
  HandoverImage({
    required this.id,
    required this.url,
    this.uploadedAt,
  });
  
  factory HandoverImage.fromJson(Map<String, dynamic> json) {
    return HandoverImage(
      id: json['id'],
      url: json['url'],
      uploadedAt: json['uploaded_at'],
    );
  }
}
```

---

### 3️⃣ صفحة عرض تفاصيل السيارة

```dart
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

class VehicleDetailsPage extends StatefulWidget {
  final int employeeId;
  
  const VehicleDetailsPage({Key? key, required this.employeeId}) : super(key: key);
  
  @override
  _VehicleDetailsPageState createState() => _VehicleDetailsPageState();
}

class _VehicleDetailsPageState extends State<VehicleDetailsPage> {
  final VehicleApiService _apiService = VehicleApiService();
  bool _isLoading = true;
  String? _error;
  
  Employee? _employee;
  Vehicle? _vehicle;
  List<HandoverRecord> _handoverRecords = [];
  
  @override
  void initState() {
    super.initState();
    _loadData();
  }
  
  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    
    try {
      final data = await _apiService.getEmployeeVehicle(widget.employeeId);
      
      setState(() {
        _employee = Employee.fromJson(data['employee']);
        _vehicle = Vehicle.fromJson(data['vehicle']);
        _handoverRecords = (data['handover_records'] as List)
            .map((record) => HandoverRecord.fromJson(record))
            .toList();
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('تفاصيل السيارة'),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: _loadData,
          ),
        ],
      ),
      body: _buildBody(),
    );
  }
  
  Widget _buildBody() {
    if (_isLoading) {
      return Center(child: CircularProgressIndicator());
    }
    
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 64, color: Colors.red),
            SizedBox(height: 16),
            Text(_error!, textAlign: TextAlign.center),
            SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadData,
              child: Text('إعادة المحاولة'),
            ),
          ],
        ),
      );
    }
    
    return SingleChildScrollView(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildEmployeeCard(),
          SizedBox(height: 16),
          _buildVehicleCard(),
          SizedBox(height: 16),
          _buildExpiryDatesCard(),
          SizedBox(height: 16),
          _buildHandoverRecordsSection(),
        ],
      ),
    );
  }
  
  // بطاقة معلومات الموظف
  Widget _buildEmployeeCard() {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'معلومات الموظف',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            Divider(),
            _buildInfoRow(Icons.person, 'الاسم', _employee!.name),
            _buildInfoRow(Icons.badge, 'الرقم الوظيفي', _employee!.employeeId),
            _buildInfoRow(Icons.phone, 'الجوال', _employee!.mobile ?? '-'),
            _buildInfoRow(Icons.work, 'الوظيفة', _employee!.jobTitle ?? '-'),
            _buildInfoRow(Icons.business, 'القسم', _employee!.department ?? '-'),
          ],
        ),
      ),
    );
  }
  
  // بطاقة معلومات السيارة
  Widget _buildVehicleCard() {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'معلومات السيارة',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            Divider(),
            _buildInfoRow(Icons.credit_card, 'رقم اللوحة', _vehicle!.plateNumber),
            _buildInfoRow(Icons.directions_car, 'النوع', '${_vehicle!.make} ${_vehicle!.model}'),
            _buildInfoRow(Icons.calendar_today, 'السنة', _vehicle!.year.toString()),
            _buildInfoRow(Icons.palette, 'اللون', _vehicle!.color ?? '-'),
            _buildInfoRow(Icons.flag, 'الحالة', _vehicle!.statusArabic),
            _buildInfoRow(Icons.person_pin, 'السائق', _vehicle!.driverName ?? '-'),
          ],
        ),
      ),
    );
  }
  
  // بطاقة تواريخ الانتهاء
  Widget _buildExpiryDatesCard() {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'تواريخ انتهاء الوثائق',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            Divider(),
            _buildExpiryDateTile(
              'التفويض',
              _vehicle!.authorizationExpiryDate,
              Icons.verified_user,
            ),
            _buildExpiryDateTile(
              'الفحص الدوري',
              _vehicle!.inspectionExpiryDate,
              Icons.build_circle,
            ),
            _buildExpiryDateTile(
              'الاستمارة',
              _vehicle!.registrationExpiryDate,
              Icons.description,
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildExpiryDateTile(String title, String? date, IconData icon) {
    if (date == null) {
      return ListTile(
        leading: Icon(icon, color: Colors.grey),
        title: Text(title),
        subtitle: Text('غير محدد'),
      );
    }
    
    final daysLeft = _vehicle!.daysUntilExpiry(date);
    Color badgeColor;
    
    if (daysLeft! < 30) {
      badgeColor = Colors.red;
    } else if (daysLeft < 90) {
      badgeColor = Colors.orange;
    } else {
      badgeColor = Colors.green;
    }
    
    return ListTile(
      leading: Icon(icon, color: badgeColor),
      title: Text(title),
      subtitle: Text(date),
      trailing: Container(
        padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: badgeColor,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Text(
          'بعد $daysLeft يوم',
          style: TextStyle(color: Colors.white, fontSize: 12),
        ),
      ),
    );
  }
  
  // قسم سجلات التسليم/الاستلام
  Widget _buildHandoverRecordsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'سجلات التسليم/الاستلام (${_handoverRecords.length})',
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
        ),
        SizedBox(height: 8),
        ListView.builder(
          shrinkWrap: true,
          physics: NeverScrollableScrollPhysics(),
          itemCount: _handoverRecords.length,
          itemBuilder: (context, index) {
            return _buildHandoverRecordCard(_handoverRecords[index]);
          },
        ),
      ],
    );
  }
  
  Widget _buildHandoverRecordCard(HandoverRecord record) {
    return Card(
      margin: EdgeInsets.only(bottom: 12),
      child: ExpansionTile(
        leading: Icon(
          record.handoverType == 'delivery' ? Icons.send : Icons.call_received,
          color: record.handoverType == 'delivery' ? Colors.blue : Colors.green,
        ),
        title: Text(record.handoverTypeArabic),
        subtitle: Text('${record.handoverDate} ${record.handoverTime ?? ''}'),
        children: [
          Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildInfoRow(Icons.person, 'المستلم/المسلم', record.personName ?? '-'),
                _buildInfoRow(Icons.supervisor_account, 'المشرف', record.supervisorName ?? '-'),
                _buildInfoRow(Icons.speed, 'الكيلومترات', record.mileage?.toString() ?? '-'),
                _buildInfoRow(Icons.local_gas_station, 'الوقود', record.fuelLevel ?? '-'),
                
                SizedBox(height: 16),
                
                // أزرار العرض
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    if (record.pdfLink != null)
                      ElevatedButton.icon(
                        onPressed: () => _openUrl(record.pdfLink!),
                        icon: Icon(Icons.picture_as_pdf),
                        label: Text('عرض PDF'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.red,
                        ),
                      ),
                    if (record.formLink != null)
                      ElevatedButton.icon(
                        onPressed: () => _openUrl(record.formLink!),
                        icon: Icon(Icons.edit),
                        label: Text('نموذج Adobe'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.blue,
                        ),
                      ),
                  ],
                ),
                
                // عرض الصور
                if (record.images.isNotEmpty) ...[
                  SizedBox(height: 16),
                  Text(
                    'صور السيارة (${record.images.length})',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 8),
                  GridView.builder(
                    shrinkWrap: true,
                    physics: NeverScrollableScrollPhysics(),
                    gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 3,
                      crossAxisSpacing: 8,
                      mainAxisSpacing: 8,
                    ),
                    itemCount: record.images.length,
                    itemBuilder: (context, index) {
                      return GestureDetector(
                        onTap: () => _showImageFullscreen(record.images[index].url),
                        child: Image.network(
                          record.images[index].url,
                          fit: BoxFit.cover,
                          loadingBuilder: (context, child, loadingProgress) {
                            if (loadingProgress == null) return child;
                            return Center(child: CircularProgressIndicator());
                          },
                          errorBuilder: (context, error, stackTrace) {
                            return Icon(Icons.error);
                          },
                        ),
                      );
                    },
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(icon, size: 20, color: Colors.grey[600]),
          SizedBox(width: 8),
          Text(
            '$label: ',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
  
  // فتح رابط URL
  Future<void> _openUrl(String url) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('لا يمكن فتح الرابط')),
      );
    }
  }
  
  // عرض الصورة بملء الشاشة
  void _showImageFullscreen(String imageUrl) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => Scaffold(
          appBar: AppBar(
            backgroundColor: Colors.black,
            iconTheme: IconThemeData(color: Colors.white),
          ),
          body: Center(
            child: InteractiveViewer(
              child: Image.network(imageUrl),
            ),
          ),
          backgroundColor: Colors.black,
        ),
      ),
    );
  }
}
```

---

## ⚠️ معالجة الأخطاء

### أنواع الأخطاء المتوقعة:

| كود الخطأ | الوصف | كيفية المعالجة |
|----------|-------|----------------|
| 200 | نجح الطلب | عرض البيانات |
| 404 | غير موجود | عرض رسالة "الموظف/السيارة غير موجود" |
| 500 | خطأ في الخادم | عرض "حدث خطأ، يرجى المحاولة لاحقاً" |
| Timeout | انتهت مهلة الاتصال | عرض "تحقق من الاتصال بالإنترنت" |

**مثال على معالجة الأخطاء:**
```dart
try {
  final data = await apiService.getEmployeeVehicle(employeeId);
  // عرض البيانات
} on SocketException {
  showError('لا يوجد اتصال بالإنترنت');
} on TimeoutException {
  showError('انتهت مهلة الاتصال');
} on HttpException {
  showError('خطأ في الاتصال بالخادم');
} catch (e) {
  showError('حدث خطأ غير متوقع: $e');
}
```

---

## 📱 Dependencies المطلوبة في pubspec.yaml

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0              # للاتصال بالـ API
  url_launcher: ^6.2.1      # لفتح روابط PDF و Adobe
```

---

## ✅ نصائح وأفضل الممارسات

### 1. التخزين المؤقت (Caching)
```dart
// حفظ البيانات محلياً لتقليل استدعاءات API
final prefs = await SharedPreferences.getInstance();
prefs.setString('vehicle_data_$employeeId', jsonEncode(data));
```

### 2. Loading States
```dart
// عرض حالة التحميل بشكل واضح
if (_isLoading) {
  return Center(
    child: Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        CircularProgressIndicator(),
        SizedBox(height: 16),
        Text('جاري تحميل البيانات...'),
      ],
    ),
  );
}
```

### 3. معالجة الصور الكبيرة
```dart
// استخدام cached_network_image للأداء الأفضل
CachedNetworkImage(
  imageUrl: imageUrl,
  placeholder: (context, url) => CircularProgressIndicator(),
  errorWidget: (context, url, error) => Icon(Icons.error),
)
```

### 4. التحقق من القيم الفارغة
```dart
// دائماً تحقق من null قبل الاستخدام
final expiryDate = vehicle.authorizationExpiryDate;
if (expiryDate != null && expiryDate.isNotEmpty) {
  // استخدم التاريخ
}
```

---

## 🔐 الأمان

### ملاحظات مهمة:
1. **لا تخزن بيانات حساسة** في SharedPreferences بدون تشفير
2. **استخدم HTTPS** في الإنتاج بدلاً من HTTP
3. **أضف مصادقة** (Authentication) للـ API في المستقبل
4. **تحقق من الأذونات** قبل فتح الروابط الخارجية

---

## 📞 الدعم الفني

للمساعدة أو الإبلاغ عن مشاكل:
- تحقق من حالة الخادم: `http://nuzum.site`
- راجع سجلات الأخطاء (Error Logs)
- تواصل مع فريق التطوير

---

## 📌 ملاحظات نهائية

1. ✅ جميع الروابط تستخدم `http://nuzum.site` كافتراضي
2. ✅ الصور والملفات متاحة مباشرة عبر الروابط
3. ✅ رابط PDF (`pdf_link`) جاهز للعرض الفوري
4. ✅ النصوص العربية مُرمزة بـ UTF-8 بشكل صحيح
5. ✅ جميع التواريخ بصيغة ISO (YYYY-MM-DD)

---

**تم بحمد الله** ✨
آخر تحديث: نوفمبر 2025
