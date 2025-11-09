# دليل ربط تطبيق Flutter بنظام نُظم

## 📌 معلومات الاتصال الأساسية

### رابط API الرئيسي
```
https://d72f2aef-918c-4148-9723-15870f8c7cf6-00-2c1ygyxvqoldk.riker.replit.dev/api/external/employee-complete-profile
```

### رابط احتياطي (localhost للتطوير)
```
http://localhost:5000/api/external/employee-complete-profile
```

### مفتاح API
```
test_location_key_2025
```

---

## 🚀 طريقة الاستخدام

### 1️⃣ إضافة المكتبة المطلوبة في `pubspec.yaml`
```yaml
dependencies:
  http: ^1.1.0
```

ثم قم بتشغيل:
```bash
flutter pub get
```

---

## 💻 كود Flutter الجاهز للنسخ

### ملف `employee_api_service.dart`

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class EmployeeApiService {
  // الروابط
  static const String primaryUrl = 'https://d72f2aef-918c-4148-9723-15870f8c7cf6-00-2c1ygyxvqoldk.riker.replit.dev/api/external/employee-complete-profile';
  static const String backupUrl = 'http://localhost:5000/api/external/employee-complete-profile';
  static const String apiKey = 'test_location_key_2025';
  
  /// جلب بيانات الموظف الكاملة
  /// 
  /// [jobNumber] - رقم الموظف الوظيفي (مطلوب)
  /// [month] - الشهر للفلترة بصيغة YYYY-MM (اختياري)
  /// [startDate] - تاريخ البداية بصيغة YYYY-MM-DD (اختياري)
  /// [endDate] - تاريخ النهاية بصيغة YYYY-MM-DD (اختياري)
  static Future<Map<String, dynamic>> getEmployeeCompleteProfile({
    required String jobNumber,
    String? month,
    String? startDate,
    String? endDate,
  }) async {
    try {
      // بناء جسم الطلب
      final Map<String, dynamic> requestBody = {
        'api_key': apiKey,
        'job_number': jobNumber,
      };
      
      // إضافة الفلاتر إذا كانت موجودة
      if (month != null && month.isNotEmpty) {
        requestBody['month'] = month;
      }
      if (startDate != null && startDate.isNotEmpty) {
        requestBody['start_date'] = startDate;
      }
      if (endDate != null && endDate.isNotEmpty) {
        requestBody['end_date'] = endDate;
      }

      // إرسال الطلب
      final response = await http.post(
        Uri.parse(primaryUrl),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode(requestBody),
      ).timeout(
        const Duration(seconds: 30),
        onTimeout: () {
          throw Exception('انتهت مهلة الاتصال بالخادم');
        },
      );

      // معالجة الاستجابة
      if (response.statusCode == 200) {
        final Map<String, dynamic> data = jsonDecode(response.body);
        
        if (data['success'] == true) {
          return data['data'];
        } else {
          throw Exception(data['message'] ?? 'حدث خطأ غير معروف');
        }
      } else if (response.statusCode == 401) {
        throw Exception('مفتاح API غير صحيح');
      } else if (response.statusCode == 404) {
        throw Exception('الموظف غير موجود');
      } else {
        throw Exception('خطأ في الخادم: ${response.statusCode}');
      }
    } catch (e) {
      // محاولة الرابط الاحتياطي في حالة الفشل
      if (e.toString().contains('Failed host lookup') || 
          e.toString().contains('انتهت مهلة')) {
        return _tryBackupUrl(
          jobNumber: jobNumber,
          month: month,
          startDate: startDate,
          endDate: endDate,
        );
      }
      rethrow;
    }
  }

  /// محاولة الرابط الاحتياطي
  static Future<Map<String, dynamic>> _tryBackupUrl({
    required String jobNumber,
    String? month,
    String? startDate,
    String? endDate,
  }) async {
    final Map<String, dynamic> requestBody = {
      'api_key': apiKey,
      'job_number': jobNumber,
    };
    
    if (month != null) requestBody['month'] = month;
    if (startDate != null) requestBody['start_date'] = startDate;
    if (endDate != null) requestBody['end_date'] = endDate;

    final response = await http.post(
      Uri.parse(backupUrl),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(requestBody),
    ).timeout(const Duration(seconds: 30));

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      if (data['success'] == true) {
        return data['data'];
      }
    }
    throw Exception('فشل الاتصال بكلا الخادمين');
  }
}
```

---

## 📱 أمثلة الاستخدام

### مثال 1: جلب كل البيانات (بدون فلترة)
```dart
try {
  final employeeData = await EmployeeApiService.getEmployeeCompleteProfile(
    jobNumber: '5216',
  );
  
  print('اسم الموظف: ${employeeData['employee']['name']}');
  print('عدد سجلات الحضور: ${employeeData['attendance'].length}');
} catch (e) {
  print('خطأ: $e');
}
```

### مثال 2: جلب بيانات شهر محدد
```dart
try {
  final employeeData = await EmployeeApiService.getEmployeeCompleteProfile(
    jobNumber: '5216',
    month: '2025-11', // شهر نوفمبر 2025
  );
  
  print('الحضور في نوفمبر: ${employeeData['attendance'].length}');
} catch (e) {
  print('خطأ: $e');
}
```

### مثال 3: جلب بيانات مدى تاريخ محدد
```dart
try {
  final employeeData = await EmployeeApiService.getEmployeeCompleteProfile(
    jobNumber: '5216',
    startDate: '2025-10-01',
    endDate: '2025-10-31',
  );
  
  print('الحضور في أكتوبر: ${employeeData['attendance'].length}');
} catch (e) {
  print('خطأ: $e');
}
```

---

## 📊 هيكل البيانات المُرجعة

```dart
{
  "employee": {
    "job_number": "5216",
    "name": "باسل الفاتح",
    "national_id": "1234567890",
    "birth_date": "1990-01-01",
    "hire_date": "2020-01-01",
    "nationality": "Saudi",
    "department": "قسم تقنية المعلومات",
    "position": "مطور برمجيات",
    "phone": "+966501234567",
    "email": "basil@example.com",
    "is_driver": false,
    "photos": {
      "personal": "https://d72f2aef-918c-4148-9723-15870f8c7cf6-00-2c1ygyxvqoldk.riker.replit.dev/static/uploads/profile.jpg",
      "id": "https://d72f2aef-918c-4148-9723-15870f8c7cf6-00-2c1ygyxvqoldk.riker.replit.dev/static/uploads/national_id.jpg",
      "license": null
    }
  },
  
  "current_car": {
    "car_id": "123",
    "plate_number": "ABC-1234",
    "model": "Toyota Camry",
    "color": "White",
    "status": "available",
    "assigned_date": "2025-01-15"
  },
  
  "previous_cars": [
    {
      "car_id": "456",
      "plate_number": "XYZ-5678",
      "model": "Honda Accord",
      "unassigned_date": "2025-01-10"
    }
  ],
  
  "attendance": [
    {
      "date": "2025-11-08",
      "check_in": "08:00",
      "check_out": "17:00",
      "status": "present",
      "hours_worked": 9.0,
      "notes": null
    }
  ],
  
  "salaries": [
    {
      "salary_id": "SAL-2025-11",
      "month": "2025-11",
      "amount": 5000.0,
      "currency": "SAR",
      "status": "paid",
      "details": {
        "base_salary": 4000.0,
        "allowances": 800.0,
        "deductions": 200.0,
        "bonuses": 400.0
      }
    }
  ],
  
  "operations": [
    {
      "operation_id": "OP-789",
      "type": "delivery",
      "date": "2025-01-15T08:30:00",
      "car_plate_number": "ABC-1234",
      "status": "completed"
    }
  ],
  
  "statistics": {
    "attendance": {
      "total_days": 30,
      "present_days": 28,
      "absent_days": 2,
      "attendance_rate": 93.33
    },
    "salaries": {
      "total_amount": 60000.0,
      "average_amount": 5000.0
    },
    "cars": {
      "current_car": true,
      "total_cars": 3
    }
  }
}
```

---

## 🎯 كيفية الوصول للبيانات في Flutter

```dart
final data = await EmployeeApiService.getEmployeeCompleteProfile(
  jobNumber: '5216',
);

// معلومات الموظف
String employeeName = data['employee']['name'];
String department = data['employee']['department'];
bool isDriver = data['employee']['is_driver'];

// السيارة الحالية
if (data['current_car'] != null) {
  String plateNumber = data['current_car']['plate_number'];
  String carModel = data['current_car']['model'];
}

// سجلات الحضور
List attendanceRecords = data['attendance'];
for (var record in attendanceRecords) {
  String date = record['date'];
  String status = record['status'];
  double hoursWorked = record['hours_worked'];
}

// الإحصائيات
int totalDays = data['statistics']['attendance']['total_days'];
double attendanceRate = data['statistics']['attendance']['attendance_rate'];
double totalSalaries = data['statistics']['salaries']['total_amount'];
```

---

## ⚠️ معالجة الأخطاء

```dart
try {
  final data = await EmployeeApiService.getEmployeeCompleteProfile(
    jobNumber: jobNumber,
  );
  
  // استخدم البيانات هنا
  
} on Exception catch (e) {
  if (e.toString().contains('الموظف غير موجود')) {
    // عرض رسالة أن الموظف غير موجود
    showDialog(...);
  } else if (e.toString().contains('مفتاح API غير صحيح')) {
    // مشكلة في المصادقة
    showDialog(...);
  } else if (e.toString().contains('انتهت مهلة')) {
    // مشكلة في الاتصال بالإنترنت
    showDialog(...);
  } else {
    // خطأ عام
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('خطأ'),
        content: Text(e.toString()),
      ),
    );
  }
}
```

---

## 🔄 مثال كامل مع واجهة مستخدم

```dart
import 'package:flutter/material.dart';

class EmployeeProfileScreen extends StatefulWidget {
  final String jobNumber;
  
  const EmployeeProfileScreen({required this.jobNumber});

  @override
  State<EmployeeProfileScreen> createState() => _EmployeeProfileScreenState();
}

class _EmployeeProfileScreenState extends State<EmployeeProfileScreen> {
  Map<String, dynamic>? employeeData;
  bool isLoading = true;
  String? errorMessage;

  @override
  void initState() {
    super.initState();
    loadEmployeeData();
  }

  Future<void> loadEmployeeData() async {
    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final data = await EmployeeApiService.getEmployeeCompleteProfile(
        jobNumber: widget.jobNumber,
      );
      
      setState(() {
        employeeData = data;
        isLoading = false;
      });
    } catch (e) {
      setState(() {
        errorMessage = e.toString();
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return Scaffold(
        appBar: AppBar(title: Text('ملف الموظف')),
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (errorMessage != null) {
      return Scaffold(
        appBar: AppBar(title: Text('ملف الموظف')),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.error, size: 64, color: Colors.red),
              SizedBox(height: 16),
              Text(errorMessage!),
              SizedBox(height: 16),
              ElevatedButton(
                onPressed: loadEmployeeData,
                child: Text('إعادة المحاولة'),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(employeeData!['employee']['name']),
      ),
      body: RefreshIndicator(
        onRefresh: loadEmployeeData,
        child: ListView(
          padding: EdgeInsets.all(16),
          children: [
            // معلومات الموظف
            Card(
              child: ListTile(
                leading: CircleAvatar(
                  backgroundImage: employeeData!['employee']['photos']['personal'] != null
                    ? NetworkImage(employeeData!['employee']['photos']['personal'])
                    : null,
                  child: employeeData!['employee']['photos']['personal'] == null
                    ? Icon(Icons.person)
                    : null,
                ),
                title: Text(employeeData!['employee']['name']),
                subtitle: Text(employeeData!['employee']['position']),
              ),
            ),
            
            SizedBox(height: 16),
            
            // الإحصائيات
            Text('الإحصائيات', style: Theme.of(context).textTheme.titleLarge),
            SizedBox(height: 8),
            Card(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('نسبة الحضور:'),
                        Text('${employeeData!['statistics']['attendance']['attendance_rate']}%'),
                      ],
                    ),
                    Divider(),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('إجمالي الرواتب:'),
                        Text('${employeeData!['statistics']['salaries']['total_amount']} ريال'),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            
            SizedBox(height: 16),
            
            // سجلات الحضور
            Text('سجلات الحضور', style: Theme.of(context).textTheme.titleLarge),
            ...List.generate(
              employeeData!['attendance'].length,
              (index) {
                final record = employeeData!['attendance'][index];
                return ListTile(
                  title: Text(record['date']),
                  subtitle: Text('${record['check_in'] ?? '-'} → ${record['check_out'] ?? '-'}'),
                  trailing: Chip(
                    label: Text(record['status']),
                    backgroundColor: record['status'] == 'present' 
                      ? Colors.green 
                      : Colors.red,
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
```

---

## ✅ اختبار الاتصال

قبل البدء، يمكنك اختبار الـ API باستخدام:

```dart
void testConnection() async {
  try {
    final data = await EmployeeApiService.getEmployeeCompleteProfile(
      jobNumber: '5216', // رقم موظف للاختبار
    );
    print('✅ الاتصال ناجح!');
    print('اسم الموظف: ${data['employee']['name']}');
  } catch (e) {
    print('❌ فشل الاتصال: $e');
  }
}
```

---

## 📞 للدعم الفني

- **رابط API**: https://d72f2aef-918c-4148-9723-15870f8c7cf6-00-2c1ygyxvqoldk.riker.replit.dev
- **مفتاح API**: test_location_key_2025
- **نقطة النهاية**: /api/external/employee-complete-profile

**ملاحظة مهمة**: 
- جميع البيانات حقيقية وليست وهمية
- النظام جاهز للاستخدام الفوري
- تأكد من استخدام HTTPS وليس HTTP
- الدومين الحالي للتطوير هو المذكور أعلاه

🚀
