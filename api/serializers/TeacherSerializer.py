from rest_framework import serializers
from api.models import Teacher


class TeacherSerializer(serializers.ModelSerializer):
    person_name = serializers.CharField(source='person.__str__', read_only=True)
    email = serializers.EmailField(source='person.email', read_only=True)
    dni = serializers.CharField(source='person.dni', read_only=True)
    profile_image = serializers.ImageField(source='person.profile_image', read_only=True)

    class Meta:
        model = Teacher
        fields = [
            'id', 'person_name', 'email', 'dni', 'profile_image',
            'contract_type', 'min_weekly_hours', 'max_unavailability_hours'
        ]
