from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from api.models import Property
from api.property_serializers import PropertyDetailSerializer


class PropertyDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        try:
            prop = Property.objects.get(id=id)
            serializer = PropertyDetailSerializer(prop)

            return Response({
                "status": True,
                "message": "Property retrieved successfully.",
                "data": serializer.data,
                "error": None
            }, status=status.HTTP_200_OK)

        except Property.DoesNotExist:
            return Response({
                "status": False,
                "message": "Property not found.",
                "data": None,
                "error": {
                    "code": "not_found",
                    "details": f"No property exists with ID {id}"
                }
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                "status": False,
                "message": "An unexpected error occurred.",
                "data": None,
                "error": {
                    "code": "internal_error",
                    "details": str(e)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
