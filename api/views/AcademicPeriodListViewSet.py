from rest_framework import viewsets, mixins
from api.models import AcademicPeriod
from api.serializers.AcademicPeriodListSerializer import AcademicPeriodListSerializer

class AcademicPeriodListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = AcademicPeriod.objects.all().order_by('-year', '-period')
    serializer_class = AcademicPeriodListSerializer
