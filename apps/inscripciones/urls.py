# urls.py para la app inscripciones
# Rutas para inscribirse a materias, ver mis inscripciones, calificaciones

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import InscripcionViewSet, CalificacionViewSet

# Configurar routers
router = DefaultRouter()
router.register(r'inscripciones', InscripcionViewSet, basename='inscripcion')
router.register(r'calificaciones', CalificacionViewSet, basename='calificacion')

urlpatterns = [
    # Rutas del router
    path('', include(router.urls)),
] 