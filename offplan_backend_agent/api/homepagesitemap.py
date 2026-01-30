from django.contrib.sitemaps import Sitemap

class HomePageSitemap(Sitemap):
    changefreq = "weekly"
    priority = 1.0

    def items(self):
        return ["/"]  # just the root URL

    def location(self, obj):
        return "/"  # explicitly return root path
