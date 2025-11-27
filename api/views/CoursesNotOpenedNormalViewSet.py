from rest_framework import viewsets
from rest_framework.response import Response
from api.models import Course, CourseOffering, AcademicPeriod

class CoursesNotOpenedNormalViewSet(viewsets.ViewSet):
    """
    Endpoint para listar cursos que NO tienen CourseOffering de tipo 'normal' en un periodo académico dado.
    """
    def list(self, request):
        period_id = request.query_params.get('academic_period_id')
        if not period_id:
            return Response({'detail': 'academic_period_id es requerido.'}, status=400)
        try:
            period = AcademicPeriod.objects.get(id=period_id)
        except AcademicPeriod.DoesNotExist:
            return Response({'detail': 'Periodo académico no encontrado.'}, status=404)
        # IDs de cursos que ya tienen offering normal en este periodo
        offered_ids = CourseOffering.objects.filter(academic_period=period, offering_type='normal').values_list('course_id', flat=True)
        # Cursos que NO están en offered_ids
        not_opened = Course.objects.exclude(id__in=offered_ids)
        data = [
            {
                'id': c.id,
                'code': c.code,
                'name': c.name,
                'credits': c.credits,
                'cycle': c.cycle
            } for c in not_opened
        ]
        return Response(data)
