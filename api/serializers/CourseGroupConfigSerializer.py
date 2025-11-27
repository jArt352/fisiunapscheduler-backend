from rest_framework import serializers
from api.models import CourseGroupConfig

class CourseGroupConfigSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source='course.code', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = CourseGroupConfig
        fields = ['id', 'course', 'course_code', 'course_name', 'num_groups']
        read_only_fields = ['id', 'course_code', 'course_name']
