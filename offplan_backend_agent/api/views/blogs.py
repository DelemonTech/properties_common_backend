# views.py
from rest_framework.generics import ListAPIView, RetrieveAPIView

from api.models import BlogPost
from api.serializers import BlogPostSerializer
class BlogPostList(ListAPIView):
    queryset = BlogPost.objects.all().order_by('-created_at')
    serializer_class = BlogPostSerializer

class BlogPostDetail(RetrieveAPIView):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    lookup_field = 'slug'
