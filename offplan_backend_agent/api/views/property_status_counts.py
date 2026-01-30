from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from api.models import Property

class PropertyStatusCountView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            ready_count = Property.objects.filter(property_status_id=1).count()
            offplan_count = Property.objects.filter(property_status_id=2).count()
            # sold_count = Property.objects.filter(sales_status_id=3).count()

            return Response({
                "status": True,
                "message": "Property status counts fetched successfully",
                "data": {
                    "ready": ready_count,
                    "offplan": offplan_count
                    # "sold": sold_count
                }
            })
        except Exception as e:
            return Response({
                "status": False,
                "message": f"Failed to fetch counts: {str(e)}",
                "data": {}
            }, status=500)
