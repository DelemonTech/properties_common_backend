from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.models import Contact
from api.serializers import ContactSerializer

class ContactEnquiryView(APIView):
    def post(self, request):
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': "Contact enquiry submitted successfully",
                'data':serializer.data,
                }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)