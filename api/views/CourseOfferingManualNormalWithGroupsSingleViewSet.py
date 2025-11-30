from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from api.models import Course, CourseOffering, AcademicPeriod, CourseGroupConfig
from api.serializers.CourseOfferingListSerializer import CourseOfferingListSerializer
from api.serializers.CourseOfferingAddNormalWithGroupsSerializer import CourseOfferingAddNormalWithGroupsSerializer
from django.db import transaction

class CourseOfferingManualNormalWithGroupsSingleViewSet(viewsets.ViewSet):
    """
    Endpoint para agregar manualmente CourseOffering de tipo 'normal' y establecer el número de grupos, curso por curso.
    """
    @action(detail=False, methods=['post'])
    @transaction.atomic
    def add_normal_with_groups_single(self, request):
        serializer = CourseOfferingAddNormalWithGroupsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course_id = serializer.validated_data['course_id']
        period_id = serializer.validated_data['academic_period_id']
        num_groups = serializer.validated_data['num_groups']
        try:
            period = AcademicPeriod.objects.get(id=period_id)
        except AcademicPeriod.DoesNotExist:
            return Response({'detail': 'Periodo académico no encontrado.'}, status=404)
        co, created = CourseOffering.objects.get_or_create(
            course_id=course_id, academic_period=period, offering_type='normal'
        )
        CourseGroupConfig.objects.update_or_create(
            course_offering=co,
            defaults={'num_groups': num_groups}
        )
        data = CourseOfferingListSerializer(co).data
        return Response({'added': [data]}, status=status.HTTP_201_CREATED)
