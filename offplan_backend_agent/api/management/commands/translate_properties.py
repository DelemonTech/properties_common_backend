import time
from django.core.management.base import BaseCommand
from deep_translator import GoogleTranslator
from api.models import Property, City, District


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

                if not prop.arabic_title and prop.title:
                    prop.arabic_title = ar_translator.translate(prop.title)
                    updated = True
                    time.sleep(1.2)

                if not prop.farsi_title and prop.title:
                    prop.farsi_title = fa_translator.translate(prop.title)
                    updated = True
                    time.sleep(1.2)

                if not prop.arabic_desc and prop.description:
                    prop.arabic_desc = ar_translator.translate(prop.description)
                    updated = True
                    time.sleep(1.2)

                if not prop.farsi_desc and prop.description:
                    prop.farsi_desc = fa_translator.translate(prop.description)
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

                if not city.arabic_city_name and city.name:
                    city.arabic_city_name = ar_translator.translate(city.name)
                    updated = True
                    time.sleep(1.2)

                if not city.farsi_city_name and city.name:
                    city.farsi_city_name = fa_translator.translate(city.name)
                    updated = True
                    time.sleep(1.2)

                if updated:
                    city.save()
                    self.stdout.write(self.style.SUCCESS(f"✅ Translated City: {city.name}"))
                else:
                    self.stdout.write(f"⏭ Skipped City: {city.name} - Already translated")

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ Error on City '{city.name}': {e}"))

        # Translate Districts
        for district in District.objects.all():
            try:
                updated = False

                if not district.arabic_dist_name and district.name:
                    district.arabic_dist_name = ar_translator.translate(district.name)
                    updated = True
                    time.sleep(1.2)

                if not district.farsi_dist_name and district.name:
                    district.farsi_dist_name = fa_translator.translate(district.name)
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
