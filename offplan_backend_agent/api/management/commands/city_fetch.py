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

       