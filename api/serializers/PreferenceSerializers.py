from rest_framework import serializers
from api.models import CourseSessionPolicy, CourseDayPreference, CourseTeacherPreference, CourseShiftPreference, TeacherUnavailability
from django.core.exceptions import ValidationError

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

    def validate(self, data):
        # Para update, instance existe; para create, no
        instance = self.instance or TeacherUnavailability(**data)
        # Asignar valores nuevos para validación
        for attr, value in data.items():
            setattr(instance, attr, value)
        try:
            instance.full_clean()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        return data
