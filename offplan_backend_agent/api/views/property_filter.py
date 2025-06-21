from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from api.models import Property
from api.serializers import PropertySerializer
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.pagination import PageNumberPagination
from .properties_list import CustomPagination  # Assuming you have a custom pagination class defined

class FilterPropertiesView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'city': openapi.Schema(type=openapi.TYPE_STRING),
                'area': openapi.Schema(type=openapi.TYPE_STRING),
                'property_type': openapi.Schema(type=openapi.TYPE_STRING),
                'min_price': openapi.Schema(type=openapi.TYPE_INTEGER),
                'max_price': openapi.Schema(type=openapi.TYPE_INTEGER),
                'min_area': openapi.Schema(type=openapi.TYPE_INTEGER),
                'max_area': openapi.Schema(type=openapi.TYPE_INTEGER),
                'property_status': openapi.Schema(type=openapi.TYPE_STRING),
            },
        )
    )
    def post(self, request):
        data = request.data
        queryset = Property.objects.all()

        if city := data.get("city"):
            queryset = queryset.filter(city__name__icontains=city)
        if area := data.get("area"):
            queryset = queryset.filter(district__name__icontains=area)
        if prop_type := data.get("property_type"):
            queryset = queryset.filter(property_type__icontains=prop_type)

        if min_price := data.get("min_price"):
            queryset = queryset.filter(low_price__gte=min_price)
        if max_price := data.get("max_price"):
            queryset = queryset.filter(low_price__lte=max_price)

        if min_area := data.get("min_area"):
            queryset = queryset.filter(min_area__gte=min_area)
        if max_area := data.get("max_area"):
            queryset = queryset.filter(min_area__lte=max_area)

        if property_status := data.get("property_status"):
            queryset = queryset.filter(property_status__icontains=property_status)

        paginator = CustomPagination()
        paginator.request = request
        paginated_qs = paginator.paginate_queryset(queryset, request)
        serializer = PropertySerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)