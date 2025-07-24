# urls.py para la app materias
# Aquí se definirán las rutas de la app materias.

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MateriaViewSet, PrerrequisitoViewSet, PeriodoViewSet

# Configurar routers
router = DefaultRouter()
router.register(r'materias', MateriaViewSet, basename='materia')
router.register(r'prerrequisitos', PrerrequisitoViewSet, basename='prerrequisito')
router.register(r'periodos', PeriodoViewSet, basename='periodo')

urlpatterns = [
    # Rutas del router
    path('', include(router.urls)),
] 