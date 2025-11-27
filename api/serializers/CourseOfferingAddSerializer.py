from rest_framework import serializers

class CourseOfferingAddSerializer(serializers.Serializer):
    course_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="IDs de los cursos a agregar manualmente al periodo."
    )
    academic_period_id = serializers.IntegerField(help_text="ID del periodo académico.")
