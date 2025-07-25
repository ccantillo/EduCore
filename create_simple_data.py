#!/usr/bin/env python
import os
import sys
import django
from decimal import Decimal
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.users.models import User
from apps.materias.models import Materia, Periodo
from apps.inscripciones.models import Inscripcion
from apps.notificaciones.models import Notificacion

def crear_datos_prueba():
    print("🚀 Creando datos de prueba básicos...")
    
    # 1. Crear período
    periodo, created = Periodo.objects.get_or_create(
        nombre="2025-1",
        defaults={
            'fecha_inicio': datetime(2025, 1, 15).date(),
            'fecha_fin': datetime(2025, 5, 15).date(),
            'estado': 'inscripciones'
        }
    )
    print(f"📅 Período: {periodo.nombre}")
    
    # 2. Crear profesor
    profesor, created = User.objects.get_or_create(
        username='prof_matematicas',
        defaults={
            'email': 'profesor@test.com',
            'first_name': 'Dr. Juan',
            'last_name': 'Pérez',
            'role': 'profesor'
        }
    )
    if created:
        profesor.set_password('profesor123')
        profesor.save()
    print(f"👨‍🏫 Profesor: {profesor.get_full_name()}")
    
    # 3. Crear estudiante
    estudiante, created = User.objects.get_or_create(
        username='estudiante1',
        defaults={
            'email': 'estudiante@test.com',
            'first_name': 'María',
            'last_name': 'García',
            'role': 'estudiante'
        }
    )
    if created:
        estudiante.set_password('estudiante123')
        estudiante.save()
    print(f"👩‍🎓 Estudiante: {estudiante.get_full_name()}")
    
    # 4. Crear materia
    materia, created = Materia.objects.get_or_create(
        codigo='MAT101',
        defaults={
            'nombre': 'Cálculo I',
            'descripcion': 'Introducción al cálculo',
            'creditos': 4,
            'profesor': profesor
        }
    )
    print(f"📚 Materia: {materia.codigo} - {materia.nombre}")
    
    # 5. Crear inscripción
    inscripcion, created = Inscripcion.objects.get_or_create(
        estudiante=estudiante,
        materia=materia,
        periodo=periodo,
        defaults={'estado': 'activa'}
    )
    if created:
        print(f"📝 Inscripción creada: {estudiante.get_full_name()} -> {materia.codigo}")
        # Crear notificación
        Notificacion.notificar_inscripcion_exitosa(inscripcion)
    
    print("✅ Datos básicos creados!")
    print("\n🔐 Credenciales:")
    print("  Estudiante: estudiante1 / estudiante123")
    print("  Profesor: prof_matematicas / profesor123")

if __name__ == '__main__':
    crear_datos_prueba() 