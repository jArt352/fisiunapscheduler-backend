from rest_framework import serializers
from api.models import CourseTeacherPreferenceRequest

class CourseTeacherPreferenceRequestSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.person.__str__', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    class Meta:
        model = CourseTeacherPreferenceRequest
        fields = [
            'id', 'course', 'course_name', 'teacher', 'teacher_name', 'level', 'notes',
            'status', 'created_at', 'reviewed_at', 'reviewed_by'
        ]
        read_only_fields = ['status', 'created_at', 'reviewed_at', 'reviewed_by']
