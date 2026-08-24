import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiClient {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  Future<bool> hasAccessToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token') != null;
  }

  Future<String?> _accessToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token');
  }

  Future<void> login(String username, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/login/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'username': username, 'password': password}),
    );

    if (response.statusCode != 200) {
      throw Exception('Usuario o contraseña incorrectos');
    }

    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', body['access'] as String);
    await prefs.setString('refresh_token', body['refresh'] as String);
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
    await prefs.remove('refresh_token');
  }

  Future<Map<String, dynamic>> profile() async {
    final response = await _get('/api/mobile/me/');
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> attendanceHistory() async {
    final response = await _get('/api/mobile/asistencias/');
    return jsonDecode(response.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> checkIn({
    required DateTime deviceDateTime,
    required double latitude,
    required double longitude,
    required double gpsAccuracy,
    required File employeePhoto,
    File? environmentPhoto,
    String deviceId = '',
  }) {
    return _sendAttendance(
      path: '/api/mobile/asistencia/entrada/',
      deviceDateTime: deviceDateTime,
      latitude: latitude,
      longitude: longitude,
      gpsAccuracy: gpsAccuracy,
      employeePhoto: employeePhoto,
      environmentPhoto: environmentPhoto,
      deviceId: deviceId,
    );
  }

  Future<Map<String, dynamic>> checkOut({
    required DateTime deviceDateTime,
    required double latitude,
    required double longitude,
    required double gpsAccuracy,
    required File employeePhoto,
    File? environmentPhoto,
    String deviceId = '',
  }) {
    return _sendAttendance(
      path: '/api/mobile/asistencia/salida/',
      deviceDateTime: deviceDateTime,
      latitude: latitude,
      longitude: longitude,
      gpsAccuracy: gpsAccuracy,
      employeePhoto: employeePhoto,
      environmentPhoto: environmentPhoto,
      deviceId: deviceId,
    );
  }

  Future<http.Response> _get(String path) async {
    final token = await _accessToken();
    final response = await http.get(
      Uri.parse('$baseUrl$path'),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode >= 400) {
      throw Exception(response.body);
    }
    return response;
  }

  Future<Map<String, dynamic>> _sendAttendance({
    required String path,
    required DateTime deviceDateTime,
    required double latitude,
    required double longitude,
    required double gpsAccuracy,
    required File employeePhoto,
    File? environmentPhoto,
    String deviceId = '',
  }) async {
    final token = await _accessToken();
    final request = http.MultipartRequest('POST', Uri.parse('$baseUrl$path'));
    request.headers['Authorization'] = 'Bearer $token';
    request.fields['device_datetime'] = deviceDateTime.toIso8601String();
    request.fields['latitude'] = latitude.toStringAsFixed(8);
    request.fields['longitude'] = longitude.toStringAsFixed(8);
    request.fields['gps_accuracy'] = gpsAccuracy.toStringAsFixed(2);
    request.fields['device_id'] = deviceId;
    request.files.add(await http.MultipartFile.fromPath('employee_photo', employeePhoto.path));
    if (environmentPhoto != null) {
      request.files.add(await http.MultipartFile.fromPath('environment_photo', environmentPhoto.path));
    }

    final streamed = await request.send();
    final response = await http.Response.fromStream(streamed);
    if (response.statusCode >= 400) {
      throw Exception(response.body);
    }
    return jsonDecode(response.body) as Map<String, dynamic>;
  }
}
