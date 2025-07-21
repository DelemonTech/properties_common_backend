from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware, is_naive
from api.models import Property
import requests
from dateutil import parser as date_parser
from django.core.management import call_command
import logging

API_KEY = "27b84afeeef929815ab080ae22b29383"
DETAIL_URL = "https://panel.estaty.app/api/v1/getProperty"
HEADERS = {
    "App-key": API_KEY,
    "Content-Type": "application/json",
}

log = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "⏱ Incremental Estaty check (every 10 minutes)"

    def handle(self, *args, **kwargs):
        print("🔍 Checking last 60 DB properties for changes...")
        recent_props = Property.objects.order_by("-updated_at")[:60]
        any_changed = False

        for prop in recent_props:
            try:
                res = requests.post(DETAIL_URL, headers=HEADERS, json={"id": prop.id})
                res.raise_for_status()
                api_data = res.json().get("property")
            except Exception as e:
                log.error(f"❌ API error for ID {prop.id}: {e}")
                continue

            if not api_data:
                print(f"❌ Property ID {prop.id} no longer in Estaty — deleting")
                prop.delete()
                any_changed = True
                continue

            if self.has_changed(prop, api_data):
                print(f"🔁 Property ID {prop.id} changed — will re-sync")
                any_changed = True
                break  # no need to continue; we’ll fetch from page 1

        if any_changed:
            print("🔁 Changes detected. Running full sync from page 1...")
            call_command("import_estaty_properties")  # Replace with your actual command name
        else:
            print("✅ No changes detected in last 60 properties.")

    def has_changed(self, db_obj, api_data):
        api_updated_raw = api_data.get("updated_at")
        if not api_updated_raw:
            return False
        try:
            api_updated = parse_datetime(api_updated_raw)
            if is_naive(api_updated):
                api_updated = make_aware(api_updated)
            return db_obj.updated_at < api_updated
        except Exception as e:
            return True
