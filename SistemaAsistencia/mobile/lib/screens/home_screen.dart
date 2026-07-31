import 'dart:io';

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

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _loading = true);
    final profile = await widget.api.profile();
    final history = await widget.api.attendanceHistory();
    if (!mounted) return;
    setState(() {
      _profile = profile;
      _history = history;
      _loading = false;
    });
  }

  Future<Position> _currentPosition() async {
    final serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      throw Exception('Activa la ubicacion del telefono');
    }

    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied || permission == LocationPermission.deniedForever) {
      throw Exception('Permiso de ubicacion denegado');
    }

    return Geolocator.getCurrentPosition(desiredAccuracy: LocationAccuracy.high);
  }

  Future<File> _takePhoto(String message) async {
    final photo = await _picker.pickImage(source: ImageSource.camera, imageQuality: 80);
    if (photo == null) {
      throw Exception(message);
    }
    return File(photo.path);
  }

  Future<void> _register(bool checkIn) async {
    setState(() => _sending = true);
    try {
      final position = await _currentPosition();
      final employeePhoto = await _takePhoto('Falta la foto del empleado');
      final environmentPhoto = await _takePhoto('Falta la foto del entorno');

      if (checkIn) {
        await widget.api.checkIn(
          deviceDateTime: DateTime.now(),
          latitude: position.latitude,
          longitude: position.longitude,
          gpsAccuracy: position.accuracy,
          employeePhoto: employeePhoto,
          environmentPhoto: environmentPhoto,
        );
      } else {
        await widget.api.checkOut(
          deviceDateTime: DateTime.now(),
          latitude: position.latitude,
          longitude: position.longitude,
          gpsAccuracy: position.accuracy,
          employeePhoto: employeePhoto,
          environmentPhoto: environmentPhoto,
        );
      }
      await _loadData();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(checkIn ? 'Entrada registrada' : 'Salida registrada')),
      );
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error.toString())));
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  Future<void> _logout() async {
    await widget.api.logout();
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => LoginScreen(api: widget.api)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mi asistencia'),
        actions: [
          IconButton(onPressed: _logout, icon: const Icon(Icons.logout), tooltip: 'Salir'),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadData,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Text(
                    '${_profile?['first_name'] ?? ''} ${_profile?['last_name'] ?? ''}',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 4),
                  Text('${_profile?['department'] ?? ''} - ${_profile?['position'] ?? ''}'),
                  const SizedBox(height: 20),
                  Row(
                    children: [
                      Expanded(
                        child: FilledButton.icon(
                          onPressed: _sending ? null : () => _register(true),
                          icon: const Icon(Icons.login),
                          label: const Text('Entrada'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _sending ? null : () => _register(false),
                          icon: const Icon(Icons.logout),
                          label: const Text('Salida'),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  Text('Historial', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  for (final item in _history)
                    Card(
                      child: ListTile(
                        title: Text('${item['date']} - ${item['status'] ?? 'Sin estado'}'),
                        subtitle: Text('Entrada: ${item['check_in_time'] ?? '-'}  Salida: ${item['check_out_time'] ?? '-'}'),
                        trailing: Text('${item['total_hours']} h'),
                      ),
                    ),
                ],
              ),
            ),
    );
  }
}
