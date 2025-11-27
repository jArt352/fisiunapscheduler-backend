from rest_framework import serializers
from api.models import AcademicPeriod



class AcademicPeriodCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicPeriod
        fields = ['year', 'period', 'start_schedule_creation', 'end_schedule_creation', 'end_date']

    def create(self, validated_data):
        period = AcademicPeriod.objects.create(**validated_data)
        return period
