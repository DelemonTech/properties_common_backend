from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import AgentDetails
from api.serializers import AgentDetailSerializer

class AgentDetailByUsernameView(APIView):
    def get(self, request, username):
        try:
            agent = AgentDetails.objects.get(username=username)
            serializer = AgentDetailSerializer(agent)
            return Response({
                "status": True,
                "message": "Agent fetched successfully",
                "data": serializer.data,
                "errors": None
            }, status=status.HTTP_200_OK)
        except AgentDetails.DoesNotExist:
            return Response({
                "status": False,
                "message": "Agent not found",
                "data": None,
                "errors": {
                    "username": ["No agent found with this username."]
                }
            }, status=status.HTTP_404_NOT_FOUND)