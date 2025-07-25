# tasks.py para la app reportes
# Tareas para generar reportes pesados en background, enviar por email

# TODO: tareas cuando las necesitemos 
from celery import shared_task
from django.utils import timezone
from apps.users.models import User
from apps.materias.models import Materia
from apps.inscripciones.models import Inscripcion
from apps.notificaciones.models import Notificacion
from django.db import models

@shared_task
def send_weekly_professor_summary():
    """
    Envía un resumen académico semanal a cada profesor con sus materias, estudiantes y promedios.
    El resumen se envía como notificación interna.
    """
    profesores = User.objects.filter(role='profesor')
    for profesor in profesores:
        materias = Materia.objects.filter(profesor=profesor)
        if not materias.exists():
            continue
        resumen = []
        for materia in materias:
            inscripciones = Inscripcion.objects.filter(materia=materia)
            estudiantes = inscripciones.count()
            promedio = inscripciones.aggregate(avg=models.Avg('nota_final'))['avg']
            resumen.append(f"- {materia.nombre} ({materia.codigo}): {estudiantes} estudiantes, promedio: {promedio or 'N/A'}")
        mensaje = (
            f"Resumen semanal de tus materias:\n\n" +
            "\n".join(resumen) +
            "\n\nRecuerda revisar el sistema para más detalles."
        )
        Notificacion.crear_notificacion(
            usuario=profesor,
            tipo='recordatorio',
            titulo='Resumen académico semanal',
            mensaje=mensaje
        ) 