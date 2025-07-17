from rest_framework import generics
from api.models import AgentDetails
from api.serializers import AgentDetailSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class AgentUpdateView(APIView):

    @swagger_auto_schema(request_body=AgentDetailSerializer)
    def put(self, request, id):
        try:
            agent = AgentDetails.objects.get(pk=id)
        except AgentDetails.DoesNotExist:
            return Response({
                "status": False,
                "message": "Agent not found",
                "data": None,
                "errors": {"id": ["No agent found with this ID."]}
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = AgentDetailSerializer(agent, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Agent updated successfully",
                "data": serializer.data,
                "errors": None
            }, status=status.HTTP_200_OK)

        return Response({
            "status": False,
            "message": "Agent update failed",
            "data": None,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
