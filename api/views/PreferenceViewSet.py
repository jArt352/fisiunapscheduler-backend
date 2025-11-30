from rest_framework import viewsets
from api.models import CourseSessionPolicy, CourseDayPreference, CourseTeacherPreference, CourseShiftPreference, TeacherUnavailability
from api.serializers.PreferenceSerializers import (
    CourseSessionPolicySerializer,
    CourseDayPreferenceSerializer,
    CourseTeacherPreferenceSerializer,
    CourseShiftPreferenceSerializer,
    TeacherUnavailabilitySerializer,
)

class CourseSessionPolicyViewSet(viewsets.ModelViewSet):
    queryset = CourseSessionPolicy.objects.all()
    serializer_class = CourseSessionPolicySerializer


from rest_framework.decorators import action
from rest_framework.response import Response
from api.serializers.CourseUpdateSerializer import CourseUpdateSerializer

class CourseDayPreferenceViewSet(viewsets.ModelViewSet):
    queryset = CourseDayPreference.objects.all()
    serializer_class = CourseDayPreferenceSerializer

    @action(detail=False, methods=['get'], url_path='complete')
    def complete(self, request):
        preferences = self.get_queryset().order_by('id')
        page = self.paginate_queryset(preferences)
        result = []
        for pref in page:
            course_data = CourseUpdateSerializer(pref.course).data
            result.append({
                'id': pref.id,
                'course_id': course_data['id'],
                'course_name': course_data['name'],
                'day': pref.get_day_display(),
                'day_value': pref.day,
                'preference': pref.get_preference_display(),
                'preference_value': pref.preference
            })
        return self.get_paginated_response(result)


from rest_framework.decorators import action
from rest_framework.response import Response
from api.serializers.CourseUpdateSerializer import CourseUpdateSerializer
from api.serializers.TeacherSerializer import TeacherSerializer

class CourseTeacherPreferenceViewSet(viewsets.ModelViewSet):
    queryset = CourseTeacherPreference.objects.all()
    serializer_class = CourseTeacherPreferenceSerializer

    @action(detail=False, methods=['get'], url_path='complete/(?P<id_teacher>[^/.]+)')
    def complete(self, request, id_teacher=None):
        preferences = self.get_queryset().order_by('id')
        if id_teacher is not None:
            preferences = preferences.filter(teacher_id=id_teacher)
        page = self.paginate_queryset(preferences)
        result = []
        for pref in page:
            course_data = CourseUpdateSerializer(pref.course).data
            teacher_data = TeacherSerializer(pref.teacher).data
            result.append({
                'id': pref.id,
                'course': course_data,
                'teacher': teacher_data,
                'level': pref.level,
                'notes': pref.notes
            })
        return self.get_paginated_response(result)

class CourseShiftPreferenceViewSet(viewsets.ModelViewSet):
    queryset = CourseShiftPreference.objects.all()
    serializer_class = CourseShiftPreferenceSerializer

class TeacherUnavailabilityViewSet(viewsets.ModelViewSet):

    queryset = TeacherUnavailability.objects.all()
    serializer_class = TeacherUnavailabilitySerializer

    from rest_framework.decorators import action
    from rest_framework.response import Response

    @action(detail=False, methods=['get'], url_path='teacher/(?P<teacher_id>[^/.]+)')
    def by_teacher(self, request, teacher_id=None):
        qs = self.get_queryset().filter(teacher_id=teacher_id)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
