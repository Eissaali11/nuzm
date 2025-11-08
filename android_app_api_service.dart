import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';

class MyHttpOverrides extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    return super.createHttpClient(context)
      ..badCertificateCallback =
          (X509Certificate cert, String host, int port) => true;
  }
}

/// إعدادات API - قم بتعديل هذه القيم فقط
class ApiConfig {
  /// 🔗 الدومين الدائم للنظام
  /// الدومين الأساسي: http://nuzum.site
  /// الدومين البديل: https://eissahr.replit.app
  static const String baseUrl = 'http://nuzum.site';
  
  /// 🔑 مفتاح API - احصل عليه من لوحة التحكم
  /// الموقع: Secrets في Replit (LOCATION_API_KEY)
  static const String apiKey = 'test_location_key_2025';
  
  /// ⏱️ مدة انتظار الطلب (بالثواني)
  static const int requestTimeout = 30;
  
  /// 📍 الرابط الكامل لـ API
  static String get locationEndpoint => '$baseUrl/api/external/employee-location';
  
  /// 🧪 رابط الاختبار
  static String get testEndpoint => '$baseUrl/api/external/test';
}

/// خدمة API لإرسال مواقع الموظفين
class ApiService {
  
  /// اختبار الاتصال بالـ API
  static Future<bool> testConnection() async {
    try {
      final response = await http
          .get(Uri.parse(ApiConfig.testEndpoint))
          .timeout(
            Duration(seconds: ApiConfig.requestTimeout),
            onTimeout: () {
              debugPrint('❌ [API TEST] Request timeout');
              throw TimeoutException('Test timeout');
            },
          );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        debugPrint('✅ [API TEST] Connection successful!');
        debugPrint('📡 Server message: ${data['message']}');
        return true;
      } else {
        debugPrint('❌ [API TEST] Failed. Status: ${response.statusCode}');
        return false;
      }
    } catch (e) {
      debugPrint('❌ [API TEST] Error: $e');
      return false;
    }
  }
  
  /// إرسال موقع الموظف إلى الخادم
  /// 
  /// المعاملات:
  /// - [apiKey]: مفتاح API (اختياري، يُستخدم من ApiConfig تلقائياً)
  /// - [jobNumber]: الرقم الوظيفي للموظف (إلزامي)
  /// - [latitude]: خط العرض (إلزامي)
  /// - [longitude]: خط الطول (إلزامي)
  /// - [accuracy]: دقة الموقع بالأمتار (اختياري)
  /// - [notes]: ملاحظات إضافية (اختياري)
  static Future<LocationResponse> sendLocation({
    String? apiKey,
    required String jobNumber,
    required double latitude,
    required double longitude,
    double? accuracy,
    String? notes,
  }) async {
    try {
      // استخدام الوقت الحالي بتنسيق UTC
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

      debugPrint('📤 [API] Sending location for employee: $jobNumber');
      debugPrint('📍 Location: ($latitude, $longitude)');
      debugPrint('🎯 Accuracy: ${accuracy?.toStringAsFixed(1) ?? 'N/A'} meters');

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
              debugPrint('❌ [API] Request timeout after ${ApiConfig.requestTimeout} seconds');
              throw TimeoutException(
                'Request timeout',
                Duration(seconds: ApiConfig.requestTimeout),
              );
            },
          );

      // معالجة الاستجابة
      final responseData = jsonDecode(response.body);

      if (response.statusCode == 200 && responseData['success'] == true) {
        debugPrint('✅ [API] Location sent successfully!');
        debugPrint('👤 Employee: ${responseData['data']?['employee_name']}');
        debugPrint('🆔 Location ID: ${responseData['data']?['location_id']}');
        
        return LocationResponse(
          success: true,
          message: responseData['message'],
          data: responseData['data'] != null 
              ? LocationData.fromJson(responseData['data'])
              : null,
        );
      } else {
        final errorMsg = responseData['error'] ?? 'Unknown error';
        debugPrint('❌ [API] Failed: $errorMsg (Status: ${response.statusCode})');
        
        return LocationResponse(
          success: false,
          error: errorMsg,
          statusCode: response.statusCode,
        );
      }
    } on TimeoutException catch (e) {
      debugPrint('⏱️ [API] Timeout: $e');
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
}

/// نموذج الاستجابة من API
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
