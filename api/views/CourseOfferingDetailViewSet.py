from rest_framework import viewsets, mixins
from api.models import CourseOffering
from api.serializers.CourseOfferingDetailSerializer import CourseOfferingDetailSerializer

class CourseOfferingDetailViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = CourseOffering.objects.all().select_related('course', 'academic_period')
    serializer_class = CourseOfferingDetailSerializer
