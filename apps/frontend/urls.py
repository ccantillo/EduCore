# urls.py para la app frontend
# Rutas para la interfaz web - páginas HTML, formularios, dashboards

from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    # Páginas principales
    path('', views.IndexView.as_view(), name='index'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # Gestión académica
    path('materias/', views.MateriasView.as_view(), name='materias'),
    path('inscripciones/', views.InscripcionesView.as_view(), name='inscripciones'),
    path('notificaciones/', views.NotificacionesView.as_view(), name='notificaciones'),
    path('reportes/', views.ReportesView.as_view(), name='reportes'),
    path('periodos/', views.PeriodosView.as_view(), name='periodos'),
    
    # Autenticación y perfil
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('perfil/', views.PerfilView.as_view(), name='perfil'),
    
    # API endpoints para AJAX
    path('api/materias/', views.api_materias, name='api_materias'),
    path('api/inscripciones/', views.api_inscripciones, name='api_inscripciones'),
    path('api/notificaciones/', views.api_notificaciones, name='api_notificaciones'),
] 