from rest_framework import serializers
from api.models import AcademicPeriod

class AcademicPeriodListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicPeriod
        fields = [
            'id', 'year', 'period', 'created_at',
            'start_schedule_creation', 'end_schedule_creation', 'end_date'
        ]
