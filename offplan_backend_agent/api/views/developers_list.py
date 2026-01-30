from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import DeveloperCompany
from api.serializers import DeveloperCompanySerializer
from rest_framework.permissions import AllowAny

class DeveloperListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        developers = DeveloperCompany.objects.all().order_by('name')
        serializer = DeveloperCompanySerializer(developers, many=True)
        return Response({
            "status": True,
            "message": "Developer list fetched successfully",
            "data": serializer.data,
            "errors": None
        }, status=status.HTTP_200_OK)
