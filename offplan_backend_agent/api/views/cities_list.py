from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import City
from api.serializers import CitySerializer
from rest_framework.permissions import AllowAny

class CityListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cities = City.objects.all().order_by("name")
        serializer = CitySerializer(cities, many=True)
        return Response({
            "status": True,
            "message": "Cities fetched successfully",
            "data": serializer.data,
            "errors": None
        }, status=status.HTTP_200_OK)
