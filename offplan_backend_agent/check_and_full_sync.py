import os
import django
import requests
from datetime import datetime, timezone

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from api.models import Property, City, District, DeveloperCompany

API_KEY = os.environ.get("ESTATY_API_KEY")
HEADERS = {
    "App-key": API_KEY,
    "Content-Type": "application/json",
}

LATEST_API_URL = "https://panel.estaty.app/api/v1/latestUpdatedProperties"
FULL_SYNC_URL = "https://panel.estaty.app/api/v1/getProperties"


def safe_get(obj, *keys):
    for key in keys:
        if obj is None:
            return None
        obj = obj.get(key)
    return obj


def format_to_external_utc(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000000Z") if dt else None


def fetch_latest_external():
    try:
        res = requests.post(LATEST_API_URL, headers=HEADERS)
        res.raise_for_status()
        data = res.json()

        if isinstance(data, dict) and "properties" in data and isinstance(data["properties"], list):
            return data["properties"]
        else:
            print("Unexpected response structure:", data)
            return []
    except Exception as e:
        print(f"Error fetching latest external properties: {e}")
        return []


def fetch_latest_local():
    return list(Property.objects.order_by("-updated_at")[:10])


def compare_updates(external_props, local_props):
    diffs = []
    local_map = {p.id: format_to_external_utc(p.updated_at) for p in local_props}

    for item in external_props:
        ext_id = item["id"]
        ext_updated_at = item["updated_at"]
        local_updated_at = local_map.get(ext_id)

        if not local_updated_at:
            diffs.append((item, "❌ Not in local DB"))
        elif ext_updated_at != local_updated_at:
            diffs.append((item, f"🛠️ Timestamp mismatch → ext: {ext_updated_at} | local: {local_updated_at}"))
        # Else: they match → do not add to diffs

    return diffs



def parse_external_datetime(dt_str):
    """Parses ISO 8601 datetime string ending with 'Z' into UTC datetime object"""
    return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)

def update_property(item):
    city_data = item.get("city") or {}
    city = None
    if city_data and city_data.get("id"):
        city, _ = City.objects.get_or_create(
            id=city_data["id"],
            defaults={"name": city_data.get("name", "")}
        )

    district_data = item.get("district") or {}
    district = None
    if district_data and district_data.get("id") and city:
        district, _ = District.objects.get_or_create(
            id=district_data["id"],
            defaults={"name": district_data.get("name", ""), "city": city}
        )

    developer_data = item.get("developer_company") or {}
    developer, _ = DeveloperCompany.objects.get_or_create(
        id=developer_data.get("id"),
        defaults={"name": developer_data.get("name", "")}
    ) if developer_data else (None, False)

    Property.objects.update_or_create(
        id=item["id"],
        defaults={
            "title": item.get("title"),
            "cover": item.get("cover"),
            "address": item.get("address"),
            "address_text": item.get("address_text"),
            "delivery_date": int(item["delivery_date"]) if item.get("delivery_date") else None,
            "min_area": item.get("min_area"),
            "low_price": item.get("low_price"),
            "city": city,
            "district": district,
            "developer": developer,
            "property_type": safe_get(item, "property_type", "name") or "",
            "property_status": safe_get(item, "property_status", "name") or "",
            "sales_status": safe_get(item, "sales_status", "name") or "",
            "updated_at": parse_external_datetime(item["updated_at"]) if item.get("updated_at") else None,
        }
    )


def full_sync_all_pages():
    print("\n🚀 Starting full database sync...\n")
    page = 1
    while True:
        print(f"📦 Page: {page}")
        response = requests.post(FULL_SYNC_URL, headers=HEADERS, json={"page": page})
        if response.status_code != 200:
            print("❌ Failed:", response.status_code)
            break

        props = response.json().get("properties", {}).get("data", [])
        if not props:
            break

        for item in props:
            update_property(item)

        if not response.json().get("properties", {}).get("next_page_url"):
            break
        page += 1

    print("✅ Full sync completed.")


# --- Main Autonomous Routine ---
if __name__ == "__main__":
    print("🔄 Comparing latest 10 updated records...")
    ext_props = fetch_latest_external()
    local_props = fetch_latest_local()
    diffs = compare_updates(ext_props, local_props)

    if not diffs:
        print("✅ No mismatch found. DB is up to date.")
    elif len(diffs) >= 10:
        print(f"⚠️ {len(diffs)} mismatches found. Performing full sync...")
        full_sync_all_pages()
    else:
        print(f"🔧 {len(diffs)} mismatches found. Updating individually...\n")
        for item, reason in diffs:
            print(f"➡️ Updating/Creating ID: {item['id']} | {reason}")
            update_property(item)

        print("\n✅ Partial sync completed.")
