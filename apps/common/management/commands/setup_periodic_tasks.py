"""
Comando Django para configurar automáticamente las tareas periódicas de Celery Beat.
Uso: python manage.py setup_periodic_tasks
"""

from django.core.management.base import BaseCommand
from apps.notificaciones.tasks import configurar_tareas_periodicas


class Command(BaseCommand):
    """
    Comando para configurar automáticamente las tareas periódicas del sistema.
    """
    
    help = 'Configura automáticamente todas las tareas periódicas de Celery Beat'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar recreación de todas las tareas (eliminar y recrear)',
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué tareas se configurarían sin ejecutar cambios',
        )
    
    def handle(self, *args, **options):
        """Ejecutar configuración de tareas periódicas."""
        
        self.stdout.write(
            self.style.HTTP_INFO('🚀 Configurando tareas periódicas...')
        )
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('MODO DRY-RUN: No se realizarán cambios')
            )
            return
        
        if options['force']:
            self.stdout.write(
                self.style.WARNING('Eliminando tareas existentes...')
            )
            self._limpiar_tareas_existentes()
        
        # Ejecutar configuración
        try:
            resultado = configurar_tareas_periodicas.delay()
            resultado_data = resultado.get(timeout=30)  # Esperar máximo 30 segundos
            
            if 'error' in resultado_data:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error: {resultado_data["error"]}')
                )
                return
            
            # Mostrar resultados
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Configuración completada: {resultado_data["tareas_configuradas"]} tareas'
                )
            )
            
            if resultado_data.get('nuevas_tareas'):
                self.stdout.write(
                    self.style.HTTP_INFO(
                        f'📋 Nuevas tareas creadas: {", ".join(resultado_data["nuevas_tareas"])}'
                    )
                )
            
            # Mostrar resumen de tareas configuradas
            self._mostrar_resumen_tareas()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error ejecutando configuración: {e}')
            )
    
    def _limpiar_tareas_existentes(self):
        """Eliminar tareas periódicas existentes."""
        try:
            from django_celery_beat.models import PeriodicTask
            
            # Nombres de tareas del sistema académico
            nombres_tareas = [
                'Envío Semanal de Resumen a Profesores',
                'Limpieza Automática de Notificaciones Antiguas',
                'Resumen Diario de Notificaciones',
            ]
            
            eliminadas = 0
            for nombre in nombres_tareas:
                count, _ = PeriodicTask.objects.filter(name=nombre).delete()
                eliminadas += count
            
            self.stdout.write(
                self.style.WARNING(f'🗑️  {eliminadas} tareas eliminadas')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error eliminando tareas: {e}')
            )
    
    def _mostrar_resumen_tareas(self):
        """Mostrar resumen de todas las tareas periódicas configuradas."""
        try:
            from django_celery_beat.models import PeriodicTask
            
            self.stdout.write('\n' + self.style.HTTP_INFO('📋 TAREAS PERIÓDICAS CONFIGURADAS:'))
            
            tareas = PeriodicTask.objects.filter(
                name__in=[
                    'Envío Semanal de Resumen a Profesores',
                    'Limpieza Automática de Notificaciones Antiguas',
                    'Resumen Diario de Notificaciones',
                ]
            ).order_by('name')
            
            for tarea in tareas:
                estado = '🟢 ACTIVA' if tarea.enabled else '🔴 INACTIVA'
                
                if tarea.crontab:
                    horario = f"{tarea.crontab.hour:02d}:{tarea.crontab.minute:02d}"
                    if tarea.crontab.day_of_week != '*':
                        dias = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
                        dia = dias[int(tarea.crontab.day_of_week)]
                        horario += f" {dia}"
                    else:
                        horario += " diario"
                else:
                    horario = "No definido"
                
                self.stdout.write(
                    f'  • {tarea.name}: {estado} - {horario}'
                )
            
            self.stdout.write(
                self.style.SUCCESS('\n✅ Configuración completada exitosamente!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error mostrando resumen: {e}')
            ) 