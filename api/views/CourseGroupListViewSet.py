from rest_framework import viewsets, mixins
from api.models import CourseGroup
from api.serializers.CourseGroupSerializer import CourseGroupSerializer


class CourseGroupListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = CourseGroupSerializer

    def get_queryset(self):
        queryset = CourseGroup.objects.all().select_related('course')
        course_id = self.request.query_params.get('course')
        if course_id is not None:
            queryset = queryset.filter(course_id=course_id)
        return queryset
