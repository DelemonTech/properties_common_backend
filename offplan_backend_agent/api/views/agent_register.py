from rest_framework import generics
from api.models import AgentDetails
from api.serializers import AgentDetailSerializer
from api.permissions.is_admin_from_other_service import IsAdminFromAuthService

class AgentRegisterView(generics.CreateAPIView):
    queryset = AgentDetails.objects.all()
    serializer_class = AgentDetailSerializer
    permission_classes = [IsAdminFromAuthService]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            agent = serializer.save()
            return Response({
                "status": True,
                "message": "Agent registered successfully",
                "data": AgentDetailSerializer(agent).data,
                "errors": None
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "status": False,
            "message": "Agent registration failed",
            "data": None,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)