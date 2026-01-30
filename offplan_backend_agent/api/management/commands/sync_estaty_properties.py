import os
import requests
import logging
from datetime import datetime, timezone
from dateutil import parser as date_parser

from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import (
    Property, City, District, DeveloperCompany, PropertyType,
    PropertyStatus, SalesStatus, Facility, PropertyUnit
)

# ✅ Setup logger
log = logging.getLogger("django")

# ✅ API details
LISTING_URL = "https://panel.estaty.app/api/v1/getProperties"
SINGLE_PROPERTY_URL = "https://panel.estaty.app/api/v1/getProperty"
FILTER_PROPERTY_URL = "https://panel.estaty.app/api/v1/filter"
API_KEY = os.getenv("ESTATY_API_KEY")

if not API_KEY:
    raise RuntimeError("❌ Missing ESTATY_API_KEY in environment variables.")

HEADERS = {
    "App-key": API_KEY,
    "Content-Type": "application/json",
}

# ✅ Utility to parse date safely
def parse_unix_date(raw_date):
    if not raw_date or not isinstance(raw_date, str):
        return None
    try:
        dt = date_parser.parse(raw_date)
        return int(dt.timestamp())
    except Exception:
        return None

# ✅ Fetch properties for a page
def fetch_external_properties(page):
    try:
        url = f"{LISTING_URL}?page={page}"
        log.info(f"🌐 Fetching properties from page {page}")
        response = requests.post(url, headers=HEADERS, json={})
        response.raise_for_status()
        data = response.json()
        return data.get("properties", {}).get("data", [])
    except requests.RequestException as e:
        log.error(f"❌ Failed to fetch page {page}: {e}")
        return []

# ✅ Fetch single property details
def fetch_property_by_id(prop_id):
    try:
        log.info(f"📥 Fetching details for property ID {prop_id}")
        response = requests.post(SINGLE_PROPERTY_URL, headers=HEADERS, json={"id": prop_id})
        response.raise_for_status()
        data = response.json()
        return data.get("property")
    except requests.RequestException as e:
        log.error(f"❌ Failed to fetch property ID {prop_id}: {e}")
        return None

# ✅ Fetch property details by name from /filter API
def fetch_property_by_name(property_name):
    try:
        log.info(f"📥 Fetching details from /filter for: {property_name}")
        response = requests.post(FILTER_PROPERTY_URL, headers=HEADERS, json={"property_name": property_name})
        response.raise_for_status()
        data = response.json()
        if data.get("properties"):
            return data["properties"][0]  # First matching property
        return None
    except requests.RequestException as e:
        log.error(f"❌ Failed to fetch property '{property_name}' from /filter: {e}")
        return None

# ✅ Merge property data
def merge_property_data(primary_data, fallback_data):
    merged = primary_data.copy()
    for key, value in fallback_data.items():
        if merged.get(key) in [None, "", []] and value not in [None, "", []]:
            log.debug(f"🆙 Filling missing field '{key}' from /filter API")
            merged[key] = value
    return merged

# ✅ Merge units
def merge_units(primary_units, fallback_units):
    fallback_map = {unit['id']: unit for unit in fallback_units if unit.get('id')}
    merged_units = []

    for unit in primary_units:
        unit_id = unit.get("id")
        fallback_unit = fallback_map.get(unit_id, {})
        merged_unit = unit.copy()

        for key, value in fallback_unit.items():
            if merged_unit.get(key) in [None, "", []] and value not in [None, "", []]:
                log.debug(f"🆙 Filling missing field '{key}' for Unit ID {unit_id} from /filter API")
                merged_unit[key] = value

        merged_units.append(merged_unit)

    return merged_units

# ✅ Update or create property and units
def update_property(internal, external):
    # 🔄 Update property fields
    internal.title = external.get("title")
    internal.description = external.get("description")
    internal.cover = external.get("cover")
    internal.address = external.get("address")
    internal.low_price = external.get("low_price") or 0
    internal.min_area = external.get("min_area") or 0
    internal.delivery_date = parse_unix_date(external.get("delivery_date"))
    internal.updated_at = date_parser.parse(external.get("updated_at")) if external.get("updated_at") else timezone.now()
    internal.save()

    # 🔄 Update units
    external_units = external.get("apartment", None)

    if external_units is None:
        log.warning(f"⚠️ No units field found in API for property {internal.id}. Skipping unit update.")
        return  # Skip units entirely

    existing_unit_ids = set(PropertyUnit.objects.filter(property=internal).values_list("id", flat=True))
    external_unit_ids = set()

    if external_units:
        for unit_data in external_units:
            unit_id = unit_data.get("id")
            if not unit_id:
                log.warning(f"⚠️ Skipping unit with no ID for Property {internal.id}")
                continue

            external_unit_ids.add(unit_id)
            created_at = date_parser.parse(unit_data.get("created_at")) if unit_data.get("created_at") else timezone.now()
            updated_at = date_parser.parse(unit_data.get("updated_at")) if unit_data.get("updated_at") else timezone.now()

            PropertyUnit.objects.update_or_create(
                id=unit_id,
                defaults={
                    "property": internal,
                    "apartment_type_id": unit_data.get("apartment_type_id"),
                    "price": unit_data.get("price") or 0,
                    "area": unit_data.get("area") or 0,
                    "floor_plan_image": unit_data.get("floor_plan_image"),
                    "unit_image": unit_data.get("unit_image"),
                    "status": unit_data.get("status") or "Unknown",
                    "created_at": created_at,
                    "updated_at": updated_at,
                },
            )

        # 🗑 Delete units no longer present
        to_delete_units = existing_unit_ids - external_unit_ids
        if to_delete_units:
            log.info(f"🗑 Deleting {len(to_delete_units)} stale units for Property ID {internal.id}")
            PropertyUnit.objects.filter(id__in=to_delete_units).delete()
    else:
        log.info(f"ℹ️ API returned empty units for property {internal.id}. Preserving existing units.")


# ✅ Django Command
class Command(BaseCommand):
    help = "Sync properties and units from Estaty API for 10 pages with fallback to /filter API"

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                page = 1
                updated_count = 0
                created_count = 0

                while page <= 12:  # Limit to 10 pages
                    props = fetch_external_properties(page)
                    if not props:
                        log.info("✅ No more data on this page.")
                        break

                    for summary in props:
                        prop_id = summary.get("id")
                        prop_name = summary.get("title")
                        if not prop_id or not prop_name:
                            log.error(f"❌ Missing property ID or title: {summary}")
                            continue

                        # Fetch from /getProperty
                        primary_data = fetch_property_by_id(prop_id)
                        if not primary_data:
                            continue

                        # Fetch from /filter by property_name
                        fallback_data = fetch_property_by_name(prop_name)

                        # Merge missing fields
                        if fallback_data:
                            primary_data = merge_property_data(primary_data, fallback_data)
                            primary_units = primary_data.get("apartment", [])
                            fallback_units = fallback_data.get("apartment", [])
                            merged_units = merge_units(primary_units, fallback_units)
                            primary_data["apartment"] = merged_units

                        # Save to DB
                        try:
                            internal = Property.objects.get(id=prop_id)
                            update_property(internal, primary_data)
                            log.info(f"✅ Updated Property ID {prop_id}")
                            updated_count += 1
                        except Property.DoesNotExist:
                            new_property = Property(id=prop_id)
                            update_property(new_property, primary_data)
                            log.info(f"➕ Created Property ID {prop_id}")
                            created_count += 1

                    page += 1

                log.info(f"\n📊 Sync Summary → Updated: {updated_count}, Created: {created_count}")

        except Exception as e:
            log.error(f"❌ Fatal error during sync: {e}")
