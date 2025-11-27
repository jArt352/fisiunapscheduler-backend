from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from api.models import Course, CourseOffering, AcademicPeriod, CourseGroupConfig
from api.serializers.CourseOfferingAddSerializer import CourseOfferingAddSerializer
from api.serializers.CourseOfferingListSerializer import CourseOfferingListSerializer
from django.db import transaction

class CourseOfferingManualNormalWithGroupsViewSet(viewsets.ViewSet):
    """
    Endpoint para agregar manualmente CourseOffering de tipo 'normal' y establecer el número de grupos.
    """
    @action(detail=False, methods=['post'])
    @transaction.atomic
    def add_normal_with_groups(self, request):
        serializer = CourseOfferingAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course_ids = serializer.validated_data['course_ids']
        period_id = serializer.validated_data['academic_period_id']
        num_groups = request.data.get('num_groups')
        if not num_groups or not isinstance(num_groups, int) or num_groups < 1:
            return Response({'detail': 'num_groups debe ser un entero positivo.'}, status=400)
        period = AcademicPeriod.objects.get(id=period_id)
        added = []
        for cid in course_ids:
            exists = CourseOffering.objects.filter(course_id=cid, academic_period=period, offering_type='normal').exists()
            if not exists:
                co = CourseOffering.objects.create(course_id=cid, academic_period=period, offering_type='normal')
                added.append(co)
            else:
                co = CourseOffering.objects.get(course_id=cid, academic_period=period, offering_type='normal')
                added.append(co)
            # Establecer el número de grupos
            CourseGroupConfig.objects.update_or_create(
                course_id=cid,
                defaults={'num_groups': num_groups}
            )
        data = CourseOfferingListSerializer(added, many=True).data
        return Response({'added': data}, status=status.HTTP_201_CREATED)
