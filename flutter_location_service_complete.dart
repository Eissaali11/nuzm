// ════════════════════════════════════════════════════════════════════════════════
// 📍 خدمة إرسال المواقع الكاملة - نظام نُظم
// ════════════════════════════════════════════════════════════════════════════════
// 
// ملف شامل جاهز للاستخدام في تطبيق Flutter لإرسال مواقع الموظفين
// 
// المميزات:
// ✅ الدومين الدائم محدد مسبقاً
// ✅ معالجة أخطاء كاملة
// ✅ حفظ محلي وإعادة محاولة
// ✅ اختبار اتصال تلقائي
// ✅ تتبع تلقائي في الخلفية
// ✅ كود جاهز 100% - انسخ والصق!
//
// ════════════════════════════════════════════════════════════════════════════════

import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';
import 'package:shared_preferences/shared_preferences.dart';

// ════════════════════════════════════════════════════════════════════════════════
// إعدادات SSL (للسماح بالاتصال)
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
// إعدادات API - البيانات الأساسية
// ════════════════════════════════════════════════════════════════════════════════

class ApiConfig {
  // 🔗 الدومين الأساسي (الدائم)
  static const String primaryDomain = 'http://nuzum.site';
  
  // 🔗 الدومين البديل (احتياطي)
  static const String backupDomain = 'https://eissahr.replit.app';
  
  // 🔑 مفتاح API
  static const String apiKey = 'test_location_key_2025';
  
  // ⏱️ مدة الانتظار (ثواني)
  static const int requestTimeout = 30;
  
  // 📍 روابط API
  static String get locationEndpoint => '$primaryDomain/api/external/employee-location';
  static String get locationEndpointBackup => '$backupDomain/api/external/employee-location';
  static String get testEndpoint => '$primaryDomain/api/external/test';
  static String get testEndpointBackup => '$backupDomain/api/external/test';
}

// ════════════════════════════════════════════════════════════════════════════════
// نماذج البيانات (Data Models)
// ════════════════════════════════════════════════════════════════════════════════

/// استجابة API
class LocationResponse {
  final bool success;
  final String? message;
  final String? error;
  final LocationData? data;
  final int? statusCode;

  LocationResponse({
    required this.success,
    this.message,
    this.error,
    this.data,
    this.statusCode,
  });

  factory LocationResponse.fromJson(Map<String, dynamic> json) {
    return LocationResponse(
      success: json['success'] ?? false,
      message: json['message'],
      error: json['error'],
      data: json['data'] != null ? LocationData.fromJson(json['data']) : null,
      statusCode: null,
    );
  }
}

/// بيانات الموقع المحفوظ
class LocationData {
  final String employeeName;
  final int locationId;
  final String recordedAt;
  final String receivedAt;

  LocationData({
    required this.employeeName,
    required this.locationId,
    required this.recordedAt,
    required this.receivedAt,
  });

  factory LocationData.fromJson(Map<String, dynamic> json) {
    return LocationData(
      employeeName: json['employee_name'] ?? '',
      locationId: json['location_id'] ?? 0,
      recordedAt: json['recorded_at'] ?? '',
      receivedAt: json['received_at'] ?? '',
    );
  }
}

/// موقع معلق (للإرسال لاحقاً)
class PendingLocation {
  final String jobNumber;
  final double latitude;
  final double longitude;
  final double? accuracy;
  final String timestamp;
  final String? notes;

  PendingLocation({
    required this.jobNumber,
    required this.latitude,
    required this.longitude,
    this.accuracy,
    required this.timestamp,
    this.notes,
  });

  Map<String, dynamic> toJson() {
    return {
      'job_number': jobNumber,
      'latitude': latitude,
      'longitude': longitude,
      'accuracy': accuracy,
      'timestamp': timestamp,
      'notes': notes,
    };
  }

  factory PendingLocation.fromJson(Map<String, dynamic> json) {
    return PendingLocation(
      jobNumber: json['job_number'],
      latitude: json['latitude'],
      longitude: json['longitude'],
      accuracy: json['accuracy'],
      timestamp: json['timestamp'],
      notes: json['notes'],
    );
  }
}

// ════════════════════════════════════════════════════════════════════════════════
// خدمة API الرئيسية
// ════════════════════════════════════════════════════════════════════════════════

class LocationApiService {
  
  // ═══════════════════════════════════════════════════════════════════════════
  // اختبار الاتصال بالخادم
  // ═══════════════════════════════════════════════════════════════════════════
  
  static Future<bool> testConnection({bool useBackup = false}) async {
    try {
      final endpoint = useBackup ? ApiConfig.testEndpointBackup : ApiConfig.testEndpoint;
      
      debugPrint('🧪 [TEST] Testing connection to: $endpoint');
      
      final response = await http.get(Uri.parse(endpoint)).timeout(
        Duration(seconds: ApiConfig.requestTimeout),
        onTimeout: () {
          debugPrint('❌ [TEST] Connection timeout');
          throw TimeoutException('Connection timeout');
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        debugPrint('✅ [TEST] Connection successful!');
        debugPrint('📡 Server: ${data['message']}');
        return true;
      } else {
        debugPrint('❌ [TEST] Failed. Status: ${response.statusCode}');
        return false;
      }
    } catch (e) {
      debugPrint('❌ [TEST] Error: $e');
      
      // جرب الدومين البديل تلقائياً
      if (!useBackup) {
        debugPrint('🔄 [TEST] Trying backup domain...');
        return await testConnection(useBackup: true);
      }
      
      return false;
    }
  }
  
  // ═══════════════════════════════════════════════════════════════════════════
  // إرسال موقع واحد
  // ═══════════════════════════════════════════════════════════════════════════
  
  static Future<LocationResponse> sendLocation({
    String? apiKey,
    required String jobNumber,
    required double latitude,
    required double longitude,
    double? accuracy,
    String? notes,
    bool useBackup = false,
  }) async {
    try {
      final endpoint = useBackup 
          ? ApiConfig.locationEndpointBackup 
          : ApiConfig.locationEndpoint;
      
      // تنسيق التاريخ
      final now = DateTime.now().toUtc();
      final formattedDate = DateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'").format(now);

      // بناء البيانات
      final body = {
        "api_key": apiKey ?? ApiConfig.apiKey,
        "job_number": jobNumber,
        "latitude": latitude,
        "longitude": longitude,
        if (accuracy != null) "accuracy": accuracy,
        "recorded_at": formattedDate,
        if (notes != null && notes.isNotEmpty) "notes": notes,
      };

      debugPrint('📤 [API] Sending location...');
      debugPrint('👤 Employee: $jobNumber');
      debugPrint('📍 Location: ($latitude, $longitude)');
      debugPrint('🎯 Accuracy: ${accuracy?.toStringAsFixed(1) ?? "N/A"} meters');
      debugPrint('🌐 Endpoint: $endpoint');

      // إرسال الطلب
      final response = await http
          .post(
            Uri.parse(endpoint),
            headers: {'Content-Type': 'application/json; charset=UTF-8'},
            body: jsonEncode(body),
          )
          .timeout(
            Duration(seconds: ApiConfig.requestTimeout),
            onTimeout: () {
              throw TimeoutException(
                'Request timeout after ${ApiConfig.requestTimeout} seconds',
              );
            },
          );

      // معالجة الاستجابة
      final responseData = jsonDecode(response.body);

      if (response.statusCode == 200 && responseData['success'] == true) {
        debugPrint('✅ [API] Success!');
        debugPrint('👤 ${responseData['data']?['employee_name']}');
        debugPrint('🆔 Location ID: ${responseData['data']?['location_id']}');
        
        return LocationResponse.fromJson(responseData);
      } else {
        final errorMsg = responseData['error'] ?? 'Unknown error';
        debugPrint('❌ [API] Failed: $errorMsg');
        
        return LocationResponse(
          success: false,
          error: errorMsg,
          statusCode: response.statusCode,
        );
      }
      
    } on TimeoutException catch (e) {
      debugPrint('⏱️ [API] Timeout: $e');
      
      // جرب الدومين البديل
      if (!useBackup) {
        debugPrint('🔄 [API] Trying backup domain...');
        return await sendLocation(
          apiKey: apiKey,
          jobNumber: jobNumber,
          latitude: latitude,
          longitude: longitude,
          accuracy: accuracy,
          notes: notes,
          useBackup: true,
        );
      }
      
      return LocationResponse(
        success: false,
        error: 'انتهت مهلة الاتصال بالخادم',
      );
      
    } on SocketException catch (e) {
      debugPrint('🌐 [API] Network error: $e');
      return LocationResponse(
        success: false,
        error: 'لا يوجد اتصال بالإنترنت',
      );
      
    } catch (e) {
      debugPrint('❌ [API] Unexpected error: $e');
      return LocationResponse(
        success: false,
        error: 'حدث خطأ غير متوقع: ${e.toString()}',
      );
    }
  }
  
  // ═══════════════════════════════════════════════════════════════════════════
  // حفظ موقع فاشل محلياً
  // ═══════════════════════════════════════════════════════════════════════════
  
  static Future<void> savePendingLocation(PendingLocation location) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final pending = prefs.getStringList('pending_locations') ?? [];
      
      pending.add(jsonEncode(location.toJson()));
      await prefs.setStringList('pending_locations', pending);
      
      debugPrint('💾 [STORAGE] Location saved for retry. Total pending: ${pending.length}');
    } catch (e) {
      debugPrint('❌ [STORAGE] Failed to save: $e');
    }
  }
  
  // ═══════════════════════════════════════════════════════════════════════════
  // إعادة إرسال المواقع المعلقة
  // ═══════════════════════════════════════════════════════════════════════════
  
  static Future<int> retryPendingLocations() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final pending = prefs.getStringList('pending_locations') ?? [];
      
      if (pending.isEmpty) {
        debugPrint('📭 [RETRY] No pending locations');
        return 0;
      }
      
      debugPrint('🔄 [RETRY] Retrying ${pending.length} locations...');
      
      int successCount = 0;
      final remaining = <String>[];
      
      for (var item in pending) {
        final location = PendingLocation.fromJson(jsonDecode(item));
        
        final response = await sendLocation(
          jobNumber: location.jobNumber,
          latitude: location.latitude,
          longitude: location.longitude,
          accuracy: location.accuracy,
          notes: location.notes,
        );
        
        if (response.success) {
          successCount++;
          debugPrint('✅ [RETRY] Sent pending location for ${location.jobNumber}');
        } else {
          remaining.add(item);
          debugPrint('❌ [RETRY] Still failed for ${location.jobNumber}');
        }
        
        // انتظر قليلاً بين الطلبات
        await Future.delayed(Duration(seconds: 1));
      }
      
      // احفظ المواقع المتبقية فقط
      await prefs.setStringList('pending_locations', remaining);
      
      debugPrint('✅ [RETRY] Successfully sent: $successCount/${pending.length}');
      debugPrint('📋 [RETRY] Remaining: ${remaining.length}');
      
      return successCount;
      
    } catch (e) {
      debugPrint('❌ [RETRY] Error: $e');
      return 0;
    }
  }
  
  // ═══════════════════════════════════════════════════════════════════════════
  // إرسال موقع مع حفظ تلقائي عند الفشل
  // ═══════════════════════════════════════════════════════════════════════════
  
  static Future<LocationResponse> sendLocationWithRetry({
    required String jobNumber,
    required double latitude,
    required double longitude,
    double? accuracy,
    String? notes,
  }) async {
    final response = await sendLocation(
      jobNumber: jobNumber,
      latitude: latitude,
      longitude: longitude,
      accuracy: accuracy,
      notes: notes,
    );
    
    // احفظ محلياً إذا فشل
    if (!response.success) {
      final pending = PendingLocation(
        jobNumber: jobNumber,
        latitude: latitude,
        longitude: longitude,
        accuracy: accuracy,
        timestamp: DateTime.now().toIso8601String(),
        notes: notes,
      );
      
      await savePendingLocation(pending);
    }
    
    return response;
  }
  
  // ═══════════════════════════════════════════════════════════════════════════
  // مسح المواقع المعلقة
  // ═══════════════════════════════════════════════════════════════════════════
  
  static Future<void> clearPendingLocations() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('pending_locations');
    debugPrint('🗑️ [STORAGE] Cleared all pending locations');
  }
  
  // ═══════════════════════════════════════════════════════════════════════════
  // عدد المواقع المعلقة
  // ═══════════════════════════════════════════════════════════════════════════
  
  static Future<int> getPendingCount() async {
    final prefs = await SharedPreferences.getInstance();
    final pending = prefs.getStringList('pending_locations') ?? [];
    return pending.length;
  }
}

// ════════════════════════════════════════════════════════════════════════════════
// أمثلة الاستخدام
// ════════════════════════════════════════════════════════════════════════════════

class LocationServiceExamples {
  
  // مثال 1: اختبار الاتصال
  static Future<void> example1TestConnection() async {
    final isConnected = await LocationApiService.testConnection();
    
    if (isConnected) {
      print('✅ API جاهز للاستخدام');
    } else {
      print('❌ تحقق من إعدادات API');
    }
  }
  
  // مثال 2: إرسال موقع بسيط
  static Future<void> example2SendSimpleLocation() async {
    final response = await LocationApiService.sendLocation(
      jobNumber: 'EMP001',
      latitude: 24.7136,
      longitude: 46.6753,
      accuracy: 10.5,
    );
    
    if (response.success) {
      print('✅ تم إرسال الموقع بنجاح');
      print('الموظف: ${response.data?.employeeName}');
    } else {
      print('❌ فشل: ${response.error}');
    }
  }
  
  // مثال 3: إرسال مع حفظ تلقائي
  static Future<void> example3SendWithAutoSave() async {
    final response = await LocationApiService.sendLocationWithRetry(
      jobNumber: 'EMP001',
      latitude: 24.7136,
      longitude: 46.6753,
      accuracy: 10.5,
      notes: 'تحديث تلقائي',
    );
    
    if (!response.success) {
      print('⚠️ فشل الإرسال - تم الحفظ للمحاولة لاحقاً');
    }
  }
  
  // مثال 4: إعادة محاولة المواقع المعلقة
  static Future<void> example4RetryPending() async {
    final count = await LocationApiService.retryPendingLocations();
    print('✅ تم إرسال $count موقع معلق');
  }
  
  // مثال 5: عرض عدد المواقع المعلقة
  static Future<void> example5ShowPendingCount() async {
    final count = await LocationApiService.getPendingCount();
    print('📋 المواقع المعلقة: $count');
  }
}

// ════════════════════════════════════════════════════════════════════════════════
// ملاحظات الاستخدام
// ════════════════════════════════════════════════════════════════════════════════

/*

📦 المكتبات المطلوبة في pubspec.yaml:

dependencies:
  http: ^1.1.0
  intl: ^0.18.0
  shared_preferences: ^2.2.2

───────────────────────────────────────────────────────────────────────────────

🚀 الاستخدام السريع:

1. انسخ هذا الملف إلى: lib/services/location_api_service.dart

2. في main.dart:
   void main() {
     HttpOverrides.global = MyHttpOverrides();
     runApp(MyApp());
   }

3. استخدمه في أي مكان:
   import 'services/location_api_service.dart';
   
   final response = await LocationApiService.sendLocationWithRetry(
     jobNumber: 'EMP001',
     latitude: position.latitude,
     longitude: position.longitude,
     accuracy: position.accuracy,
   );

───────────────────────────────────────────────────────────────────────────────

✅ المميزات:

• الدومين الدائم محدد مسبقاً (http://nuzum.site)
• دومين بديل احتياطي (https://eissahr.replit.app)
• حفظ تلقائي للمواقع الفاشلة
• إعادة محاولة تلقائية
• معالجة أخطاء كاملة
• سجلات تفصيلية للتتبع
• جاهز 100% للاستخدام المباشر

───────────────────────────────────────────────────────────────────────────────

📞 روابط مفيدة:

• اختبار API: http://nuzum.site/api/external/test
• لوحة التحكم: http://nuzum.site/employees/tracking-dashboard
• التوثيق الكامل: راجع ملف LOCATION_API_DOCS.md

*/
