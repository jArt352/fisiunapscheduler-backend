
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from api.models import Teacher
from api.serializers import TeacherSerializer


class TeacherViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Teacher.objects.select_related('person').all()
        person_id = self.request.query_params.get('person')
        if person_id:
            queryset = queryset.filter(person_id=person_id)
        return queryset

    @action(detail=False, methods=['get'])
    def me(self, request):
        user = request.user
        if not user or not user.is_authenticated:
            return Response({'detail': 'No autenticado'}, status=401)
        try:
            teacher = Teacher.objects.select_related('person').get(person__user=user)
            data = TeacherSerializer(teacher, context={'request': request}).data
            return Response(data)
        except Teacher.DoesNotExist:
            return Response({'detail': 'El usuario autenticado no es docente'}, status=404)
