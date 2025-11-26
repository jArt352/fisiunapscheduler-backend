from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from api.serializers.PersonCreateSerializer import PersonCreateSerializer
from api.models import Person


class PersonCreateViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """ViewSet que solo expone la acción `create` para crear Person + optional User + roles."""
    serializer_class = PersonCreateSerializer
    queryset = Person.objects.all()

    def create(self, request, *args, **kwargs):
        # Support bulk create: accept a list of person objects or a single object
        data = request.data
        if isinstance(data, list):
            results = []
            created = []
            for item in data:
                serializer = self.get_serializer(data=item)
                try:
                    serializer.is_valid(raise_exception=True)
                    person = serializer.save()
                    results.append({'status': 'ok', 'id': person.id})
                    created.append(person)
                except Exception as e:
                    # serializer.errors is preferred when ValidationError
                    err = getattr(e, 'detail', str(e))
                    results.append({'status': 'error', 'error': err})

            # Return list of results and created objects summary
            return Response({'results': results}, status=status.HTTP_207_MULTI_STATUS)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        person = serializer.save()
        return Response(self.get_serializer(person).data, status=status.HTTP_201_CREATED)
