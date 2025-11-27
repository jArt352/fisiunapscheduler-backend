from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import authenticate

from api.models import Person


COOKIE_NAME = 'refresh_token'


class JWTAuthViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.action in ['login', 'refresh']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def _set_refresh_cookie(self, response, refresh_token):
        # set cookie parameters
        secure = not settings.DEBUG
        max_age = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())
        response.set_cookie(
            COOKIE_NAME,
            str(refresh_token),
            httponly=True,
            secure=secure,
            samesite='Lax',
            max_age=max_age,
            # ensure cookie path matches the refresh/logout endpoints
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

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # rotate/blacklist handled by simplejwt settings when using token refresh endpoint
        response = Response({
            'access': access_token,
            'user': {
                'id': user.id,
                'username': user.get_username(),
                'email': getattr(user, 'email', None),
            }
        }, status=status.HTTP_200_OK)

        # set refresh cookie
        self._set_refresh_cookie(response, refresh)

        # include person info if available
        try:
            person = Person.objects.get(user=user)
            response.data['person_id'] = person.id
            # return roles as an array of role names (strings)
            response.data['roles'] = [g.name for g in person.roles.all()]
            # include person details for frontend convenience
            profile_image = None
            try:
                if person.profile_image and hasattr(person.profile_image, 'url'):
                    profile_image = request.build_absolute_uri(person.profile_image.url)
            except Exception:
                profile_image = None

            response.data['person'] = {
                'first_name': person.first_name,
                'last_name': person.last_name,
                'middle_name': person.middle_name,
                'profile_image': profile_image,
            }
        except Person.DoesNotExist:
            response.data['person_id'] = None
            response.data['roles'] = []

        return response

    @action(detail=False, methods=['post'])
    def refresh(self, request):
        # read refresh token from cookie
        token = request.COOKIES.get(COOKIE_NAME)
        if not token:
            return Response({'detail': 'No refresh token cookie present.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(token)
        except Exception as e:
            return Response({'detail': 'Refresh token inválido.'}, status=status.HTTP_401_UNAUTHORIZED)

        # blacklist the old refresh (rotation) if supported, then create a new one
        try:
            refresh.blacklist()
        except Exception:
            pass

        new_refresh = RefreshToken.for_user(refresh.user)
        access = str(new_refresh.access_token)

        response = Response({'access': access}, status=status.HTTP_200_OK)
        # set new refresh cookie (rotation)
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
                profile_image = None

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
        # invalidate refresh token from cookie (blacklist)
        token = request.COOKIES.get(COOKIE_NAME)
        if token:
            try:
                refresh = RefreshToken(token)
                try:
                    refresh.blacklist()
                except Exception:
                    pass
            except Exception:
                pass

        response = Response({'detail': 'Sesión cerrada correctamente.'}, status=status.HTTP_200_OK)
        # delete cookie
        response.delete_cookie(COOKIE_NAME, path='/api/jwt/refresh/')
        return response