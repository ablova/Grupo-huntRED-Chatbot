# Grupo huntRED® Mobile

Aplicación móvil de Grupo huntRED® que integra el contenido web existente con capacidades nativas.

## Requisitos Previos

- Flutter SDK (versión 3.0.0 o superior)
- Dart SDK (versión 3.0.0 o superior)
- Android Studio / Xcode (para desarrollo)
- Un editor de código (VS Code recomendado)

## Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/tu-usuario/huntred-mobile.git
cd huntred-mobile
```

2. Instala las dependencias:
```bash
flutter pub get
```

3. Configura el entorno de desarrollo:
```bash
flutter doctor
```

## Ejecución

1. Para ejecutar en modo desarrollo:
```bash
flutter run
```

2. Para ejecutar en modo release:
```bash
flutter run --release
```

## Estructura del Proyecto

```
lib/
  ├── core/
  │   ├── theme/
  │   └── config/
  ├── features/
  │   ├── home/
  │   ├── webview/
  │   └── auth/
  └── main.dart
```

## Características

- Integración con contenido web existente
- Navegación nativa con Material 3
- Tema claro/oscuro
- Efectos de cristal y animaciones
- Autenticación segura
- Almacenamiento local

## Desarrollo

1. Para crear un nuevo build:
```bash
flutter build apk  # Para Android
flutter build ios  # Para iOS
```

2. Para ejecutar tests:
```bash
flutter test
```

## Contribución

1. Crea una rama para tu feature:
```bash
git checkout -b feature/nueva-caracteristica
```

2. Haz commit de tus cambios:
```bash
git commit -m 'Agrega nueva característica'
```

3. Push a la rama:
```bash
git push origin feature/nueva-caracteristica
```

## Soporte

Para soporte, contacta al equipo de desarrollo o crea un issue en el repositorio. 