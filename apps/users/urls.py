# urls.py para la app users
# Aquí se definirán las rutas de la app users.

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView,
)

from .views import AuthViewSet, UserViewSet, ProfileViewSet

# Configurar routers
router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles', ProfileViewSet, basename='profile')

urlpatterns = [
    # Rutas del router
    path('', include(router.urls)),
    
    # Rutas JWT estándar
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
] 