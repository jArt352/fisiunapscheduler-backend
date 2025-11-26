from rest_framework.routers import DefaultRouter
from api.views import PersonCreateViewSet, GroupViewSet, AuthViewSet, JWTAuthViewSet

router = DefaultRouter()
router.register(r'persons/create', PersonCreateViewSet, basename='person-create')
router.register(r'groups', GroupViewSet, basename='groups')
router.register(r'auth', AuthViewSet, basename='auth')
# JWT auth (login -> sets refresh cookie, refresh -> uses cookie, logout -> clears cookie)
router.register(r'jwt', JWTAuthViewSet, basename='jwt-auth')
