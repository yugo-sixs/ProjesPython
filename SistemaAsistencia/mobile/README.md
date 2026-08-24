# App móvil Flutter

Cliente inicial para registrar entrada, salida, ubicación GPS y fotografías.

## Completar estructura nativa

Si las carpetas `android/` e `ios/` están vacías, instala Flutter y ejecuta:

```bash
cd mobile
flutter create .
flutter pub get
```

## Ejecutar

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Notas:

- `10.0.2.2` apunta al host desde el emulador Android.
- En un teléfono físico usa la IP local de tu computadora, por ejemplo `http://192.168.1.20:8000`.
- El backend debe ejecutarse con `python manage.py runserver 0.0.0.0:8000`.

## Permisos Android

Agregar en `android/app/src/main/AndroidManifest.xml`:

```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
```

## Permisos iOS

Agregar en `ios/Runner/Info.plist`:

```xml
<key>NSCameraUsageDescription</key>
<string>La app necesita tomar fotografías para registrar asistencia.</string>
<key>NSLocationWhenInUseUsageDescription</key>
<string>La app necesita guardar la ubicación del registro de asistencia.</string>
```
