from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from api.models import Course, CourseOffering, AcademicPeriod
from api.serializers.CourseOfferingAddSerializer import CourseOfferingAddSerializer
from api.serializers.CourseOfferingListSerializer import CourseOfferingListSerializer
from django.db import transaction

class CourseOfferingManualNormalViewSet(viewsets.ViewSet):
    """
    Endpoint para agregar manualmente CourseOffering de tipo 'normal'.
    """
    @action(detail=False, methods=['post'])
    @transaction.atomic
    def add_normal(self, request):
        serializer = CourseOfferingAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course_ids = serializer.validated_data['course_ids']
        period_id = serializer.validated_data['academic_period_id']
        period = AcademicPeriod.objects.get(id=period_id)
        added = []
        for cid in course_ids:
            exists = CourseOffering.objects.filter(course_id=cid, academic_period=period, offering_type='normal').exists()
            if not exists:
                co = CourseOffering.objects.create(course_id=cid, academic_period=period, offering_type='normal')
                added.append(co)
        data = CourseOfferingListSerializer(added, many=True).data
        return Response({'added': data}, status=status.HTTP_201_CREATED)
