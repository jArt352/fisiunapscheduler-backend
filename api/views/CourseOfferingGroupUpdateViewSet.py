from rest_framework import viewsets, mixins
from api.models import CourseOffering
from api.serializers.CourseOfferingGroupUpdateSerializer import CourseOfferingGroupUpdateSerializer

class CourseOfferingGroupUpdateViewSet(mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = CourseOffering.objects.all()
    serializer_class = CourseOfferingGroupUpdateSerializer
