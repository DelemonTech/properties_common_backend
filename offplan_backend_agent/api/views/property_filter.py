from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from api.models import Property
from api.serializers import PropertySerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .properties_list import CustomPagination


class FilterPropertiesView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'city': openapi.Schema(type=openapi.TYPE_STRING),
                'district': openapi.Schema(type=openapi.TYPE_STRING),
                'property_type': openapi.Schema(type=openapi.TYPE_STRING),
                'unit_type': openapi.Schema(type=openapi.TYPE_STRING),
                'rooms': openapi.Schema(type=openapi.TYPE_STRING),
                'delivery_year': openapi.Schema(type=openapi.TYPE_INTEGER),
                'min_price': openapi.Schema(type=openapi.TYPE_INTEGER),
                'max_price': openapi.Schema(type=openapi.TYPE_INTEGER),
                'min_area': openapi.Schema(type=openapi.TYPE_INTEGER),
                'max_area': openapi.Schema(type=openapi.TYPE_INTEGER),
                'property_status': openapi.Schema(type=openapi.TYPE_STRING),
                'sales_status': openapi.Schema(type=openapi.TYPE_STRING),  # <-- New field
            },
        )
    )
    def post(self, request):
        data = request.data
        queryset = Property.objects.all()

        if city := data.get("city"):
            queryset = queryset.filter(city__name__icontains=city)

        if district := data.get("district"):
            queryset = queryset.filter(district__name__icontains=district)

        if prop_type := data.get("property_type"):
            queryset = queryset.filter(property_type__name__icontains=prop_type)

        if unit_type := data.get("unit_type"):
            queryset = queryset.filter(grouped_apartments__unit_type__icontains=unit_type)

        if rooms := data.get("rooms"):
            queryset = queryset.filter(grouped_apartments__rooms=rooms)

        if delivery_year := data.get("delivery_year"):
            queryset = queryset.filter(delivery_date__icontains=str(delivery_year))

        if min_price := data.get("min_price"):
            queryset = queryset.filter(low_price__gte=min_price)
        if max_price := data.get("max_price"):
            queryset = queryset.filter(low_price__lte=max_price)

        if min_area := data.get("min_area"):
            queryset = queryset.filter(min_area__gte=min_area)
        if max_area := data.get("max_area"):
            queryset = queryset.filter(min_area__lte=max_area)

        if property_status := data.get("property_status"):
            queryset = queryset.filter(property_status__name__icontains=property_status)

        if sales_status := data.get("sales_status"):
            queryset = queryset.filter(sales_status__name__icontains=sales_status)

        paginator = CustomPagination()
        paginator.request = request
        paginated_qs = paginator.paginate_queryset(queryset.distinct(), request)
        serializer = PropertySerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)
