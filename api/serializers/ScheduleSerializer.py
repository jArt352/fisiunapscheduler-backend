from rest_framework import serializers
from api.models import Schedule


class ScheduleSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source='room.name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    group_code = serializers.CharField(source='group.code', read_only=True)
    teacher_name = serializers.SerializerMethodField()
    id_persona = serializers.SerializerMethodField()


    class Meta:
        model = Schedule
        fields = [
            'id', 'course', 'course_name', 'group', 'group_code', 'teacher', 'teacher_name', 'id_persona',
            'room', 'room_name', 'day_of_week', 'start_time', 'end_time', 'session_type'
        ]

    def get_teacher_name(self, obj):
        if obj.teacher and obj.teacher.person:
            return f"{obj.teacher.person.first_name} {obj.teacher.person.last_name}"
        return None

    def get_id_persona(self, obj):
        if obj.teacher and obj.teacher.person:
            return obj.teacher.person.id
        return None
