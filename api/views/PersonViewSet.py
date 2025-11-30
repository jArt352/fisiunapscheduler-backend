from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from api.models import Person
from api.serializers.PersonSerializer import PersonSerializer

class PersonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = [AllowAny]
