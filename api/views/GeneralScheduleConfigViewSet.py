from rest_framework import viewsets
from api.models import GeneralScheduleConfig
from api.serializers.GeneralScheduleConfigSerializer import GeneralScheduleConfigSerializer

class GeneralScheduleConfigViewSet(viewsets.ModelViewSet):
    queryset = GeneralScheduleConfig.objects.all()
    serializer_class = GeneralScheduleConfigSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
