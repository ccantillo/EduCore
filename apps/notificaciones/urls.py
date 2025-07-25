# urls.py para la app notificaciones
# Aquí se definirán las rutas de la app notificaciones.

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import NotificacionViewSet

# Configurar routers
router = DefaultRouter()
router.register(r'notificaciones', NotificacionViewSet, basename='notificacion')

urlpatterns = [
    # Rutas del router
    path('', include(router.urls)),
] 