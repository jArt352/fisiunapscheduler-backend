from rest_framework import serializers
from api.models import CourseGroup

class CourseGroupSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source='course_offering.course.code')
    course_name = serializers.CharField(source='course_offering.course.name')

    class Meta:
        model = CourseGroup
        fields = ['id', 'course_code', 'course_name', 'code']
