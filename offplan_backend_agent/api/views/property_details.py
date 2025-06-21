from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import Property
from api.serializers import PropertySerializer
from rest_framework.permissions import AllowAny


class PropertyDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        try:
            prop = Property.objects.get(id=id)
            serializer = PropertySerializer(prop)
            return Response({
                "status": True,
                "message": "Property fetched successfully",
                "data": serializer.data,
                "errors": None
            }, status=status.HTTP_200_OK)
        except Property.DoesNotExist:
            return Response({
                "status": False,
                "message": "Property not found",
                "data": None,
                "errors": {
                    "id": ["No property found with this ID."]
                }
            }, status=status.HTTP_404_NOT_FOUND)