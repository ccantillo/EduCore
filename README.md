# 🎓 Sistema de Gestión Académica - Backend Django

## 📋 Descripción

Sistema de gestión académica completo desarrollado con Django y Django REST Framework. Permite gestionar usuarios, materias, inscripciones, calificaciones, notificaciones y reportes en un entorno universitario.

### ✨ Características Principales

- **🔐 Autenticación JWT** con roles diferenciados (admin, profesor, estudiante)
- **📚 Gestión Académica** completa con validaciones de prerrequisitos y límites de créditos
- **📊 Reportes CSV** automáticos para estudiantes y profesores
- **🔔 Sistema de Notificaciones** automáticas con Django Signals
- **⚡ Tareas Asíncronas** con Celery + Redis + Beat
- **🌐 Frontend Web** integrado con templates responsivos
- **📖 API REST** completamente documentada con Swagger/ReDoc
- **🐳 Dockerización** completa con docker-compose

---

## 🛠️ Tecnologías

- **Backend**: Python 3.10+, Django 4.x, Django REST Framework
- **Autenticación**: JWT (djangorestframework-simplejwt)
- **Base de Datos**: PostgreSQL
- **Tareas Asíncronas**: Celery + Redis + Django Celery Beat
- **Frontend**: Bootstrap 5, JavaScript Vanilla
- **Documentación**: Swagger (drf-yasg) y ReDoc
- **Testing**: Pytest
- **Contenerización**: Docker + docker-compose
- **Linting**: Black, isort, flake8

---

## 🚀 Instalación

### 📋 Requisitos Previos

- Python 3.10+
- PostgreSQL 12+
- Redis 6+
- Git

### 💻 Instalación Local

#### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd "prueba tecnica"
```

#### 2. Crear entorno virtual

```bash
# En Windows
python -m venv env
.\env\Scripts\activate

# En Linux/Mac
python3 -m venv env
source env/bin/activate
```

#### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

#### 4. Configurar variables de entorno

Copia el archivo de ejemplo y configura las variables:

```bash
copy env.example .env
```

Edita `.env` con tus configuraciones:

```env
# Django
SECRET_KEY=tu-secret-key-super-segura
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos
DATABASE_URL=postgresql://usuario:password@localhost:5432/academia_db
DB_NAME=academia_db
DB_USER=usuario
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Email (opcional para desarrollo)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

#### 5. Configurar base de datos

```bash
# Crear base de datos PostgreSQL
createdb academia_db

# Ejecutar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser
```

#### 6. Cargar datos de prueba (opcional)

```bash
python create_test_data.py
```

#### 7. Ejecutar el servidor

```bash
# Servidor Django
python manage.py runserver

# En otra terminal: Redis (si no está ejecutándose)
redis-server

# En otra terminal: Celery Worker
celery -A config worker --loglevel=info

# En otra terminal: Celery Beat (tareas programadas)
celery -A config beat --loglevel=info
```

### 🐳 Instalación con Docker

#### 1. Clonar y configurar

```bash
git clone <repository-url>
cd "prueba tecnica"
copy env.example .env
```

#### 2. Ejecutar con Docker Compose

```bash
# Construir e iniciar todos los servicios
docker-compose up --build

# En modo detached (segundo plano)
docker-compose up -d --build
```

#### 3. Crear superusuario (en otro terminal)

```bash
docker-compose exec web python manage.py createsuperuser
```

#### 4. ✅ Los datos se cargan automáticamente

**Usuarios de demostración**: Se crean automáticamente al iniciar los contenedores.

**Datos de prueba opcionales**: Puedes cargar datos adicionales configurando variables en `.env`:

```bash
# En tu archivo .env, descomenta UNA de estas opciones:

# Opción 1: Datos completos (recomendado para demostración)
CREATE_TEST_DATA=true

# Opción 2: Datos básicos (mínimo para pruebas)
CREATE_SIMPLE_DATA=true
```

**Comandos manuales** (si no usas Docker):

```bash
# Crear usuarios de demostración
python manage.py create_demo_users

# Cargar datos completos de prueba
python create_test_data.py

# Cargar datos básicos de prueba
python create_simple_data.py
```

---

## 💾 Persistencia de Datos en Docker

### ✅ **Datos que SE MANTIENEN entre reinicios:**
- **Base de datos PostgreSQL**: Volumen `postgres_data`
- **Cache Redis**: Volumen `redis_data`
- **Usuarios y datos creados**: Se guardan automáticamente

### 🔄 **Carga automática de datos:**
- **Usuarios demo**: Se crean automáticamente al iniciar (`admin`, `profesor1`, `estudiante1`)
- **Datos de prueba**: Opcionales via variables de entorno
- Script `docker-entrypoint.sh` ejecuta migraciones y carga datos configurados

### 📚 **Tipos de datos de prueba disponibles:**

#### 🎯 **Datos Completos** (`CREATE_TEST_DATA=true`)
- **4 profesores** (matemáticas, física, química, programación)
- **5 estudiantes** con nombres reales
- **6 materias** con prerrequisitos
- **2 períodos** académicos (2025-1, 2025-2)
- **Inscripciones** reales con diferentes estados
- **Calificaciones** parciales
- **Notificaciones** automáticas

#### ⚡ **Datos Básicos** (`CREATE_SIMPLE_DATA=true`)
- 1 profesor, 1 estudiante, 1 materia, 1 período
- Para pruebas rápidas y desarrollo

### 🚀 **En servidor de producción:**
```bash
# Los datos persisten automáticamente
docker-compose up -d --build

# Verificar usuarios de demostración
docker-compose exec web python manage.py create_demo_users
```

---

## 🌐 Acceso al Sistema

### URLs Principales

- **Frontend Web**: http://localhost:8000/
- **Admin Django**: http://localhost:8000/admin/
- **API REST**: http://localhost:8000/api/v1/
- **Documentación Swagger**: http://localhost:8000/swagger/
- **Documentación ReDoc**: http://localhost:8000/redoc/

### 👥 Usuarios de Prueba

Si cargaste los datos de prueba:

```
Admin:
- Username: admin
- Password: admin123

Profesor:
- Username: profesor1
- Password: profesor123

Estudiante:
- Username: estudiante1
- Password: estudiante123
```

---

## 📖 Uso de la API

### 🔐 Autenticación

#### 1. Obtener Token JWT

```bash
POST /api/v1/users/login/
Content-Type: application/json

{
    "username": "admin",
    "password": "admin123"
}
```

Respuesta:
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
        "id": 1,
        "username": "admin",
        "role": "admin"
    }
}
```

#### 2. Usar Token en Requests

```bash
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### 📚 Endpoints Principales

#### Usuarios
```
GET    /api/v1/users/usuarios/          # Listar usuarios
POST   /api/v1/users/usuarios/          # Crear usuario
GET    /api/v1/users/usuarios/{id}/     # Detalle usuario
PUT    /api/v1/users/usuarios/{id}/     # Actualizar usuario
DELETE /api/v1/users/usuarios/{id}/     # Eliminar usuario
```

#### Materias
```
GET    /api/v1/materias/materias/       # Listar materias
POST   /api/v1/materias/materias/       # Crear materia
GET    /api/v1/materias/materias/{id}/  # Detalle materia
```

#### Inscripciones
```
GET    /api/v1/inscripciones/inscripciones/     # Listar inscripciones
POST   /api/v1/inscripciones/inscripciones/     # Crear inscripción
GET    /api/v1/inscripciones/mis_inscripciones/ # Mis inscripciones (estudiantes)
```

#### Reportes CSV (Cumple PDF)
```
GET    /api/reportes/estudiante/{id}/    # Reporte CSV estudiante
GET    /api/reportes/profesor/{id}/      # Reporte CSV profesor
```

### 📝 Ejemplos de Uso

#### Crear Inscripción

```bash
POST /api/v1/inscripciones/inscripciones/
Authorization: Bearer <token>
Content-Type: application/json

{
    "estudiante": 2,
    "materia": 1,
    "periodo": 1
}
```

#### Calificar Estudiante

```bash
POST /api/v1/inscripciones/calificaciones/
Authorization: Bearer <token>
Content-Type: application/json

{
    "inscripcion": 1,
    "tipo": "final",
    "nota": 4.5,
    "descripcion": "Examen final"
}
```

---

## 🧪 Testing

### Configuración de Tests

```bash
# Instalar dependencias de testing
pip install pytest pytest-django pytest-cov

# Ejecutar tests
pytest

# Tests con cobertura
pytest --cov=apps --cov-report=html

# Tests específicos
pytest apps/users/tests/
```

### Estructura de Tests

```
apps/
├── users/
│   └── tests/
│       ├── test_models.py
│       ├── test_views.py
│       └── test_permissions.py
├── inscripciones/
│   └── tests/
│       ├── test_decorators.py
│       └── test_validations.py
```

---

## 📊 Documentación Técnica

### 🗄️ Esquema de Base de Datos

- **Documentación detallada**: [docs/database_schema.md](docs/database_schema.md)
- **Diagrama visual renderizado**: [docs/visual_diagrams.md](docs/visual_diagrams.md)

### 🔄 Diagrama de Flujo

- **Documentación detallada**: [docs/project_flow.md](docs/project_flow.md)
- **Diagrama visual renderizado**: [docs/visual_diagrams.md](docs/visual_diagrams.md)

### 🏗️ Arquitectura del Proyecto

```
prueba tecnica/
├── apps/                    # Aplicaciones Django
│   ├── users/              # Usuarios y autenticación
│   ├── materias/           # Materias y prerrequisitos
│   ├── inscripciones/      # Inscripciones y calificaciones
│   ├── notificaciones/     # Sistema de notificaciones
│   ├── reportes/           # Generación de reportes
│   ├── common/             # Decoradores y middleware
│   └── frontend/           # Interface web
├── config/                 # Configuración Django
│   ├── settings/           # Settings modulares
│   └── celery.py          # Configuración Celery
├── docs/                   # Documentación
├── templates/              # Templates HTML
├── docker-compose.yml      # Orquestación Docker
└── requirements.txt        # Dependencias Python
```

---

## 🔧 Características Avanzadas

### 🛡️ Decoradores de Validación

El sistema incluye decoradores personalizados para validaciones automáticas:

```python
from apps.common.decorators import validate_prerequisites, validate_credit_limits

@validate_prerequisites
@validate_credit_limits
def create_inscription(request):
    # Valida automáticamente prerrequisitos y límites de créditos
    pass
```

### 📡 Signals Automáticas

- **Bienvenida**: Email automático al crear usuario
- **Inscripción**: Notificación al inscribirse en materia
- **Calificación**: Notificación al recibir calificación

### ⚡ Tareas Programadas (Celery)

- **Resumen Semanal**: Envío automático a profesores los lunes
- **Limpieza**: Eliminación de notificaciones antiguas cada semana
- **Emails**: Procesamiento asíncrono de correos electrónicos

### 🚀 Optimizaciones ORM

- `select_related()` para relaciones ForeignKey
- `prefetch_related()` para relaciones ManyToMany
- `annotate()` para cálculos agregados
- Índices de base de datos optimizados

---

## 🐛 Troubleshooting

### Problemas Comunes

#### 1. Error de Base de Datos
```bash
# Verificar conexión PostgreSQL
pg_isready -h localhost -p 5432

# Recrear migraciones si es necesario
python manage.py makemigrations --empty apps_name
python manage.py migrate
```

#### 2. Error de Redis
```bash
# Verificar Redis
redis-cli ping

# Limpiar cache si es necesario
redis-cli flushall
```

#### 3. Error de Permisos
```bash
# Verificar superusuario
python manage.py shell
>>> from apps.users.models import User
>>> User.objects.filter(is_superuser=True)
```

#### 4. Problemas con Celery
```bash
# Reiniciar worker
celery -A config worker --loglevel=info --purge

# Verificar tareas
celery -A config inspect active
```

### Logs

```bash
# Ver logs en desarrollo
tail -f logs/django.log

# Ver logs en Docker
docker-compose logs -f web
docker-compose logs -f celery
```

---

## 📈 Próximas Mejoras

- [ ] Implementar tests automatizados (70% cobertura)
- [ ] WebSockets para notificaciones en tiempo real
- [ ] API GraphQL como alternativa
- [ ] Integración con CI/CD
- [ ] Métricas y monitoreo con Prometheus
- [ ] Optimización de consultas SQL

---

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -am 'feat: agregar nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crea un Pull Request

### Estilo de Código

El proyecto usa:
- **Black** para formateo automático
- **isort** para ordenar imports
- **flake8** para linting

```bash
# Formatear código
black .
isort .

# Verificar estilo
flake8 .
```

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

---

## 👨‍💻 Autor

Desarrollado como prueba técnica para demostrar conocimientos en:
- Django y Django REST Framework
- Arquitectura de software
- API REST design
- Patrones de diseño
- Buenas prácticas de desarrollo

---

## 📞 Soporte

Para dudas o problemas:
1. Revisar la documentación en `/docs/`
2. Consultar la documentación API en `/swagger/`
3. Verificar los logs de la aplicación
4. Crear un issue en el repositorio

**¡Disfruta explorando el sistema! 🎉** 