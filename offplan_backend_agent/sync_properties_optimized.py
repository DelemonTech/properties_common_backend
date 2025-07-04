import os
import django
import requests
import logging
from datetime import datetime
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
from api.models import (
    Property, City, District, DeveloperCompany, PropertyType,
    PropertyStatus, SalesStatus, Facility, PropertyUnit,
    GroupedApartment, PropertyImage, PaymentPlan, PaymentPlanValue
)

# ✅ API Configuration
FILTERS_URL = "https://panel.estaty.app/api/v1/getFilters"
LISTING_URL = "https://panel.estaty.app/api/v1/getProperties"
SINGLE_PROPERTY_URL = "https://panel.estaty.app/api/v1/getProperty"
API_KEY = os.getenv("ESTATY_API_KEY")

if not API_KEY:
    raise RuntimeError("❌ Missing ESTATY_API_KEY environment variable.")

HEADERS = {
    "App-key": API_KEY,
    "Content-Type": "application/json",
}

# ✅ Parse date safely to UNIX timestamp
def parse_unix_date(raw_date):
    if not raw_date or not isinstance(raw_date, str):
        return None
    try:
        if '/' in raw_date:
            dt = datetime.strptime(raw_date, "%m/%Y")
        else:
            dt = date_parser.parse(raw_date)
        return int(dt.timestamp())
    except Exception:
        return None

# ✅ Upsert helper for related models
def upsert_related_model(model, data):
    if not data:
        return None

    if isinstance(data, dict):
        obj, _ = model.objects.update_or_create(
            id=data["id"],
            defaults={"name": data.get("name", f"Unnamed {model.__name__}")}
        )
        return obj

    obj = model.objects.filter(id=data).first()
    if not obj:
        log.warning(f"⚠️ {model.__name__} ID={data} received without name. Skipping creation.")
    return obj

# ✅ Sync Filters API
def sync_filters():
    try:
        log.info("🌐 Fetching filter data...")
        response = requests.post(FILTERS_URL, headers=HEADERS, json={})
        response.raise_for_status()
        filters = response.json()

        for city in filters.get("cities", []):
            upsert_related_model(City, city)

        for district in filters.get("districts", []):
            city_obj = City.objects.filter(id=district.get("city_id")).first()
            if not city_obj and district.get("city"):
                city_obj = upsert_related_model(City, district["city"])
            District.objects.update_or_create(
                id=district["id"],
                defaults={
                    "name": district.get("name", f"Unnamed District"),
                    "city": city_obj,
                },
            )

        for dev in filters.get("developer_companies", []):
            upsert_related_model(DeveloperCompany, dev)
        
        for prop_type in filters.get("property_types", []):
            upsert_related_model(PropertyType, prop_type)

        for status in filters.get("property_statuses", []):
            upsert_related_model(PropertyStatus, status)

        for sales in filters.get("sales_statuses", []):
            upsert_related_model(SalesStatus, sales)

        for fac in filters.get("facilities", []):
            upsert_related_model(Facility, fac)

        log.info("✅ Filters synced successfully.")
    except requests.RequestException as e:
        log.error(f"❌ Failed to fetch filters: {e}")

# ✅ Fetch property list (IDs only)
def fetch_external_properties(page):
    try:
        url = f"{LISTING_URL}?page={page}" if page > 1 else LISTING_URL
        log.info(f"🌐 Fetching property IDs: {url}")
        response = requests.post(url, headers=HEADERS, json={})
        response.raise_for_status()
        data = response.json()
        return data.get("properties", {}).get("data", [])
    except requests.RequestException as e:
        log.error(f"❌ Failed to fetch page {page}: {e}")
        return []

# ✅ Fetch full property details by ID
def fetch_property_by_id(prop_id):
    try:
        log.info(f"📥 Fetching details for property ID {prop_id}")
        response = requests.post(SINGLE_PROPERTY_URL, headers=HEADERS, json={"id": prop_id})
        response.raise_for_status()
        return response.json().get("property")
    except requests.RequestException as e:
        log.error(f"❌ Failed to fetch property ID {prop_id}: {e}")
        return None

# ✅ Sync Grouped Apartments
def sync_grouped_apartments(prop, external_grouped_apartments):
    prop.grouped_apartments.all().delete()
    for apt_data in external_grouped_apartments:
        normalized = {k.lower(): v for k, v in apt_data.items()}
        GroupedApartment.objects.create(
            property=prop,
            unit_type=normalized.get("unit_type", "Unknown"),
            rooms=normalized.get("rooms", "Unknown"),
            min_price=normalized.get("min_price", 0.0),
            min_area=normalized.get("min_area", 0.0),
        )

# ✅ Sync property units
def sync_property_units(prop, external_units):
    PropertyUnit.objects.filter(property=prop).delete()
    for unit_data in external_units:
        PropertyUnit.objects.update_or_create(
            id=unit_data.get("id"),
            defaults={
                "property": prop,
                "apartment_type_id": unit_data.get("apartment_type_id"),
                "no_of_baths": unit_data.get("no_of_baths"),
                "status": unit_data.get("status"),
                "area": unit_data.get("area"),
                "area_type": unit_data.get("area_type"),
                "start_area": unit_data.get("start_area"),
                "end_area": unit_data.get("end_area"),
                "price": unit_data.get("price"),
                "price_type": unit_data.get("price_type"),
                "start_price": unit_data.get("start_price"),
                "end_price": unit_data.get("end_price"),
                "floor_no": unit_data.get("floor_no"),
                "apt_no": unit_data.get("apt_no"),
                "floor_plan_image": unit_data.get("floor_plan_image"),
                "unit_image": unit_data.get("unit_image"),
                "created_at": date_parser.parse(unit_data.get("created_at")) if unit_data.get("created_at") else None,
                "updated_at": date_parser.parse(unit_data.get("updated_at")) if unit_data.get("updated_at") else None,
                "unit_count": unit_data.get("unit_count", 1),
                "is_demand": unit_data.get("is_demand", False),
            },
        )

# ✅ Sync property images
def sync_property_images(prop, external_images):
    PropertyImage.objects.filter(property=prop).delete()
    for img_data in external_images:
        PropertyImage.objects.create(
            property=prop,
            image=img_data.get("image"),
            type=img_data.get("type"),
            created_at=date_parser.parse(img_data.get("created_at")) if img_data.get("created_at") else None,
            updated_at=date_parser.parse(img_data.get("updated_at")) if img_data.get("updated_at") else None,
        )

# ✅ Sync payment plans
def sync_payment_plans(prop, external_payment_plans):
    prop.payment_plans.all().delete()
    for plan in external_payment_plans:
        payment_plan = PaymentPlan.objects.create(
        property=prop,
        name=plan.get("name", "Unnamed Plan"),
        description=plan.get("description") or ""
    )
        for value in plan.get("values", []):
            PaymentPlanValue.objects.create(
                property_payment_plan=payment_plan,
                name=value.get("name", ""),
                value=value.get("value", "")
            )

# ✅ Sync facilities
def sync_facilities(prop, external_facilities):
    prop.facilities.clear()
    for fac_data in external_facilities:
        facility = upsert_related_model(Facility, fac_data.get("facility") or fac_data)
        if facility:
            prop.facilities.add(facility)

# ✅ Update internal property
def update_internal_property(internal, external):
    internal.title = external.get("title")
    internal.description = external.get("description")
    internal.cover = external.get("cover")
    internal.address = external.get("address")
    internal.address_text = external.get("address_text")
    internal.delivery_date = parse_unix_date(external.get("delivery_date"))
    internal.completion_rate = external.get("completion_rate")
    internal.residential_units = external.get("residential_units")
    internal.commercial_units = external.get("commercial_units")
    internal.payment_plan = external.get("payment_plan")
    internal.post_delivery = external.get("post_delivery") or False
    internal.payment_minimum_down_payment = external.get("payment_minimum_down_payment") or 0
    internal.guarantee_rental_guarantee = external.get("guarantee_rental_guarantee") or False
    internal.guarantee_rental_guarantee_value = external.get("guarantee_rental_guarantee_value") or 0
    internal.downPayment = external.get("downPayment") or 0
    internal.low_price = external.get("low_price") or 0
    internal.min_area = external.get("min_area") or 0

    # Related models
    internal.city = upsert_related_model(City, external.get("city"))
    district_obj = upsert_related_model(District, external.get("district"))
    if district_obj and not district_obj.city:
        district_obj.city = internal.city
        district_obj.save()
    internal.district = district_obj

    internal.developer = upsert_related_model(DeveloperCompany, external.get("developer_company"))
    internal.property_type = upsert_related_model(PropertyType, external.get("property_type"))
    internal.property_status = upsert_related_model(PropertyStatus, external.get("property_status"))
    internal.sales_status = upsert_related_model(SalesStatus, external.get("sales_status"))

    updated_at_str = external.get("updated_at")
    if updated_at_str:
        internal.updated_at = date_parser.parse(updated_at_str)

    internal.save()

    # Sync nested data
    sync_grouped_apartments(internal, external.get("grouped_apartments", []))
    sync_property_units(internal, external.get("property_units", []))
    sync_property_images(internal, external.get("property_images", []))
    sync_payment_plans(internal, external.get("payment_plans", []))
    sync_facilities(internal, external.get("property_facilities", []))

# ✅ Main execution
def main():
    sync_filters()
    page = 1
    updated_count = 0
    created_count = 0
    unchanged_counter = 0

    while True:
        props = fetch_external_properties(page)
        if not props:
            log.info("✅ No more data.")
            break

        for summary in props:
            prop_id = summary.get("id")
            if not prop_id:
                log.error(f"❌ Missing property 'id': {summary}")
                continue

            full_data = fetch_property_by_id(prop_id)
            if not full_data:
                continue

            try:
                internal = Property.objects.get(id=prop_id)

                # ✅ Check if the property is unchanged based on updated_at
                external_updated_at = date_parser.parse(full_data.get("updated_at")) if full_data.get("updated_at") else None
                if external_updated_at and internal.updated_at and external_updated_at <= internal.updated_at:
                    unchanged_counter += 1
                    log.info(f"🔄 Property ID {prop_id} unchanged ({unchanged_counter}/60).")

                    # ✅ Stop if 15 unchanged records are found
                    if unchanged_counter >= 60:
                        log.info("🚦 15 consecutive unchanged properties found. Stopping sync.")
                        log.info(f"\n📊 Sync Summary → Updated: {updated_count}, Created: {created_count}")
                        return

                    continue  # ✅ Skip update since unchanged

                # ✅ Update property if external data is newer
                update_internal_property(internal, full_data)
                log.info(f"✅ Updated Property ID {prop_id}")
                updated_count += 1
                unchanged_counter = 0  # ✅ Reset counter on update

            except Property.DoesNotExist:
                # ✅ Create new property
                new_property = Property(id=prop_id)
                update_internal_property(new_property, full_data)
                log.info(f"➕ Created Property ID {prop_id}")
                created_count += 1
                unchanged_counter = 0  # ✅ Reset counter on creation
        page += 1

    log.info(f"\n📊 Sync Summary → Updated: {updated_count}, Created: {created_count}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error(f"❌ Fatal error during sync: {e}")