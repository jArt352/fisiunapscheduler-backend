from rest_framework.permissions import AllowAny
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from api.models import Course
from api.serializers.CourseUpdateSerializer import CourseUpdateSerializer

class CourseUpdateViewSet(mixins.UpdateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseUpdateSerializer
    permission_classes = [AllowAny]
