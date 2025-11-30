from rest_framework import serializers
from api.models import GeneralScheduleConfig

class GeneralScheduleConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneralScheduleConfig
        fields = '__all__'
