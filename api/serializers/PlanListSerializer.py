from rest_framework import serializers
from api.models import Plan, Course

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'code', 'name', 'cycle', 'practical_hours', 'theoretical_hours', 'credits']

class PlanWithCoursesSerializer(serializers.ModelSerializer):
    courses = CourseSerializer(many=True, read_only=True)
    class Meta:
        model = Plan
        fields = ['id', 'name', 'description', 'school', 'start_year', 'end_year', 'is_active', 'courses']
