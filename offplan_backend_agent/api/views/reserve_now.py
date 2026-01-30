from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import ReserveNow,PropertyUnit
from api.serializers import ReserveNowSerializer


class ReserveNowView(APIView):
    def post (self,request,id):
        unit = PropertyUnit.objects.get(id=id)
        serializer = ReserveNowSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(unit_id=unit)
            return Response({
                "message":"Reservation submitted successfully",
                "data":serializer.data
            },status=status.HTTP_201_CREATED)
        
        return Response({
            "message":"Error in submitting ",
            "errors":serializer.errors
        },status=status.HTTP_400_BAD_REQUEST)