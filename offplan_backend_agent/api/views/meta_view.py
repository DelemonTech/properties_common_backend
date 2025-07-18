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
