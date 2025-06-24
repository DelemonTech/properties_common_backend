from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import Property
from api.serializers import PropertySerializer
from api.property_serializers import PropertyDetailSerializer  # Ensure this serializer is defined
from rest_framework.permissions import AllowAny


# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import AllowAny
# from rest_framework import status
# from django.shortcuts import get_object_or_404
# from .models import Property
# from .serializers import PropertyDetailSerializer  # Make sure this is the detailed one

class PropertyDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        try:
            prop = Property.objects.get(id=id)
            serializer = PropertyDetailSerializer(prop)
            return Response({
                "property": serializer.data
            }, status=status.HTTP_200_OK)
        except Property.DoesNotExist:
            return Response({
                "property": None,
                "error": {
                    "message": "No property found with this ID.",
                    "code": "not_found"
                }
            }, status=status.HTTP_404_NOT_FOUND)
