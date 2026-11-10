import 'dart:io';

import 'package:device_info_plus/device_info_plus.dart';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';

import '../services/api_client.dart';
import 'login_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.api});
  final ApiClient api;
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ImagePicker _picker = ImagePicker();
  Map<String, dynamic>? _profile;
  List<dynamic> _history = [];
  bool _loading = true;
  bool _sending = false;
  String? _loadError;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _loading = true;
      _loadError = null;
    });
    try {
      final profile = await widget.api.profile();
      final history = await widget.api.attendanceHistory();
      if (!mounted) return;
      setState(() {
        _profile = profile;
        _history = history;
      });
    } catch (error) {
      if (!mounted) return;
      if (!await widget.api.hasAccessToken()) {
        if (!mounted) return;
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => LoginScreen(api: widget.api)),
        );
        return;
      }
      setState(() => _loadError = error.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<Position> _currentPosition() async {
    if (!await Geolocator.isLocationServiceEnabled()) {
      throw const ApiException(
          'Activa la ubicación del teléfono para registrar asistencia.');
    }
    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      throw const ApiException('El permiso de ubicación fue denegado.');
    }
    return Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.high,
      timeLimit: const Duration(seconds: 20),
    );
  }

  Future<File> _takeEmployeePhoto() async {
    final photo = await _picker.pickImage(
        source: ImageSource.camera,
        preferredCameraDevice: CameraDevice.front,
        imageQuality: 80);
    if (photo == null) {
      throw const ApiException('La foto del empleado es obligatoria.');
    }
    return File(photo.path);
  }

  Future<File?> _takeEnvironmentPhoto() async {
    final takePhoto = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Foto del entorno'),
        content: const Text(
            '¿Deseas capturar también el lugar donde se realiza el registro?'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Omitir')),
          FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Tomar foto')),
        ],
      ),
    );
    if (takePhoto != true) return null;
    final photo =
        await _picker.pickImage(source: ImageSource.camera, imageQuality: 80);
    return photo == null ? null : File(photo.path);
  }

  Future<String> _getDeviceId() async {
    final info = DeviceInfoPlugin();
    if (Platform.isAndroid) return (await info.androidInfo).id;
    if (Platform.isIOS) return (await info.iosInfo).identifierForVendor ?? '';
    return '';
  }

  Future<void> _register(bool checkIn) async {
    final capturedAt = DateTime.now();
    setState(() => _sending = true);
    try {
      final position = await _currentPosition();
      final employeePhoto = await _takeEmployeePhoto();
      if (!mounted) return;
      final environmentPhoto = await _takeEnvironmentPhoto();
      final deviceId = await _getDeviceId();
      final result = (
        deviceDateTime: capturedAt,
        latitude: position.latitude,
        longitude: position.longitude,
        gpsAccuracy: position.accuracy,
        employeePhoto: employeePhoto,
        environmentPhoto: environmentPhoto,
        deviceId: deviceId,
      );
      if (checkIn) {
        await widget.api.checkIn(
            deviceDateTime: result.deviceDateTime,
            latitude: result.latitude,
            longitude: result.longitude,
            gpsAccuracy: result.gpsAccuracy,
            employeePhoto: result.employeePhoto,
            environmentPhoto: result.environmentPhoto,
            deviceId: result.deviceId);
      } else {
        await widget.api.checkOut(
            deviceDateTime: result.deviceDateTime,
            latitude: result.latitude,
            longitude: result.longitude,
            gpsAccuracy: result.gpsAccuracy,
            employeePhoto: result.employeePhoto,
            environmentPhoto: result.environmentPhoto,
            deviceId: result.deviceId);
      }
      await _loadData();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content:
                Text(checkIn ? 'Entrada registrada.' : 'Salida registrada.')));
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(error.toString())));
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  Future<void> _logout() async {
    await widget.api.logout();
    if (mounted) {
      Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => LoginScreen(api: widget.api)));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mi asistencia'), actions: [
        IconButton(
            onPressed: _logout,
            icon: const Icon(Icons.logout),
            tooltip: 'Salir')
      ]),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _loadError != null
              ? _errorView()
              : _content(),
    );
  }

  Widget _errorView() => Center(
      child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Text(_loadError!, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton.icon(
                onPressed: _loadData,
                icon: const Icon(Icons.refresh),
                label: const Text('Reintentar'))
          ])));

  Widget _content() => RefreshIndicator(
        onRefresh: _loadData,
        child: ListView(padding: const EdgeInsets.all(16), children: [
          Text(
              '${_profile?['first_name'] ?? ''} ${_profile?['last_name'] ?? ''}',
              style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 4),
          Text(
              '${_profile?['department'] ?? ''} - ${_profile?['position'] ?? ''}'),
          const SizedBox(height: 20),
          Row(children: [
            Expanded(
                child: FilledButton.icon(
                    onPressed: _sending ? null : () => _register(true),
                    icon: const Icon(Icons.login),
                    label: const Text('Entrada'))),
            const SizedBox(width: 12),
            Expanded(
                child: OutlinedButton.icon(
                    onPressed: _sending ? null : () => _register(false),
                    icon: const Icon(Icons.logout),
                    label: const Text('Salida')))
          ]),
          if (_sending)
            const Padding(
                padding: EdgeInsets.only(top: 16),
                child: LinearProgressIndicator()),
          const SizedBox(height: 24),
          Text('Historial', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          for (final item in _history)
            Card(
                child: ListTile(
                    title: Text(
                        '${item['date']} - ${item['status_label'] ?? item['status'] ?? 'Sin estado'}'),
                    subtitle: Text(
                        'Entrada: ${item['check_in_time'] ?? '-'}  Salida: ${item['check_out_time'] ?? '-'}'),
                    trailing: Text('${item['total_hours']} h'))),
        ]),
      );
}
