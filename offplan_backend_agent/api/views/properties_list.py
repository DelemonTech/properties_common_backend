from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from django.urls import reverse
from api.models import Property
from api.serializers import PropertySerializer


class CustomPagination(PageNumberPagination):
    page_size = 12

    def get_paginated_response(self, data):
        request = self.request
        current_page = self.page.number
        base_url = request.build_absolute_uri().split('?')[0]

        return Response({
            "count": self.page.paginator.count,
            "current_page": current_page,
            "next_page_url": self.get_next_link(),
            "previous_page_url": self.get_previous_link(),
            "results": data,
        })


class PropertyListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request):
        properties = Property.objects.order_by("-updated_at")
        paginator = CustomPagination()
        paginator.request = request
        paginated_qs = paginator.paginate_queryset(properties, request)
        serializer = PropertySerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)
