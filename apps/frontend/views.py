# views.py para la app frontend
# Vistas para la interfaz web - dashboards, formularios, páginas principales

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
import requests
from django.conf import settings


class IndexView(TemplateView):
    """Vista principal del sistema."""
    template_name = 'frontend/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sistema Académico'
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard principal según el rol del usuario."""
    template_name = 'frontend/dashboard.html'
    
    def get_template_names(self):
        user = self.request.user
        if user.is_authenticated:
            if user.role == 'admin':
                return ['frontend/dashboard_admin.html']
            elif user.role == 'profesor':
                return ['frontend/dashboard_profesor.html']
            elif user.role == 'estudiante':
                return ['frontend/dashboard_estudiante.html']
        return ['frontend/dashboard.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dashboard'
        context['user_role'] = self.request.user.role
        return context


class MateriasView(LoginRequiredMixin, TemplateView):
    """Vista para gestión de materias."""
    template_name = 'frontend/materias.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Materias'
        return context


class InscripcionesView(LoginRequiredMixin, TemplateView):
    """Vista para gestión de inscripciones."""
    template_name = 'frontend/inscripciones.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Inscripciones'
        return context


class NotificacionesView(LoginRequiredMixin, TemplateView):
    """Vista para notificaciones."""
    template_name = 'frontend/notificaciones.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Notificaciones'
        return context


class ReportesView(LoginRequiredMixin, TemplateView):
    """Vista para reportes."""
    template_name = 'frontend/reportes.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Reportes'
        # Solo admins y profesores pueden ver reportes
        if not (self.request.user.role in ['admin', 'profesor']):
            return redirect('frontend:dashboard')
        return context


# Vistas de autenticación personalizadas
class CustomLoginView(auth_views.LoginView):
    """Vista de login personalizada."""
    template_name = 'frontend/auth/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return '/dashboard/'
    
    def form_valid(self, form):
        messages.success(self.request, f'¡Bienvenido, {form.get_user().get_full_name()}!')
        return super().form_valid(form)


class CustomLogoutView(auth_views.LogoutView):
    """Vista de logout personalizada."""
    next_page = '/'
    
    def dispatch(self, request, *args, **kwargs):
        messages.info(request, 'Has cerrado sesión exitosamente.')
        return super().dispatch(request, *args, **kwargs)


class PerfilView(LoginRequiredMixin, TemplateView):
    """Vista para gestión de perfil de usuario."""
    template_name = 'frontend/perfil.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mi Perfil'
        return context


class PeriodosView(LoginRequiredMixin, TemplateView):
    """Vista para gestión de períodos académicos."""
    template_name = 'frontend/periodos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Períodos Académicos'
        # Solo admins pueden acceder a períodos
        if self.request.user.role != 'admin':
            from django.shortcuts import redirect
            return redirect('frontend:dashboard')
        return context


# Vistas AJAX para interactuar con la API
@login_required
@require_http_methods(["GET"])
def api_materias(request):
    """Endpoint para obtener materias via AJAX."""
    try:
        # Aquí podrías hacer una llamada interna a tu API REST
        # O simplemente usar los modelos directamente
        from apps.materias.models import Materia
        
        materias = Materia.objects.filter(estado='activa')
        if request.user.role == 'profesor':
            materias = materias.filter(profesor=request.user)
        elif request.user.role == 'estudiante':
            # Estudiantes ven todas las materias activas
            pass
        
        data = [
            {
                'id': materia.id,
                'codigo': materia.codigo,
                'nombre': materia.nombre,
                'descripcion': materia.descripcion or '',
                'creditos': materia.creditos,
                'estado': materia.estado,
                'profesor': materia.profesor.get_full_name() if materia.profesor else 'Sin asignar',
                'estudiantes_count': materia.inscripciones.filter(estado='activa').count()
            }
            for materia in materias.select_related('profesor').prefetch_related('inscripciones')
        ]
        
        return JsonResponse({'materias': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_inscripciones(request):
    """Endpoint para obtener inscripciones via AJAX."""
    try:
        from apps.inscripciones.models import Inscripcion
        
        if request.user.role == 'estudiante':
            inscripciones = Inscripcion.objects.filter(
                estudiante=request.user
            ).select_related('materia', 'periodo')
        elif request.user.role == 'profesor':
            inscripciones = Inscripcion.objects.filter(
                materia__profesor=request.user
            ).select_related('estudiante', 'materia', 'periodo')
        else:  # admin
            inscripciones = Inscripcion.objects.all().select_related(
                'estudiante', 'materia', 'periodo'
            )
        
        data = [
            {
                'id': insc.id,
                'estudiante': insc.estudiante.get_full_name(),
                'materia': f"{insc.materia.codigo} - {insc.materia.nombre}",
                'periodo': insc.periodo.nombre,
                'estado': insc.estado,
                'nota_final': float(insc.nota_final) if insc.nota_final else None,
                'fecha_inscripcion': insc.fecha_inscripcion.strftime('%d/%m/%Y')
            }
            for insc in inscripciones
        ]
        
        return JsonResponse({'inscripciones': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_notificaciones(request):
    """Endpoint para obtener notificaciones via AJAX."""
    try:
        from apps.notificaciones.models import Notificacion
        
        notificaciones = Notificacion.objects.filter(
            usuario=request.user
        ).order_by('-fecha_creacion')[:10]  # Últimas 10
        
        data = [
            {
                'id': notif.id,
                'tipo': notif.tipo,
                'titulo': notif.titulo,
                'mensaje': notif.mensaje,
                'estado': notif.estado,
                'fecha': notif.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
                'es_no_leida': notif.es_no_leida
            }
            for notif in notificaciones
        ]
        
        return JsonResponse({'notificaciones': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500) 