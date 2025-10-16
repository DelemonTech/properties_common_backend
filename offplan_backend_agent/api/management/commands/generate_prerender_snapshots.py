import os
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.conf import settings
from api.models import AgentDetails, BlogPost

class Command(BaseCommand):
    help = 'Generate pre-rendered HTML snapshots for SEO'

    def handle(self, *args, **options):
        output_dir = os.path.join(settings.BASE_DIR, 'public', 'pre_rendered')
        os.makedirs(output_dir, exist_ok=True)

        # 1️⃣ Agents
        agents = AgentDetails.objects.all()
        for agent in agents:
            filename = f"agents-{agent.username}.html"  # use username
            html = render_to_string('agent_detail.html', {'agent': agent})
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
            self.stdout.write(self.style.SUCCESS(f'Generated agent snapshot: {filename}'))

        # 2️⃣ Blogs
        blogs = BlogPost.objects.all()
        for blog in blogs:
            filename = f"blog-{blog.slug}.html"
            html = render_to_string('blog_detail.html', {'blog': blog})
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
            self.stdout.write(self.style.SUCCESS(f'Generated blog snapshot: {filename}'))

        # 3️⃣ Static pages
        static_pages = ['blogs', 'contact']
        for page in static_pages:
            html = render_to_string(f'{page}.html')
            filename = f"{page}.html"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
            self.stdout.write(self.style.SUCCESS(f'Generated static page snapshot: {filename}'))
