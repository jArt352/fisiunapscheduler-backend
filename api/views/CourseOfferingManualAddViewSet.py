from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from api.models import Course, CourseOffering, AcademicPeriod
from api.serializers.CourseOfferingAddSerializer import CourseOfferingAddSerializer
from api.serializers.CourseOfferingListSerializer import CourseOfferingListSerializer
from django.db import transaction

class CourseOfferingManualAddViewSet(viewsets.ViewSet):
    """
    Endpoint para agregar cursos manualmente a CourseOffering solo si no existen ya para ese periodo y tipo.
    Si el periodo es I o II, el tipo será 'nivelacion'. Si es III, será 'vacacional'.
    """
    @action(detail=False, methods=['post'])
    @transaction.atomic
    def add_courses(self, request):
        serializer = CourseOfferingAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course_ids = serializer.validated_data['course_ids']
        period_id = serializer.validated_data['academic_period_id']
        period = AcademicPeriod.objects.get(id=period_id)
        if period.period in ['I', 'II']:
            offering_type = 'nivelacion'
        elif period.period == 'III':
            offering_type = 'vacacional'
        else:
            return Response({'detail': 'Periodo inválido.'}, status=400)

        # Solo agregar cursos que no tengan offering manual de este tipo en este periodo
        added = []
        for cid in course_ids:
            exists = CourseOffering.objects.filter(course_id=cid, academic_period=period, offering_type=offering_type).exists()
            if not exists:
                co = CourseOffering.objects.create(course_id=cid, academic_period=period, offering_type=offering_type)
                added.append(co)
        data = CourseOfferingListSerializer(added, many=True).data
        return Response({'added': data}, status=status.HTTP_201_CREATED)
