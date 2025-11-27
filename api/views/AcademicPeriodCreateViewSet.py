from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from api.serializers.AcademicPeriodCreateSerializer import AcademicPeriodCreateSerializer
from api.models import AcademicPeriod

class AcademicPeriodCreateViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = AcademicPeriod.objects.all()
    serializer_class = AcademicPeriodCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        period = serializer.save()
        return Response({
            'id': period.id,
            'year': period.year,
            'period': period.period,
            'start_schedule_creation': period.start_schedule_creation,
            'end_schedule_creation': period.end_schedule_creation,
            'end_date': period.end_date,
        }, status=status.HTTP_201_CREATED)
