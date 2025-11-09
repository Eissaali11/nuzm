# دليل ربط Flutter مع API نظام نُظم

## 📱 إعداد المشروع

### 1. إضافة Dependencies في `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  dio: ^5.3.3
  flutter_secure_storage: ^9.0.0
  provider: ^6.1.0
  intl: ^0.18.1
```

---

## 🔧 إعداد API Client

### ملف: `lib/services/api_service.dart`

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  // استخدم الرابط الفعلي للـ API
  static const String baseUrl = 'https://eissahr.replit.app';
  final storage = const FlutterSecureStorage();

  // حفظ التوكن
  Future<void> saveToken(String token) async {
    await storage.write(key: 'jwt_token', value: token);
  }

  // جلب التوكن
  Future<String?> getToken() async {
    return await storage.read(key: 'jwt_token');
  }

  // حذف التوكن (تسجيل الخروج)
  Future<void> deleteToken() async {
    await storage.delete(key: 'jwt_token');
  }

  // Headers مع التوكن
  Future<Map<String, String>> getHeaders() async {
    final token = await getToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  // تسجيل الدخول
  Future<Map<String, dynamic>?> login(String employeeId, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'employee_id': employeeId,
          'password': password,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        if (data['success']) {
          await saveToken(data['token']);
          return data;
        }
      }
      return null;
    } catch (e) {
      print('Login error: $e');
      return null;
    }
  }

  // جلب قائمة الطلبات
  Future<List<dynamic>> getRequests({
    int page = 1,
    int perPage = 20,
    String? status,
    String? type,
  }) async {
    try {
      final headers = await getHeaders();
      
      String queryParams = '?page=$page&per_page=$perPage';
      if (status != null) queryParams += '&status=$status';
      if (type != null) queryParams += '&type=$type';

      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/requests$queryParams'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        return data['requests'] ?? [];
      }
      return [];
    } catch (e) {
      print('Get requests error: $e');
      return [];
    }
  }

  // جلب تفاصيل طلب معين
  Future<Map<String, dynamic>?> getRequestDetails(int requestId) async {
    try {
      final headers = await getHeaders();
      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/requests/$requestId'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        return data['request'];
      }
      return null;
    } catch (e) {
      print('Get request details error: $e');
      return null;
    }
  }

  // إنشاء طلب جديد
  Future<int?> createRequest(Map<String, dynamic> requestData) async {
    try {
      final headers = await getHeaders();
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/requests'),
        headers: headers,
        body: jsonEncode(requestData),
      );

      if (response.statusCode == 201) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        return data['request_id'];
      }
      return null;
    } catch (e) {
      print('Create request error: $e');
      return null;
    }
  }

  // جلب أنواع الطلبات
  Future<List<dynamic>> getRequestTypes() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/requests/types'),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        return data['types'] ?? [];
      }
      return [];
    } catch (e) {
      print('Get request types error: $e');
      return [];
    }
  }

  // جلب الإحصائيات
  Future<Map<String, dynamic>?> getStatistics() async {
    try {
      final headers = await getHeaders();
      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/requests/statistics'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        return data['statistics'];
      }
      return null;
    } catch (e) {
      print('Get statistics error: $e');
      return null;
    }
  }

  // جلب السيارات
  Future<List<dynamic>> getVehicles() async {
    try {
      final headers = await getHeaders();
      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/vehicles'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        return data['vehicles'] ?? [];
      }
      return [];
    } catch (e) {
      print('Get vehicles error: $e');
      return [];
    }
  }

  // جلب الإشعارات
  Future<Map<String, dynamic>?> getNotifications({
    bool unreadOnly = false,
    int page = 1,
  }) async {
    try {
      final headers = await getHeaders();
      final queryParams = '?unread_only=$unreadOnly&page=$page';
      
      final response = await http.get(
        Uri.parse('$baseUrl/api/v1/notifications$queryParams'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        return jsonDecode(utf8.decode(response.bodyBytes));
      }
      return null;
    } catch (e) {
      print('Get notifications error: $e');
      return null;
    }
  }

  // تعليم إشعار كمقروء
  Future<bool> markNotificationAsRead(int notificationId) async {
    try {
      final headers = await getHeaders();
      final response = await http.put(
        Uri.parse('$baseUrl/api/v1/notifications/$notificationId/read'),
        headers: headers,
      );

      return response.statusCode == 200;
    } catch (e) {
      print('Mark notification error: $e');
      return false;
    }
  }
}
```

---

## 🔐 صفحة تسجيل الدخول

### ملف: `lib/screens/login_screen.dart`

```dart
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _employeeIdController = TextEditingController();
  final _passwordController = TextEditingController();
  final _apiService = ApiService();
  bool _isLoading = false;

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    final result = await _apiService.login(
      _employeeIdController.text.trim(),
      _passwordController.text,
    );

    setState(() => _isLoading = false);

    if (result != null && result['success']) {
      if (!mounted) return;
      Navigator.pushReplacementNamed(context, '/home');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('تم تسجيل الدخول بنجاح')),
      );
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('خطأ في البيانات، حاول مرة أخرى')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.business, size: 80, color: Colors.blue),
                  const SizedBox(height: 24),
                  const Text(
                    'نظام نُظم',
                    style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 48),
                  
                  // رقم الموظف
                  TextFormField(
                    controller: _employeeIdController,
                    decoration: const InputDecoration(
                      labelText: 'رقم الموظف',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.person),
                    ),
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return 'الرجاء إدخال رقم الموظف';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 16),
                  
                  // كلمة المرور
                  TextFormField(
                    controller: _passwordController,
                    obscureText: true,
                    decoration: const InputDecoration(
                      labelText: 'كلمة المرور',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.lock),
                    ),
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return 'الرجاء إدخال كلمة المرور';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 24),
                  
                  // زر الدخول
                  SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: ElevatedButton(
                      onPressed: _isLoading ? null : _login,
                      child: _isLoading
                          ? const CircularProgressIndicator(color: Colors.white)
                          : const Text('تسجيل الدخول', style: TextStyle(fontSize: 18)),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _employeeIdController.dispose();
    _passwordController.dispose();
    super.dispose();
  }
}
```

---

## 📋 صفحة قائمة الطلبات

### ملف: `lib/screens/requests_list_screen.dart`

```dart
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class RequestsListScreen extends StatefulWidget {
  const RequestsListScreen({Key? key}) : super(key: key);

  @override
  State<RequestsListScreen> createState() => _RequestsListScreenState();
}

class _RequestsListScreenState extends State<RequestsListScreen> {
  final _apiService = ApiService();
  List<dynamic> _requests = [];
  bool _isLoading = true;
  String? _selectedStatus;

  @override
  void initState() {
    super.initState();
    _loadRequests();
  }

  Future<void> _loadRequests() async {
    setState(() => _isLoading = true);
    
    final requests = await _apiService.getRequests(
      status: _selectedStatus,
    );
    
    setState(() {
      _requests = requests;
      _isLoading = false;
    });
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'PENDING':
        return Colors.orange;
      case 'APPROVED':
        return Colors.green;
      case 'REJECTED':
        return Colors.red;
      case 'COMPLETED':
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('الطلبات'),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.filter_list),
            onSelected: (value) {
              setState(() {
                _selectedStatus = value == 'ALL' ? null : value;
              });
              _loadRequests();
            },
            itemBuilder: (context) => [
              const PopupMenuItem(value: 'ALL', child: Text('الكل')),
              const PopupMenuItem(value: 'PENDING', child: Text('قيد الانتظار')),
              const PopupMenuItem(value: 'APPROVED', child: Text('موافق عليه')),
              const PopupMenuItem(value: 'REJECTED', child: Text('مرفوض')),
              const PopupMenuItem(value: 'COMPLETED', child: Text('مكتمل')),
            ],
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadRequests,
              child: _requests.isEmpty
                  ? const Center(child: Text('لا توجد طلبات'))
                  : ListView.builder(
                      padding: const EdgeInsets.all(8),
                      itemCount: _requests.length,
                      itemBuilder: (context, index) {
                        final request = _requests[index];
                        return Card(
                          margin: const EdgeInsets.symmetric(vertical: 8),
                          child: ListTile(
                            title: Text(request['title'] ?? 'بدون عنوان'),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const SizedBox(height: 4),
                                Text(request['type_display'] ?? ''),
                                if (request['amount'] != null)
                                  Text('المبلغ: ${request['amount']} ر.س'),
                              ],
                            ),
                            trailing: Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12,
                                vertical: 6,
                              ),
                              decoration: BoxDecoration(
                                color: _getStatusColor(request['status']),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                request['status_display'] ?? '',
                                style: const TextStyle(color: Colors.white),
                              ),
                            ),
                            onTap: () {
                              Navigator.pushNamed(
                                context,
                                '/request-details',
                                arguments: request['id'],
                              );
                            },
                          ),
                        );
                      },
                    ),
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.pushNamed(context, '/create-request').then((_) {
            _loadRequests();
          });
        },
        child: const Icon(Icons.add),
      ),
    );
  }
}
```

---

## ➕ صفحة إنشاء طلب

### ملف: `lib/screens/create_request_screen.dart`

```dart
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class CreateRequestScreen extends StatefulWidget {
  const CreateRequestScreen({Key? key}) : super(key: key);

  @override
  State<CreateRequestScreen> createState() => _CreateRequestScreenState();
}

class _CreateRequestScreenState extends State<CreateRequestScreen> {
  final _formKey = GlobalKey<FormState>();
  final _apiService = ApiService();
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _amountController = TextEditingController();
  
  List<dynamic> _requestTypes = [];
  String? _selectedType;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadRequestTypes();
  }

  Future<void> _loadRequestTypes() async {
    final types = await _apiService.getRequestTypes();
    setState(() {
      _requestTypes = types;
    });
  }

  Future<void> _submitRequest() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedType == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('الرجاء اختيار نوع الطلب')),
      );
      return;
    }

    setState(() => _isLoading = true);

    final requestData = {
      'type': _selectedType,
      'title': _titleController.text.trim(),
      'description': _descriptionController.text.trim(),
      'amount': double.tryParse(_amountController.text) ?? 0.0,
      'details': {},
    };

    final requestId = await _apiService.createRequest(requestData);

    setState(() => _isLoading = false);

    if (requestId != null) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('تم إنشاء الطلب بنجاح')),
      );
      Navigator.pop(context);
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('حدث خطأ، حاول مرة أخرى')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('طلب جديد'),
      ),
      body: _requestTypes.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // نوع الطلب
                    DropdownButtonFormField<String>(
                      decoration: const InputDecoration(
                        labelText: 'نوع الطلب',
                        border: OutlineInputBorder(),
                      ),
                      value: _selectedType,
                      items: _requestTypes.map((type) {
                        return DropdownMenuItem<String>(
                          value: type['value'],
                          child: Text(type['label_ar']),
                        );
                      }).toList(),
                      onChanged: (value) {
                        setState(() => _selectedType = value);
                      },
                      validator: (value) {
                        if (value == null) return 'الرجاء اختيار نوع الطلب';
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),
                    
                    // العنوان
                    TextFormField(
                      controller: _titleController,
                      decoration: const InputDecoration(
                        labelText: 'العنوان',
                        border: OutlineInputBorder(),
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'الرجاء إدخال العنوان';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),
                    
                    // الوصف
                    TextFormField(
                      controller: _descriptionController,
                      decoration: const InputDecoration(
                        labelText: 'الوصف',
                        border: OutlineInputBorder(),
                      ),
                      maxLines: 4,
                    ),
                    const SizedBox(height: 16),
                    
                    // المبلغ
                    TextFormField(
                      controller: _amountController,
                      decoration: const InputDecoration(
                        labelText: 'المبلغ (ر.س)',
                        border: OutlineInputBorder(),
                      ),
                      keyboardType: TextInputType.number,
                    ),
                    const SizedBox(height: 24),
                    
                    // زر الإرسال
                    SizedBox(
                      height: 50,
                      child: ElevatedButton(
                        onPressed: _isLoading ? null : _submitRequest,
                        child: _isLoading
                            ? const CircularProgressIndicator(color: Colors.white)
                            : const Text('إرسال الطلب', style: TextStyle(fontSize: 18)),
                      ),
                    ),
                  ],
                ),
              ),
            ),
    );
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    _amountController.dispose();
    super.dispose();
  }
}
```

---

## 📤 رفع الملفات (Dio)

### ملف: `lib/services/file_upload_service.dart`

```dart
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class FileUploadService {
  static const String baseUrl = 'https://eissahr.replit.app';
  final dio = Dio();
  final storage = const FlutterSecureStorage();

  Future<Map<String, dynamic>?> uploadFiles(
    int requestId,
    List<File> files,
  ) async {
    try {
      final token = await storage.read(key: 'jwt_token');
      if (token == null) return null;

      List<MultipartFile> multipartFiles = [];
      for (var file in files) {
        multipartFiles.add(
          await MultipartFile.fromFile(
            file.path,
            filename: file.path.split('/').last,
          ),
        );
      }

      FormData formData = FormData.fromMap({
        'files': multipartFiles,
      });

      final response = await dio.post(
        '$baseUrl/api/v1/requests/$requestId/upload',
        data: formData,
        options: Options(
          headers: {
            'Authorization': 'Bearer $token',
          },
        ),
        onSendProgress: (sent, total) {
          print('Upload progress: ${(sent / total * 100).toStringAsFixed(0)}%');
        },
      );

      if (response.statusCode == 200) {
        return response.data;
      }
      return null;
    } catch (e) {
      print('Upload error: $e');
      return null;
    }
  }
}
```

---

## 🎨 الصفحة الرئيسية مع الإحصائيات

### ملف: `lib/screens/home_screen.dart`

```dart
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _apiService = ApiService();
  Map<String, dynamic>? _statistics;
  int _unreadNotifications = 0;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    
    final stats = await _apiService.getStatistics();
    final notifications = await _apiService.getNotifications(unreadOnly: true);
    
    setState(() {
      _statistics = stats;
      _unreadNotifications = notifications?['unread_count'] ?? 0;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('نظام نُظم'),
        actions: [
          Stack(
            children: [
              IconButton(
                icon: const Icon(Icons.notifications),
                onPressed: () {
                  Navigator.pushNamed(context, '/notifications');
                },
              ),
              if (_unreadNotifications > 0)
                Positioned(
                  right: 8,
                  top: 8,
                  child: Container(
                    padding: const EdgeInsets.all(4),
                    decoration: const BoxDecoration(
                      color: Colors.red,
                      shape: BoxShape.circle,
                    ),
                    child: Text(
                      '$_unreadNotifications',
                      style: const TextStyle(color: Colors.white, fontSize: 10),
                    ),
                  ),
                ),
            ],
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadData,
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'الإحصائيات',
                      style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 16),
                    
                    GridView.count(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      crossAxisCount: 2,
                      mainAxisSpacing: 16,
                      crossAxisSpacing: 16,
                      children: [
                        _buildStatCard(
                          'الكل',
                          _statistics?['total'] ?? 0,
                          Colors.blue,
                          Icons.list_alt,
                        ),
                        _buildStatCard(
                          'قيد الانتظار',
                          _statistics?['pending'] ?? 0,
                          Colors.orange,
                          Icons.pending,
                        ),
                        _buildStatCard(
                          'موافق عليه',
                          _statistics?['approved'] ?? 0,
                          Colors.green,
                          Icons.check_circle,
                        ),
                        _buildStatCard(
                          'مرفوض',
                          _statistics?['rejected'] ?? 0,
                          Colors.red,
                          Icons.cancel,
                        ),
                      ],
                    ),
                    
                    const SizedBox(height: 24),
                    
                    ElevatedButton.icon(
                      onPressed: () {
                        Navigator.pushNamed(context, '/requests');
                      },
                      icon: const Icon(Icons.list),
                      label: const Text('عرض جميع الطلبات'),
                      style: ElevatedButton.styleFrom(
                        minimumSize: const Size(double.infinity, 50),
                      ),
                    ),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildStatCard(String title, int count, Color color, IconData icon) {
    return Card(
      elevation: 4,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 40, color: color),
            const SizedBox(height: 8),
            Text(
              '$count',
              style: TextStyle(
                fontSize: 32,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            Text(title, style: const TextStyle(fontSize: 16)),
          ],
        ),
      ),
    );
  }
}
```

---

## 🚀 الاستخدام السريع

### في `main.dart`:

```dart
import 'package:flutter/material.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/requests_list_screen.dart';
import 'screens/create_request_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'نظام نُظم',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        fontFamily: 'Cairo', // تأكد من إضافة خط عربي
      ),
      initialRoute: '/login',
      routes: {
        '/login': (context) => const LoginScreen(),
        '/home': (context) => const HomeScreen(),
        '/requests': (context) => const RequestsListScreen(),
        '/create-request': (context) => const CreateRequestScreen(),
      },
    );
  }
}
```

---

## ✅ نصائح مهمة

1. **تغيير الرابط**: استبدل `https://eissahr.replit.app` بالرابط الفعلي بعد النشر
2. **معالجة الأخطاء**: أضف try-catch في جميع استدعاءات الـ API
3. **التوكن**: يتم حفظه بشكل آمن في Flutter Secure Storage
4. **رفع الملفات**: استخدم dio للملفات الكبيرة (حتى 500MB)
5. **Refresh**: استخدم RefreshIndicator لسحب الصفحة للتحديث

---

## 📞 اختبار الربط

```dart
// اختبار سريع
void testApi() async {
  final api = ApiService();
  
  // تسجيل دخول
  final result = await api.login('EMP001', 'password123');
  print('Login: $result');
  
  // جلب الطلبات
  final requests = await api.getRequests();
  print('Requests: ${requests.length}');
}
```

الآن التطبيق جاهز للربط مع API نظام نُظم! 🎉
