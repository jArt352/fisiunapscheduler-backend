from rest_framework import serializers

class CourseOfferingAddNormalWithGroupsSerializer(serializers.Serializer):
    course_id = serializers.IntegerField(help_text="ID del curso a agregar manualmente como normal.")
    academic_period_id = serializers.IntegerField(help_text="ID del periodo académico.")
    num_groups = serializers.IntegerField(help_text="Número de grupos a crear.")
