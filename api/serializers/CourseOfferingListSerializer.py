from rest_framework import serializers
from api.models import CourseOffering

class CourseOfferingListSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source='course.code')
    course_name = serializers.CharField(source='course.name')
    credits = serializers.IntegerField(source='course.credits')
    cycle = serializers.IntegerField(source='course.cycle')
    num_groups = serializers.SerializerMethodField()

    class Meta:
        model = CourseOffering
        fields = [
            'id', 'course_code', 'course_name', 'credits', 'cycle',
            'offering_type', 'academic_period', 'num_groups'
        ]

    def get_num_groups(self, obj):
        return obj.groups.count()
