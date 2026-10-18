import 'package:dio/dio.dart';

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;

  late final Dio dio;
  String? _token;
  int? userId;
  void Function()? onUnauthorized;
  String? roleCode;
  static const apiBaseUrl = String.fromEnvironment('API_BASE_URL');

  ApiClient._internal() {
    dio = Dio(
      BaseOptions(
        baseUrl: apiBaseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 15),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          if (_token != null && _token!.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $_token';
          }
          return handler.next(options);
        },
        onError: (DioException e, handler) {
          if (e.response?.statusCode == 401) {
            clearToken();
            onUnauthorized?.call();
          }
          // 统一错误处理与弱网映射
          return handler.next(e);
        },
      ),
    );
  }

  void setToken(String token, int id, String role) {
    _token = token;
    userId = id;
    roleCode = role;
  }

  void clearToken() {
    _token = null;
    userId = null;
    roleCode = null;
  }
}
