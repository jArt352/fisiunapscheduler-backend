from rest_framework import serializers
from api.models import CourseGroup, CourseOffering

class CourseGroupBulkCreateSerializer(serializers.Serializer):
    course_offering = serializers.PrimaryKeyRelatedField(queryset=CourseOffering.objects.all())
    num_groups = serializers.IntegerField(min_value=1)

    def create(self, validated_data):
        course_offering = validated_data['course_offering']
        num_groups = validated_data['num_groups']
        created = []
        last_code = CourseGroup.objects.filter(course_offering=course_offering).order_by('-code').first()
        start = int(last_code.code) + 1 if last_code and last_code.code.isdigit() else 1
        for i in range(start, start + num_groups):
            group = CourseGroup.objects.create(course_offering=course_offering, code=str(i))
            created.append(group)
        return created
