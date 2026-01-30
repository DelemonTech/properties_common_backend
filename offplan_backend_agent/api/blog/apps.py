from django.apps import AppConfig

class BlogConfig(AppConfig):
    name = 'api.blog'

    def ready(self):
        import api.blog.signals
