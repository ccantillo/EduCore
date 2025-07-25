#!/bin/bash

# Script de inicialización para Docker
# Se ejecuta automáticamente al iniciar el contenedor

set -e

echo "🐳 Iniciando configuración de Django..."

# Esperar a que la base de datos esté lista
echo "⏳ Esperando base de datos..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "✅ Base de datos conectada"

# Ejecutar migraciones
echo "🔄 Ejecutando migraciones..."
python manage.py migrate

# Configurar tareas periódicas automáticamente
# Solo se ejecuta en el servicio web principal, no en celery workers
if [[ "$1" == *"runserver"* ]] || [[ "$1" == *"gunicorn"* ]] || [[ -z "$1" ]]; then
    echo "⚙️ Configurando tareas periódicas de Celery Beat..."
    python manage.py setup_periodic_tasks || echo "⚠️ Error configurando tareas periódicas, continuando..."
fi

# Crear usuarios de demostración
echo "👥 Creando usuarios de demostración..."
python manage.py create_demo_users

# Cargar datos de prueba opcionales
if [ "$CREATE_TEST_DATA" = "true" ]; then
    echo "📚 Cargando datos de prueba completos..."
    python create_test_data.py
elif [ "$CREATE_SIMPLE_DATA" = "true" ]; then
    echo "📝 Cargando datos de prueba básicos..."
    python create_simple_data.py
fi

# Recopilar archivos estáticos (en producción)
if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.production" ]; then
    echo "📁 Recopilando archivos estáticos..."
    python manage.py collectstatic --noinput
fi

echo "🚀 Configuración completada. Iniciando servidor..."

# Ejecutar el comando original
exec "$@" 