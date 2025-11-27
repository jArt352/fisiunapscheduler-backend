from rest_framework import viewsets
from api.models import Shift
from api.serializers.ShiftSerializer import ShiftSerializer

class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all().order_by('start_time')
    serializer_class = ShiftSerializer
