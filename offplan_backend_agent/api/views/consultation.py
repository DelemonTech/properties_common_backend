from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import Consultation
from api.serializers import ConsultationSerializer
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class ConsultationView(APIView):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(responses={200: ConsultationSerializer(many=True)})
    def get(self, request):
        consultations=Consultation.objects.all()
        serializer=ConsultationSerializer(consultations, many=True)
        return Response({
            "status": True,
            "message": "consultations data fetched successfully",
            "data": serializer.data,
            "errors": None
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=ConsultationSerializer)
    def post(self,request):
        serializer=ConsultationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'success': True,
                    'data': serializer.data,
                    'message': 'Consultation details successfully submitted',
                    'error': 'none'
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {
                'success': False,
                'data': serializer.errors,
                'message': 'Failed to submit Consultation details',
                'error': 'none'
            },
            status=status.HTTP_400_BAD_REQUEST
        )    
        