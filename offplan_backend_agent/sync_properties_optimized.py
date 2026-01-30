import os
import django
import requests
import logging
from django.db import transaction
from datetime import datetime
from dateutil import parser as date_parser

# ✅ Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "backend.settings"))
django.setup()

from api.models import (
    Property, City, District, DeveloperCompany, PropertyType,
    PropertyStatus, SalesStatus, Facility, PropertyUnit,
    GroupedApartment, PropertyImage, PaymentPlan, PaymentPlanValue
)

# ✅ Logging setup
log = logging.getLogger("django")

# ✅ API Configuration
FILTERS_URL = "https://panel.estaty.app/api/v1/getFilters"
LISTING_URL = "https://panel.estaty.app/api/v1/getProperties"
SINGLE_PROPERTY_URL = "https://panel.estaty.app/api/v1/getProperty"
FILTER_PROPERTIES_URL = "https://panel.estaty.app/api/v1/filter"
API_KEY = os.getenv("ESTATY_API_KEY")

if not API_KEY:
    raise RuntimeError("❌ Missing ESTATY_API_KEY in Django settings.")

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
            defaults={"name": data.get("name", f"Unnamed {model.__name__}")},
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
                    "name": district.get("name", "Unnamed District"),
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


# ✅ Fetch all properties and apartments from /filter
def fetch_all_properties_and_apartments():
    try:
        log.info("🌐 Fetching all properties from /filter...")
        response = requests.post(FILTER_PROPERTIES_URL, headers=HEADERS, json={})
        response.raise_for_status()
        data = response.json()
        property_apartments_map = {}
        for prop in data.get("properties", []):
            prop_id = prop.get("id")
            apartments = prop.get("apartment", [])
            property_apartments_map[prop_id] = apartments
        log.info(f"✅ Cached apartments for {len(property_apartments_map)} properties")
        return property_apartments_map
    except requests.RequestException as e:
        log.error(f"❌ Failed to fetch properties from /filter: {e}")
        return {}


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
        data = response.json()
        log.info(f"🔎 Property {prop_id}")
        return data.get("property")
    except requests.RequestException as e:
        log.error(f"❌ Failed to fetch property ID {prop_id}: {e}")
        return None


# ✅ Delete properties not in external API
def delete_removed_properties(external_property_ids):
    """
    Delete local properties that no longer exist in the external API.
    """
    local_property_ids = set(Property.objects.values_list("id", flat=True))
    external_property_ids_set = set(external_property_ids)

    to_delete_ids = local_property_ids - external_property_ids_set
    if to_delete_ids:
        log.info(f"🗑 Deleting {len(to_delete_ids)} properties no longer present in API.")
        batch_size = 100
        to_delete_ids = list(to_delete_ids)
        for i in range(0, len(to_delete_ids), batch_size):
            batch = to_delete_ids[i:i + batch_size]
            Property.objects.filter(id__in=batch).delete()
        log.info("✅ Deleted all missing properties.")
    else:
        log.info("✅ No properties to delete. All local properties exist in API.")


# ✅ Sync grouped apartments
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


# ✅ Sync property units
def sync_property_units(prop, external_units):
    log.info(f"📦 Syncing {len(external_units)} units for Property ID {prop.id}")

    if not external_units:
        log.warning(f"⚠️ No property units found for property {prop.id}. Skipping units sync.")
        return

    existing_unit_ids = set(PropertyUnit.objects.filter(property=prop).values_list('id', flat=True))
    external_unit_ids = set()

    for unit_data in external_units:
        unit_id = unit_data.get("id")
        if not unit_id:
            log.warning(f"⚠️ Skipping unit with no ID for Property {prop.id}")
            continue

        external_unit_ids.add(unit_id)
        log.info(f"✅ Syncing Unit ID {unit_id}, Apt No: {unit_data.get('apt_no')}")

        PropertyUnit.objects.update_or_create(
            id=unit_id,
            defaults={
                "property": prop,
                "apartment_id": unit_data.get("apartment_id"),  # 🆕 Save apartment_id
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
                "unit_count": unit_data.get("unit_count") or 1,
                "is_demand": bool(unit_data.get("is_demand", False)),
            },
        )

    # Delete units not in external data
    units_to_delete = existing_unit_ids - external_unit_ids
    if units_to_delete:
        log.info(f"🗑 Deleting {len(units_to_delete)} units no longer present in API for Property {prop.id}")
        PropertyUnit.objects.filter(id__in=units_to_delete).delete()


# ✅ Sync payment plans
def sync_payment_plans(prop, external_payment_plans):
    prop.payment_plans.all().delete()
    for plan in external_payment_plans:
        payment_plan = PaymentPlan.objects.create(
            property=prop,
            name=plan.get("name", "Unnamed Plan"),
            description=plan.get("description") or "",
        )
        for value in plan.get("values", []):
            PaymentPlanValue.objects.create(
                property_payment_plan=payment_plan,
                name=value.get("name", ""),
                value=value.get("value", ""),
            )


# ✅ Sync facilities
def sync_facilities(prop, external_facilities):
    prop.facilities.clear()
    for fac_data in external_facilities:
        facility = upsert_related_model(Facility, fac_data.get("facility") or fac_data)
        if facility:
            prop.facilities.add(facility)


# ✅ Update internal property
def update_internal_property(internal, external, property_apartments_map):
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

    # ✅ Fetch units from map
    units = external.get("apartment", []) or property_apartments_map.get(internal.id, [])

    sync_property_units(internal, units)
    sync_property_images(internal, external.get("property_images", []))
    sync_payment_plans(internal, external.get("payment_plans", []))
    sync_facilities(internal, external.get("property_facilities", []))


# ✅ Main Command Class
# class Command(BaseCommand):
#     help = "Sync properties from external API"

def main():
    try:
        with transaction.atomic():  # 🛡 Wrap in transaction for safety
            sync_filters()
            property_apartments_map = fetch_all_properties_and_apartments()
            page = 1
            updated_count = 0
            created_count = 0
            unchanged_counter = 0

            all_external_property_ids = []

            while True:
                props = fetch_external_properties(page)
                if not props:
                    log.info("✅ No more data.")
                    break

                # Collect external property IDs for deletion check
                external_ids = [p.get("id") for p in props if p.get("id")]
                all_external_property_ids.extend(external_ids)

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

                        # ✅ Check if unchanged
                        external_updated_at = date_parser.parse(full_data.get("updated_at")) if full_data.get("updated_at") else None
                        if external_updated_at and internal.updated_at and external_updated_at <= internal.updated_at:
                            # ✅ Even if property unchanged, check units for updates
                            log.info(f"🔄 Property ID {prop_id} unchanged. Checking units for changes.")

                            units = full_data.get("apartment", []) or property_apartments_map.get(prop_id, [])
                            db_units = PropertyUnit.objects.filter(property=internal).values("id", "updated_at")

                            # 🆕 Compare unit counts first
                            if len(units) != db_units.count():
                                log.info(f"🆕 Unit count mismatch for property {prop_id}. Syncing units.")
                                sync_property_units(internal, units)
                            else:
                                # 🆕 Compare individual unit updated_at timestamps
                                unit_changed = False
                                db_units_map = {u["id"]: u["updated_at"] for u in db_units}
                                for unit in units:
                                    unit_id = unit.get("id")
                                    unit_updated_at = date_parser.parse(unit.get("updated_at")) if unit.get("updated_at") else None
                                    db_updated_at = db_units_map.get(unit_id)

                                    if unit_updated_at and (not db_updated_at or unit_updated_at > db_updated_at):
                                        unit_changed = True
                                        log.info(f"🆕 Unit ID {unit_id} updated. Sync required.")
                                        break

                                if unit_changed:
                                    sync_property_units(internal, units)
                                else:
                                    log.info(f"✅ No changes in units for property {prop_id}. Skipping unit sync.")

                            unchanged_counter += 1
                            if unchanged_counter >= 60:
                                log.info("🚦 60 consecutive unchanged properties found. Stopping sync.")
                                log.info(f"\n📊 Sync Summary → Updated: {updated_count}, Created: {created_count}")
                                return
                            continue

                        # ✅ Update property
                        update_internal_property(internal, full_data, property_apartments_map)
                        log.info(f"✅ Updated Property ID {prop_id}")
                        updated_count += 1
                        unchanged_counter = 0  # Reset

                    except Property.DoesNotExist:
                        # ✅ Create new property
                        new_property = Property(id=prop_id)
                        update_internal_property(new_property, full_data, property_apartments_map)
                        log.info(f"➕ Created Property ID {prop_id}")
                        created_count += 1
                        unchanged_counter = 0  # Reset
                page += 1

            # 🗑 Delete properties not in external API
            delete_removed_properties(all_external_property_ids)

            log.info(f"\n📊 Sync Summary → Updated: {updated_count}, Created: {created_count}")

    except Exception as e:
        log.error(f"❌ Fatal error during sync: {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error(f"❌ Fatal error during sync: {e}")