# Firebase Storage - Instrucciones de Integración

## ✅ Setup Completado

Tu proyecto ya está conectado a Firebase Storage. Aquí está todo lo que se configuró:

### 📁 Archivos Creados/Modificados

1. **`firebase-key.json`** (en la raíz del proyecto)
   - Archivo de credenciales de Firebase Admin SDK
   - ⚠️ **IMPORTANTE**: Está en `.gitignore` para que no se suba a GitHub
   - **NO COMPARTAS** este archivo con nadie

2. **`firebase_service.py`** (módulo de Firebase)
   - Maneja toda la lógica de subida a Firebase Storage
   - Funciones:
     - `upload_image_to_firebase()` - Sube imágenes a Firebase
     - `delete_image_from_firebase()` - Elimina imágenes de Firebase

3. **`main.py`** - Backend mejorado con 3 nuevos endpoints:
   - `POST /upload-image` - Subir imágenes genéricas
   - `POST /upload-player-photo` - Subir fotos de jugadores (actualiza BD automáticamente)
   - `POST /upload-team-logo` - Subir logos de equipos (actualiza BD automáticamente)

4. **`ImageUploader.vue`** - Componente Vue reutilizable
   - Ubicación: `frontend-liga-vue/src/components/ImageUploader.vue`
   - Maneja selección, vista previa y subida de imágenes
   - Emite eventos de éxito/error

---

## 🚀 Cómo Usar

### Opción 1: Usar el componente en tus vistas

```vue
<template>
  <div>
    <h1>Subir Foto de Jugador</h1>
    
    <!-- Para fotos de jugadores -->
    <ImageUploader
      :player-id="123"
      upload-endpoint="/upload-player-photo"
      @upload-success="onPhotoUploaded"
      @upload-error="onPhotoError"
    />
  </div>
</template>

<script>
import ImageUploader from '@/components/ImageUploader.vue';

export default {
  components: {
    ImageUploader
  },
  methods: {
    onPhotoUploaded(data) {
      console.log('Foto subida:', data.url);
      // Aquí puedes hacer algo con la URL
    },
    onPhotoError(error) {
      console.error('Error:', error);
    }
  }
}
</script>
```

### Opción 2: Para logos de equipos

```vue
<ImageUploader
  :team-id="456"
  upload-endpoint="/upload-team-logo"
  @upload-success="onLogoUploaded"
/>
```

### Opción 3: Subir imágenes genéricas

```vue
<ImageUploader
  folder="galeria"
  @upload-success="onImageUploaded"
/>
```

---

## 📋 Props del Componente

```javascript
{
  folder: String,              // Carpeta en Firebase (default: "images")
  uploadEndpoint: String,      // Endpoint a usar (default: "/upload-image")
  playerId: Number,            // ID del jugador (para fotos de jugadores)
  teamId: Number               // ID del equipo (para logos)
}
```

## 📤 Eventos Emitidos

```javascript
// Cuando la subida es exitosa
@upload-success="(data) => {
  // data = { url, filename, playerId, teamId }
}"

// Cuando hay error
@upload-error="(error) => {
  // error = objeto con detalles del error
}"
```

---

## 🔧 Variables de Entorno (Opcional)

Si quieres cambiar la URL del servidor, crea un archivo `.env.local` en la carpeta `frontend-liga-vue/`:

```
VUE_APP_API_URL=http://localhost:8000
```

---

## 📊 Estructura en Firebase Storage

Las imágenes se organizan automáticamente así:

```
ligadeportivabarrialconocoto.firebasestorage.app
├── images/
│   └── 2026/06/10/uuid.jpg
├── jugadores/
│   └── 2026/06/10/uuid.jpg
└── equipos/
    └── 2026/06/10/uuid.jpg
```

---

## ✨ Características

✅ Validación de tipo de archivo (JPG, PNG, GIF, WebP)
✅ Validación de tamaño máximo (5MB)
✅ Vista previa de imagen antes de subir
✅ Indicador de progreso de carga
✅ Actualización automática de la base de datos
✅ URLs públicas generadas automáticamente
✅ Organización por carpeta y fecha
✅ Manejo de errores completo

---

## 🐛 Troubleshooting

### Error: "firebase-key.json no encontrado"
- Asegúrate de que el archivo está en la raíz del proyecto
- Reinicia el servidor con `uvicorn main:app --reload`

### Error: "CORS error"
- Ya está configurado en `main.py`
- Si aún falla, verifica que el servidor FastAPI está corriendo

### Error: "Archivo demasiado grande"
- El límite es 5MB
- Comprime o redimensiona la imagen antes de subir

### La imagen se subió pero no se ve
- Verifica los permisos de Firebase Storage en la consola
- Asegúrate de que el bucket está configurado correctamente

---

## 🔒 Seguridad

⚠️ **IMPORTANTE**:
1. El archivo `firebase-key.json` está protegido en `.gitignore`
2. Las credenciales se cargan del lado del servidor (Python), NO del cliente (Vue)
3. Todos los archivos subidos se guardan con nombres únicos (UUID)
4. Se validan tipos y tamaños de archivos

---

## 📝 Próximos Pasos

1. Agrega ImageUploader a tus vistas (Login, JugadorDashboard, AdminDashboard)
2. Personaliza los estilos CSS según tu diseño
3. Prueba subiendo algunas imágenes
4. Verifica en Firebase Console que se guardaron correctamente

¡Ahora tu aplicación puede manejar imágenes! 🎉
