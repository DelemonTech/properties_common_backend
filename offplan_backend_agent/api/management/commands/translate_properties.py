import re
import time
from django.core.management.base import BaseCommand
from deep_translator import GoogleTranslator
from api.models import Property, City, District


def clean_text(text):
    # Remove everything except letters, numbers, and spaces
    return re.sub(r'[^\w\s]', '', text).strip()


class Command(BaseCommand):
    help = 'Translate Property, City, and District titles/descriptions to Arabic and Farsi'

    def handle(self, *args, **kwargs):
        ar_translator = GoogleTranslator(source='auto', target='ar')
        fa_translator = GoogleTranslator(source='auto', target='fa')

        # Translate Properties
        properties = Property.objects.all()
        for prop in properties:
            try:
                updated = False

                if prop.arabic_title and prop.title:
                    cleaned_title = clean_text(prop.title)
                    prop.arabic_title = ar_translator.translate(cleaned_title)
                    updated = True
                    time.sleep(1.2)

                if prop.farsi_title and prop.title:
                    cleaned_title = clean_text(prop.title)
                    prop.farsi_title = fa_translator.translate(cleaned_title)
                    updated = True
                    time.sleep(1.2)

                if prop.arabic_desc and prop.description:
                    cleaned_desc = clean_text(prop.description)
                    prop.arabic_desc = ar_translator.translate(cleaned_desc)
                    updated = True
                    time.sleep(1.2)

                if prop.farsi_desc and prop.description:
                    cleaned_desc = clean_text(prop.description)
                    prop.farsi_desc = fa_translator.translate(cleaned_desc)
                    updated = True
                    time.sleep(1.2)

                if updated:
                    prop.save()
                    self.stdout.write(self.style.SUCCESS(f"✅ Translated Property: {prop.id} - {prop.title}"))
                else:
                    self.stdout.write(f"⏭ Skipped Property: {prop.id} - Already translated")

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ Error on Property ID {prop.id}: {e}"))

        # Translate Cities
        for city in City.objects.all():
            try:
                updated = False

                if city.arabic_city_name and city.name:
                    cleaned_name = clean_text(city.name)
                    city.arabic_city_name = ar_translator.translate(cleaned_name)
                    updated = True
                    time.sleep(1.2)

                if city.farsi_city_name and city.name:
                    cleaned_name = clean_text(city.name)
                    city.farsi_city_name = fa_translator.translate(cleaned_name)
                    updated = True
                    time.sleep(1.2)

                if updated:
                    city.save()
                    self.stdout.write(self.style.SUCCESS(f"✅ Translated City: {city.name}"))
                else:
                    self.stdout.write(f" Skipped City: {city.name} - Already translated")

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ Error on City '{city.name}': {e}"))

        # Translate Districts
        for district in District.objects.all():
            try:
                updated = False

                if district.arabic_dist_name and district.name:
                    cleaned_name = clean_text(district.name)
                    district.arabic_dist_name = ar_translator.translate(cleaned_name)
                    updated = True
                    time.sleep(1.2)

                if district.farsi_dist_name and district.name:
                    cleaned_name = clean_text(district.name)
                    district.farsi_dist_name = fa_translator.translate(cleaned_name)
                    updated = True
                    time.sleep(1.2)

                if updated:
                    district.save()
                    self.stdout.write(self.style.SUCCESS(f"✅ Translated District: {district.name}"))
                else:
                    self.stdout.write(f"⏭ Skipped District: {district.name} - Already translated")

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ Error on District '{district.name}': {e}"))

        self.stdout.write(self.style.SUCCESS("🎉 All translations completed successfully."))
