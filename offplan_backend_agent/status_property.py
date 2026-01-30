import os
import django
import requests

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from api.models import Property, PropertyStatus

# 🔑 Get API key from environment
API_KEY = os.getenv("ESTATY_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ Missing ESTATY_API_KEY in environment variables.")

SINGLE_PROPERTY_URL = "https://panel.estaty.app/api/v1/getProperty"
HEADERS = {
    "App-key": API_KEY,
    "Content-Type": "application/json",
}


def update_property_status():
    updated = 0
    skipped = 0

    properties = Property.objects.all()
    print(f"🔍 Found {properties.count()} properties in local DB.")

    for prop in properties:
        payload = {"id": prop.id}
        try:
            response = requests.post(SINGLE_PROPERTY_URL, json=payload, headers=HEADERS, timeout=10)

            if response.status_code == 200:
                external_data = response.json().get("property", {})
                external_status_id = external_data.get("property_status_id")

                if external_status_id:
                    # Fetch or create PropertyStatus in local DB
                    property_status, created = PropertyStatus.objects.get_or_create(
                        id=external_status_id,
                        defaults={"name": external_data.get("property_status", {}).get("name", f"Status {external_status_id}")}
                    )

                    if prop.property_status_id != external_status_id:
                        old_status = prop.property_status.name if prop.property_status else "None"
                        prop.property_status = property_status
                        prop.save(update_fields=["property_status"])
                        updated += 1
                        print(f"✅ Updated Property ID {prop.id}: {old_status} → {property_status.name}")
                    else:
                        skipped += 1
                        print(f"➡️ Skipped Property ID {prop.id}: status unchanged ({property_status.name})")
                else:
                    print(f"⚠️ No 'property_status_id' in external data for Property ID {prop.id}")

            else:
                print(f"❌ Failed to fetch Property ID {prop.id}: HTTP {response.status_code}")

        except requests.RequestException as e:
            print(f"❌ Request error for Property ID {prop.id}: {e}")

    print("\n📊 Summary:")
    print(f"✔️ Total Updated: {updated}")
    print(f"➡️ Total Skipped: {skipped}")
    print("🎉 Done.")


if __name__ == "__main__":
    update_property_status()
