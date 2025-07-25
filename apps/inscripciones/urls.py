# urls.py para la app inscripciones
# Aquí se definirán las rutas de la app inscripciones.

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