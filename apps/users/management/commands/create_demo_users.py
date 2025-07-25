"""
Management command para crear usuarios de demostración automáticamente.
Se ejecuta al hacer deploy para asegurar que las cuentas de prueba existan.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from apps.users.models import User


class Command(BaseCommand):
    help = 'Crear usuarios de demostración para el sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recrear usuarios aunque ya existan',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS('🎯 Creando usuarios de demostración...')
        )

        # Lista de usuarios de demostración
        demo_users = [
            {
                'username': 'admin',
                'email': 'admin@academia.com',
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'role': 'admin',
                'password': 'admin123',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'profesor1',
                'email': 'profesor1@academia.com',
                'first_name': 'Profesor',
                'last_name': 'Demo',
                'role': 'profesor',
                'password': 'profesor123',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'estudiante1',
                'email': 'estudiante1@academia.com',
                'first_name': 'María',
                'last_name': 'García',
                'role': 'estudiante',
                'password': 'estudiante123',
                'is_staff': False,
                'is_superuser': False,
            }
        ]

        created_count = 0
        updated_count = 0

        for user_data in demo_users:
            username = user_data['username']
            password = user_data.pop('password')
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults=user_data
            )

            if created:
                user.set_password(password)
                user.save()
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Usuario {username} creado')
                )
            elif force:
                # Actualizar usuario existente si se usa --force
                for field, value in user_data.items():
                    setattr(user, field, value)
                user.set_password(password)
                user.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'🔄 Usuario {username} actualizado')
                )
            else:
                # Solo actualizar contraseña si el usuario ya existe
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'🔑 Contraseña de {username} actualizada')
                )

        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Proceso completado:\n'
                f'   • Usuarios creados: {created_count}\n'
                f'   • Usuarios actualizados: {updated_count}\n'
            )
        )
        
        # Mostrar credenciales
        self.stdout.write('\n🔑 CREDENCIALES DE DEMOSTRACIÓN:')
        self.stdout.write('=' * 40)
        for user_data in demo_users:
            if user_data['role'] == 'admin':
                icon = '👑'
            elif user_data['role'] == 'profesor':
                icon = '👨‍🏫'
            else:
                icon = '👨‍🎓'
            
            # Necesitamos restaurar la password para mostrarla
            if user_data['username'] == 'admin':
                password = 'admin123'
            elif user_data['username'] == 'profesor1':
                password = 'profesor123'
            else:
                password = 'estudiante123'
                
            self.stdout.write(
                f'{icon} {user_data["role"].title()}: '
                f'{user_data["username"]} / {password}'
            )
        
        self.stdout.write('\n🌐 Acceso: http://localhost:8000/')
        self.stdout.write('=' * 50) 