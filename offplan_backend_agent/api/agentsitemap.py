from django.contrib.sitemaps import Sitemap
from .models import AgentDetails

class AgentDetailsSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return AgentDetails.objects.all()

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return f"/{obj.username}"  # Directly return username path
