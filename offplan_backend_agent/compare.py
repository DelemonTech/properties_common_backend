import os
import django
import requests
from datetime import datetime, timezone

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from api.models import Property

API_KEY = os.environ.get("ESTATY_API_KEY")
HEADERS = {
    "App-key": API_KEY,
    "Content-Type": "application/json",
}
EXTERNAL_API_URL = "https://panel.estaty.app/api/v1/latestUpdatedProperties"

def fetch_latest_external():
    try:
        response = requests.post(EXTERNAL_API_URL, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and isinstance(data.get("properties"), list):
            return data["properties"]
        else:
            print("⚠️ Unexpected response format:", data)
            return []
    except Exception as e:
        print(f"❌ Error fetching external properties: {e}")
        return []

def fetch_latest_local():
    return list(Property.objects.order_by("-updated_at")[:10])

def format_to_external_utc(dt: datetime):
    """Format to match external API timestamp"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000000Z")

def compare_and_print():
    ext_props = fetch_latest_external()
    local_props = fetch_latest_local()

    print("\n📡 External Latest 10:")
    print("------------------------------------------------------------")
    for item in ext_props:
        print(f"ID: {item['id']} | Title: {item['title']} | Updated At: {item['updated_at']}")
    print("------------------------------------------------------------")

    print("\n💾 Local Latest 10:")
    print("------------------------------------------------------------")
    for prop in local_props:
        print(f"ID: {prop.id} | Title: {prop.title} | Updated At: {format_to_external_utc(prop.updated_at)}")
    print("------------------------------------------------------------")

    print("\n🔍 Side-by-side Comparison:")
    print("------------------------------------------------------------------------------------------")
    local_map = {prop.id: (prop.title, format_to_external_utc(prop.updated_at)) for prop in local_props}

    for item in ext_props:
        ext_id = item["id"]
        ext_title = item["title"]
        ext_updated = item["updated_at"]
        local_info = local_map.get(ext_id)

        if not local_info:
            print(f"ID: {ext_id} → ❌ Not in local DB")
        else:
            local_title, local_updated = local_info
            status = "✅ Match" if ext_updated == local_updated else f"🛠️ Mismatch → ext: {ext_updated} | local: {local_updated}"
            print(f"ID: {ext_id} | {ext_title} → {status}")
    print("------------------------------------------------------------------------------------------")

if __name__ == "__main__":
    compare_and_print()
