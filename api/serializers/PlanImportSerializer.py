from rest_framework import serializers
from api.models import Plan, Course, School


class CourseInputSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=200)
    credits = serializers.IntegerField(required=False, default=0)
    hours_theory = serializers.IntegerField(required=False, default=0)
    hours_practice = serializers.IntegerField(required=False, default=0)
    cycle = serializers.IntegerField(required=False)


class PlanImportSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    school = serializers.IntegerField()  # maps to School id
    start_year = serializers.IntegerField()
    end_year = serializers.IntegerField(required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False, default=True)
    courses = serializers.ListField(child=CourseInputSerializer())

    def validate_school(self, value):
        try:
            School.objects.get(pk=value)
        except School.DoesNotExist:
            raise serializers.ValidationError('Escuela no encontrada')
        return value

    def create(self, validated_data):
        school_id = validated_data.pop('school')
        courses_data = validated_data.pop('courses', [])
        school = School.objects.get(pk=school_id)

        plan = Plan.objects.create(school=school, **validated_data)

        created = []
        errors = []
        for idx, c in enumerate(courses_data):
            try:
                course = Course.objects.create(
                    code=c.get('code'),
                    name=c.get('name'),
                    credits=c.get('credits') or 0,
                    cycle=c.get('cycle') or 0,
                    practical_hours=c.get('hours_practice') or 0,
                    theoretical_hours=c.get('hours_theory') or 0,
                    plan=plan
                )
                created.append({'index': idx, 'id': course.id, 'code': course.code})
            except Exception as e:
                errors.append({'index': idx, 'error': str(e), 'code': c.get('code')})

        return {'plan': plan, 'created_courses': created, 'errors': errors}
