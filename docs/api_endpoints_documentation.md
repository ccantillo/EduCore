# 📚 API Académica - Documentación de Endpoints

## 📋 Información General

- **Base URL**: `http://localhost:8000/api/v1/`
- **Autenticación**: JWT Bearer Token
- **Formatos soportados**: JSON
- **Documentación interactiva**: 
  - Swagger UI: `http://localhost:8000/swagger/`
  - ReDoc: `http://localhost:8000/redoc/`

## 🔐 Autenticación

### Headers requeridos para endpoints protegidos:
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Roles del sistema:
- **admin**: Acceso completo a todo el sistema
- **profesor**: Gestión de materias asignadas y calificaciones
- **estudiante**: Consulta de materias e inscripciones propias

---

## 👤 USERS APP - Gestión de Usuarios

### 🔑 AuthViewSet - `/api/v1/users/auth/`

#### Registro de Usuario
```http
POST /api/v1/users/auth/register/
```

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "password_confirm": "string",
  "first_name": "string",
  "last_name": "string",
  "role": "admin|profesor|estudiante",
  "phone": "string (optional)"
}
```

**Response (201):**
```json
{
  "message": "Usuario registrado exitosamente",
  "user": {
    "id": 1,
    "username": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "role": "estudiante",
    "role_display": "Estudiante",
    "phone": "string",
    "is_active": true,
    "created_at": "2025-01-23T10:00:00Z",
    "updated_at": "2025-01-23T10:00:00Z",
    "profile": {
      "birth_date": null,
      "address": "",
      "student_id": null,
      "professional_id": null,
      "created_at": "2025-01-23T10:00:00Z",
      "updated_at": "2025-01-23T10:00:00Z"
    }
  },
  "tokens": {
    "refresh": "string",
    "access": "string"
  }
}
```

#### Inicio de Sesión
```http
POST /api/v1/users/auth/login/
```

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "message": "Inicio de sesión exitoso",
  "user": {
    "id": 1,
    "username": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "role": "estudiante",
    "role_display": "Estudiante",
    "phone": "string",
    "is_active": true,
    "created_at": "2025-01-23T10:00:00Z",
    "updated_at": "2025-01-23T10:00:00Z",
    "profile": {...}
  },
  "tokens": {
    "refresh": "string",
    "access": "string"
  }
}
```

### 🧑‍🎓 UserViewSet - `/api/v1/users/users/`

#### Listar Usuarios (Admin)
```http
GET /api/v1/users/users/
```

**Query Parameters:**
- `page`: Número de página
- `page_size`: Elementos por página

**Response (200):**
```json
{
  "count": 100,
  "next": "string",
  "previous": "string",
  "results": [
    {
      "id": 1,
      "username": "string",
      "email": "string",
      "first_name": "string",
      "last_name": "string",
      "role": "estudiante",
      "role_display": "Estudiante",
      "phone": "string",
      "is_active": true,
      "created_at": "2025-01-23T10:00:00Z",
      "updated_at": "2025-01-23T10:00:00Z",
      "profile": {...}
    }
  ]
}
```

#### Obtener Usuario Específico
```http
GET /api/v1/users/users/{id}/
```

#### Crear Usuario (Admin)
```http
POST /api/v1/users/users/
```

#### Actualizar Usuario
```http
PUT /api/v1/users/users/{id}/
PATCH /api/v1/users/users/{id}/
```

**Request Body (PATCH):**
```json
{
  "first_name": "string",
  "last_name": "string",
  "phone": "string"
}
```

#### Eliminar Usuario (Admin)
```http
DELETE /api/v1/users/users/{id}/
```

#### Obtener Información Propia
```http
GET /api/v1/users/users/me/
```

#### Cambiar Contraseña
```http
POST /api/v1/users/users/change_password/
```

**Request Body:**
```json
{
  "old_password": "string",
  "new_password": "string",
  "new_password_confirm": "string"
}
```

#### Obtener Perfil de Usuario
```http
GET /api/v1/users/users/{id}/profile/
```

#### Actualizar Perfil de Usuario
```http
PUT /api/v1/users/users/{id}/update_profile/
PATCH /api/v1/users/users/{id}/update_profile/
```

**Request Body:**
```json
{
  "birth_date": "2000-01-01",
  "address": "string"
}
```

### 📋 ProfileViewSet - `/api/v1/users/profiles/`

Endpoints estándar CRUD para gestión de perfiles extendidos.

### 🔑 JWT Endpoints

#### Obtener Token
```http
POST /api/v1/users/token/
```

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

#### Renovar Token
```http
POST /api/v1/users/token/refresh/
```

**Request Body:**
```json
{
  "refresh": "string"
}
```

#### Verificar Token
```http
POST /api/v1/users/token/verify/
```

**Request Body:**
```json
{
  "token": "string"
}
```

---

## 📚 MATERIAS APP - Gestión Académica

### 📖 MateriaViewSet - `/api/v1/materias/materias/`

#### Listar Materias
```http
GET /api/v1/materias/materias/
```

**Response (200):**
```json
{
  "count": 50,
  "next": "string",
  "previous": "string",
  "results": [
    {
      "id": 1,
      "codigo": "MAT101",
      "nombre": "Cálculo I",
      "creditos": 4,
      "estado": "activa",
      "profesor_nombre": "Dr. Juan Pérez",
      "estudiantes_inscritos_count": 25
    }
  ]
}
```

#### Obtener Materia Específica
```http
GET /api/v1/materias/materias/{id}/
```

**Response (200):**
```json
{
  "id": 1,
  "codigo": "MAT101",
  "nombre": "Cálculo I",
  "descripcion": "Curso de cálculo diferencial e integral",
  "creditos": 4,
  "estado": "activa",
  "profesor": {
    "id": 1,
    "username": "profesor1",
    "email": "profesor@example.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "role": "profesor",
    "role_display": "Profesor"
  },
  "prerrequisitos": [
    {
      "id": 1,
      "prerrequisito": 2,
      "prerrequisito_codigo": "MAT100",
      "prerrequisito_nombre": "Precálculo",
      "tipo": "obligatorio",
      "created_at": "2025-01-23T10:00:00Z"
    }
  ],
  "estudiantes_inscritos_count": 25,
  "inscripciones_activas": {
    "total": 25,
    "estudiantes": [
      {
        "id": 3,
        "username": "estudiante1",
        "nombre_completo": "María García"
      }
    ]
  },
  "created_at": "2025-01-23T10:00:00Z",
  "updated_at": "2025-01-23T10:00:00Z"
}
```

#### Crear Materia (Admin/Profesor)
```http
POST /api/v1/materias/materias/
```

**Request Body:**
```json
{
  "codigo": "MAT102",
  "nombre": "Cálculo II",
  "descripcion": "Continuación del curso de cálculo",
  "creditos": 4,
  "estado": "activa",
  "profesor": 1
}
```

#### Actualizar Materia (Admin/Profesor)
```http
PUT /api/v1/materias/materias/{id}/
PATCH /api/v1/materias/materias/{id}/
```

#### Eliminar Materia (Admin/Profesor)
```http
DELETE /api/v1/materias/materias/{id}/
```

#### Listar Materias Disponibles para Inscripción
```http
GET /api/v1/materias/materias/disponibles/
```

#### Buscar Materias
```http
GET /api/v1/materias/materias/buscar/?q={query}
```

#### Materias del Profesor Actual
```http
GET /api/v1/materias/materias/mis_materias/
```

### 🔗 PrerrequisitoViewSet - `/api/v1/materias/prerrequisitos/`

#### Listar Prerrequisitos
```http
GET /api/v1/materias/prerrequisitos/
```

#### Crear Prerrequisito (Admin/Profesor)
```http
POST /api/v1/materias/prerrequisitos/
```

**Request Body:**
```json
{
  "materia": 1,
  "prerrequisito": 2,
  "tipo": "obligatorio"
}
```

#### Prerrequisitos por Materia
```http
GET /api/v1/materias/prerrequisitos/por_materia/?materia_id={id}
```

### 📅 PeriodoViewSet - `/api/v1/materias/periodos/`

#### Listar Períodos (Admin)
```http
GET /api/v1/materias/periodos/
```

**Response (200):**
```json
{
  "count": 10,
  "next": "string",
  "previous": "string", 
  "results": [
    {
      "id": 1,
      "nombre": "2025-1",
      "fecha_inicio": "2025-01-15",
      "fecha_fin": "2025-05-15",
      "estado": "inscripciones",
      "es_activo": true,
      "created_at": "2025-01-23T10:00:00Z",
      "updated_at": "2025-01-23T10:00:00Z"
    }
  ]
}
```

#### Crear Período (Admin)
```http
POST /api/v1/materias/periodos/
```

**Request Body:**
```json
{
  "nombre": "2025-2",
  "fecha_inicio": "2025-08-15",
  "fecha_fin": "2025-12-15",
  "estado": "planificacion"
}
```

#### Períodos Activos
```http
GET /api/v1/materias/periodos/activos/
```

#### Cambiar Estado de Período
```http
POST /api/v1/materias/periodos/{id}/cambiar_estado/
```

**Request Body:**
```json
{
  "estado": "en_curso"
}
```

---

## 📝 INSCRIPCIONES APP - Gestión de Inscripciones

### ✍️ InscripcionViewSet - `/api/v1/inscripciones/inscripciones/`

#### Listar Inscripciones
```http
GET /api/v1/inscripciones/inscripciones/
```

**Response (200):**
```json
{
  "count": 100,
  "next": "string",
  "previous": "string",
  "results": [
    {
      "id": 1,
      "estudiante_nombre": "María García",
      "materia_codigo": "MAT101",
      "materia_nombre": "Cálculo I",
      "periodo_nombre": "2025-1",
      "estado": "activa",
      "nota_final": null,
      "fecha_inscripcion": "2025-01-23T10:00:00Z"
    }
  ]
}
```

#### Obtener Inscripción Específica
```http
GET /api/v1/inscripciones/inscripciones/{id}/
```

**Response (200):**
```json
{
  "id": 1,
  "estudiante": {
    "id": 3,
    "username": "estudiante1",
    "email": "estudiante@example.com",
    "first_name": "María",
    "last_name": "García",
    "role": "estudiante"
  },
  "materia": {
    "id": 1,
    "codigo": "MAT101",
    "nombre": "Cálculo I",
    "creditos": 4,
    "profesor": {...}
  },
  "periodo": {
    "id": 1,
    "nombre": "2025-1",
    "fecha_inicio": "2025-01-15",
    "fecha_fin": "2025-05-15",
    "estado": "inscripciones"
  },
  "estado": "activa",
  "nota_final": null,
  "fecha_inscripcion": "2025-01-23T10:00:00Z",
  "fecha_retiro": null,
  "calificaciones": [
    {
      "id": 1,
      "tipo": "parcial_1",
      "nota": 4.2,
      "peso": 30,
      "comentarios": "Buen desempeño",
      "created_at": "2025-02-15T10:00:00Z"
    }
  ],
  "aprobada": false,
  "reprobada": false,
  "activa": true,
  "created_at": "2025-01-23T10:00:00Z",
  "updated_at": "2025-01-23T10:00:00Z"
}
```

#### Crear Inscripción
```http
POST /api/v1/inscripciones/inscripciones/
```

**Request Body:**
```json
{
  "estudiante": 3,
  "materia": 1,
  "periodo": 1
}
```

#### Actualizar Inscripción
```http
PUT /api/v1/inscripciones/inscripciones/{id}/
PATCH /api/v1/inscripciones/inscripciones/{id}/
```

**Request Body:**
```json
{
  "estado": "retirada",
  "fecha_retiro": "2025-03-01T10:00:00Z"
}
```

#### Mis Inscripciones (Estudiante)
```http
GET /api/v1/inscripciones/inscripciones/mis_inscripciones/
```

#### Inscripciones Activas
```http
GET /api/v1/inscripciones/inscripciones/activas/
```

#### Inscripciones Aprobadas
```http
GET /api/v1/inscripciones/inscripciones/aprobadas/
```

#### Promedio del Estudiante
```http
GET /api/v1/inscripciones/inscripciones/promedio_estudiante/?estudiante_id={id}
```

**Response (200):**
```json
{
  "estudiante_id": 3,
  "estudiante_nombre": "María García",
  "promedio_general": 4.25,
  "total_creditos": 16,
  "materias_aprobadas": 3,
  "materias_reprobadas": 1,
  "materias_activas": 4
}
```

#### Inscribir Estudiante
```http
POST /api/v1/inscripciones/inscripciones/inscribir_estudiante/
```

#### Retirar de Materia
```http
POST /api/v1/inscripciones/inscripciones/{id}/retirar/
```

#### Aprobar/Reprobar Materia (Profesor)
```http
POST /api/v1/inscripciones/inscripciones/{id}/finalizar/
```

**Request Body:**
```json
{
  "nota_final": 4.5,
  "estado": "aprobada"
}
```

### 📊 CalificacionViewSet - `/api/v1/inscripciones/calificaciones/`

#### Listar Calificaciones (Profesor/Admin)
```http
GET /api/v1/inscripciones/calificaciones/
```

#### Crear Calificación (Profesor)
```http
POST /api/v1/inscripciones/calificaciones/
```

**Request Body:**
```json
{
  "inscripcion": 1,
  "tipo": "parcial_1",
  "nota": 4.2,
  "peso": 30,
  "comentarios": "Buen desempeño en el examen"
}
```

#### Crear Múltiples Calificaciones
```http
POST /api/v1/inscripciones/calificaciones/bulk_create/
```

**Request Body:**
```json
{
  "calificaciones": [
    {
      "inscripcion": 1,
      "tipo": "parcial_1",
      "nota": 4.2,
      "peso": 30,
      "comentarios": "Bien"
    },
    {
      "inscripcion": 2,
      "tipo": "parcial_1",
      "nota": 3.8,
      "peso": 30,
      "comentarios": "Regular"
    }
  ]
}
```

---

## 🔔 NOTIFICACIONES APP - Sistema de Notificaciones

### 📢 NotificacionViewSet - `/api/v1/notificaciones/notificaciones/`

#### Listar Notificaciones del Usuario
```http
GET /api/v1/notificaciones/notificaciones/
```

**Response (200):**
```json
{
  "count": 25,
  "next": "string",
  "previous": "string",
  "results": [
    {
      "id": 1,
      "tipo": "inscripcion_exitosa",
      "titulo": "Inscripción exitosa",
      "estado": "no_leida",
      "fecha_creacion": "2025-01-23T10:00:00Z"
    }
  ]
}
```

#### Obtener Notificación Específica
```http
GET /api/v1/notificaciones/notificaciones/{id}/
```

**Response (200):**
```json
{
  "id": 1,
  "usuario": 3,
  "tipo": "inscripcion_exitosa",
  "titulo": "Inscripción exitosa",
  "mensaje": "Te has inscrito exitosamente en la materia Cálculo I",
  "estado": "no_leida",
  "fecha_creacion": "2025-01-23T10:00:00Z",
  "fecha_lectura": null,
  "es_no_leida": true,
  "es_leida": false,
  "es_archivada": false,
  "created_at": "2025-01-23T10:00:00Z",
  "updated_at": "2025-01-23T10:00:00Z"
}
```

#### Crear Notificación (Admin)
```http
POST /api/v1/notificaciones/notificaciones/
```

**Request Body:**
```json
{
  "usuario": 3,
  "tipo": "recordatorio",
  "titulo": "Recordatorio de pago",
  "mensaje": "Recuerda realizar el pago de matrícula antes del 30 de enero"
}
```

#### Actualizar Estado de Notificación
```http
PATCH /api/v1/notificaciones/notificaciones/{id}/
```

**Request Body:**
```json
{
  "estado": "leida"
}
```

#### Marcar como Leída
```http
POST /api/v1/notificaciones/notificaciones/{id}/marcar_leida/
```

#### Archivar Notificación
```http
POST /api/v1/notificaciones/notificaciones/{id}/archivar/
```

#### Notificaciones No Leídas
```http
GET /api/v1/notificaciones/notificaciones/no_leidas/
```

#### Actualizar Múltiples Notificaciones
```http
POST /api/v1/notificaciones/notificaciones/bulk_update/
```

**Request Body:**
```json
{
  "notificacion_ids": [1, 2, 3],
  "accion": "marcar_leidas"
}
```

#### Estadísticas de Notificaciones
```http
GET /api/v1/notificaciones/notificaciones/estadisticas/
```

**Response (200):**
```json
{
  "total": 25,
  "no_leidas": 5,
  "leidas": 18,
  "archivadas": 2,
  "porcentaje_leidas": 72.0
}
```

---

## 📊 REPORTES APP - Generación de Reportes

### 📋 ReporteViewSet - `/api/v1/reportes/reportes/`

#### Listar Reportes Generados
```http
GET /api/v1/reportes/reportes/
```

**Response (200):**
```json
{
  "count": 15,
  "next": "string",
  "previous": "string",
  "results": [
    {
      "id": 1,
      "tipo": "estudiante",
      "nombre_archivo": "reporte_estudiante_3_2025_01_23.csv",
      "estado": "completado",
      "registros_procesados": 12,
      "solicitante_nombre": "Dr. Juan Pérez",
      "created_at": "2025-01-23T10:00:00Z",
      "completado_at": "2025-01-23T10:02:30Z",
      "tiempo_generacion": "2.5 minutos"
    }
  ]
}
```

#### Obtener Reporte Específico
```http
GET /api/v1/reportes/reportes/{id}/
```

#### Descargar Reporte
```http
GET /api/v1/reportes/reportes/{id}/descargar/
```

**Response**: Archivo CSV para descarga

#### Eliminar Reporte (Admin)
```http
DELETE /api/v1/reportes/reportes/{id}/
```

#### Estadísticas de Reportes
```http
GET /api/v1/reportes/reportes/estadisticas/
```

**Response (200):**
```json
{
  "total_reportes": 50,
  "reportes_completados": 45,
  "reportes_pendientes": 2,
  "reportes_error": 3,
  "promedio_tiempo_generacion": 1.5,
  "reportes_por_tipo": {
    "estudiante": 25,
    "profesor": 15,
    "general": 10
  },
  "reportes_por_estado": {
    "completado": 45,
    "pendiente": 2,
    "error": 3
  }
}
```

### 🎓 ReporteEstudianteViewSet - `/api/v1/reportes/estudiantes/`

#### Generar Reporte de Estudiante
```http
GET /api/v1/reportes/estudiantes/{id}/reporte/?periodo_id={periodo_id}
```

**Query Parameters:**
- `periodo_id` (opcional): ID del período específico

**Response (201):**
```json
{
  "mensaje": "Reporte generado exitosamente",
  "reporte_id": 15,
  "nombre_archivo": "reporte_estudiante_3_2025_01_23.csv",
  "estado": "completado"
}
```

### 👨‍🏫 ReporteProfesorViewSet - `/api/v1/reportes/profesores/`

#### Generar Reporte de Profesor (Admin)
```http
GET /api/v1/reportes/profesores/{id}/reporte/?periodo_id={periodo_id}
```

**Query Parameters:**
- `periodo_id` (opcional): ID del período específico

**Response (201):**
```json
{
  "mensaje": "Reporte generado exitosamente",
  "reporte_id": 16,
  "nombre_archivo": "reporte_profesor_1_2025_01_23.csv",
  "estado": "completado"
}
```

---

## 📖 Documentación Swagger/ReDoc

### Swagger UI
```http
GET /swagger/
```
Interfaz interactiva para probar todos los endpoints

### ReDoc
```http
GET /redoc/
```
Documentación legible y bien estructurada

### Schema JSON
```http
GET /api-schema/
```
Schema OpenAPI en formato JSON

---

## 🚨 Códigos de Estado HTTP

- **200**: Éxito
- **201**: Creado exitosamente
- **204**: Eliminado exitosamente (sin contenido)
- **400**: Solicitud incorrecta (errores de validación)
- **401**: No autenticado
- **403**: Sin permisos
- **404**: Recurso no encontrado
- **500**: Error interno del servidor

## 📝 Ejemplos de Errores

### Error de Validación (400)
```json
{
  "field_name": ["Este campo es requerido."],
  "another_field": ["Este valor ya existe."]
}
```

### Error de Autenticación (401)
```json
{
  "detail": "Token de autenticación no proporcionado."
}
```

### Error de Permisos (403)
```json
{
  "detail": "No tienes permisos para realizar esta acción."
}
```

### Error de Recurso No Encontrado (404)
```json
{
  "detail": "No encontrado."
}
```

---

## 🔄 Flujo de Trabajo Típico

### Para Estudiantes:
1. Registrarse: `POST /api/v1/users/auth/register/`
2. Iniciar sesión: `POST /api/v1/users/auth/login/`
3. Ver materias disponibles: `GET /api/v1/materias/materias/disponibles/`
4. Inscribirse a materia: `POST /api/v1/inscripciones/inscripciones/`
5. Ver mis inscripciones: `GET /api/v1/inscripciones/inscripciones/mis_inscripciones/`
6. Ver notificaciones: `GET /api/v1/notificaciones/notificaciones/`

### Para Profesores:
1. Iniciar sesión: `POST /api/v1/users/auth/login/`
2. Ver mis materias: `GET /api/v1/materias/materias/mis_materias/`
3. Ver estudiantes inscritos: `GET /api/v1/inscripciones/inscripciones/`
4. Calificar estudiantes: `POST /api/v1/inscripciones/calificaciones/`
5. Finalizar materia: `POST /api/v1/inscripciones/inscripciones/{id}/finalizar/`

### Para Administradores:
1. Gestionar usuarios: CRUD en `/api/v1/users/users/`
2. Gestionar materias: CRUD en `/api/v1/materias/materias/`
3. Gestionar períodos: CRUD en `/api/v1/materias/periodos/`
4. Generar reportes: Endpoints en `/api/v1/reportes/` 