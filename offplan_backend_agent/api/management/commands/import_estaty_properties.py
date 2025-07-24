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

API_KEY = "27b84afeeef929815ab080ae22b29383"
LISTING_URL = "https://panel.estaty.app/api/v1/getProperties"
DETAIL_URL = "https://panel.estaty.app/api/v1/getProperty"
FILTER_URL = "https://estaty.app/api/v1/filter"
FILTERS_URL = "https://panel.estaty.app/api/v1/getFilters"

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
        self.stdout.write(self.style.SUCCESS("🔄 Syncing filter data from Estaty..."))
        self.sync_filters_from_estaty()

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
                detail = self.fetch_property_details(prop_id)
                if detail:
                    print(f"📦 Fetched property ID: {prop_id} - {detail.get('title', 'No Title')}")
                    self.save_property_to_db(detail)
                total_imported += 1
            page += 1

        self.delete_removed_properties(estaty_ids)
        self.stdout.write(self.style.SUCCESS(f"🏑 Done! Total properties saved: {total_imported}"))

        try:
            self.stdout.write(self.style.SUCCESS("🚀 Starting Property Unit import..."))
            call_command("import_property_unit")
            self.stdout.write(self.style.SUCCESS("✅ Property Unit import completed successfully."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Failed to import property units: {str(e)}"))

# --------------- FETCHING ALL FILTERS BY /getFilters ENDPOINT -----------------------

    def sync_filters_from_estaty(self):
        try:
            response = requests.post(FILTERS_URL, headers=HEADERS)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            log.error(f"❌ Failed to fetch filter data: {e}")
            return

        # Cities
        api_ids = set()
        for city in data.get("cites", []):
            api_ids.add(city["id"])
            City.objects.update_or_create(
                id=city["id"],
                defaults={"name": city["name"]}
            )
        City.objects.exclude(id__in=api_ids).delete()

        # Districts
        api_ids = set()
        cities_by_id = {c.id: c for c in City.objects.all()}
        for district in data.get("districts", []):
            district_id = district.get("id")
            name = district.get("name", "Unknown")
            city_id = district.get("city_id")
            city_obj = cities_by_id.get(city_id)

            api_ids.add(district_id)

            try:
                obj = District.objects.get(id=district_id)
                obj.name = name
                obj.city = city_obj
                obj.save()
            except District.DoesNotExist:
                District.objects.create(id=district_id, name=name, city=city_obj)
        District.objects.exclude(id__in=api_ids).delete()

        # Developer Companies
        api_ids = set()
        for dev in data.get("developer_companies", []):
            api_ids.add(dev["id"])
            DeveloperCompany.objects.update_or_create(
                id=dev["id"],
                defaults={"name": dev["name"]}
            )
        DeveloperCompany.objects.exclude(id__in=api_ids).delete()

        # Property Types
        api_ids = set()
        for ptype in data.get("property_types", []):
            api_ids.add(ptype["id"])
            PropertyType.objects.update_or_create(
                id=ptype["id"],
                defaults={"name": ptype["name"]}
            )
            print(ptype, "ptype")
        PropertyType.objects.exclude(id__in=api_ids).delete()

        # Property Statuses
        api_ids = set()
        for status in data.get("property_statuses", []):
            api_ids.add(status["id"])
            PropertyStatus.objects.update_or_create(
                id=status["id"],
                defaults={"name": status["name"]}
            )
        PropertyStatus.objects.exclude(id__in=api_ids).delete()

        # Sales Statuses
        api_ids = set()
        for status in data.get("sales_statuses", []):
            api_ids.add(status["id"])
            SalesStatus.objects.update_or_create(
                id=status["id"],
                defaults={"name": status["name"]}
            )
        SalesStatus.objects.exclude(id__in=api_ids).delete()

        # Facilities
        api_ids = set()
        for facility in data.get("facilities", []):
            api_ids.add(facility["id"])
            Facility.objects.update_or_create(
                id=facility["id"],
                defaults={"name": facility["name"]}
            )
        Facility.objects.exclude(id__in=api_ids).delete()

        self.stdout.write(self.style.SUCCESS("✅ Filters synced from Estaty"))

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
        to_delete_ids = local_ids - estaty_ids

        if to_delete_ids:
            for prop in Property.objects.filter(id__in=to_delete_ids):
                self.stdout.write(self.style.WARNING(f"🗑 Deleting property {prop.id} and its related units..."))
                PropertyUnit.objects.filter(property=prop).delete()
                prop.delete()

            self.stdout.write(self.style.WARNING(f"🗑 Deleted {len(to_delete_ids)} missing properties from DB"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ No properties deleted. DB is in sync."))
                
# --------------- SAVING PROPERTIES AND ITS DETAILS TO DATABASE -----------------------

    def save_property_to_db(self, data):
        if not data.get("id"):
            log.warning(f"⚠️ Skipping invalid property (missing ID): {data}")
            return None
        
        title = data.get("title") or f"Untitled Property {data['id']}"
        print(title,'title')

        

        # --- (only by ID) ---
        developer_id = (data.get("developer_company") or {}).get("id")
        print(developer_id,'dev')
        city_id = (data.get("city") or {}).get("id")
        print(city_id,'city')
        district_id = (data.get("district") or {}).get("id")
        print(district_id,'dist')
        property_type_id = (data.get("property_type") or {}).get("id")
        print(property_type_id,'type')
        property_status_id = (data.get("property_status") or {}).get("id")
        print(property_status_id,'status')
        sales_status_id = (data.get("sales_status") or {}).get("id")
        print(sales_status_id,'sales')

        developer = DeveloperCompany.objects.filter(id=developer_id).first()
        city = City.objects.filter(id=city_id).first()
        district = District.objects.filter(id=district_id).first()
        prop_type = PropertyType.objects.filter(id=property_type_id).first()
        prop_status = PropertyStatus.objects.filter(id=property_status_id).first()
        sales_status = SalesStatus.objects.filter(id=sales_status_id).first()
        
        if not developer:
            log.warning(f"❌ Missing developer with ID {developer_id}")
        if not city:
            log.warning(f"❌ Missing city with ID {city_id}")
        if not district:
            log.warning(f"❌ Missing district with ID {district_id}")
        if not prop_type:
            log.warning(f"❌ Missing property type with ID {property_type_id}")
        if not prop_status:
            log.warning(f"❌ Missing property status with ID {property_status_id}")
        if not sales_status:
            log.warning(f"❌ Missing sales status with ID {sales_status_id}")

        

        updated_at_raw = parse_datetime(data.get("updated_at")) or now()
        updated_at = make_aware(updated_at_raw) if is_naive(updated_at_raw) else updated_at_raw

        with transaction.atomic():
            prop, _ = Property.objects.update_or_create(
                id=data["id"],
                defaults={
                    "title": title,
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

            # Facilities (safe get by ID only)
            prop.facilities.clear()
            for f in data.get("property_facilities", []):
                f_data = f.get("facility", {})
                f_id = f_data.get("id")
                if f_id:
                    facility = Facility.objects.filter(id=f_id).first()
                    if facility:
                        prop.facilities.add(facility)

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