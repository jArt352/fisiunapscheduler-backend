from rest_framework import viewsets, mixins
from api.models import AcademicPeriod
from api.serializers.AcademicPeriodUpdateSerializer import AcademicPeriodUpdateSerializer

class AcademicPeriodUpdateViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = AcademicPeriod.objects.all()
    serializer_class = AcademicPeriodUpdateSerializer
