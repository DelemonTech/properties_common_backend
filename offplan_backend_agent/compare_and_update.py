import os
import django
import requests
import logging
from dateutil import parser as date_parser

# ✅ Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "backend.settings"))
django.setup()

# ✅ Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger()

# ✅ Import models
from api.models import Property, City, District, DeveloperCompany, PropertyType, PropertyStatus, SalesStatus

# ✅ Configuration
EXTERNAL_URL = "https://panel.estaty.app/api/v1/getProperties"
API_KEY = os.getenv("ESTATY_API_KEY")

if not API_KEY:
    raise RuntimeError("❌ Missing ESTATY_API_KEY environment variable.")

HEADERS = {
    "App-key": API_KEY,
    "Content-Type": "application/json",
}

# ✅ Helpers
def fetch_external_properties(page):
    try:
        if page == 1:
            url = EXTERNAL_URL
            payload = {}
        else:
            url = f"{EXTERNAL_URL}?page={page}"
            payload = {}

        log.info(f"\U0001F310 Fetching: {url}")
        response = requests.post(url, headers=HEADERS, json=payload)
        response.raise_for_status()
        data = response.json()

        if isinstance(data.get("property"), dict):
            return [data["property"]]
        elif isinstance(data.get("properties", {}).get("data"), list):
            return data["properties"]["data"]
        else:
            log.warning("⚠️ Unexpected structure in response.")
            return []

    except requests.RequestException as e:
        log.error(f"❌ Request failed on page {page}: {e}")
        return []

def get_or_none(model, data):
    if not data:
        return None
    if isinstance(data, dict):
        return model.objects.filter(id=data.get("id")).first()
    return model.objects.filter(id=data).first()

def update_internal_property(internal, external):
    internal.title = external.get("title")
    internal.description = external.get("description")
    internal.cover = external.get("cover")
    internal.address = external.get("address")
    internal.address_text = external.get("address_text")
    internal.delivery_date = external.get("delivery_date")
    internal.completion_rate = external.get("completion_rate")
    internal.residential_units = external.get("residential_units")
    internal.commercial_units = external.get("commercial_units")
    internal.payment_plan = external.get("payment_plan")
    
    # Handle boolean/int fields safely with fallback
    internal.post_delivery = external.get("post_delivery") or 0
    internal.payment_minimum_down_payment = external.get("payment_minimum_down_payment") or 0
    internal.guarantee_rental_guarantee = external.get("guarantee_rental_guarantee") or 0
    internal.guarantee_rental_guarantee_value = external.get("guarantee_rental_guarantee_value") or 0
    internal.downPayment = external.get("downPayment") or 0
    internal.low_price = external.get("low_price") or 0
    internal.min_area = external.get("min_area") or 0

    # Foreign keys
    internal.city = get_or_none(City, external.get("city"))
    internal.district = get_or_none(District, external.get("district"))
    internal.developer = get_or_none(DeveloperCompany, external.get("developer_company"))
    internal.property_type = get_or_none(PropertyType, external.get("property_type"))
    internal.property_status = get_or_none(PropertyStatus, external.get("property_status"))
    internal.sales_status = get_or_none(SalesStatus, external.get("sales_status"))

    # updated_at
    updated_at_str = external.get("updated_at")
    if updated_at_str:
        internal.updated_at = date_parser.parse(updated_at_str)

    internal.save()

def is_different(internal, external):
    if internal.description != external.get("description"):
        log.info(f"✏️ Description updated for Property ID {internal.id}")
        return True
    fields_to_check = [
        ("title", external.get("title")),
        ("description", external.get("description")),
        ("cover", external.get("cover")),
        ("address", external.get("address")),
        ("address_text", external.get("address_text")),
        ("delivery_date", external.get("delivery_date")),
        ("completion_rate", external.get("completion_rate")),
        ("residential_units", external.get("residential_units")),
        ("commercial_units", external.get("commercial_units")),
        ("payment_plan", external.get("payment_plan")),
        ("post_delivery", external.get("post_delivery") or 0),
        ("payment_minimum_down_payment", external.get("payment_minimum_down_payment") or 0),
        ("guarantee_rental_guarantee", external.get("guarantee_rental_guarantee") or 0),
        ("guarantee_rental_guarantee_value", external.get("guarantee_rental_guarantee_value") or 0),
        ("downPayment", external.get("downPayment") or 0),
        ("low_price", external.get("low_price") or 0),
        ("min_area", external.get("min_area") or 0),
    ]

    for field, ext_val in fields_to_check:
        if getattr(internal, field, None) != ext_val:
            return True

    # Also compare foreign keys by ID
    fk_fields = {
        "city_id": external.get("city", {}).get("id"),
        "district_id": external.get("district", {}).get("id"),
        "developer_id": external.get("developer_company", {}).get("id"),
        "property_type_id": external.get("property_type", {}).get("id"),
        "property_status_id": external.get("property_status", {}).get("id"),
        "sales_status_id": external.get("sales_status", {}).get("id"),
    }

    for field, ext_val in fk_fields.items():
        if getattr(internal, field, None) != ext_val:
            return True

    return False

def main():
    page = 1
    updated_count = 0
    skipped_count = 0
    created_count = 0

    while True:
        props = fetch_external_properties(page)
        if props is None:
            log.warning("⚠️ Aborting due to fetch error.")
            break
        if not props:
            log.warning("⚠️ No more data.")
            break

        for ext in props:
            prop_id = ext.get("id")
            if not prop_id:
                continue

            try:
                internal = Property.objects.get(id=prop_id)

                if is_different(internal, ext):
                    update_internal_property(internal, ext)
                    log.info(f"✅ Updated Property ID {prop_id}")
                    updated_count += 1
                else:
                    log.info(f"🔁 Skipped Property ID {prop_id} (no change)")
                    skipped_count += 1

            except Property.DoesNotExist:
                log.info(f"➕ Creating new Property ID {prop_id}")
                new_property = Property(id=prop_id)
                update_internal_property(new_property, ext)
                created_count += 1

        page += 1

    log.info(f"\n✅ Sync Summary → Updated: {updated_count}, Created: {created_count}, Skipped: {skipped_count}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error(f"❌ Fatal error during sync: {e}")
