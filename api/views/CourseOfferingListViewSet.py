from rest_framework import viewsets, mixins
from api.models import CourseOffering
from api.serializers.CourseOfferingListSerializer import CourseOfferingListSerializer

class CourseOfferingListViewSet(mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = CourseOffering.objects.all().select_related('course', 'academic_period')
    serializer_class = CourseOfferingListSerializer
