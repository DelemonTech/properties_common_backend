import requests
import logging
from datetime import datetime
from django.utils.timezone import make_aware, now, is_naive
from django.utils.dateparse import parse_datetime
from django.core.management.base import BaseCommand
from dateutil import parser as date_parser
from django.core.management import call_command
from typing import Optional
import json
from django.db import transaction

from api.models import (
    City, District, DeveloperCompany, PropertyType, PropertyStatus, SalesStatus,
    Facility, Property, GroupedApartment, PropertyUnit, PropertyImage,
    PaymentPlan, PaymentPlanValue
)

# Constants
API_KEY = "27b84afeeef929815ab080ae22b29383"
LISTING_URL = "https://panel.estaty.app/api/v1/getProperties"
DETAIL_URL = "https://panel.estaty.app/api/v1/getProperty"
FILTER_URL = "https://estaty.app/api/v1/filter"
HEADERS = {
    "App-key": API_KEY,
    "Content-Type": "application/json",
}

log = logging.getLogger(__name__)

def convert_mm_yyyy_to_yyyymm(date_str: str) -> Optional[int]:
    try:
        month, year = date_str.strip().split('/')
        return int(f"{year}{int(month):02d}")
    except Exception:
        return None

class Command(BaseCommand):
    help = "Import and save Estaty properties"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("✅ Starting Estaty property import..."))
        page = 1
        total_imported = 0
        estaty_ids = set()

        while True:
            properties = self.fetch_property_ids(page)
            if not properties:
                break

            for prop in properties:
                prop_id = prop.get("id")
                if not prop_id:
                    continue
                
                estaty_ids.add(prop_id)
                print('set id',estaty_ids)
                detail = self.fetch_property_details(prop_id)
                if detail:
                    print(f"📦 Fetched property ID: {prop_id} - {detail.get('title', 'No Title')}")
                    self.save_property_to_db(detail)

            
                total_imported += 1
            page += 1
        self.delete_removed_properties(estaty_ids)
        self.stdout.write(self.style.SUCCESS(f"🏁 Done! Total properties saved: {total_imported}"))
        try:
            self.stdout.write(self.style.SUCCESS("🚀 Starting Property Unit import..."))
            call_command("import_property_unit")
            self.stdout.write(self.style.SUCCESS("✅ Property Unit import completed successfully."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Failed to import property units: {str(e)}"))
            
# --------------- FETCHING ALL PROPETIES BY /getProperties ENDPOINT -----------------------

    def fetch_property_ids(self, page=1):
        """Fetch properties from the /getProperties endpoint"""
        try:
            url = f"{LISTING_URL}?page={page}" if page > 1 else LISTING_URL
            response = requests.post(url, headers=HEADERS, json={})
            response.raise_for_status()
            data = response.json()
            return data.get("properties", {}).get("data", [])
        except Exception as e:
            log.error(f"❌ Error fetching property list (page {page}): {e}")
            return []
        
# --------------- FETCHING PROPERTY DETAILS BY ID BY /getProperty ENDPOINT -----------------------

    def fetch_property_details(self, prop_id):
        """Fetch property details from /getProperty endpoint"""
        try:
            response = requests.post(DETAIL_URL, headers=HEADERS, json={"id": prop_id})
            response.raise_for_status()
            return response.json().get("property")
        except Exception as e:
            log.error(f"❌ Error fetching details for ID {prop_id}: {e}")
            return None
        
# --------------- DELETION OF PROPERTIES NO LONGER EXISTS IN ESTATY API -----------------------

    def delete_removed_properties(self, estaty_ids: set):
        local_ids = set(Property.objects.values_list("id", flat=True))
        to_delete = local_ids - estaty_ids
        if to_delete:
            deleted_count, _ = Property.objects.filter(id__in=to_delete).delete()
            self.stdout.write(self.style.WARNING(f"🗑 Deleted {deleted_count} missing properties from DB"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ No properties deleted. DB is in sync."))
            
# --------------- SAVING PROPERTIES AND ITS DETAILS TO DATABASE -----------------------

    def save_property_to_db(self, data):
        """Save property and related information to the database"""
        if not data.get("id") or not data.get("title"):
            log.warning(f"⚠️ Skipping invalid property data: {data}")
            return None

        developer_data = data.get("developer_company") or {}
        developer_name = developer_data.get("name", "Unknown")
        developer_id = developer_data.get("id")

        if developer_id:
            developer, _ = DeveloperCompany.objects.update_or_create(
                id=developer_id,
                defaults={"name": developer_name}
            )
        else:
            developer, _ = DeveloperCompany.objects.get_or_create(name=developer_name)

        city, _ = City.objects.get_or_create(name=(data.get("city") or {}).get("name", "Unknown"))
        district, _ = District.objects.get_or_create(
            name=(data.get("district") or {}).get("name", "Unknown"),
            city=city
        )
        prop_type, _ = PropertyType.objects.get_or_create(
            name=(data.get("property_type") or {}).get("name", "Unknown")
        )
        prop_status, _ = PropertyStatus.objects.get_or_create(
            name=(data.get("property_status") or {}).get("name", "Unknown")
        )
        sales_status, _ = SalesStatus.objects.get_or_create(
            name=(data.get("sales_status") or {}).get("name", "Unknown")
        )
        
        updated_at_raw = parse_datetime(data.get("updated_at")) or now()
        updated_at = make_aware(updated_at_raw) if is_naive(updated_at_raw) else updated_at_raw

        with transaction.atomic():
            prop, _ = Property.objects.update_or_create(
                id=data["id"],
                defaults={
                    "title": data.get("title"),
                    "description": data.get("description") or "",
                    "cover": data.get("cover"),
                    "address": data.get("address"),
                    "address_text": data.get("address_text"),
                    "delivery_date": convert_mm_yyyy_to_yyyymm(data.get("delivery_date")),
                    "city": city,
                    "district": district,
                    "developer": developer,
                    "property_type": prop_type,
                    "property_status": prop_status,
                    "sales_status": sales_status,
                    "completion_rate": data.get("completion_rate") or 0,
                    "residential_units": data.get("residential_units") or 0,
                    "commercial_units": data.get("commercial_units") or 0,
                    "payment_plan": data.get("payment_plan") or 0,
                    "post_delivery": data.get("post_delivery") == 1,
                    "payment_minimum_down_payment": data.get("payment_minimum_down_payment") or 0,
                    "guarantee_rental_guarantee": data.get("guarantee_rental_guarantee") == 1,
                    "guarantee_rental_guarantee_value": data.get("guarantee_rental_guarantee_value") or 0,
                    "downPayment": data.get("downPayment") or 0,
                    "low_price": data.get("low_price") or 0,
                    "min_area": data.get("min_area") or 0,
                    "updated_at": updated_at
                }
            )

        
        # Facilities
        prop.facilities.clear()
        for f in data.get("property_facilities", []):
            f_data = f.get("facility", {})
            if not f_data:
                continue
            facility_obj, _ = Facility.objects.get_or_create(
                id=f_data["id"],
                defaults={"name": f_data["name"]}
            )
            prop.facilities.add(facility_obj)

        # Grouped Apartments
        prop.grouped_apartments.all().delete()
        for g in data.get("grouped_apartments") or []:
            GroupedApartment.objects.create(
                property=prop,
                unit_type=g.get("Unit_Type", ""),
                rooms=g.get("Rooms", ""),
                min_price=g.get("min_price"),
                min_area=g.get("min_area")
            )

        # Images
        prop.property_images.all().delete()
        for img in data.get("property_images") or []:
            PropertyImage.objects.create(
                property=prop,
                image=img.get("image"),
                type=img.get("type", 2),
                created_at=make_aware(datetime.now())
            )

        # Payment Plans
        prop.payment_plans.all().delete()
        for plan in data.get("payment_plans") or []:
            pp = PaymentPlan.objects.create(
                property=prop,
                name=plan.get("name"),
                description=plan.get("description") or ""
            )
            for val in plan.get("values", []):
                PaymentPlanValue.objects.create(
                    property_payment_plan=pp,
                    name=val.get("name"),
                    value=val.get("value")
                )

        return prop

        