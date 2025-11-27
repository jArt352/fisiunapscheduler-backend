from rest_framework import serializers
from api.models import AcademicPeriod



class AcademicPeriodCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicPeriod
        fields = ['year', 'period', 'start_schedule_creation', 'end_schedule_creation', 'end_date']

    def validate(self, attrs):
        # Solo permitir crear si no hay periodo activo (sin cierre)
        if AcademicPeriod.objects.filter(end_date__isnull=True).exists():
            raise serializers.ValidationError("Ya existe un periodo académico activo (sin cierre). Cierre el periodo anterior antes de crear uno nuevo.")
        return attrs

    def create(self, validated_data):
        period = AcademicPeriod.objects.create(**validated_data)
        return period
