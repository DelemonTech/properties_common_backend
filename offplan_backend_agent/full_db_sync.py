import os
import django
import requests
import logging
from dateutil import parser as date_parser

# ✅ Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "backend.settings"))
django.setup()

# ✅ Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger()

# ✅ Import models
from api.models import (
    Property, City, District, DeveloperCompany,
    PropertyType, PropertyStatus, SalesStatus
)

# ✅ Configuration
API_URL = "https://panel.estaty.app/api/v1/getProperties"
API_KEY = os.getenv("ESTATY_API_KEY")

if not API_KEY:
    raise RuntimeError("❌ ESTATY_API_KEY environment variable is not set.")

HEADERS = {
    "App-key": API_KEY,
    "Content-Type": "application/json"
}


# ✅ Foreign Key helper
def parse_fk(model, data):
    if isinstance(data, dict) and "id" in data:
        obj, _ = model.objects.get_or_create(
            id=data["id"],
            defaults={"name": data.get("name", "")}
        )
        return obj
    return None


# ✅ Property update/create logic
def update_or_create_property(data):
    prop_id = data.get("id")
    if not prop_id:
        return

    # Foreign Keys
    city = parse_fk(City, data.get("city"))
    district = parse_fk(District, data.get("district"))
    developer = parse_fk(DeveloperCompany, data.get("developer_company"))
    property_type = parse_fk(PropertyType, data.get("property_type"))
    property_status = parse_fk(PropertyStatus, data.get("property_status"))
    sales_status = parse_fk(SalesStatus, data.get("sales_status"))

    # updated_at parsing
    updated_at = None
    if data.get("updated_at"):
        try:
            updated_at = date_parser.parse(data["updated_at"])
        except Exception:
            pass

    Property.objects.update_or_create(
        id=prop_id,
        defaults={
            "title": data.get("title"),
            "description": data.get("description", ""),
            "cover": data.get("cover"),
            "address": data.get("address"),
            "address_text": data.get("address_text"),
            "delivery_date": data.get("delivery_date"),
            "completion_rate": data.get("completion_rate"),
            "residential_units": data.get("residential_units"),
            "commercial_units": data.get("commercial_units"),
            "payment_plan": data.get("payment_plan"),
            "post_delivery": data.get("post_delivery", False),
            "payment_minimum_down_payment": data.get("payment_minimum_down_payment"),
            "guarantee_rental_guarantee": data.get("guarantee_rental_guarantee", False),
            "guarantee_rental_guarantee_value": data.get("guarantee_rental_guarantee_value"),
            "downPayment": data.get("downPayment"),
            "low_price": data.get("low_price"),
            "min_area": data.get("min_area"),
            "updated_at": updated_at,

            # Foreign keys
            "city": city,
            "district": district,
            "developer": developer,
            "property_type": property_type,
            "property_status": property_status,
            "sales_status": sales_status,
        }
    )


# ✅ External fetcher
def fetch_properties(page):
    try:
        response = requests.post(API_URL, headers=HEADERS, json={"page": page})
        response.raise_for_status()
        return response.json().get("properties", {}).get("data", [])
    except Exception as e:
        log.error(f"❌ Error fetching page {page}: {e}")
        return []


# ✅ Sync routine
def full_sync():
    log.info("🚀 Starting full database sync from external API...")
    page = 1
    total_synced = 0

    while True:
        properties = fetch_properties(page)
        if not properties:
            break

        for item in properties:
            prop_data = item.get("property")
            if prop_data:
                update_or_create_property(prop_data)
                total_synced += 1

        log.info(f"✅ Page {page} synced ({len(properties)} properties)")
        page += 1

    log.info(f"\n✅ Full sync completed. Total properties synced: {total_synced}")


# ✅ Run main
if __name__ == "__main__":
    try:
        full_sync()
    except Exception as e:
        log.error(f"❌ Fatal error during sync: {e}")
