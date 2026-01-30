import re
from django.core.cache import cache
from django.shortcuts import render
from django.http import HttpResponseRedirect
import requests

CRAWLER_USER_AGENTS = re.compile(
    r"googlebot|bingbot|yandex|duckduckbot|baiduspider|facebook|twitterbot|linkedinbot|whatsapp|telegrambot|slackbot|redditbot|quora link preview|pinterest|tumblr|vkbot",
    re.I
)

def agent_meta_view(request, username):
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    if CRAWLER_USER_AGENTS.search(user_agent):
        cache_key = f"agent_meta:{username}"
        meta_data = cache.get(cache_key)

        if not meta_data:
            api_url = f"https://offplan.market/api/agent/{username}/"
            try:
                response = requests.get(api_url, timeout=5)
                if response.status_code == 200 and response.json().get("status"):
                    agent = response.json()["data"]
                    profile_image = agent.get('profile_image_url')
                    if not profile_image:
                        profile_image = "https://offplan.market/static/default-agent.jpg"

                    meta_data = {
                        "title": f"{agent['name']} | Offplan Expert – Offplan.Market",
                        "description": agent.get('bio', f"Explore premium off-plan projects with {agent['name']}. Click to view listings & contact now."),
                        "image": profile_image,
                        "url": request.build_absolute_uri(),
                    }
                    cache.set(cache_key, meta_data, timeout=300)
                else:
                    raise Exception("Agent not found")
            except Exception:
                meta_data = {
                    "title": "Agent Not Found",
                    "description": "This agent profile does not exist.",
                    "image": "https://offplan.market/static/default-agent.jpg",
                    "url": request.build_absolute_uri(),
                }

        return render(request, "agent_meta_template.html", meta_data)

    react_url = f"https://offplan.market/{username}"
    return HttpResponseRedirect(react_url)

def blogs_listing_meta_view(request):
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    if CRAWLER_USER_AGENTS.search(user_agent):
        meta_data = {
            "title": "Latest Real Estate Insights | Blog",
            "description": "Stay updated with the latest trends, tips, and insights in Dubai real estate market.",
            "image": "https://offplan.market/static/default-blog.jpg",
            "url": request.build_absolute_uri(),
        }
        return render(request, "meta_template.html", meta_data)

    return HttpResponseRedirect("https://offplan.market/blogs/")

from api.models import BlogPost

def blog_detail_meta_view(request, slug):
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    if CRAWLER_USER_AGENTS.search(user_agent):
        try:
            post = BlogPost.objects.get(slug=slug)
            image = post.image.url if post.image else "https://offplan.market/static/default-blog.jpg"
            meta_data = {
                "title": post.meta_title or post.title,
                "description": post.meta_description or (post.content[:160] if post.content else "Blog article"),
                "image": request.build_absolute_uri(image),
                "url": request.build_absolute_uri(),
            }
        except BlogPost.DoesNotExist:
            meta_data = {
                "title": "Blog Not Found",
                "description": "This blog post does not exist.",
                "image": "https://offplan.market/static/default-blog.jpg",
                "url": request.build_absolute_uri(),
            }
        return render(request, "meta_template.html", meta_data)

    return HttpResponseRedirect(f"https://offplan.market/blog/{slug}/")


def contact_meta_view(request, username):
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    if CRAWLER_USER_AGENTS.search(user_agent):
        meta_data = {
            "title": "Contact Sahar Kalhor - Senior Property Consultant | OFFPLAN.MARKET",
            "description": "Get in touch with Sahar Kalhor for expert property consultation in Dubai. Call +971 52 952 9687 or send a message for personalized real estate advice.",
            "image": "https://offplan.market/static/default-contact.jpg",
            "url": f"https://offplan.market/{username}/contact",
        }
        return render(request, "meta_template.html", meta_data)

    return HttpResponseRedirect(f"https://offplan.market/{username}/contact")


def about_meta_view(request, username):
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    if CRAWLER_USER_AGENTS.search(user_agent):
        meta_data = {
            "title": "About Sahar Kalhor - Senior Property Consultant | OFFPLAN.MARKET",
            "description": "Meet Sahar Kalhor, your trusted Senior Property Consultant specializing in Dubai's off-plan real estate market. 6+ years experience, 150+ successful deals.",
            "image": "https://offplan.market/static/default-agent.jpg",
            "url": f"https://offplan.market/{username}/about",
        }
        return render(request, "meta_template.html", meta_data)

    return HttpResponseRedirect(f"https://offplan.market/{username}/about")
