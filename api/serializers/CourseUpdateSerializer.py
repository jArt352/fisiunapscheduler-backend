from rest_framework import serializers
from api.models import Course

class CourseUpdateSerializer(serializers.ModelSerializer):
    credits = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Course
        fields = ['id', 'name', 'theoretical_hours', 'practical_hours', 'cycle', 'code', 'credits']
        read_only_fields = ['id', 'code', 'plan']

    def update(self, instance, validated_data):
        # Si se provee 'credits', puedes manejarlo aquí si tu modelo lo soporta
        # pero en tu modelo actual no hay campo credits, así que lo ignoramos
        validated_data.pop('credits', None)
        return super().update(instance, validated_data)
