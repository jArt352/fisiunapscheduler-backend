from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from api.serializers.PlanImportSerializer import PlanImportSerializer


class PlanImportViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Endpoint para crear un Plan junto a sus cursos en bloque.

    POST payload ejemplo:
    {
      "name": "Plan 2020 Ingeniería",
      "description": "",
      "school": 1,          # id de School
      "start_year": 2020,
      "end_year": null,
      "courses": [ { ... }, { ... } ]
    }
    """
    serializer_class = PlanImportSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        plan = result.get('plan')
        created = result.get('created_courses', [])
        errors = result.get('errors', [])

        return Response({
            'plan_id': plan.id,
            'plan_name': plan.name,
            'created_courses': created,
            'errors': errors
        }, status=status.HTTP_201_CREATED)
