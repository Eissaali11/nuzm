// ════════════════════════════════════════════════════════════════════════════════
// 📍 خدمة API المُصححة - نظام نُظم
// ════════════════════════════════════════════════════════════════════════════════
//
// ✅ تم تصحيح الروابط من المؤقت إلى الدائم
// ❌ القديم: https://d72f2aef-918c-4148-9723-15870f8c7cf6-00-2c1ygyxvqoldk.riker.replit.dev
// ✅ الجديد: http://nuzum.site + https://eissahr.replit.app
//
// ════════════════════════════════════════════════════════════════════════════════

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';

// ════════════════════════════════════════════════════════════════════════════════
// تعطيل فحص SSL (للسماح بالاتصال)
// ════════════════════════════════════════════════════════════════════════════════

class MyHttpOverrides extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    return super.createHttpClient(context)
      ..badCertificateCallback =
          (X509Certificate cert, String host, int port) => true;
  }
}

// ════════════════════════════════════════════════════════════════════════════════
// 🔗 روابط API المُصححة
// ════════════════════════════════════════════════════════════════════════════════

class ApiConfig {
  // ❌ الرابط القديم (مؤقت - لا تستخدمه):
  // https://d72f2aef-918c-4148-9723-15870f8c7cf6-00-2c1ygyxvqoldk.riker.replit.dev
  
  // ✅ الدومين الدائم الأساسي
  static const String baseUrl = 'http://nuzum.site';
  
  // ✅ الدومين البديل (احتياطي)
  static const String backupUrl = 'https://eissahr.replit.app';
  
  // 🔑 مفتاح API
  static const String apiKey = 'test_location_key_2025';
  
  // ⏱️ مدة انتظار الطلب (ثواني)
  static const int requestTimeout = 30;
  
  // 📍 روابط نقاط النهاية (Endpoints)
  static String get locationEndpoint => '$baseUrl/api/external/employee-location';
  static String get locationEndpointBackup => '$backupUrl/api/external/employee-location';
  static String get testEndpoint => '$baseUrl/api/external/test';
  static String get testEndpointBackup => '$backupUrl/api/external/test';
}

// ════════════════════════════════════════════════════════════════════════════════
// خدمة API الرئيسية
// ════════════════════════════════════════════════════════════════════════════════

class ApiService {
  
  // ────────────────────────────────────────────────────────────────────────────
  // 🧪 اختبار الاتصال
  // ────────────────────────────────────────────────────────────────────────────
  
  static Future<bool> testConnection() async {
    try {
      debugPrint('🧪 [TEST] Testing connection to: ${ApiConfig.testEndpoint}');
      
      final response = await http
          .get(Uri.parse(ApiConfig.testEndpoint))
          .timeout(
            Duration(seconds: ApiConfig.requestTimeout),
            onTimeout: () {
              debugPrint('⏱️ [TEST] Timeout - trying backup...');
              throw TimeoutException('Timeout');
            },
          );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        debugPrint('✅ [TEST] Connection successful!');
        debugPrint('📡 Server message: ${data['message']}');
        return true;
      } else {
        debugPrint('❌ [TEST] Failed with status: ${response.statusCode}');
        return false;
      }
    } catch (e) {
      debugPrint('⚠️ [TEST] Primary failed: $e');
      
      // جرب الدومين البديل
      try {
        debugPrint('🔄 [TEST] Trying backup: ${ApiConfig.testEndpointBackup}');
        
        final response = await http
            .get(Uri.parse(ApiConfig.testEndpointBackup))
            .timeout(Duration(seconds: ApiConfig.requestTimeout));
        
        if (response.statusCode == 200) {
          debugPrint('✅ [TEST] Backup connection successful!');
          return true;
        }
      } catch (backupError) {
        debugPrint('❌ [TEST] Backup also failed: $backupError');
      }
      
      return false;
    }
  }
  
  // ────────────────────────────────────────────────────────────────────────────
  // 📤 إرسال الموقع
  // ────────────────────────────────────────────────────────────────────────────
  
  static Future<bool> sendLocation({
    required String apiKey,
    required String jobNumber,
    required double latitude,
    required double longitude,
    double? accuracy,
  }) async {
    try {
      // تنسيق الوقت
      final now = DateTime.now().toUtc();
      final formattedDate = DateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'").format(now);

      // بناء البيانات
      final body = {
        "api_key": apiKey,
        "job_number": jobNumber,
        "latitude": latitude,
        "longitude": longitude,
        "accuracy": accuracy,
        "recorded_at": formattedDate,
      };

      debugPrint('📤 [API] Sending location...');
      debugPrint('🌐 Endpoint: ${ApiConfig.locationEndpoint}');
      debugPrint('👤 Job Number: $jobNumber');
      debugPrint('📍 Coordinates: ($latitude, $longitude)');
      debugPrint('🎯 Accuracy: ${accuracy?.toStringAsFixed(1) ?? "N/A"}m');

      // إرسال الطلب
      final response = await http
          .post(
            Uri.parse(ApiConfig.locationEndpoint),
            headers: {'Content-Type': 'application/json; charset=UTF-8'},
            body: jsonEncode(body),
          )
          .timeout(
            Duration(seconds: ApiConfig.requestTimeout),
            onTimeout: () {
              debugPrint('⏱️ [API] Request timeout - trying backup...');
              throw TimeoutException('Request timeout');
            },
          );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        if (data['success'] == true) {
          debugPrint('✅ [API] Location sent successfully!');
          debugPrint('👤 Employee: ${data['data']?['employee_name']}');
          debugPrint('🆔 Location ID: ${data['data']?['location_id']}');
          return true;
        } else {
          debugPrint('❌ [API] Server error: ${data['error']}');
          return false;
        }
      } else {
        debugPrint('❌ [API] HTTP error: ${response.statusCode}');
        debugPrint('📄 Response: ${response.body}');
        return false;
      }
      
    } on TimeoutException catch (e) {
      debugPrint('⏱️ [API] Timeout: $e');
      
      // جرب الدومين البديل
      return await _sendLocationToBackup(
        apiKey: apiKey,
        jobNumber: jobNumber,
        latitude: latitude,
        longitude: longitude,
        accuracy: accuracy,
      );
      
    } on SocketException catch (e) {
      debugPrint('🌐 [API] Network error: $e');
      return false;
      
    } catch (e) {
      debugPrint('❌ [API] Unexpected error: $e');
      return false;
    }
  }
  
  // ────────────────────────────────────────────────────────────────────────────
  // 🔄 إرسال للدومين البديل
  // ────────────────────────────────────────────────────────────────────────────
  
  static Future<bool> _sendLocationToBackup({
    required String apiKey,
    required String jobNumber,
    required double latitude,
    required double longitude,
    double? accuracy,
  }) async {
    try {
      debugPrint('🔄 [BACKUP] Trying backup domain...');
      
      final now = DateTime.now().toUtc();
      final formattedDate = DateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'").format(now);

      final body = {
        "api_key": apiKey,
        "job_number": jobNumber,
        "latitude": latitude,
        "longitude": longitude,
        "accuracy": accuracy,
        "recorded_at": formattedDate,
      };

      final response = await http
          .post(
            Uri.parse(ApiConfig.locationEndpointBackup),
            headers: {'Content-Type': 'application/json; charset=UTF-8'},
            body: jsonEncode(body),
          )
          .timeout(Duration(seconds: ApiConfig.requestTimeout));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          debugPrint('✅ [BACKUP] Location sent successfully via backup!');
          return true;
        }
      }
      
      debugPrint('❌ [BACKUP] Backup also failed');
      return false;
      
    } catch (e) {
      debugPrint('❌ [BACKUP] Error: $e');
      return false;
    }
  }
}

// ════════════════════════════════════════════════════════════════════════════════
// 📋 نموذج مبسط للاستخدام
// ════════════════════════════════════════════════════════════════════════════════

class LocationExample {
  
  // مثال 1: اختبار الاتصال
  static Future<void> testApi() async {
    final isConnected = await ApiService.testConnection();
    
    if (isConnected) {
      print('✅ API متصل وجاهز');
    } else {
      print('❌ فشل الاتصال - تحقق من الإنترنت');
    }
  }
  
  // مثال 2: إرسال موقع
  static Future<void> sendCurrentLocation() async {
    final success = await ApiService.sendLocation(
      apiKey: ApiConfig.apiKey,
      jobNumber: 'EMP001',
      latitude: 24.7136,
      longitude: 46.6753,
      accuracy: 10.5,
    );
    
    if (success) {
      print('✅ تم إرسال الموقع بنجاح');
    } else {
      print('❌ فشل إرسال الموقع');
    }
  }
}

// ════════════════════════════════════════════════════════════════════════════════
// 📝 ملاحظات الاستخدام
// ════════════════════════════════════════════════════════════════════════════════

/*

✅ التصحيحات المطبقة:

1. الرابط المؤقت القديم (تم إزالته):
   ❌ https://d72f2aef-918c-4148-9723-15870f8c7cf6-00-2c1ygyxvqoldk.riker.replit.dev

2. الروابط الدائمة الجديدة (تم التطبيق):
   ✅ http://nuzum.site (الأساسي)
   ✅ https://eissahr.replit.app (البديل)

───────────────────────────────────────────────────────────────────────────────

📦 المكتبات المطلوبة في pubspec.yaml:

dependencies:
  http: ^1.1.0
  intl: ^0.18.0

───────────────────────────────────────────────────────────────────────────────

🚀 الاستخدام:

1. في main.dart:
   void main() {
     HttpOverrides.global = MyHttpOverrides();
     runApp(MyApp());
   }

2. اختبار الاتصال:
   await ApiService.testConnection();

3. إرسال موقع:
   await ApiService.sendLocation(
     apiKey: ApiConfig.apiKey,
     jobNumber: 'EMP001',
     latitude: position.latitude,
     longitude: position.longitude,
     accuracy: position.accuracy,
   );

───────────────────────────────────────────────────────────────────────────────

✨ المميزات:

• روابط دائمة ومستقرة
• دومين بديل احتياطي تلقائي
• معالجة أخطاء كاملة
• سجلات تفصيلية
• جاهز للاستخدام المباشر

───────────────────────────────────────────────────────────────────────────────

📞 اختبار الروابط:

• الأساسي: http://nuzum.site/api/external/test
• البديل: https://eissahr.replit.app/api/external/test

*/
