from rest_framework.views import APIView
from rest_framework.response import Response
from api.models import AgentDetails
from api.serializers import AgentDetailSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

class AgentListView(APIView):
    def get(self, request):
        agents = AgentDetails.objects.order_by('id')
        
        paginator = PageNumberPagination()
        paginated_agents = paginator.paginate_queryset(agents, request)
        serializer = AgentDetailSerializer(paginated_agents, many=True)
        
        return Response({
            "status": True,
            "message": "Agents fetched successfully",
            "data": {
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": serializer.data
            },
            "errors": None
        }, status=status.HTTP_200_OK)