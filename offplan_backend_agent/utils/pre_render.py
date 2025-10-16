import os
from django.template.loader import render_to_string
from django.conf import settings
from api.models import Agent, Blog  # your actual models

FRONTEND_PUBLIC = os.path.join(settings.BASE_DIR, '../../offplan_frontend/public/pre_rendered')

def generate_html_snapshots():
    os.makedirs(FRONTEND_PUBLIC, exist_ok=True)

    # Agents
    for agent in Agent.objects.all():
        html = render_to_string('agent_detail.html', {'agent': agent})
        filename = f"agents-{agent.slug}.html"  # e.g., agents-sahar.html
        with open(os.path.join(FRONTEND_PUBLIC, filename), 'w', encoding='utf-8') as f:
            f.write(html)

    # Blogs
    for blog in Blog.objects.all():
        html = render_to_string('blog_detail.html', {'blog': blog})
        filename = f"blogs-{blog.slug}.html"  # e.g., blogs-off-plan-projects-in-sharjah-a-comprehensive-guide-for-2025.html
        with open(os.path.join(FRONTEND_PUBLIC, filename), 'w', encoding='utf-8') as f:
            f.write(html)

    # Contact page
    html = render_to_string('contact.html')
    with open(os.path.join(FRONTEND_PUBLIC, 'contact.html'), 'w', encoding='utf-8') as f:
        f.write(html)
