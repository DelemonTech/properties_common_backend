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
import os
from dotenv import load_dotenv
from django.db import transaction
from django.core.files.base import ContentFile
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

from api.models import (
    City, District, DeveloperCompany, PropertyType, PropertyStatus, SalesStatus,
    Facility, Property, GroupedApartment, PropertyUnit, PropertyImage,
    PaymentPlan, PaymentPlanValue
)

API_KEY = os.getenv("ESTATY_API_KEY")
LISTING_URL = "https://panel.estaty.app/api/v1/getProperties"
DETAIL_URL = "https://panel.estaty.app/api/v1/getProperty"
FILTER_URL = "https://panel.estaty.app/api/v1/filter"
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

    def download_image(self, url: str, field_name: str = "image"):
        """Downloads an image from URL and returns a ContentFile tuple (name, content)"""
        if not url:
            return None, None
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                file_name = os.path.basename(url.split("?")[0])  # strip query params
                return file_name, ContentFile(response.content)
        except Exception as e:
            self.stderr.write(self.style.WARNING(f"⚠️ Could not download {field_name} from {url}: {e}"))
        return None, None
    
    def download_images_for_property(self, prop, images_data):
        """Download all images for a property concurrently"""
        existing_images = set(
            os.path.basename(img.image.name)
            for img in prop.property_images.all()
            if img.image
        )

        # Filter only new images
        to_download = []
        for img in images_data:
            img_url = img.get("image")
            if not img_url:
                continue
            url_file_name = os.path.basename(img_url.split("?")[0])
            if url_file_name not in existing_images:
                to_download.append(img)

        if not to_download:
            return  # ✅ Nothing new to download

        def download_single(img):
            img_url = img.get("image")
            file_name, content = self.download_image(img_url, "property image")
            return img, file_name, content

        # ✅ Download all images concurrently (5 at a time)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(download_single, img): img for img in to_download}
            for future in as_completed(futures):
                img, file_name, content = future.result()
                if file_name and content:
                    img_instance = PropertyImage(
                        property=prop,
                        type=img.get("type", 2),
                        created_at=make_aware(datetime.now())
                    )
                    img_instance.image.save(file_name, content, save=False)
                    img_instance.save()

    def handle(self, *args, **options):
        # self.stdout.write(self.style.SUCCESS("🔄 Syncing filter data from Estaty..."))
        # self.sync_filters_from_estaty()

        self.sync_developers_detailed()

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

        # --- SAFETY VALVE ---
        if not estaty_ids:
            self.stdout.write(self.style.ERROR("❌ No properties fetched from API. Aborting deletion to protect local data."))
            return # STOP HERE. Do not delete anything!

        self.delete_removed_properties(estaty_ids)
        self.stdout.write(self.style.SUCCESS(f"🏑 Done! Total properties saved: {total_imported}"))

        try:
            self.stdout.write(self.style.SUCCESS("🚀 Starting Property Unit import..."))
            call_command("import_property_unit")
            self.stdout.write(self.style.SUCCESS("✅ Property Unit import completed successfully."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Failed to import property units: {str(e)}"))

    def download_and_save_logo(self, developer_instance, logo_url):
        if not logo_url:
            return

        try:
            # Note: requests is already imported in your script
            response = requests.get(logo_url, timeout=10)
            if response.status_code == 200:
                # Extract the file name (e.g., 'logo.png')
                file_name = os.path.basename(logo_url)
                
                # Save the binary content to the ImageField
                developer_instance.logo.save(
                    file_name, 
                    ContentFile(response.content), 
                    save=True
                )
        except Exception as e:
            self.stderr.write(self.style.WARNING(f"⚠️ Could not download logo for {developer_instance.name}: {e}"))

    def sync_developers_detailed(self):
        """Fetches detailed developer data from the /filter endpoint"""
        self.stdout.write(self.style.SUCCESS("🔍 Syncing detailed developer profiles..."))
        try:
            response = requests.post(FILTER_URL, headers=HEADERS, json={})
            response.raise_for_status()
            data = response.json()
            
            properties = data.get("properties", [])
            
            count = 0
            seen_developer_ids = set()  # ✅ Track processed developers

            for prop_data in properties:
                dev_data = prop_data.get("developer_company")
                if not dev_data or not dev_data.get("id"):
                    continue

                dev_id = dev_data.get("id")

                # ✅ Skip if we already processed this developer
                if dev_id in seen_developer_ids:
                    continue
                seen_developer_ids.add(dev_id)

                developer, created = DeveloperCompany.objects.update_or_create(
                    id=dev_id,
                    defaults={
                        "name": dev_data.get("name"),
                        "slug": dev_data.get("slug"),
                        "user_id": dev_data.get("user_id"),
                        "website": dev_data.get("website"),
                        "email": dev_data.get("email"),
                        "phone": dev_data.get("phone"),
                        "address": dev_data.get("address"),
                        "overview": dev_data.get("overview"),
                    }
                ) 
                
                # Handle Logo Download
                logo_url = dev_data.get("logo")
                if logo_url:
                    url_file_name = os.path.basename(logo_url.split("?")[0])
                    current_name = os.path.basename(developer.logo.name) if developer.logo else None
                    
                    if not developer.logo or current_name != url_file_name:
                        self.stdout.write(f"📥 Downloading logo for: {developer.name}")
                        file_name, content = self.download_image(logo_url, "developer logo")
                        if file_name and content:
                            developer.logo.save(file_name, content, save=True)
                    
                count += 1
            
            self.stdout.write(self.style.SUCCESS(f"✅ Detailed Developer Sync Complete ({count} unique developers processed)"))
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Failed to sync detailed developers: {e}"))
# --------------- FETCHING ALL FILTERS BY /getFilters ENDPOINT -----------------------

    # def sync_filters_from_estaty(self):
    #     try:
    #         response = requests.post(FILTERS_URL, headers=HEADERS)
    #         response.raise_for_status()
    #         data = response.json()
    #     except Exception as e:
    #         log.error(f"❌ Failed to fetch filter data: {e}")
    #         return

    #     # Cities
    #     api_ids = set()
    #     for city in data.get("cites", []):
    #         api_ids.add(city["id"])
    #         City.objects.update_or_create(
    #             id=city["id"],
    #             defaults={"name": city["name"]}
    #         )
    #     City.objects.exclude(id__in=api_ids).delete()

    #     # Districts
    #     api_ids = set()
    #     cities_by_id = {c.id: c for c in City.objects.all()}
    #     for district in data.get("districts", []):
    #         district_id = district.get("id")
    #         name = district.get("name", "Unknown")
    #         city_id = district.get("city_id")
    #         city_obj = cities_by_id.get(city_id)

    #         api_ids.add(district_id)

    #         try:
    #             obj = District.objects.get(id=district_id)
    #             obj.name = name
    #             obj.city = city_obj
    #             obj.save()
    #         except District.DoesNotExist:
    #             District.objects.create(id=district_id, name=name, city=city_obj)
    #     District.objects.exclude(id__in=api_ids).delete()

    #     # Developer Companies
    #     api_ids = set()
    #     for dev in data.get("developer_companies", []):
    #         api_ids.add(dev["id"])
    #         DeveloperCompany.objects.update_or_create(
    #             id=dev["id"],
    #             defaults={"name": dev["name"]}
    #         )
    #     DeveloperCompany.objects.exclude(id__in=api_ids).delete()

    #     # Property Types
    #     api_ids = set()
    #     for ptype in data.get("property_types", []):
    #         api_ids.add(ptype["id"])
    #         PropertyType.objects.update_or_create(
    #             id=ptype["id"],
    #             defaults={"name": ptype["name"]}
    #         )
    #         print(ptype, "ptype")
    #     PropertyType.objects.exclude(id__in=api_ids).delete()

    #     # Property Statuses
    #     api_ids = set()
    #     for status in data.get("property_statuses", []):
    #         api_ids.add(status["id"])
    #         PropertyStatus.objects.update_or_create(
    #             id=status["id"],
    #             defaults={"name": status["name"]}
    #         )
    #     PropertyStatus.objects.exclude(id__in=api_ids).delete()

    #     # Sales Statuses
    #     api_ids = set()
    #     for status in data.get("sales_statuses", []):
    #         api_ids.add(status["id"])
    #         SalesStatus.objects.update_or_create(
    #             id=status["id"],
    #             defaults={"name": status["name"]}
    #         )
    #     SalesStatus.objects.exclude(id__in=api_ids).delete()

    #     # Facilities
    #     api_ids = set()
    #     for facility in data.get("facilities", []):
    #         api_ids.add(facility["id"])
    #         Facility.objects.update_or_create(
    #             id=facility["id"],
    #             defaults={"name": facility["name"]}
    #         )
    #     Facility.objects.exclude(id__in=api_ids).delete()

    #     self.stdout.write(self.style.SUCCESS("✅ Filters synced from Estaty"))

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

        # Developer
        dev_data = data.get("developer_company") or {}
        dev_id = dev_data.get("id")
        if dev_id:
            developer, created = DeveloperCompany.objects.get_or_create(
                id=dev_id,
                defaults={"name": dev_data.get("name") or "Unnamed Developer"}
            )
        else:
            developer = None       

        # City
        city_data = data.get("city") or {}
        city, _ = City.objects.update_or_create(
            id=city_data.get("id"),
            defaults={"name": city_data.get("name") or "Unnamed City"}
        )

        # District
        district_data = data.get("district") or {}
        district_id = district_data.get("id")
        if not district_id:
            log.warning(f"⚠️ Skipping property due to missing district ID: {district_data}")
            return None

        District.objects.filter(id=district_id).update(
            name=district_data.get("name") or "Unnamed District",
            city=city
        )
        district, created = District.objects.get_or_create(
            id=district_id,
            defaults={
                "name": district_data.get("name") or "Unnamed District",
                "city": city
            }
        )

        # Property Type
        prop_type_data = data.get("property_type") or {}
        prop_type, _ = PropertyType.objects.update_or_create(
            id=prop_type_data.get("id"),
            defaults={"name": prop_type_data.get("name") or "Unnamed Type"}
        )

        # Property Status
        prop_status_data = data.get("property_status") or {}
        prop_status, _ = PropertyStatus.objects.update_or_create(
            id=prop_status_data.get("id"),
            defaults={"name": prop_status_data.get("name") or "Unnamed Status"}
        )

        # Sales Status
        sales_status_data = data.get("sales_status") or {}
        sales_status, _ = SalesStatus.objects.update_or_create(
            id=sales_status_data.get("id"),
            defaults={"name": sales_status_data.get("name") or "Unnamed Sales Status"}
        )

        updated_at_raw = parse_datetime(data.get("updated_at")) or now()
        updated_at = make_aware(updated_at_raw) if is_naive(updated_at_raw) else updated_at_raw

        with transaction.atomic():
            # ✅ Always update text/data fields
            prop, created = Property.objects.update_or_create(
                id=data["id"],
                defaults={
                    "title": title,
                    "description": data.get("description") or "",
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

            # ✅ Cover - only download if changed
            cover_url = data.get("cover")
            if cover_url:
                url_file_name = os.path.basename(cover_url.split("?")[0])
                current_name = os.path.basename(prop.cover.name) if prop.cover else None
                if not prop.cover or current_name != url_file_name:
                    file_name, content = self.download_image(cover_url, "property cover")
                    if file_name and content:
                        prop.cover.save(file_name, content, save=True)

            # ✅ Facilities - always re-sync (fast, no file downloads)
            prop.facilities.clear()
            for f in data.get("property_facilities", []):
                f_data = f.get("facility", {})
                f_id = f_data.get("id")
                f_name = f_data.get("name")
                if not f_id:
                    continue
                facility, _ = Facility.objects.get_or_create(
                    id=f_id,
                    defaults={"name": f_name or "Unnamed Facility"}
                )
                prop.facilities.add(facility)

            # ✅ Grouped Apartments - re-sync only if count changed
            incoming_apartments = data.get("grouped_apartments") or []
            if prop.grouped_apartments.count() != len(incoming_apartments):
                prop.grouped_apartments.all().delete()
                for g in incoming_apartments:
                    GroupedApartment.objects.create(
                        property=prop,
                        unit_type=g.get("Unit_Type", ""),
                        rooms=g.get("Rooms", ""),
                        min_price=g.get("min_price"),
                        min_area=g.get("min_area")
                    )

            
            self.download_images_for_property(prop, data.get("property_images") or [])

            # ✅ Payment Plans - re-sync only if count changed
            incoming_plans = data.get("payment_plans") or []
            if prop.payment_plans.count() != len(incoming_plans):
                prop.payment_plans.all().delete()
                for plan in incoming_plans:
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