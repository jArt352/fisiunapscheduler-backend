from rest_framework.permissions import AllowAny
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from api.models import CourseTeacherPreferenceRequest, Person
from api.serializers.CourseTeacherPreferenceRequestSerializer import CourseTeacherPreferenceRequestSerializer

class CourseTeacherPreferenceRequestViewSet(viewsets.ModelViewSet):
    queryset = CourseTeacherPreferenceRequest.objects.all()
    serializer_class = CourseTeacherPreferenceRequestSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # El docente autenticado crea la solicitud
        teacher = self.request.user.person.teacher
        serializer.save(teacher=teacher, status='pendiente')

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        # Solo director de escuela puede aceptar
        req = self.get_object()
        user = request.user
        if not hasattr(user.person, 'school_director_roles') or not user.person.school_director_roles.exists():
            return Response({'detail': 'Solo el director de escuela puede aceptar.'}, status=403)
        req.status = 'aceptado'
        req.reviewed_at = timezone.now()
        req.reviewed_by = user.person
        req.save()
        return Response(self.get_serializer(req).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        # Solo director de escuela puede rechazar
        req = self.get_object()
        user = request.user
        if not hasattr(user.person, 'school_director_roles') or not user.person.school_director_roles.exists():
            return Response({'detail': 'Solo el director de escuela puede rechazar.'}, status=403)
        req.status = 'rechazado'
        req.reviewed_at = timezone.now()
        req.reviewed_by = user.person
        req.save()
        return Response(self.get_serializer(req).data)
