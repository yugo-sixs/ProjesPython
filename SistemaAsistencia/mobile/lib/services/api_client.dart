import 'dart:convert';
import 'dart:io';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

class ApiException implements Exception {
  const ApiException(this.message);
  final String message;
  @override
  String toString() => message;
}

class ApiClient {
  static const String baseUrl = String.fromEnvironment('API_BASE_URL',
      defaultValue: 'http://10.0.2.2:8000');
  static const _accessTokenKey = 'access_token';
  static const _refreshTokenKey = 'refresh_token';
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  Future<bool> hasAccessToken() async =>
      (await _storage.read(key: _accessTokenKey)) != null;
  Future<String?> _accessToken() => _storage.read(key: _accessTokenKey);

  Future<void> login(String username, String password) async {
    final response = await http.post(Uri.parse('$baseUrl/api/auth/login/'),
        headers: const {'Content-Type': 'application/json'},
        body: jsonEncode({'username': username, 'password': password}));
    if (response.statusCode != 200) {
      throw ApiException(
          _errorMessage(response, 'Usuario o contraseña incorrectos'));
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final access = body['access'] as String?;
    final refresh = body['refresh'] as String?;
    if (access == null || refresh == null) {
      throw const ApiException('El servidor no devolvió una sesión válida.');
    }
    await _storage.write(key: _accessTokenKey, value: access);
    await _storage.write(key: _refreshTokenKey, value: refresh);
  }

  Future<void> logout() => _storage.deleteAll();
  Future<Map<String, dynamic>> profile() async =>
      jsonDecode((await _get('/api/mobile/me/')).body) as Map<String, dynamic>;
  Future<List<dynamic>> attendanceHistory() async =>
      jsonDecode((await _get('/api/mobile/asistencias/')).body)
          as List<dynamic>;

  Future<Map<String, dynamic>> checkIn(
          {required DateTime deviceDateTime,
          required double latitude,
          required double longitude,
          required double gpsAccuracy,
          required File employeePhoto,
          File? environmentPhoto,
          String deviceId = ''}) =>
      _sendAttendance(
          path: '/api/mobile/asistencia/entrada/',
          deviceDateTime: deviceDateTime,
          latitude: latitude,
          longitude: longitude,
          gpsAccuracy: gpsAccuracy,
          employeePhoto: employeePhoto,
          environmentPhoto: environmentPhoto,
          deviceId: deviceId);
  Future<Map<String, dynamic>> checkOut(
          {required DateTime deviceDateTime,
          required double latitude,
          required double longitude,
          required double gpsAccuracy,
          required File employeePhoto,
          File? environmentPhoto,
          String deviceId = ''}) =>
      _sendAttendance(
          path: '/api/mobile/asistencia/salida/',
          deviceDateTime: deviceDateTime,
          latitude: latitude,
          longitude: longitude,
          gpsAccuracy: gpsAccuracy,
          employeePhoto: employeePhoto,
          environmentPhoto: environmentPhoto,
          deviceId: deviceId);

  Future<http.Response> _get(String path) async {
    var response = await _getWithToken(path, await _accessToken());
    if (response.statusCode == 401 && await _refreshAccessToken()) {
      response = await _getWithToken(path, await _accessToken());
    }
    _ensureSuccess(response);
    return response;
  }

  Future<http.Response> _getWithToken(String path, String? token) =>
      http.get(Uri.parse('$baseUrl$path'),
          headers: {'Authorization': 'Bearer ${token ?? ''}'});

  Future<Map<String, dynamic>> _sendAttendance(
      {required String path,
      required DateTime deviceDateTime,
      required double latitude,
      required double longitude,
      required double gpsAccuracy,
      required File employeePhoto,
      File? environmentPhoto,
      required String deviceId}) async {
    var response = await _sendMultipart(
        path,
        await _accessToken(),
        deviceDateTime,
        latitude,
        longitude,
        gpsAccuracy,
        employeePhoto,
        environmentPhoto,
        deviceId);
    if (response.statusCode == 401 && await _refreshAccessToken()) {
      response = await _sendMultipart(
          path,
          await _accessToken(),
          deviceDateTime,
          latitude,
          longitude,
          gpsAccuracy,
          employeePhoto,
          environmentPhoto,
          deviceId);
    }
    _ensureSuccess(response);
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<http.Response> _sendMultipart(
      String path,
      String? token,
      DateTime deviceDateTime,
      double latitude,
      double longitude,
      double gpsAccuracy,
      File employeePhoto,
      File? environmentPhoto,
      String deviceId) async {
    final request = http.MultipartRequest('POST', Uri.parse('$baseUrl$path'));
    request.headers['Authorization'] = 'Bearer ${token ?? ''}';
    request.fields.addAll({
      'device_datetime': deviceDateTime.toIso8601String(),
      'latitude': latitude.toStringAsFixed(8),
      'longitude': longitude.toStringAsFixed(8),
      'gps_accuracy': gpsAccuracy.toStringAsFixed(2),
      'device_id': deviceId
    });
    request.files.add(await http.MultipartFile.fromPath(
        'employee_photo', employeePhoto.path));
    if (environmentPhoto != null) {
      request.files.add(await http.MultipartFile.fromPath(
          'environment_photo', environmentPhoto.path));
    }
    return http.Response.fromStream(await request.send());
  }

  Future<bool> _refreshAccessToken() async {
    final refresh = await _storage.read(key: _refreshTokenKey);
    if (refresh == null) return false;
    final response = await http.post(Uri.parse('$baseUrl/api/auth/refresh/'),
        headers: const {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh': refresh}));
    if (response.statusCode != 200) {
      await logout();
      return false;
    }
    final access = (jsonDecode(response.body) as Map<String, dynamic>)['access']
        as String?;
    if (access == null) {
      await logout();
      return false;
    }
    await _storage.write(key: _accessTokenKey, value: access);
    return true;
  }

  void _ensureSuccess(http.Response response) {
    if (response.statusCode >= 400) {
      throw ApiException(_errorMessage(
          response, 'No fue posible comunicarse con el servidor.'));
    }
  }

  String _errorMessage(http.Response response, String fallback) {
    try {
      final body = jsonDecode(response.body);
      if (body is Map<String, dynamic>) {
        if (body['detail'] is String) return body['detail'] as String;
        for (final value in body.values) {
          if (value is List && value.isNotEmpty) return value.first.toString();
          if (value is String) return value;
        }
      }
    } catch (_) {}
    return fallback;
  }
}
