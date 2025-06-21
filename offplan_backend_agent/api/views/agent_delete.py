from rest_framework import generics
from api.models import AgentDetails
from api.serializers import AgentDetailSerializer
from api.permissions.is_admin_from_other_service import IsAdminFromAuthService
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

class AgentDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminFromAuthService]

    def delete(self, request, id):
        try:
            agent = AgentDetails.objects.get(pk=id)
            agent.delete()
            return Response({
                "status": True,
                "message": "Agent deleted successfully",
                "data": None,
                "errors": None
            }, status=status.HTTP_204_NO_CONTENT)
        except AgentDetails.DoesNotExist:
            return Response({
                "status": False,
                "message": "Agent not found",
                "data": None,
                "errors": {"id": ["No agent found with this ID."]}
            }, status=status.HTTP_404_NOT_FOUND)
