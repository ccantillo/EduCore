# 📚 Documentación del API Académica

Este directorio contiene toda la documentación necesaria para utilizar el sistema de gestión académica.

## 📋 Archivos de Documentación

### 📖 `api_endpoints_documentation.md`
Documentación completa de todos los endpoints del API con:
- Información general del API
- Detalles de autenticación JWT
- Descripción completa de cada endpoint
- Ejemplos de request y response
- Códigos de estado HTTP
- Flujos de trabajo típicos por rol de usuario

### 📮 `API_Academica_Postman_Collection.json`
Colección completa de Postman que incluye:
- Todos los endpoints organizados por categorías
- Variables de entorno preconfiguradas
- Scripts de autenticación automática
- Ejemplos de datos de prueba
- Tests básicos para validar respuestas

### 🛣️ `roadmap.md`
Registro completo del progreso del proyecto con:
- Fases de desarrollo completadas
- Tareas pendientes
- Historial de cambios por fecha
- Referencias a commits importantes

---

## 🚀 Cómo Usar la Colección de Postman

### 1. Importar la Colección

1. Abre Postman
2. Click en "Import" 
3. Selecciona el archivo `API_Academica_Postman_Collection.json`
4. La colección se importará con todas las carpetas organizadas

### 2. Variables de Entorno

La colección incluye variables preconfiguradas:

- `{{base_url}}`: `http://localhost:8000/api/v1`
- `{{access_token}}`: Se actualiza automáticamente al hacer login
- `{{refresh_token}}`: Se actualiza automáticamente al hacer login

### 3. Flujo de Trabajo Recomendado

#### Para Empezar:
1. **Register User**: Crear un nuevo usuario
2. **Login**: Iniciar sesión (actualiza automáticamente los tokens)
3. Usar cualquier endpoint autenticado

#### Para Estudiantes:
1. Login con credenciales de estudiante
2. **List Materias** → Ver materias disponibles
3. **Create Inscripcion** → Inscribirse a una materia
4. **Mis Inscripciones** → Ver mis inscripciones
5. **List Notificaciones** → Ver notificaciones

#### Para Profesores:
1. Login con credenciales de profesor  
2. **Mis Materias (Profesor)** → Ver materias asignadas
3. **List Inscripciones** → Ver estudiantes inscritos
4. **Create Calificacion** → Calificar estudiantes
5. **Finalizar Materia** → Aprobar/reprobar estudiantes

#### Para Administradores:
1. Login con credenciales de admin
2. **List Users** → Gestionar usuarios
3. **Create Materia** → Crear nuevas materias
4. **Create Periodo** → Gestionar períodos académicos
5. **Generate Reporte Estudiante/Profesor** → Generar reportes

---

## 🔐 Autenticación

### Configuración Automática
La colección incluye scripts que:
- Extraen automáticamente los tokens del login
- Agregan el header `Authorization: Bearer <token>` a requests autenticados
- Excluyen autenticación para endpoints públicos

### Renovación de Tokens
Si el token expira:
1. Usar **Refresh Token** para obtener un nuevo access token
2. O hacer **Login** nuevamente

---

## 📊 Estructura de la Colección

```
🔐 Authentication
├── Register User
├── Login  
├── Refresh Token
└── Verify Token

👤 Users Management
├── List Users
├── Get Current User
├── Update User
├── Change Password
└── Profile Management

📚 Materias
├── List/Create/Update Materias
├── Materias Disponibles
├── Buscar Materias
└── Mis Materias (Profesor)

🔗 Prerrequisitos
├── List/Create Prerrequisitos
└── Prerrequisitos por Materia

📅 Periodos
├── List/Create Periodos
├── Periodos Activos
└── Cambiar Estado Periodo

📝 Inscripciones
├── List/Create/Update Inscripciones
├── Mis Inscripciones
├── Promedio Estudiante
└── Finalizar Materia

📊 Calificaciones
├── List/Create Calificaciones
└── Bulk Create Calificaciones

🔔 Notificaciones
├── List/Create/Update Notificaciones
├── Marcar como Leída
├── Bulk Update
└── Estadísticas

📊 Reportes
├── List Reportes
├── Generate Reportes
├── Download Reportes
└── Estadísticas

📖 Documentation
├── Swagger UI
├── ReDoc
└── OpenAPI Schema
```

---

## 🧪 Testing y Validación

### Tests Automáticos
Cada request incluye tests básicos que validan:
- Tiempo de respuesta < 5000ms
- Headers apropiados
- Mensajes útiles para errores de autenticación

### Datos de Prueba
Los ejemplos incluyen datos realistas:
- Usuarios con roles específicos
- Materias con códigos universitarios típicos
- Fechas y períodos académicos coherentes
- Calificaciones dentro del rango 0.0-5.0

---

## 📖 Documentación Adicional

### Swagger UI
Interfaz interactiva disponible en: `http://localhost:8000/swagger/`

### ReDoc  
Documentación legible disponible en: `http://localhost:8000/redoc/`

### Endpoints de Documentación
- **Swagger UI**: Interfaz para probar endpoints
- **ReDoc**: Documentación estructurada y legible
- **OpenAPI Schema**: Schema en formato JSON

---

## 🔧 Configuración del Servidor

### Requisitos Previos
1. Servidor Django corriendo en `http://localhost:8000`
2. Base de datos configurada y migrada
3. Usuarios de prueba creados

### Variables de Entorno Importantes
```bash
DEBUG=True
SECRET_KEY=your-secret-key
DB_NAME=academic_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

---

## 🆘 Troubleshooting

### Error 401 (No autenticado)
- Verificar que hiciste login
- Verificar que el token no ha expirado
- Usar **Refresh Token** si es necesario

### Error 403 (Sin permisos)
- Verificar que tu rol tiene permisos para ese endpoint
- Algunos endpoints requieren rol específico (admin, profesor)

### Error 404 (No encontrado)
- Verificar que el ID del recurso existe
- Verificar la URL del endpoint

### Error 400 (Datos inválidos)
- Verificar el formato del JSON en el request body
- Verificar que todos los campos requeridos están presentes
- Verificar tipos de datos (números, fechas, etc.)

---

## 📞 Soporte

Para preguntas sobre la API o problemas con la documentación:

1. Consultar la documentación completa en `api_endpoints_documentation.md`
2. Revisar el roadmap del proyecto en `roadmap.md`
3. Verificar la configuración en los archivos de settings del proyecto

---

**¡La documentación está completa y lista para usar! 🎉** 