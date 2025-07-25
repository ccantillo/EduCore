# 🛠️ Development Roadmap – Prueba Técnica Backend Django

## ✅ Phase 1 – Setup & Project Structure
- [x] Initialize Git repository and create .gitignore, README.md, and .env.example.
- [x] Setup Django project with modular architecture (apps: users, materias, notificaciones, reportes, common).
- [x] Install and configure Django REST Framework.
- [x] Setup PostgreSQL or MySQL connection (via environment variables).
- [x] Add base settings for development (config/settings/dev.py).

## ✅ Phase 2 – Authentication & Users
- [x] Create User model with custom roles (admin, profesor, estudiante).
- [x] Implement registration and login with JWT (access + refresh).
- [x] Setup token endpoints using rest_framework_simplejwt.
- [x] Create permissions and middleware to restrict access based on roles.
- [ ] Write unit tests for authentication and role middleware.

## ✅ Phase 3 – Academic Core Logic
**Models**
- [x] Materia: nombre, código, créditos, prerrequisitos, profesor asignado.
- [x] Estudiante y Profesor: perfil extendido de User.
- [x] Inscripción: relación estudiante-materia, estado, nota.

**Validar:**
- [x] Requisitos de inscripción.
- [x] Créditos máximos por semestre.
- [x] Prerrequisitos aprobados.

**Endpoints**
- [x] Estudiante: inscribir, ver materias, ver histórico, ver promedio.
- [x] Profesor: ver materias, calificar, finalizar materias.
- [x] Admin: crear materias y usuarios, asignar profesores.

**Tests**
- [ ] Unit tests for models and validators.
- [ ] Integration tests for endpoints.

## ✅ Phase 4 – Notifications
- [x] Create Notificación model (usuario, tipo, mensaje, fecha, estado).
- [x] Use signals: al crear usuario (email bienvenida), al calificar estudiante.
- [x] Endpoint para consultar notificaciones.
- [ ] Test for signal logic and API responses.

## ✅ Phase 5 – Reports
- [x] Implement protected CSV endpoints: /api/reportes/estudiante/{id}/, /api/reportes/profesor/{id}/.
- [x] CSV must contain nombre, materias, calificaciones, estado, promedio.
- [ ] Write unit tests for CSV generation.

## ✅ Phase 6 – Advanced ORM Logic
- [x] Use select_related and prefetch_related in views.
- [x] Implement annotate, Exists, and Subquery where needed (e.g., promedios).
- [ ] Add custom managers and querysets if needed.
- [x] Add tests to ensure queries are optimized.

## ✅ Phase 7 – Scheduled Tasks (Celery + Beat)
- [x] Setup Celery + Redis + Beat.
- [x] Task 1: Enviar resumen académico semanal a profesores.
- [x] Task 2: Borrar notificaciones antiguas.
- [x] Add tests for tasks (using Celery test harness or mock).

## ✅ Phase 8 – Testing Coverage
- [ ] Review test coverage with pytest-cov.
- [ ] Write missing tests for edge cases, permission enforcement, business rules.
- [ ] Validate endpoints with Swagger or Postman collection.

## 🐳 Phase 9 – Docker & Deployment (Optional)
- [x] Create Dockerfile and docker-compose.yml (App + DB + Redis).
- [x] Add .env.example with all config vars.
- [x] Confirm app boots with docker-compose up --build.

## 📘 Phase 10 – Documentation & Polish
- [x] Expose Swagger at /swagger/ and Redoc at /redoc/.
- [ ] Complete README.md: instalación local, uso de Docker, uso de la API, cómo correr tests.
- [ ] Optional: add CI/CD pipeline with GitHub Actions.

---

## 📋 Tareas Completadas

### [2025-07-23]
- ✅ Inicializado repositorio Git con .gitignore y README.md
- ✅ Creada estructura modular de Django con apps: users, materias, inscripciones, notificaciones, reportes, common
- ✅ Instaladas y configuradas todas las dependencias (DRF, JWT, Celery, Redis, etc.)
- ✅ Configuración modular de settings (base, development, production, testing)
- ✅ Configuración de linting y formateo (black, isort, flake8)
- ✅ Configuración de testing con pytest y coverage
- ✅ Archivos base creados en todas las apps siguiendo las mejores prácticas

### [2025-07-24]
- ✅ Implementado modelo de usuario personalizado con roles (admin, profesor, estudiante)
- ✅ Creado modelo Profile para información extendida de usuarios
- ✅ Implementados serializers para registro, login y gestión de usuarios
- ✅ Creados permisos personalizados basados en roles
- ✅ Implementadas vistas con ViewSets para autenticación y gestión de usuarios
- ✅ Configurado middleware personalizado para control de acceso y logging
- ✅ Configuradas URLs con routers de DRF y endpoints JWT estándar
- ✅ Configurado Swagger/ReDoc para documentación de API
- ✅ Ejecutadas migraciones y creado superusuario de prueba
- ✅ Servidor funcionando correctamente en modo desarrollo
- ✅ Implementados modelos académicos: Materia, Prerrequisito, Periodo, Inscripcion, Calificacion
- ✅ Creados serializers completos para todas las entidades académicas
- ✅ Implementadas vistas con ViewSets para gestión de materias e inscripciones
- ✅ Configuradas validaciones de prerrequisitos y límites de créditos
- ✅ Implementados endpoints para estudiantes, profesores y administradores
- ✅ Configuradas URLs y ejecutadas migraciones para nuevas funcionalidades
- ✅ Implementado modelo de notificaciones con tipos y estados
- ✅ Creadas señales automáticas para bienvenida, inscripciones y calificaciones
- ✅ Implementados serializers y ViewSets para gestión de notificaciones
- ✅ Configuradas URLs y ejecutadas migraciones para sistema de notificaciones
- ✅ Implementado modelo de reportes generados con seguimiento y estados
- ✅ Creado servicio completo para generación de reportes CSV de estudiantes y profesores
- ✅ Implementados serializers y ViewSets para gestión de reportes con permisos
- ✅ Configuradas URLs protegidas y ejecutadas migraciones para sistema de reportes
- ✅ Creada documentación completa de endpoints del API con ejemplos de request/response
- ✅ Generada colección de Postman completa con todos los endpoints organizados por categorías
- ✅ Implementados scripts de autenticación automática en la colección de Postman
- ✅ Documentados flujos de trabajo típicos para cada tipo de usuario (admin, profesor, estudiante)
- ✅ Implementado sistema completo de Docker con Dockerfile y docker-compose.yml
- ✅ Configurados servicios de PostgreSQL, Redis, Django, Celery y Celery Beat en contenedores
- ✅ Creado archivo .env.example con todas las variables de configuración necesarias
- ✅ Configuración de volúmenes persistentes para datos de base de datos y Redis
- ✅ Orquestación completa de servicios con dependencias y networking interno

### [2025-07-25]
- ✅ Implementado frontend web completo como monolito integrado en Django
- ✅ Creada app frontend con vistas, URLs y templates responsivos usando Bootstrap 5
- ✅ Implementado sistema de autenticación web con login/logout personalizado
- ✅ Creado template base con navegación, sidebar dinámico según roles y notificaciones en tiempo real
- ✅ Desarrollado dashboard específico para estudiantes con estadísticas y resúmenes interactivos
- ✅ Implementadas páginas funcionales para materias, inscripciones, notificaciones y reportes
- ✅ Integrado JavaScript vanilla para consumir APIs REST internas del backend
- ✅ Configurado sistema híbrido: API REST para datos + Templates Django para presentación
- ✅ Agregadas páginas con filtros, búsquedas, modales y funcionalidades interactivas
- ✅ Implementado diseño responsive con iconografía Bootstrap Icons y UX moderna
- ✅ Configuradas URLs de autenticación y redirecciones automáticas según roles
- ✅ Creados dashboards específicos para administradores y profesores con funcionalidades por rol
- ✅ Corregidos problemas de autenticación añadiendo soporte para SessionAuthentication en DRF
- ✅ Solucionados errores 401 en endpoints por configuración incorrecta de permisos múltiples

### [2025-07-25] (Continued)
- ✅ Fixed dashboard template errors by creating missing `dashboard_admin.html` and `dashboard_profesor.html` templates
- ✅ Resolved 401 authentication errors by adding SessionAuthentication support for frontend cookies
- ✅ Fixed ViewSet permissions to use proper role-based access control with dynamic `get_permissions()` methods
- ✅ Enhanced reportes download endpoint with comprehensive error handling for missing reports and files
- ✅ Fixed frontend hardcoded data (est_001, prof_001) to use dynamic API data from `/api/v1/reportes/reportes/`
- ✅ Created test data and CSV files to support development and testing
- ✅ Improved error messages and user feedback throughout the application

### [2025-01-24] (PDF Compliance Updates)
- ✅ **Reportes CSV - PDF Compliance**: Implemented exact PDF-compliant endpoints `/api/reportes/estudiante/{id}/` and `/api/reportes/profesor/{id}/` that return CSV directly
- ✅ **Decoradores**: Implemented prerequisite validation decorator `@validate_prerequisites` and credit limits decorator `@validate_credit_limits` in `apps/common/decorators.py`
- ✅ **Applied Decorators**: Applied both decorators to the `InscripcionViewSet.create()` method for automatic validation during enrollment
- ✅ **Schema Documentation**: Created complete Entity Relationship Diagram (ERD) showing all database models and relationships
- ✅ **Project Flow Documentation**: Created comprehensive project flow diagram showing authentication, role-based access, validation flow, and system architecture
- ✅ **Updated URLs**: Added specific URL patterns that match PDF requirements exactly while maintaining existing advanced functionality
- ✅ **Enhanced CSV Reports**: Implemented direct CSV response with proper headers including name, subjects, grades, status, and average as required by PDF

### [2025-01-25] (Production Ready & Bug Fixes)
- ✅ **Docker Data Persistence**: Implemented comprehensive Docker data persistence system with automatic user creation on container startup
- ✅ **Django Management Commands**: Created `create_demo_users` command for automatic demo account setup (`admin`, `profesor1`, `estudiante1`)
- ✅ **Docker Entrypoint Script**: Added `docker-entrypoint.sh` for automatic database migration, user creation, and optional test data loading
- ✅ **Production Deployment**: Enhanced Docker configuration with netcat for database connection waiting and proper initialization sequence
- ✅ **Frontend Bug Fix**: Resolved "undefined" display issue in materias page by fixing API data structure inconsistencies
- ✅ **Test Data System**: Improved `create_test_data.py` with better error handling and existing data management
- ✅ **Documentation Updates**: Enhanced README.md with comprehensive Docker persistence documentation and deployment instructions
- ✅ **Environment Configuration**: Added optional test data loading via `CREATE_TEST_DATA` and `CREATE_SIMPLE_DATA` environment variables
- ✅ **Reports Implementation Cleanup**: Fixed reports interface to comply exactly with document requirements using correct endpoints `/api/v1/reportes/estudiante/{id}/` and `/api/v1/reportes/profesor/{id}/`
- ✅ **CSV Structure Optimization**: Simplified CSV report structure to be more readable and direct, following "Nombre, materias, calificaciones, estado, promedio general" format from requirements
- ✅ **Frontend Reports Interface**: Removed custom report generator that was not required, keeping only individual student/professor report selectors as specified in document
- ✅ **User Endpoints Fix**: Corrected user listing endpoints to use `/api/v1/users/users/?role=estudiante` with proper role filtering and permissions for admins and professors
- ✅ **Reports Template Cleanup**: Cleaned up report template by removing unnecessary advanced filters and custom report builders not specified in requirements

### [2025-01-25] (Visual Diagrams Implementation)
- ✅ **Visual ERD Diagram**: Created rendered visual version of Entity Relationship Diagram showing complete database schema with all entities and relationships
- ✅ **Visual Project Flow Diagram**: Created rendered visual version of project flow diagram with color-coded sections for roles, validations, database operations, async tasks, and API endpoints  
- ✅ **Visual Documentation**: Added comprehensive visual diagrams documentation in `docs/visual_diagrams.md` with diagram descriptions and technical details
- ✅ **README Integration**: Updated main README.md to reference both detailed Mermaid documentation and visual rendered diagrams for easy access
- ✅ **Roadmap Update**: Documented completion of visual diagrams as additional deliverable beyond requirements specifications 