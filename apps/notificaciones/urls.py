# urls.py para la app notificaciones
# Rutas para ver notificaciones, marcarlas como leídas, configuraciones

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