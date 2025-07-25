#!/usr/bin/env python
import os
import sys
import django
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.users.models import User, Profile
from apps.materias.models import Materia, Periodo, Prerrequisito
from apps.inscripciones.models import Inscripcion, Calificacion
from apps.notificaciones.models import Notificacion

def crear_datos_prueba():
    """Crear datos de prueba completos para el sistema académico."""
    
    print("🚀 Iniciando creación de datos de prueba...")
    
    # 1. Crear períodos académicos
    print("📅 Creando períodos académicos...")
    periodo_actual, created = Periodo.objects.get_or_create(
        nombre="2025-1",
        defaults={
            'fecha_inicio': datetime(2025, 1, 15).date(),
            'fecha_fin': datetime(2025, 5, 15).date(),
            'estado': 'inscripciones'
        }
    )
    if created:
        print(f"  ✅ Período creado: {periodo_actual.nombre}")
    
    periodo_siguiente, created = Periodo.objects.get_or_create(
        nombre="2025-2",
        defaults={
            'fecha_inicio': datetime(2025, 8, 15).date(),
            'fecha_fin': datetime(2025, 12, 15).date(),
            'estado': 'planificacion'
        }
    )
    if created:
        print(f"  ✅ Período creado: {periodo_siguiente.nombre}")
    
    # 2. Crear profesores
    print("👨‍🏫 Creando profesores...")
    profesores = [
        {
            'username': 'prof_matematicas',
            'email': 'matematicas@universidad.edu',
            'first_name': 'Dr. Juan',
            'last_name': 'Pérez',
            'role': 'profesor'
        },
        {
            'username': 'prof_fisica',
            'email': 'fisica@universidad.edu',
            'first_name': 'Dra. María',
            'last_name': 'González',
            'role': 'profesor'
        },
        {
            'username': 'prof_quimica',
            'email': 'quimica@universidad.edu',
            'first_name': 'Dr. Carlos',
            'last_name': 'Rodríguez',
            'role': 'profesor'
        },
        {
            'username': 'prof_programacion',
            'email': 'programacion@universidad.edu',
            'first_name': 'Ing. Ana',
            'last_name': 'Martínez',
            'role': 'profesor'
        }
    ]
    
    profesores_creados = []
    for prof_data in profesores:
        profesor, created = User.objects.get_or_create(
            username=prof_data['username'],
            defaults=prof_data
        )
        if created:
            profesor.set_password('profesor123')
            profesor.save()
            print(f"  ✅ Profesor creado: {profesor.get_full_name()}")
        profesores_creados.append(profesor)
    
    # 3. Crear estudiantes
    print("👩‍🎓 Creando estudiantes...")
    estudiantes = [
        {
            'username': 'estudiante1',
            'email': 'maria.garcia@estudiante.edu',
            'first_name': 'María',
            'last_name': 'García',
            'role': 'estudiante'
        },
        {
            'username': 'estudiante2',
            'email': 'juan.lopez@estudiante.edu',
            'first_name': 'Juan',
            'last_name': 'López',
            'role': 'estudiante'
        },
        {
            'username': 'estudiante3',
            'email': 'ana.torres@estudiante.edu',
            'first_name': 'Ana',
            'last_name': 'Torres',
            'role': 'estudiante'
        },
        {
            'username': 'estudiante4',
            'email': 'luis.morales@estudiante.edu',
            'first_name': 'Luis',
            'last_name': 'Morales',
            'role': 'estudiante'
        },
        {
            'username': 'estudiante5',
            'email': 'sofia.ramirez@estudiante.edu',
            'first_name': 'Sofía',
            'last_name': 'Ramírez',
            'role': 'estudiante'
        }
    ]
    
    estudiantes_creados = []
    for est_data in estudiantes:
        estudiante, created = User.objects.get_or_create(
            username=est_data['username'],
            defaults=est_data
        )
        if created:
            estudiante.set_password('estudiante123')
            estudiante.save()
            print(f"  ✅ Estudiante creado: {estudiante.get_full_name()}")
        estudiantes_creados.append(estudiante)
    
    # 4. Crear materias
    print("📚 Creando materias...")
    materias_data = [
        {
            'codigo': 'MAT101',
            'nombre': 'Cálculo I',
            'descripcion': 'Introducción al cálculo diferencial e integral',
            'creditos': 4,
            'profesor': profesores_creados[0]  # Dr. Juan Pérez
        },
        {
            'codigo': 'MAT201',
            'nombre': 'Cálculo II',
            'descripcion': 'Continuación del cálculo diferencial e integral',
            'creditos': 4,
            'profesor': profesores_creados[0]  # Dr. Juan Pérez
        },
        {
            'codigo': 'FIS101',
            'nombre': 'Física I',
            'descripcion': 'Mecánica clásica y termodinámica',
            'creditos': 3,
            'profesor': profesores_creados[1]  # Dra. María González
        },
        {
            'codigo': 'QUI101',
            'nombre': 'Química General',
            'descripcion': 'Fundamentos de química general',
            'creditos': 3,
            'profesor': profesores_creados[2]  # Dr. Carlos Rodríguez
        },
        {
            'codigo': 'PRG101',
            'nombre': 'Programación I',
            'descripcion': 'Introducción a la programación',
            'creditos': 4,
            'profesor': profesores_creados[3]  # Ing. Ana Martínez
        },
        {
            'codigo': 'PRG201',
            'nombre': 'Programación II',
            'descripcion': 'Estructuras de datos y algoritmos',
            'creditos': 4,
            'profesor': profesores_creados[3]  # Ing. Ana Martínez
        }
    ]
    
    materias_creadas = []
    for mat_data in materias_data:
        materia, created = Materia.objects.get_or_create(
            codigo=mat_data['codigo'],
            defaults=mat_data
        )
        if created:
            print(f"  ✅ Materia creada: {materia.codigo} - {materia.nombre}")
        materias_creadas.append(materia)
    
    # 5. Crear prerrequisitos (simplificados)
    print("🔗 Creando prerrequisitos...")
    mat101 = Materia.objects.get(codigo='MAT101')
    mat201 = Materia.objects.get(codigo='MAT201')
    prg101 = Materia.objects.get(codigo='PRG101')
    prg201 = Materia.objects.get(codigo='PRG201')
    
    prerrequisitos = [
        (mat201, mat101, 'obligatorio'),  # Cálculo II requiere Cálculo I
        (prg201, prg101, 'obligatorio'),  # Programación II requiere Programación I
    ]
    
    for materia, prereq, tipo in prerrequisitos:
        prerrequisito, created = Prerrequisito.objects.get_or_create(
            materia=materia,
            prerrequisito=prereq,
            defaults={'tipo': tipo}
        )
        if created:
            print(f"  ✅ Prerrequisito: {materia.codigo} requiere {prereq.codigo}")
    
    # 6. Crear inscripciones (respetando prerrequisitos)
    print("📝 Creando inscripciones...")
    
    # Primero crear inscripciones que serán aprobadas (prerrequisitos)
    inscripciones_aprobadas = [
        # Luis Morales - aprueba prerrequisitos
        (estudiantes_creados[3], mat101, periodo_actual, 'aprobada'),
        (estudiantes_creados[3], prg101, periodo_actual, 'aprobada'),
        
        # Juan López - aprueba programación I
        (estudiantes_creados[1], prg101, periodo_actual, 'aprobada'),
        
        # Ana Torres - aprueba programación I
        (estudiantes_creados[2], prg101, periodo_actual, 'aprobada'),
    ]
    
    print("📝 Creando inscripciones aprobadas (prerrequisitos)...")
    for estudiante, materia, periodo, estado in inscripciones_aprobadas:
        inscripcion, created = Inscripcion.objects.get_or_create(
            estudiante=estudiante,
            materia=materia,
            periodo=periodo,
            defaults={'estado': estado}
        )
        if created:
            # Asignar nota aprobada
            inscripcion.nota_final = Decimal('4.2')
            inscripcion.save()
            print(f"  ✅ Inscripción aprobada: {estudiante.get_full_name()} -> {materia.codigo}")
    
    # Luego crear inscripciones activas (solo materias sin prerrequisitos complejos)
    inscripciones_activas = [
        # María García - materias básicas sin prerrequisitos
        (estudiantes_creados[0], mat101, periodo_actual, 'activa'),
        (estudiantes_creados[0], Materia.objects.get(codigo='QUI101'), periodo_actual, 'activa'),
        (estudiantes_creados[0], prg101, periodo_actual, 'activa'),
        
        # Juan López - materias básicas
        (estudiantes_creados[1], mat101, periodo_actual, 'activa'),
        (estudiantes_creados[1], Materia.objects.get(codigo='QUI101'), periodo_actual, 'activa'),
        
        # Ana Torres - materias básicas
        (estudiantes_creados[2], mat101, periodo_actual, 'activa'),
        (estudiantes_creados[2], Materia.objects.get(codigo='QUI101'), periodo_actual, 'activa'),
        
        # Luis Morales - puede acceder a materias avanzadas (ya aprobó prerrequisitos)
        (estudiantes_creados[3], prg201, periodo_actual, 'activa'),  # Ya aprobó PRG101
        
        # Sofía Ramírez - materias básicas
        (estudiantes_creados[4], mat101, periodo_actual, 'activa'),
        (estudiantes_creados[4], Materia.objects.get(codigo='QUI101'), periodo_actual, 'activa'),
    ]
    
    print("📝 Creando inscripciones activas...")
    inscripciones_creadas = []
    for estudiante, materia, periodo, estado in inscripciones_activas:
        inscripcion, created = Inscripcion.objects.get_or_create(
            estudiante=estudiante,
            materia=materia,
            periodo=periodo,
            defaults={'estado': estado}
        )
        if created:
            print(f"  ✅ Inscripción activa: {estudiante.get_full_name()} -> {materia.codigo}")
            inscripciones_creadas.append(inscripcion)
            
            # Crear notificación de inscripción
            Notificacion.notificar_inscripcion_exitosa(inscripcion)
    
    # 7. Crear algunas calificaciones
    print("📊 Creando calificaciones...")
    inscripciones_activas = Inscripcion.objects.filter(estado='activa')[:5]
    
    for inscripcion in inscripciones_activas:
                 # Parcial 1
         Calificacion.objects.get_or_create(
             inscripcion=inscripcion,
             tipo='parcial_1',
             defaults={
                 'nota': Decimal('4.0'),
                 'peso': 30,
                 'comentarios': 'Buen desempeño en el primer parcial'
             }
         )
         
         # Parcial 2 para algunos
         if inscripcion.id % 2 == 0:
             Calificacion.objects.get_or_create(
                 inscripcion=inscripcion,
                 tipo='parcial_2',
                 defaults={
                     'nota': Decimal('3.8'),
                     'peso': 30,
                     'comentarios': 'Desempeño regular'
                 }
             )
    
    print("🎉 ¡Datos de prueba creados exitosamente!")
    print("\n📊 Resumen:")
    print(f"  - Profesores: {User.objects.filter(role='profesor').count()}")
    print(f"  - Estudiantes: {User.objects.filter(role='estudiante').count()}")
    print(f"  - Materias: {Materia.objects.count()}")
    print(f"  - Períodos: {Periodo.objects.count()}")
    print(f"  - Inscripciones: {Inscripcion.objects.count()}")
    print(f"  - Calificaciones: {Calificacion.objects.count()}")
    print(f"  - Notificaciones: {Notificacion.objects.count()}")
    
    print("\n🔐 Credenciales de prueba:")
    print("  Estudiantes: estudiante1, estudiante2, etc. (contraseña: estudiante123)")
    print("  Profesores: prof_matematicas, prof_fisica, etc. (contraseña: profesor123)")
    print("  Admin: carlos (ya existente)")


if __name__ == '__main__':
    crear_datos_prueba() 