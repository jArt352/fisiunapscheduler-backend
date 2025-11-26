from django.contrib.auth.models import Group
from rest_framework import viewsets
from api.serializers.GroupSerializer import GroupSerializer


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """Lista los grupos de autenticación con su id y nombre."""
    queryset = Group.objects.all().order_by('id')
    serializer_class = GroupSerializer
