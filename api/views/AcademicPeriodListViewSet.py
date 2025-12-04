from rest_framework import viewsets, mixins
from api.models import AcademicPeriod
from api.serializers.AcademicPeriodListSerializer import AcademicPeriodListSerializer
from django.utils import timezone

class AcademicPeriodListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = AcademicPeriod.objects.all().order_by('-year', '-period')
    serializer_class = AcademicPeriodListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtro para obtener el periodo académico actual
        current = self.request.query_params.get('current', None)
        if current and current.lower() in ['true', '1']:
            now = timezone.now()
            queryset = queryset.filter(
                created_at__lte=now
            ).exclude(
                end_date__lt=now
            )
        return queryset
