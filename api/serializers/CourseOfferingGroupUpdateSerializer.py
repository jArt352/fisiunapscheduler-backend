from rest_framework import serializers
from api.models import CourseOffering

class CourseOfferingGroupUpdateSerializer(serializers.ModelSerializer):
    num_groups = serializers.IntegerField(write_only=True)

    class Meta:
        model = CourseOffering
        fields = ['id', 'num_groups']

    def update(self, instance, validated_data):
        from api.models import CourseGroup
        num_groups = validated_data.get('num_groups')
        course = instance.course
        current = course.groups.count()
        # Crear o eliminar grupos para igualar a num_groups
        if num_groups > current:
            for i in range(current + 1, num_groups + 1):
                CourseGroup.objects.create(course=course, code=str(i), capacity=0)
        elif num_groups < current:
            groups = course.groups.order_by('-code')[:current - num_groups]
            for g in groups:
                g.delete()
        return instance
