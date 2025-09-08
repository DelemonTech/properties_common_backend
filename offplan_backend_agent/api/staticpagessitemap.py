from django.contrib.sitemaps import Sitemap

class StaticPagesSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return ['contact', 'about', 'blogs']  # list of static page slugs

    def location(self, obj):
        return f"/{obj}"