from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import authenticate
from api.models import Person

COOKIE_NAME = 'refresh_token'

class JWTAuthViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def _set_refresh_cookie(self, response, refresh_token):
        # Calculamos el tiempo de vida
        try:
            max_age = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())
        except (AttributeError, KeyError):
            # Fallback seguro: 7 días en segundos
            max_age = 7 * 24 * 60 * 60

        # CONFIGURACIÓN CRÍTICA PARA LOCALHOST:
        secure = False if settings.DEBUG else True

        response.set_cookie(
            COOKIE_NAME,
            str(refresh_token),
            httponly=True,
            secure=secure, 
            samesite='Lax',
            max_age=max_age,
            path='/api/jwt/refresh/'
        )

    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'detail': 'username and password required'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request=request, username=username, password=password)
        if user is None:
            return Response({'detail': 'Credenciales inválidas.'}, status=status.HTTP_401_UNAUTHORIZED)

        # 1. Generamos el Refresh Token Base
        refresh = RefreshToken.for_user(user)

        # 2. INYECCIÓN DE ROLES AL INICIAR SESIÓN (CRÍTICO)
        # Esto asegura que el usuario entre con un 'active_role' desde el segundo 0
        person_data = None
        try:
            person = Person.objects.get(user=user)
            roles = person.roles.all()
            
            if roles.exists():
                # Lógica de prioridad: Si es admin, entra como admin. Si no, el primero que tenga.
                # Puedes ajustar esta lógica según tu negocio.
                default_role = 'admin' if roles.filter(name='admin').exists() else roles.first().name
                
                # Inyectamos los datos en el token encriptado
                refresh['active_role'] = default_role
                refresh['roles'] = [r.name for r in roles]

            # Preparamos datos para la respuesta JSON (Frontend UI)
            person_id = person.id
            roles_list = [g.name for g in roles]
            
            profile_image = None
            try:
                if person.profile_image and hasattr(person.profile_image, 'url'):
                    profile_image = request.build_absolute_uri(person.profile_image.url)
            except Exception:
                pass

            person_data = {
                'first_name': person.first_name,
                'last_name': person.last_name,
                'middle_name': person.middle_name,
                'profile_image': profile_image,
            }

        except Person.DoesNotExist:
            person_id = None
            roles_list = []

        # 3. Generamos el Access Token (que ahora incluye los roles inyectados arriba)
        access_token = str(refresh.access_token)

        response = Response({
            'access': access_token,
            'user': {
                'id': user.id,
                'username': user.get_username(),
                'email': getattr(user, 'email', None),
            },
            'person_id': person_id,
            'roles': roles_list,
            'person': person_data
        }, status=status.HTTP_200_OK)

        self._set_refresh_cookie(response, refresh)
        return response

    @action(detail=False, methods=['post'])
    def refresh(self, request):
        token = request.COOKIES.get(COOKIE_NAME)
        
        if not token:
            return Response({'detail': 'No refresh token cookie present.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(token)
        except Exception:
            return Response({'detail': 'Refresh token inválido.'}, status=status.HTTP_401_UNAUTHORIZED)

        if settings.SIMPLE_JWT.get('BLACKLIST_AFTER_ROTATION', False):
            try:
                refresh.blacklist()
            except Exception:
                pass

        # Generamos nuevo refresh token
        new_refresh = RefreshToken.for_user(refresh.user)
        
        # OJO: Al refrescar, tratamos de preservar el active_role del token anterior si es posible,
        # o dejamos que el frontend fuerce un switch si se pierde.
        # Por simplicidad, aquí regeneramos el token base.
        # Si quisieras persistir el rol activo en el refresh automático, deberías leerlo del 'refresh' viejo
        # y copiarlo al 'new_refresh'.
        try:
            old_payload = refresh.payload
            if 'active_role' in old_payload:
                new_refresh['active_role'] = old_payload['active_role']
            if 'roles' in old_payload:
                new_refresh['roles'] = old_payload['roles']
        except:
            pass

        access = str(new_refresh.access_token)

        response = Response({'access': access}, status=status.HTTP_200_OK)
        self._set_refresh_cookie(response, new_refresh)
        return response

    @action(detail=False, methods=['get'])
    def me(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({'detail': 'No authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            person = Person.objects.get(user=user)
            profile_image = None
            try:
                if person.profile_image and hasattr(person.profile_image, 'url'):
                    profile_image = request.build_absolute_uri(person.profile_image.url)
            except Exception:
                pass

            data = {
                'user': {
                    'id': user.id,
                    'username': user.get_username(),
                    'email': getattr(user, 'email', None),
                },
                'person_id': person.id,
                'person': {
                    'first_name': person.first_name,
                    'last_name': person.last_name,
                    'middle_name': person.middle_name,
                    'profile_image': profile_image,
                },
                'roles': [g.name for g in person.roles.all()]
            }
            return Response(data, status=status.HTTP_200_OK)
        except Person.DoesNotExist:
            return Response({'user': {'id': user.id, 'username': user.get_username(), 'email': getattr(user, 'email', None)}, 'person_id': None, 'roles': []}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        token = request.COOKIES.get(COOKIE_NAME)
        if token:
            try:
                refresh = RefreshToken(token)
                refresh.blacklist()
            except Exception:
                pass
        
        response = Response({'detail': 'Logout successful'}, status=status.HTTP_200_OK)
        response.delete_cookie(COOKIE_NAME, path='/api/jwt/refresh/')
        return response

    @action(detail=False, methods=['post'], url_path='switch-role')
    def switch_role(self, request):
        role_name = request.data.get('role')
        if not role_name:
            return Response({'detail': 'Role name required'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.is_authenticated:
            return Response({'detail': 'Unauthenticated'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            person = Person.objects.get(user=user)
            
            # 1. Validamos permisos
            if not person.roles.filter(name=role_name).exists():
                return Response({'detail': 'No tienes permisos para este rol.'}, status=status.HTTP_403_FORBIDDEN)
            
            # 2. Generamos nuevo token
            refresh = RefreshToken.for_user(user)
            
            # 3. 🔥 CRÍTICO: Inyectamos el rol activo en el nuevo token 🔥
            refresh['active_role'] = role_name 
            refresh['roles'] = [r.name for r in person.roles.all()] # Opcional pero útil
            
            access = str(refresh.access_token)
            
            return Response({
                'detail': 'Role switched successfully', 
                'access': access # <--- NextAuth necesita esto
            }, status=status.HTTP_200_OK)

        except Person.DoesNotExist:
            return Response({'detail': 'Person profile not found'}, status=status.HTTP_404_NOT_FOUND)