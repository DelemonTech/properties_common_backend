from django.core.management.base import BaseCommand
import requests
import logging
import os
from datetime import datetime
from dateutil import parser as date_parser
from api.models import Property, City, District, DeveloperCompany, PropertyType, PropertyStatus, SalesStatus

# ✅ Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger()

# ✅ API Configuration
LISTING_URL = "https://panel.estaty.app/api/v1/getProperties"
SINGLE_PROPERTY_URL = "https://panel.estaty.app/api/v1/getProperty"
API_KEY = os.getenv("ESTATY_API_KEY")

HEADERS = {
    "App-key": API_KEY,
    "Content-Type": "application/json",
}

def parse_delivery_date(raw_date):
    if not raw_date:
        return None
    try:
        return int(date_parser.parse(raw_date).timestamp())
    except Exception:
        pass
    try:
        return int(datetime.strptime(raw_date, "%m/%Y").timestamp())
    except Exception:
        pass
    return None

def fetch_external_properties(page):
    try:
        url = f"{LISTING_URL}?page={page}" if page > 1 else LISTING_URL
        response = requests.post(url, headers=HEADERS, json={})
        response.raise_for_status()
        return response.json().get("properties", {}).get("data", [])
    except requests.RequestException as e:
        log.error(f"❌ Fetch failed page {page}: {e}")
        return []

def fetch_property_by_id(prop_id):
    try:
        response = requests.post(SINGLE_PROPERTY_URL, headers=HEADERS, json={"id": prop_id})
        response.raise_for_status()
        return response.json().get("property")
    except requests.RequestException as e:
        log.error(f"❌ Failed to fetch ID {prop_id}: {e}")
        return None

def get_or_none(model, data):
    if not data:
        return None
    return model.objects.filter(id=data.get("id") if isinstance(data, dict) else data).first()

def update_internal_property(internal, external):
    internal.title = external.get("title")
    internal.description = external.get("description")
    internal.cover = external.get("cover")
    internal.address = external.get("address")
    internal.address_text = external.get("address_text")
    internal.delivery_date = parse_delivery_date(external.get("delivery_date"))
    internal.completion_rate = external.get("completion_rate")
    internal.residential_units = external.get("residential_units")
    internal.commercial_units = external.get("commercial_units")
    internal.payment_plan = external.get("payment_plan")
    internal.post_delivery = external.get("post_delivery") or 0
    internal.payment_minimum_down_payment = external.get("payment_minimum_down_payment") or 0
    internal.guarantee_rental_guarantee = external.get("guarantee_rental_guarantee") or 0
    internal.guarantee_rental_guarantee_value = external.get("guarantee_rental_guarantee_value") or 0
    internal.downPayment = external.get("downPayment") or 0
    internal.low_price = external.get("low_price") or 0
    internal.min_area = external.get("min_area") or 0
    internal.city = get_or_none(City, external.get("city"))
    internal.district = get_or_none(District, external.get("district"))
    internal.developer = get_or_none(DeveloperCompany, external.get("developer_company"))
    internal.property_type = get_or_none(PropertyType, external.get("property_type"))
    internal.property_status = get_or_none(PropertyStatus, external.get("property_status"))
    internal.sales_status = get_or_none(SalesStatus, external.get("sales_status"))
    updated_at = external.get("updated_at")
    if updated_at:
        internal.updated_at = date_parser.parse(updated_at)
    internal.save()

def is_different(internal, external):
    def field_changed(name, new_val):
        return getattr(internal, name, None) != new_val

    fields = {
        "title": external.get("title"),
        "description": external.get("description"),
        "cover": external.get("cover"),
        "address": external.get("address"),
        "address_text": external.get("address_text"),
        "delivery_date": parse_delivery_date(external.get("delivery_date")),
        "completion_rate": external.get("completion_rate"),
        "residential_units": external.get("residential_units"),
        "commercial_units": external.get("commercial_units"),
        "payment_plan": external.get("payment_plan"),
        "post_delivery": external.get("post_delivery") or 0,
        "payment_minimum_down_payment": external.get("payment_minimum_down_payment") or 0,
        "guarantee_rental_guarantee": external.get("guarantee_rental_guarantee") or 0,
        "guarantee_rental_guarantee_value": external.get("guarantee_rental_guarantee_value") or 0,
        "downPayment": external.get("downPayment") or 0,
        "low_price": external.get("low_price") or 0,
        "min_area": external.get("min_area") or 0,
    }

    for field, value in fields.items():
        if field_changed(field, value):
            return True

    fk_fields = {
    "city_id": external.get("city", {}).get("id") if external.get("city") else None,
    "district_id": external.get("district", {}).get("id") if external.get("district") else None,
    "developer_id": external.get("developer_company", {}).get("id") if external.get("developer_company") else None,
    "property_type_id": external.get("property_type", {}).get("id") if external.get("property_type") else None,
    "property_status_id": external.get("property_status", {}).get("id") if external.get("property_status") else None,
    "sales_status_id": external.get("sales_status", {}).get("id") if external.get("sales_status") else None,
    }


    for field, value in fk_fields.items():
        if field_changed(field, value):
            return True

    return False

class Command(BaseCommand):
    help = "Sync properties from Estaty API and stop early if no changes"

    def handle(self, *args, **options):
        if not API_KEY:
            self.stderr.write("❌ Missing ESTATY_API_KEY environment variable.")
            return

        page = 1
        updated_count = 0
        created_count = 0

        while True:
            props = fetch_external_properties(page)
            if not props:
                self.stdout.write("✅ No more data.")
                break

            any_changes = False

            for summary in props:
                prop_id = summary.get("id")
                if not prop_id:
                    continue

                full_data = fetch_property_by_id(prop_id)
                if not full_data:
                    continue

                try:
                    internal = Property.objects.get(id=prop_id)
                    if is_different(internal, full_data):
                        update_internal_property(internal, full_data)
                        log.info(f"✅ Updated Property ID {prop_id}")
                        updated_count += 1
                        any_changes = True
                    else:
                        log.info(f"🔁 Skipped Property ID {prop_id} (no change)")

                except Property.DoesNotExist:
                    new_property = Property(id=prop_id)
                    update_internal_property(new_property, full_data)
                    log.info(f"➕ Created Property ID {prop_id}")
                    created_count += 1
                    any_changes = True

            if not any_changes:
                self.stdout.write("🛑 All properties unchanged. Sync stopped early.")
                break

            page += 1

        self.stdout.write(self.style.SUCCESS(f"\n📊 Sync Completed → Updated: {updated_count}, Created: {created_count}"))
