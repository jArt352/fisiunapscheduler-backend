from rest_framework.permissions import AllowAny
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from api.models import Plan
from api.serializers.PlanListSerializer import PlanWithCoursesSerializer

class PlanListViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.all().select_related('school').prefetch_related('courses')
    serializer_class = PlanWithCoursesSerializer
    permission_classes = [AllowAny]
