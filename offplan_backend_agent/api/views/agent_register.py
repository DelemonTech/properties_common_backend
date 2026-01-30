from rest_framework import generics
from api.models import AgentDetails
from api.serializers import AgentDetailSerializer
# from api.permissions.is_admin_from_other_service import IsAdminFromAuthService
from rest_framework.response import Response  # ✅ Add this
from rest_framework import status  # ✅ Add this


class AgentRegisterView(generics.CreateAPIView):
    queryset = AgentDetails.objects.all()
    serializer_class = AgentDetailSerializer

    def create(self, request, *args, **kwargs):
        username = request.data.get("username")
        if not username:
            return Response({
                "status": False,
                "message": "Username is required",
                "data": None,
                "errors": {"username": ["This field is required."]}
            }, status=status.HTTP_400_BAD_REQUEST)

        # 🚀 Create new or update existing
        agent, created = AgentDetails.objects.update_or_create(
            username=username,
            defaults=request.data
        )

        return Response({
            "status": True,
            "message": "Agent registered successfully" if created else "Agent updated successfully",
            "data": AgentDetailSerializer(agent).data,
            "errors": None
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
