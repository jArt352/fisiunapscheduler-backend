from rest_framework import viewsets, mixins
from api.models import CourseGroupConfig
from api.serializers.CourseGroupConfigSerializer import CourseGroupConfigSerializer

class CourseGroupConfigViewSet(mixins.UpdateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = CourseGroupConfig.objects.select_related('course').all()
    serializer_class = CourseGroupConfigSerializer
