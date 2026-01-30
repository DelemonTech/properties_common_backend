from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import Subscription
from api.serializers import SubscriptionSerializer
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema

class SubscribeView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=SubscriptionSerializer)
    def post(self, request):
        serializer = SubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Subscribed successfully",
                "data": serializer.data,
                "errors": None
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "message": "Subscription failed",
            "data": [],
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
