import re
from django.core.cache import cache
from django.shortcuts import render
from django.http import HttpResponseRedirect
import requests

# Detect crawlers using User-Agent
CRAWLER_USER_AGENTS = re.compile(
    r"googlebot|bingbot|yandex|duckduckbot|baiduspider|facebook|twitterbot|linkedinbot|whatsapp|telegrambot|slackbot|redditbot|quora link preview|pinterest|tumblr|vkbot",
    re.I
)

def agent_meta_view(request, username):
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    if CRAWLER_USER_AGENTS.search(user_agent):
        # ✅ Crawlers: Fetch meta data from API
        cache_key = f"agent_meta:{username}"
        meta_data = cache.get(cache_key)

        if not meta_data:
            api_url = f"https://offplan.market/api/agent/{username}/"
            try:
                response = requests.get(api_url, timeout=5)
                if response.status_code == 200 and response.json().get("status"):
                    agent = response.json()["data"]
                    meta_data = {
                        "title": f"{agent['name']} | Offplan Expert – Offplan.Market",
                        "description": agent.get('bio', f"Explore premium off-plan projects with {agent['name']}. Click to view listings & contact now."),
                        "image": "https://offplan.market/lovable-uploads/93c61de1-b334-4926-a59a-2934c6cb5135.png",
                        "url": request.build_absolute_uri(),
                    }
                    # Cache for 5 minutes
                    cache.set(cache_key, meta_data, timeout=300)
                else:
                    raise Exception("Agent not found")
            except Exception:
                meta_data = {
                    "title": "Agent Not Found",
                    "description": "This agent profile does not exist.",
                    "image": "https://offplan.market/lovable-uploads/93c61de1-b334-4926-a59a-2934c6cb5135.png",
                    "url": request.build_absolute_uri(),
                }

        # Render meta template for crawlers
        return render(request, "agent_meta_template.html", meta_data)

    # 👤 Normal users → Redirect to React frontend
    react_url = f"https://offplan.market/{username}"
    return HttpResponseRedirect(react_url)
