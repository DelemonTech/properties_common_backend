# api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import AgentDetails
from api.serializers import AgentDetailsFrontendSerializer

class AgentListFrontendView(APIView):
    def get(self, request):
        agents = AgentDetails.objects.all()
        serializer = AgentDetailsFrontendSerializer(agents, many=True)
        
        response_data = {
            "status": "success",
            "message": "Agents fetched successfully",
            "results": serializer.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
