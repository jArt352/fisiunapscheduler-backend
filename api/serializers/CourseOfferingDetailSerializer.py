from rest_framework import serializers
from api.models import CourseOffering, CourseGroup

class CourseOfferingDetailSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source='course.code')
    course_name = serializers.CharField(source='course.name')
    credits = serializers.IntegerField(source='course.credits')
    cycle = serializers.IntegerField(source='course.cycle')
    groups = serializers.SerializerMethodField()

    class Meta:
        model = CourseOffering
        fields = [
            'id', 'course_code', 'course_name', 'credits', 'cycle',
            'offering_type', 'academic_period', 'capacity', 'groups'
        ]

    def get_groups(self, obj):
        return [
            {
                'id': g.id,
                'code': g.code,
                'capacity': g.capacity,
                'teacher': g.teacher_id,
                'room': g.room_id,
                'shift': g.shift
            }
            for g in obj.course.groups.all()
        ]
