# App móvil Flutter

Cliente Flutter para registrar entrada, salida, ubicación GPS y fotografías desde Android e iOS.

## Completar estructura nativa

La estructura nativa Android/iOS ya está incluida. Ejecuta `flutter pub get` al clonar el proyecto.

## Ejecutar

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Notas:

- `10.0.2.2` apunta al host desde el emulador Android.
- En un teléfono físico usa la IP local de tu computadora, por ejemplo `http://192.168.1.20:8000`.
- El backend debe ejecutarse con `python manage.py runserver 0.0.0.0:8000`.
- Para iPhone físico configura una URL HTTPS válida; iOS bloquea HTTP por seguridad.
- En Android el acceso HTTP sólo queda permitido para compilaciones de depuración. Producción debe usar HTTPS.

Los permisos de cámara, ubicación e Internet ya están configurados en Android e iOS. La foto del empleado y el GPS son obligatorios; la foto del entorno se puede omitir.

## Preparación Android

Antes de generar el APK por primera vez, acepta las licencias del SDK con:

```bash
flutter doctor --android-licenses
```

En Android Studio abre **SDK Manager > SDK Tools** e instala **NDK (Side by side) 28.2.13676358**. Después genera el APK:

```bash
flutter build apk --debug --dart-define=API_BASE_URL=http://IP_DE_TU_SERVIDOR:8000
```

Para compilar y firmar iOS necesitas una Mac con Xcode y una cuenta de Apple Developer; los archivos del proyecto iOS ya están preparados.
