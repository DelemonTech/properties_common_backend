import os
import django
import requests
import urllib3
from django.core.files.base import ContentFile

# 1. Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import Property, PropertyImage

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# CONFIGURATION
API_URL = "https://panel.estaty.app/api/v1/filter"
APP_KEY = "6614693c2bcd2c0ada15fe1414255c4d"

def sync_data():
    session = requests.Session()
    session.headers.update({
        "App-key": APP_KEY,
        "Content-Type": "application/json",
        "User-Agent": "PostmanRuntime/7.36.0"
    })

    try:
        print("Fetching data from Estaty API...")
        response = session.post(API_URL, json={}, timeout=(15, 120), verify=False)
        response.raise_for_status()

        properties_data = response.json().get("properties", [])
        print(f"Found {len(properties_data)} properties. Starting Sync...")

        for data in properties_data:
            # A. Create or Update the main Property
            prop_instance, created = Property.objects.get_or_create(
                id=data['id'],
                defaults={'title': data.get('title', 'No Title')}
            )

            print(f"Processing ID {prop_instance.id}: {prop_instance.title}")

            # --- NEW CHANGE: DELETE EXISTING IMAGES ---
            # This deletes the PropertyImage records and removes files from S3
            print(f"  - Clearing existing gallery images for ID {prop_instance.id}...")
            prop_instance.property_images.all().delete() 

            # B. Prepare image list
            images_to_download = []

            # Update Property Cover directly
            if data.get('cover'):
                cover_url = data['cover']
                file_name = cover_url.split("/")[-1]
                try:
                    cover_res = session.get(cover_url, timeout=(10, 60), verify=False)
                    if cover_res.status_code == 200:
                        # This replaces the old file on S3 with the new one
                        prop_instance.cover.save(file_name, ContentFile(cover_res.content), save=True)
                        print(f"  - Updated Cover on S3: {file_name}")
                except Exception as e:
                    print(f"  - Failed to update cover: {e}")

            # Prepare Gallery images
            gallery = data.get('property_images', [])
            for g_item in gallery:
                if g_item.get('image'):
                    images_to_download.append({'url': g_item['image'], 'type': g_item.get('type', 1)})

            # C. Download and Save New Gallery Images
            for img_info in images_to_download:
                url = img_info['url']
                file_name = url.split("/")[-1]

                try:
                    img_res = session.get(url, timeout=(10, 60), verify=False)
                    if img_res.status_code == 200:
                        new_img_obj = PropertyImage(
                            property=prop_instance,
                            type=img_info['type']
                        )
                        file_content = ContentFile(img_res.content)
                        # Triggers a fresh upload to S3
                        new_img_obj.image.save(file_name, file_content, save=True)
                        print(f"    - Saved New Image to S3: {file_name}")
                except Exception as e:
                    print(f"    - Failed to download {file_name}: {e}")
                    
    except Exception as e:
        print(f"FATAL ERROR: {e}")

if __name__ == "__main__":
    sync_data()
