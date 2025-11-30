from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login, logout as django_logout

from api.serializers.AuthSerializer import LoginSerializer, LogoutSerializer
from api.models import Person


class AuthViewSet(viewsets.ViewSet):
    """Simple auth endpoints using token auth.

    Endpoints:
    - POST /api/auth/login/  -> {username, password} returns {token, user}
    - POST /api/auth/logout/ -> requires token; deletes token
    """

    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(request=request, username=username, password=password)
        if user is None:
            return Response({'detail': 'Credenciales inválidas.'}, status=status.HTTP_401_UNAUTHORIZED)

        # create or get token
        token, created = Token.objects.get_or_create(user=user)

        # optional: also create session cookie for browsable API
        django_login(request, user)

        # try to find related Person
        try:
            person = Person.objects.get(user=user)
            person_id = person.id
            roles = [{'id': g.id, 'name': g.name} for g in person.roles.all()]
        except Person.DoesNotExist:
            person_id = None
            roles = []

        data = {
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.get_username(),
                'email': getattr(user, 'email', None),
            },
            'person_id': person_id,
            'roles': roles,
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        # require authentication
        user = request.user
        # delete token if present
        try:
            token = Token.objects.get(user=user)
            token.delete()
        except Token.DoesNotExist:
            pass

        try:
            django_logout(request)
        except Exception:
            pass

        return Response({'detail': 'Sesión cerrada correctamente.'}, status=status.HTTP_200_OK)
