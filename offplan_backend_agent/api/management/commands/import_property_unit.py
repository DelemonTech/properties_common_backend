import json
import logging
import requests
from dateutil import parser as date_parser
from django.core.management.base import BaseCommand
from api.models import Property, PropertyUnit
import os
from dotenv import load_dotenv

load_dotenv()

# Set up logging
log = logging.getLogger(__name__)

# API endpoints and headers
API_KEY = os.getenv("ESTATY_API_KEY")
GET_PROPERTIES_URL = "https://panel.estaty.app/api/v1/getProperties"
FILTER_URL = "https://panel.estaty.app/api/v1/filter"
HEADERS = {
    "App-key": API_KEY,
    "Content-Type": "application/json",
}


class Command(BaseCommand):
    help = "Import Property Units from Estaty API using /getProperties and /filter"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚀 Starting property unit import..."))
        all_properties = self.fetch_all_properties()
        page=1
        total_saved = 0

        for prop in all_properties:
            title = prop.get("title")
            if not title:
                continue

            self.stdout.write(f"🔍 Fetching details for '{title}'")

            property_data = self.fetch_property_details_by_title(title)
            if not property_data:
                self.stdout.write(self.style.WARNING(f"⚠️ No data found for '{title}'"))
                continue

            prop_id = property_data.get("id")
            try:
                property_instance = Property.objects.get(id=prop_id)
            except Property.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"⚠️ Property ID {prop_id} not found in DB."))
                continue

            apartment_list = property_data.get("apartment", [])
            if apartment_list:
                saved_count = self.save_apartments(property_instance, apartment_list)
                total_saved += saved_count
                self.stdout.write(self.style.SUCCESS(f"✅ Saved {saved_count} units for '{title}'"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ No apartments found for '{title}'"))
        page += 1
        self.stdout.write(self.style.SUCCESS(f"🏁 Done! Total PropertyUnits imported: {total_saved}"))

    def fetch_all_properties(self):
        all_properties = []
        url = GET_PROPERTIES_URL

        while url:
            try:
                response = requests.post(url, headers=HEADERS)
                response.raise_for_status()
                data = response.json()

                page_properties = data.get("properties", {}).get("data", [])
                all_properties.extend(page_properties)

                url = data.get("properties", {}).get("next_page_url")
                self.stdout.write(self.style.NOTICE(f"📄 Fetched {len(page_properties)} properties, next page: {url}"))

            except requests.RequestException as e:
                log.error(f"❌ Failed to fetch properties from {url}: {e}")
                break  # Stop fetching if a request fails

        return all_properties

    def fetch_property_details_by_title(self, title):
        try:
            response = requests.post(FILTER_URL, headers=HEADERS, json={"property_name": title})
            response.raise_for_status()
            data = response.json()
            return data.get("properties", [])[0] if data.get("properties") else None

        except requests.HTTPError as e:
            if response.status_code == 500:
                log.warning(f"⚠️ Skipping '{title}' due to 500 Internal Server Error.")
            else:
                log.error(f"❌ HTTPError for '{title}': {e}")
            return None

        except requests.RequestException as e:
            log.error(f"❌ RequestException for '{title}': {e}")
            return None

    def save_apartments(self, property_instance, apartment_list):
        saved = 0
        for unit_data in apartment_list:
            unit_id = unit_data.get("id")
            if not unit_id:
                continue

            # Safely parse and clean floor_plan_image JSON field
            floor_plan_raw = unit_data.get("floor_plan_image")
            floor_plan_image = ""
            if floor_plan_raw:
                try:
                    parsed_images = json.loads(floor_plan_raw)
                    if isinstance(parsed_images, list) and parsed_images:
                        # Clean and normalize the first image URL
                        floor_plan_image = parsed_images[0].replace("\\/", "/")
                except json.JSONDecodeError:
                    floor_plan_image = ""
                    log.warning(f"⚠️ Invalid JSON for unit {unit_id} floor_plan_image, using empty string.")

            try:
                unit, created = PropertyUnit.objects.update_or_create(
                    id=unit_id,
                    defaults={
                        "property": property_instance,
                        "apartment_id": unit_data.get("apartment_id"),
                        "apartment_type_id": unit_data.get("apartment_type_id"),
                        "status": unit_data.get("status") or "Unknown",
                        "area": unit_data.get("area") or 0,
                        "price": unit_data.get("price") or 0,
                        "apt_no": unit_data.get("apt_no"),
                        "floor_plan_image": floor_plan_image,
                        "unit_image": unit_data.get("unit_image"),
                        "created_at": date_parser.parse(unit_data["created_at"]),
                        "updated_at": date_parser.parse(unit_data["updated_at"]),
                    }
                )
                saved += 1
            except Exception as e:
                log.error(f"❌ Failed to save unit {unit_id}: {str(e)}")

        log.info(f"✅ Saved {saved} apartment units.")        
        return saved
