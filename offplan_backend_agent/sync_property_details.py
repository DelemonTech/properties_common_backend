import os
import django
import requests
from time import sleep
from django.utils.dateparse import parse_datetime

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from api.models import (
    Property, GroupedApartment, PropertyImage,
    PropertyFacility, Facility, PaymentPlan, PaymentPlanValue
)

API_KEY = os.getenv("ESTATY_API_KEY")  # Make sure this is set in your environment
HEADERS = {"App-key": API_KEY, "Content-Type": "application/json"}
DETAIL_API_URL = "https://panel.estaty.app/api/v1/getProperty?id="


def fetch_property_detail(prop_id):
    try:
        res = requests.post(f"{DETAIL_API_URL}{prop_id}", headers=HEADERS)
        res.raise_for_status()
        return res.json().get("property", {})
    except Exception as e:
        print(f"❌ Error fetching details for ID {prop_id}: {e}")
        return None


def sync_property_details(prop, data):
    # Update simple fields
    prop.description = data.get("description")
    prop.completion_rate = data.get("completion_rate") or 0
    prop.residential_units = data.get("residential_units") or 0
    prop.commercial_units = data.get("commercial_units") or 0
    prop.payment_plan = data.get("payment_plan") or 0
    prop.post_delivery = data.get("post_delivery", False)
    prop.payment_minimum_down_payment = data.get("payment_minimum_down_payment") or 0
    prop.guarantee_rental_guarantee = data.get("guarantee_rental_guarantee", False)
    prop.guarantee_rental_guarantee_value = data.get("guarantee_rental_guarantee_value") or 0
    prop.downPayment = data.get("downPayment") or 0

    prop.save()

    # Sync Grouped Apartments
    GroupedApartment.objects.filter(property=prop).delete()
    for ga in data.get("grouped_apartments", []):
        GroupedApartment.objects.create(
            property=prop,
            unit_type=ga.get("Unit_Type", ""),
            rooms=ga.get("Rooms", ""),
            min_price=ga.get("min_price"),
            min_area=ga.get("min_area")
        )

    # Sync Property Images
    PropertyImage.objects.filter(property=prop).delete()
    for img in data.get("property_images", []):
        PropertyImage.objects.create(
            property=prop,
            image=img["image"],
            type=img["type"]
        )

    # Sync Facilities
    PropertyFacility.objects.filter(property=prop).delete()
    for pf in data.get("property_facilities", []):
        facility_data = pf.get("facility")
        if not facility_data:
            continue
        facility, _ = Facility.objects.get_or_create(
            id=facility_data["id"],
            defaults={"name": facility_data["name"]}
        )
        PropertyFacility.objects.create(
            property=prop,
            facility=facility
        )

    # Sync Payment Plans
    PaymentPlan.objects.filter(property=prop).delete()
    for pp in data.get("payment_plans", []):
        payment_plan = PaymentPlan.objects.create(
            property=prop,
            name=pp.get("name", ""),
            description=pp.get("description", "")
        )

        for val in pp.get("values", []):
            PaymentPlanValue.objects.create(
                property_payment_plan=payment_plan,
                name=val.get("name", ""),
                value=val.get("value", "")
            )


def run_sync():
    properties = Property.objects.all()
    total = properties.count()

    for i, prop in enumerate(properties, start=1):
        print(f"➡️ [{i}/{total}] Syncing Property ID: {prop.id}")
        data = fetch_property_detail(prop.id)
        if data:
            try:
                sync_property_details(prop, data)
            except Exception as e:
                print(f"❌ Failed to sync ID {prop.id}: {e}")
        else:
            print(f"⚠️ Skipping ID {prop.id} due to fetch error.")
        sleep(0.3)  # slight delay to avoid overwhelming API

    print("✅ Property detail sync completed.")


if __name__ == "__main__":
    run_sync()
