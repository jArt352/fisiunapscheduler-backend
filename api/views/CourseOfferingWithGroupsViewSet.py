from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from api.models import Course, CourseOffering, AcademicPeriod, CourseGroupConfig
from api.serializers.CourseOfferingAddSerializer import CourseOfferingAddSerializer
from api.serializers.CourseOfferingListSerializer import CourseOfferingListSerializer
from django.db import transaction

class CourseOfferingWithGroupsViewSet(viewsets.ViewSet):
    """
    Endpoint para abrir cursos (CourseOffering) y establecer el número de grupos en un solo paso.
    Si el periodo es I o II, el tipo será 'nivelacion'. Si es III, será 'vacacional'.
    """
    @action(detail=False, methods=['post'])
    @transaction.atomic
    def open_with_groups(self, request):
        serializer = CourseOfferingAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course_ids = serializer.validated_data['course_ids']
        period_id = serializer.validated_data['academic_period_id']
        num_groups = request.data.get('num_groups')
        if not num_groups or not isinstance(num_groups, int) or num_groups < 1:
            return Response({'detail': 'num_groups debe ser un entero positivo.'}, status=400)
        period = AcademicPeriod.objects.get(id=period_id)
        if period.period in ['I', 'II']:
            offering_type = 'nivelacion'
        elif period.period == 'III':
            offering_type = 'vacacional'
        else:
            return Response({'detail': 'Periodo inválido.'}, status=400)

        added = []
        for cid in course_ids:
            co, created = CourseOffering.objects.get_or_create(
                course_id=cid, academic_period=period, offering_type=offering_type
            )
            # Establecer el número de grupos
            CourseGroupConfig.objects.update_or_create(
                course_offering=co,
                defaults={'num_groups': num_groups}
            )
            added.append(co)
        data = CourseOfferingListSerializer(added, many=True).data
        return Response({'added': data}, status=status.HTTP_201_CREATED)
