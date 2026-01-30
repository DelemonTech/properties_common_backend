from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import Property, PropertyStatus
from rest_framework.permissions import AllowAny
from django.db.models import Count
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

status_param = openapi.Parameter(
    'status',
    openapi.IN_QUERY,
    description="Filter by property status (e.g., Ready, Off Plan, Sold Out, or Total for all statuses)",
    type=openapi.TYPE_STRING,
    required=True,
    enum=["Ready", "Off Plan", "Sold Out", "Total"],  # ✅ Added Total
)

class PropertyByStatusView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(manual_parameters=[status_param])
    def get(self, request):
        status_name = request.query_params.get('status')
        if not status_name:
            return Response({
                "status": False,
                "message": "Missing 'status' query parameter",
                "data": [],
                "errors": None
            }, status=status.HTTP_200_OK)

        # Handle Total separately
        if status_name.lower() == "total":
            city_data = (
                Property.objects
                .values('city__id', 'city__name')
                .annotate(property_count=Count('id'))
                .order_by('-property_count')
            )

            results = []
            for city in city_data:
                results.append({
                    "city_id": city['city__id'],
                    "city_name": city['city__name'],
                    "property_count": city['property_count'],
                    "filter_status": "Total"
                })

            return Response({
                "status": True,
                "message": "All properties grouped by city (Total)",
                "data": results,
                "errors": None
            }, status=status.HTTP_200_OK)

        # Handle Ready / Off Plan / Sold Out
        property_status = PropertyStatus.objects.filter(name__iexact=status_name).first()
        if not property_status:
            return Response({
                "status": False,
                "message": f"No matching PropertyStatus for '{status_name}'",
                "data": [],
                "errors": None
            }, status=status.HTTP_404_NOT_FOUND)

        properties = Property.objects.filter(property_status=property_status)
        city_data = (
            properties.values('city__id', 'city__name')
            .annotate(property_count=Count('id'))
            .order_by('-property_count')
        )

        results = []
        for city in city_data:
            results.append({
                "city_id": city['city__id'],
                "city_name": city['city__name'],
                "property_count": city['property_count'],
                "filter_status": property_status.name
            })

        return Response({
            "status": True,
            "message": f"Properties filtered by status '{status_name}'",
            "data": results,
            "errors": None
        }, status=status.HTTP_200_OK)
