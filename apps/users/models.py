# models.py para la app users
# Aquí se definirán los modelos relacionados con usuarios, roles y perfiles.

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class User(AbstractUser):
    """
    Modelo de usuario personalizado con roles específicos para el sistema académico.
    Extiende AbstractUser para mantener compatibilidad con Django.
    """
    
    # Opciones de roles
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('profesor', 'Profesor'),
        ('estudiante', 'Estudiante'),
    ]
    
    # Campos adicionales
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='estudiante',
        verbose_name='Rol'
    )
    
    # Validación de teléfono colombiano
    phone_regex = RegexValidator(
        regex=r'^(\+57)?[0-9]{10}$',
        message="El número de teléfono debe estar en formato: '+573001234567' o '3001234567'"
    )
    
    phone = models.CharField(
        validators=[phone_regex],
        max_length=15,
        blank=True,
        verbose_name='Teléfono'
    )
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        db_table = 'users'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        """Verifica si el usuario es administrador."""
        return self.role == 'admin'
    
    @property
    def is_profesor(self):
        """Verifica si el usuario es profesor."""
        return self.role == 'profesor'
    
    @property
    def is_estudiante(self):
        """Verifica si el usuario es estudiante."""
        return self.role == 'estudiante'
    
    def get_role_display_name(self):
        """Obtiene el nombre legible del rol."""
        return dict(self.ROLE_CHOICES)[self.role]


class Profile(models.Model):
    """
    Perfil extendido para información adicional de usuarios.
    Separado del modelo User para mantener flexibilidad.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Usuario'
    )
    
    # Información personal
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de nacimiento'
    )
    
    address = models.TextField(
        blank=True,
        verbose_name='Dirección'
    )
    
    # Información académica (para estudiantes)
    student_id = models.CharField(
        max_length=20,
        blank=True,
        unique=True,
        verbose_name='Código de estudiante'
    )
    
    # Información profesional (para profesores)
    professional_id = models.CharField(
        max_length=20,
        blank=True,
        unique=True,
        verbose_name='Código profesional'
    )
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')
    
    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'
        db_table = 'user_profiles'
    
    def __str__(self):
        return f"Perfil de {self.user.get_full_name()}"
    
    def save(self, *args, **kwargs):
        """Sobrescribe save para generar códigos automáticamente."""
        if not self.student_id and self.user.is_estudiante:
            # Generar código de estudiante único
            last_student = Profile.objects.filter(
                student_id__isnull=False,
                student_id__gt=''
            ).order_by('-student_id').first()
            
            if last_student and last_student.student_id:
                try:
                    last_number = int(last_student.student_id)
                    self.student_id = f"{last_number + 1:06d}"
                except ValueError:
                    self.student_id = "000001"
            else:
                self.student_id = "000001"
        
        if not self.professional_id and self.user.is_profesor:
            # Generar código profesional único
            last_professor = Profile.objects.filter(
                professional_id__isnull=False,
                professional_id__gt=''
            ).exclude(professional_id='').order_by('-professional_id').first()
            
            if last_professor and last_professor.professional_id:
                try:
                    # Remover la 'P' del inicio y convertir a número
                    last_number = int(last_professor.professional_id[1:])
                    self.professional_id = f"P{last_number + 1:04d}"
                except (ValueError, IndexError):
                    self.professional_id = "P0001"
            else:
                self.professional_id = "P0001"
        
        super().save(*args, **kwargs) 