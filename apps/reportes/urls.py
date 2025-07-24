# urls.py para la app reportes
# Aquí se definirán las rutas de la app reportes.

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ReporteViewSet,
    ReporteEstudianteViewSet,
    ReporteProfesorViewSet
)

# Configurar routers
router = DefaultRouter()
router.register(r'reportes', ReporteViewSet, basename='reporte')
router.register(r'estudiantes', ReporteEstudianteViewSet, basename='reporte_estudiante')
router.register(r'profesores', ReporteProfesorViewSet, basename='reporte_profesor')

urlpatterns = [
    # Rutas del router
    path('', include(router.urls)),
] 