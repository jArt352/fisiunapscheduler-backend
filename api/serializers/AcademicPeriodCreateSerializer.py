from rest_framework import serializers
from api.models import AcademicPeriod



class AcademicPeriodCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicPeriod
        fields = ['year', 'period', 'start_schedule_creation', 'end_schedule_creation', 'end_date']

    def validate(self, attrs):
        # Solo permitir crear si no hay periodo activo (sin cierre)
        if AcademicPeriod.objects.filter(end_date__isnull=True).exists():
            raise serializers.ValidationError("Ya existe un periodo académico activo (sin cierre). Cierre el periodo anterior antes de crear uno nuevo.")
        return attrs

    def create(self, validated_data):
        from api.models import Plan, Course, CourseOffering, CourseGroup
        period = AcademicPeriod.objects.create(**validated_data)
        # Buscar plan activo
        plan = Plan.objects.filter(is_active=True).first()
        if plan and period.period in ["I", "II"]:
            # Determinar ciclos a ofertar
            if period.period == "I":
                ciclos = [1, 3, 5, 7, 9]
            else:
                ciclos = [2, 4, 6, 8, 10]
            cursos = plan.courses.filter(cycle__in=ciclos)
            for curso in cursos:
                offering, created = CourseOffering.objects.get_or_create(
                    course=curso,
                    academic_period=period,
                    offering_type="normal",
                    defaults={"capacity": 0}
                )
                # Crear grupo por defecto si no existe
                if not CourseGroup.objects.filter(course=curso).exists():
                    CourseGroup.objects.create(course=curso, code="1", capacity=0)
        return period
