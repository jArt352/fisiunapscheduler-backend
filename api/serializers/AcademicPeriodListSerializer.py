from rest_framework import serializers
from api.models import AcademicPeriod


from django.utils import timezone

class AcademicPeriodListSerializer(serializers.ModelSerializer):
    phase_config_start = serializers.SerializerMethodField()
    phase_config_end = serializers.SerializerMethodField()
    phase_creation_start = serializers.SerializerMethodField()
    phase_creation_end = serializers.SerializerMethodField()
    phase_changes_start = serializers.SerializerMethodField()
    phase_changes_end = serializers.SerializerMethodField()
    current_phase = serializers.SerializerMethodField()

    class Meta:
        model = AcademicPeriod
        fields = [
            'id', 'year', 'period', 'created_at',
            'start_schedule_creation', 'end_schedule_creation', 'end_date',
            'phase_config_start', 'phase_config_end',
            'phase_creation_start', 'phase_creation_end',
            'phase_changes_start', 'phase_changes_end',
            'current_phase'
        ]

    def get_phase_config_start(self, obj):
        return obj.created_at

    def get_phase_config_end(self, obj):
        return obj.start_schedule_creation

    def get_phase_creation_start(self, obj):
        return obj.start_schedule_creation

    def get_phase_creation_end(self, obj):
        return obj.end_schedule_creation

    def get_phase_changes_start(self, obj):
        return obj.end_schedule_creation

    def get_phase_changes_end(self, obj):
        return obj.end_date

    def get_current_phase(self, obj):
        now = timezone.now()
        if obj.created_at and now < obj.start_schedule_creation:
            return 'configuracion'
        elif obj.start_schedule_creation and now < obj.end_schedule_creation:
            return 'creacion_horarios'
        elif obj.end_schedule_creation and (obj.end_date is None or now < obj.end_date):
            return 'cambios'
        elif obj.end_date and now >= obj.end_date:
            return 'cerrado'
        return 'desconocido'
