from rest_framework.permissions import AllowAny
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from api.models import Plan
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from api.serializers.PlanListSerializer import PlanWithCoursesSerializer

class PlanAdminViewSet(mixins.UpdateModelMixin, mixins.DestroyModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanWithCoursesSerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        plan = self.get_object()
        plan.is_active = True
        plan.save()
        return Response({'status': 'Plan activado', 'is_active': plan.is_active})

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate(self, request, pk=None):
        plan = self.get_object()
        plan.is_active = False
        plan.save()
        return Response({'status': 'Plan desactivado', 'is_active': plan.is_active})
