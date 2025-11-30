from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from api.models import CourseGroup
from api.serializers.CourseGroupBulkCreateSerializer import CourseGroupBulkCreateSerializer

class CourseGroupBulkCreateViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def create_groups(self, request):
        serializer = CourseGroupBulkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course_offering = serializer.validated_data['course_offering']
        num_groups = serializer.validated_data['num_groups']
        current = course_offering.groups.count()
        # Si hay que crear más
        if num_groups > current:
            for i in range(current + 1, num_groups + 1):
                CourseGroup.objects.create(course_offering=course_offering, code=str(i))
        # Si hay que eliminar
        elif num_groups < current:
            groups = course_offering.groups.order_by('-code')[:current - num_groups]
            for g in groups:
                g.delete()
        # Devuelve el listado actualizado
        groups = course_offering.groups.order_by('code').all()
        return Response({'groups': [{'id': g.id, 'code': g.code} for g in groups]}, status=status.HTTP_200_OK)
