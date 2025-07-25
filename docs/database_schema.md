# Esquema de Base de Datos (ERD)

Este diagrama muestra la estructura completa de la base de datos del sistema académico, incluyendo todas las entidades y sus relaciones.

```mermaid
erDiagram
    User {
        int id PK
        string username UK
        string email UK
        string first_name
        string last_name
        string password
        string role
        boolean is_active
        datetime date_joined
        datetime last_login
    }
    
    Profile {
        int id PK
        int user_id FK
        text biografia
        string telefono
        date fecha_nacimiento
        int creditos_maximos_semestre
        decimal promedio_acumulado
        datetime created_at
        datetime updated_at
    }
    
    Materia {
        int id PK
        string nombre
        string codigo UK
        int creditos
        text descripcion
        int profesor_id FK
        boolean activa
        datetime created_at
        datetime updated_at
    }
    
    Prerrequisito {
        int id PK
        int materia_id FK
        int materia_prerrequisito_id FK
        string tipo
    }
    
    Periodo {
        int id PK
        string nombre
        date fecha_inicio
        date fecha_fin
        boolean activo
        datetime created_at
        datetime updated_at
    }
    
    Inscripcion {
        int id PK
        int estudiante_id FK
        int materia_id FK
        int periodo_id FK
        string estado
        decimal nota_final
        datetime fecha_inscripcion
        datetime fecha_retiro
        datetime created_at
        datetime updated_at
    }
    
    Calificacion {
        int id PK
        int inscripcion_id FK
        string tipo
        decimal nota
        string descripcion
        datetime fecha_calificacion
        datetime created_at
        datetime updated_at
    }
    
    Notificacion {
        int id PK
        int usuario_id FK
        string tipo
        string titulo
        text mensaje
        boolean leida
        datetime created_at
        datetime updated_at
    }
    
    ReporteGenerado {
        int id PK
        int solicitante_id FK
        string tipo
        string nombre_archivo
        string ruta_archivo
        json parametros
        string estado
        int registros_procesados
        text mensaje_error
        datetime created_at
        datetime updated_at
        datetime completado_at
    }
    
    %% Relaciones
    User ||--o{ Profile : "has"
    User ||--o{ Materia : "teaches"
    User ||--o{ Inscripcion : "enrolls"
    User ||--o{ Notificacion : "receives"
    User ||--o{ ReporteGenerado : "requests"
    
    Materia ||--o{ Prerrequisito : "has_prerequisites"
    Materia ||--o{ Prerrequisito : "is_prerequisite_of"
    Materia ||--o{ Inscripcion : "has_enrollments"
    
    Periodo ||--o{ Inscripcion : "contains"
    
    Inscripcion ||--o{ Calificacion : "has_grades"
```

## Descripción de Entidades

### User
Modelo de usuario personalizado que extiende el User de Django.
- **Roles**: admin, profesor, estudiante
- **Campos clave**: username (único), email (único), role

### Profile
Perfil extendido para cada usuario con información adicional.
- **Relación**: OneToOne con User
- **Información académica**: créditos máximos, promedio acumulado

### Materia
Representa las materias/asignaturas del sistema.
- **Profesor**: ForeignKey a User (role='profesor')
- **Campos**: nombre, código único, créditos, descripción

### Prerrequisito
Relación many-to-many entre materias para definir prerrequisitos.
- **Tipos**: obligatorio, recomendado
- **Validación**: Automática en inscripciones

### Periodo
Períodos académicos (semestres).
- **Estado**: Solo uno puede estar activo
- **Inscripciones**: Vinculadas a períodos específicos

### Inscripcion
Relación estudiante-materia en un período específico.
- **Estados**: activa, aprobada, reprobada, retirada, cancelada
- **Validaciones**: Prerrequisitos, límites de créditos

### Calificacion
Calificaciones detalladas de las inscripciones.
- **Tipos**: parcial, final, quiz, taller
- **Rango**: 0.0 - 5.0 (aprobación >= 3.0)

### Notificacion
Sistema de notificaciones para usuarios.
- **Tipos**: bienvenida, inscripcion, calificacion, recordatorio
- **Estado**: leída/no leída

### ReporteGenerado
Registro de reportes CSV generados en el sistema.
- **Estados**: pendiente, generando, completado, error
- **Tipos**: estudiante, profesor, materia, general 