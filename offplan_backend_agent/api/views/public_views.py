from rest_framework import viewsets, status
from rest_framework.response import Response
from api.models import AgentDetails
from api.serializers import AgentDetailSerializer

class PublicAgentDetailViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AgentDetails.objects.all()
    serializer_class = AgentDetailSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        return Response({
            "status": True,
            "message": "Agents list fetched successfully",
            "data": serializer.data,
            "errors": None
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)

            return Response({
                "status": True,
                "message": "Agent details fetched successfully",
                "data": serializer.data,
                "errors": None
            }, status=status.HTTP_200_OK)

        except AgentDetails.DoesNotExist:
            return Response({
                "status": False,
                "message": "Agent not found",
                "data": None,
                "errors": {
                    "id": ["No agent found with this ID."]
                }
            }, status=status.HTTP_404_NOT_FOUND)
