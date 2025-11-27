from rest_framework import serializers
from api.models import AcademicPeriod

class AcademicPeriodUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicPeriod
        fields = ['year', 'period', 'start_schedule_creation', 'end_schedule_creation', 'end_date']
