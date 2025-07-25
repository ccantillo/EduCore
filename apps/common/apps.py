from django.apps import AppConfig
from django.db import transaction


class CommonConfig(AppConfig):
    """
    Configuración de la app common.
    Incluye configuraciones globales del sistema.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.common'
    verbose_name = 'Común'
    
    def ready(self):
        """
        Configuraciones que se ejecutan cuando Django está listo.
        """
        # Solo ejecutar en el proceso principal, no en workers
        import os
        import sys
        
        # No ejecutar durante migraciones o comandos de Django
        if (
            'migrate' in sys.argv or 
            'makemigrations' in sys.argv or 
            'collectstatic' in sys.argv or
            'test' in sys.argv or
            'check' in sys.argv
        ):
            return
            
        # No ejecutar en workers de Celery
        if 'celery' in sys.argv or 'worker' in sys.argv or 'beat' in sys.argv:
            return
            
        # Solo ejecutar una vez en el proceso principal
        if os.environ.get('RUN_MAIN', None) != 'true':
            try:
                self._configure_periodic_tasks()
            except Exception as e:
                # Log el error pero no fallar el inicio de Django
                print(f"⚠️ Error configurando tareas periódicas automáticamente: {e}")
    
    def _configure_periodic_tasks(self):
        """
        Configurar automáticamente las tareas periódicas al iniciar Django.
        """
        try:
            from django.db import connection
            from django.core.management import call_command
            
            # Verificar que las tablas existan (post-migración)
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name='django_celery_beat_periodictask'
                    );
                """)
                tables_exist = cursor.fetchone()[0]
            
            if tables_exist:
                # Configurar tareas periódicas usando el comando Django
                print("🔧 Configurando tareas periódicas automáticamente...")
                
                # Usar transaction.on_commit para asegurar que se ejecute después de las migraciones
                transaction.on_commit(lambda: self._setup_tasks_delayed())
            else:
                print("ℹ️ Tablas de Celery Beat no encontradas, omitiendo configuración de tareas")
                
        except Exception as e:
            print(f"⚠️ Error en configuración automática de tareas: {e}")
    
    def _setup_tasks_delayed(self):
        """
        Configurar tareas con delay para evitar problemas de timing.
        """
        try:
            from apps.notificaciones.tasks import configurar_tareas_periodicas
            
            # Ejecutar de forma asíncrona para no bloquear el inicio
            result = configurar_tareas_periodicas.delay()
            print("✅ Tareas periódicas programadas para configuración automática")
            
        except Exception as e:
            print(f"⚠️ Error programando configuración de tareas: {e}")
            # Fallback: ejecutar de forma síncrona
            try:
                from django.core.management import call_command
                call_command('setup_periodic_tasks')
                print("✅ Tareas periódicas configuradas (fallback)")
            except Exception as fallback_error:
                print(f"❌ Error en fallback de configuración: {fallback_error}") 