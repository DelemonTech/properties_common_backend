import os
import requests
import logging
from datetime import datetime
from dateutil import parser as date_parser

from django.core.management.base import BaseCommand
from django.db import DatabaseError, IntegrityError, transaction
from api.models import (
    Property, City, District, DeveloperCompany, PropertyType,
    PropertyStatus, SalesStatus, Facility, PropertyUnit,
    GroupedApartment, PropertyImage, PaymentPlan, PaymentPlanValue
)

log = logging.getLogger("django")

LISTING_URL = "https://panel.estaty.app/api/v1/getProperties"
SINGLE_PROPERTY_URL = "https://panel.estaty.app/api/v1/getProperty"
API_KEY = os.getenv("ESTATY_API_KEY")

if not API_KEY:
    raise RuntimeError("❌ Missing ESTATY_API_KEY in Django settings.")

HEADERS = {
    "App-key": API_KEY,
    "Content-Type": "application/json",
}


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


def update_property(internal, external):
    internal.title = external.get("title")
    internal.description = external.get("description")
    internal.cover = external.get("cover")
    internal.address = external.get("address")
    internal.low_price = external.get("low_price") or 0
    internal.min_area = external.get("min_area") or 0
    internal.delivery_date = parse_unix_date(external.get("delivery_date"))
    internal.updated_at = date_parser.parse(external.get("updated_at")) if external.get("updated_at") else None
    internal.save()


def parse_unix_date(raw_date):
    if not raw_date or not isinstance(raw_date, str):
        return None
    try:
        dt = date_parser.parse(raw_date)
        return int(dt.timestamp())
    except Exception:
        return None


# class Command(BaseCommand):
#     help = "Sync properties from external API for 10 pages only"

def main(self, *args, **options):
    try:
        with transaction.atomic():
            page = 1
            updated_count = 0
            created_count = 0

            while page <= 10:  # 🚨 Stop after 10 pages
                props = fetch_external_properties(page)
                if not props:
                    log.info("✅ No more data on this page.")
                    break

                for summary in props:
                    prop_id = summary.get("id")
                    if not prop_id:
                        log.error(f"❌ Missing property 'id': {summary}")
                        continue

                    external_data = fetch_property_by_id(prop_id)
                    if not external_data:
                        continue

                    try:
                        internal = Property.objects.get(id=prop_id)
                        update_property(internal, external_data)
                        log.info(f"✅ Updated Property ID {prop_id}")
                        updated_count += 1
                    except Property.DoesNotExist:
                        new_property = Property(id=prop_id)
                        update_property(new_property, external_data)
                        log.info(f"➕ Created Property ID {prop_id}")
                        created_count += 1

                page += 1

            log.info(f"\n📊 Sync Summary → Updated: {updated_count}, Created: {created_count}")

    except Exception as e:
        log.error(f"❌ Fatal error during sync: {e}")

if __name__ == "__main__":
    main()
