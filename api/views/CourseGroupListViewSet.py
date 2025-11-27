from rest_framework import viewsets, mixins
from api.models import CourseGroup
from api.serializers.CourseGroupSerializer import CourseGroupSerializer

class CourseGroupListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = CourseGroup.objects.all().select_related('course')
    serializer_class = CourseGroupSerializer
