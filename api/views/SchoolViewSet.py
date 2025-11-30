from rest_framework.permissions import AllowAny
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from api.models import School
from api.serializers.SchoolSerializer import SchoolSerializer

class SchoolViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = School.objects.all().select_related('faculty')
    serializer_class = SchoolSerializer
    permission_classes = [AllowAny]
