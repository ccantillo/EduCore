# Prueba Técnica Backend Django

Este proyecto es una API académica construida con Django y Django REST Framework, diseñada para gestionar usuarios, materias, inscripciones, notificaciones y reportes en un entorno universitario.

## 🛠️ Tecnologías principales
- Python 3.10+
- Django 4.x
- Django REST Framework
- JWT (djangorestframework-simplejwt)
- Celery + Redis
- PostgreSQL
- Docker + docker-compose

## 🚀 Instalación rápida
Próximamente: instrucciones detalladas para instalación local y con Docker.

## 📚 Estructura del proyecto
Consulta el archivo `docs/roadmap.md` para ver el plan de desarrollo y los avances.

---

> Proyecto desarrollado como parte de una prueba técnica. Para dudas o sugerencias, contacta al responsable del repositorio. 

## Tareas programadas (Celery Beat)

Para programar las tareas periódicas, accede al admin de Django y usa el modelo Periodic Task de django-celery-beat. Ejemplo sugerido:

- `delete_old_notifications`: Ejecutar diariamente (cada 24h)
- `send_weekly_professor_summary`: Ejecutar cada lunes a las 8:00 AM

Puedes ajustar la periodicidad desde el admin o usando migraciones personalizadas. 