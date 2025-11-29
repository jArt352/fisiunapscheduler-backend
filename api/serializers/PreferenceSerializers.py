from rest_framework import serializers
from api.models import CourseSessionPolicy, CourseDayPreference, CourseTeacherPreference, CourseShiftPreference, TeacherUnavailability

class CourseSessionPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseSessionPolicy
        fields = '__all__'

class CourseDayPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseDayPreference
        fields = '__all__'

class CourseTeacherPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseTeacherPreference
        fields = '__all__'

class CourseShiftPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseShiftPreference
        fields = '__all__'

class TeacherUnavailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherUnavailability
        fields = '__all__'
