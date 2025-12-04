from rest_framework import viewsets
from api.models import Room
from api.serializers.RoomFullSerializer import RoomFullSerializer

class RoomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Room.objects.select_related('site').all().order_by('name')
    serializer_class = RoomFullSerializer
