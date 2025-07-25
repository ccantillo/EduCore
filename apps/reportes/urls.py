# urls.py para la app reportes
# Rutas para generar reportes, descargar archivos, ver historial

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ReporteViewSet,
    ReporteEstudianteViewSet,
    ReporteProfesorViewSet,
    EstudianteReportAPIView,
    ProfesorReportAPIView
)

# Configurar routers
router = DefaultRouter()
router.register(r'reportes', ReporteViewSet, basename='reporte')
router.register(r'estudiantes', ReporteEstudianteViewSet, basename='reporte_estudiante')
router.register(r'profesores', ReporteProfesorViewSet, basename='reporte_profesor')

urlpatterns = [
    # Endpoints específicos que cumplen exactamente con los requisitos del PDF
    path('estudiante/<int:id>/', EstudianteReportAPIView.as_view(), name='reporte_estudiante_csv'),
    path('profesor/<int:id>/', ProfesorReportAPIView.as_view(), name='reporte_profesor_csv'),
    
    # Rutas del router (endpoints avanzados existentes)
    path('', include(router.urls)),
] 