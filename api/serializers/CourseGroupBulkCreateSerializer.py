from rest_framework import serializers
from api.models import CourseGroup, Course

class CourseGroupBulkCreateSerializer(serializers.Serializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    num_groups = serializers.IntegerField(min_value=1)

    def create(self, validated_data):
        course = validated_data['course']
        num_groups = validated_data['num_groups']
        created = []
        # Buscar el máximo code existente para ese curso
        last_code = CourseGroup.objects.filter(course=course).order_by('-code').first()
        start = int(last_code.code) + 1 if last_code and last_code.code.isdigit() else 1
        for i in range(start, start + num_groups):
            group = CourseGroup.objects.create(course=course, code=str(i))
            created.append(group)
        return created
