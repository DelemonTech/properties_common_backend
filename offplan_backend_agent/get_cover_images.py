import os
import django
import requests
import urllib3
from django.core.files.base import ContentFile

# 1. Setup Django Environment
# Replace 'your_project_name' with the actual name of your project folder
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Import your models after django.setup()
# Replace 'your_app_name' with the name of your app
from api.models import Property

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# CONFIGURATION
API_URL = "https://panel.estaty.app/api/v1/filter"
APP_KEY = "6614693c2bcd2c0ada15fe1414255c4d"

def update_property_covers():
    session = requests.Session()
    session.headers.update({
        "App-key": APP_KEY,
        "Content-Type": "application/json",
        "User-Agent": "PostmanRuntime/7.36.0"
    })

    try:
        print("Connecting to API...")
        response = session.post(API_URL, json={}, timeout=(15, 120), verify=False)
        response.raise_for_status()
        
        properties_data = response.json().get("properties", [])
        print(f"Syncing {len(properties_data)} property covers to S3 and Database...")

        for data in properties_data:
            prop_id = data.get('id')
            external_url = data.get('cover')

            if not prop_id or not external_url:
                continue

            # Fetch existing property or create it
            prop_instance, created = Property.objects.get_or_create(
                id=prop_id,
                defaults={'title': data.get('title', 'Unknown Title')}
            )

            file_name = external_url.split("/")[-1]

            # CHECK: Only update if the current path isn't already the S3 version of this file
            if not prop_instance.cover or file_name not in str(prop_instance.cover):
                print(f"Updating ID {prop_id}: Downloading {file_name}...")
                
                try:
                    img_res = session.get(external_url, timeout=(10, 60), verify=False)
                    if img_res.status_code == 200:
                        # Wrap content for Django's ImageField
                        file_content = ContentFile(img_res.content)
                        
                        # .save() uploads to S3 and updates the DB path automatically
                        prop_instance.cover.save(file_name, file_content, save=True)
                        print(f"  [DB UPDATED] New S3 path saved for ID {prop_id}")
                    else:
                        print(f"  [ERROR] HTTP {img_res.status_code} for ID {prop_id}")
                except Exception as e:
                    print(f"  [FAILED] ID {prop_id}: {e}")
            else:
                print(f"Skipping ID {prop_id}: DB already points to S3 path.")

    except Exception as e:
        print(f"FATAL ERROR: {e}")

if __name__ == "__main__":
    update_property_covers()
