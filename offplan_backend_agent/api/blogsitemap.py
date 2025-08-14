from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import BlogPost

class BlogPostSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return BlogPost.objects.all()

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return f"/blogs/{obj.slug}"  # Directly return the full path
