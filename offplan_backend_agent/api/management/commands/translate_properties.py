import re
import time
from itertools import chain
from django.core.management.base import BaseCommand
from deep_translator import GoogleTranslator
from api.models import *


def clean_text(text):
    # Remove everything except letters, numbers, and spaces
    return re.sub(r'[^\w\s]', '', text).strip()


class Command(BaseCommand):
    help = 'Translate Property, City, and District titles/descriptions to Arabic and Farsi'

    def handle(self, *args, **kwargs):
        ar_translator = GoogleTranslator(source='auto', target='ar')
        fa_translator = GoogleTranslator(source='auto', target='fa')
        
        off_status = PropertyStatus.objects.get(name__iexact='Off Plan')
        ready_status = PropertyStatus.objects.get(name__iexact='Ready')

        # Translate Properties
        properties = Property.objects.all()[:50]
        offplan = Property.objects.filter(property_status=off_status).order_by('-updated_at')[:50]
        ready = Property.objects.filter(property_status=ready_status).order_by('-updated_at')[:50]
        combined = list(chain(offplan, ready, properties))
        print(combined,'combined')
        for prop in combined:
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
        
        
        # group apartments
        for grouped in GroupedApartment.objects.all():
            try:
                updated = False

                if grouped.ar_unit_type and grouped.unit_type:
                    cleaned_name = clean_text(grouped.unit_type)
                    grouped.ar_unit_type = ar_translator.translate(cleaned_name)
                    updated = True
                    time.sleep(1.2)

                if grouped.fa_unit_type and grouped.unit_type:
                    cleaned_name = clean_text(grouped.unit_type)
                    grouped.fa_unit_type = fa_translator.translate(cleaned_name)
                    updated = True
                    time.sleep(1.2)
                
                if grouped.ar_rooms and grouped.rooms:
                    cleaned_name = clean_text(grouped.rooms)
                    grouped.ar_rooms = ar_translator.translate(cleaned_name)
                    updated = True
                    time.sleep(1.2)

                if grouped.fa_rooms and grouped.rooms:
                    cleaned_name = clean_text(grouped.rooms)
                    grouped.fa_rooms = fa_translator.translate(cleaned_name)
                    updated = True
                    time.sleep(1.2)


                if updated:
                    grouped.save()
                    self.stdout.write(self.style.SUCCESS(f"✅ Translated grouped apartment: {grouped.unit_type}"))
                else:
                    self.stdout.write(f" Skipped grouped apartment: {grouped.unit_type} - Already translated")

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ Error on grouped apartment '{grouped.unit_type}': {e}"))
        
        # facilities
        for facility in Facility.objects.all():
            try:
                updated = False

                if facility.ar_facility and facility.name:
                    cleaned_name = clean_text(facility.name)
                    facility.ar_facility = ar_translator.translate(cleaned_name)
                    updated = True
                    time.sleep(1.2)

                if facility.fa_facility and facility.name:
                    cleaned_name = clean_text(facility.name)
                    facility.fa_facility = fa_translator.translate(cleaned_name)
                    updated = True
                    time.sleep(1.2)

                if updated:
                    facility.save()
                    self.stdout.write(self.style.SUCCESS(f"✅ Translated facility: {facility.name}"))
                else:
                    self.stdout.write(f" Skipped facility: {facility.name} - Already translated")

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ Error on facility '{facility.name}': {e}"))
            
        # payment plan
        for payment in PaymentPlan.objects.all():
            try:
                updated = False

                if payment.ar_plan_name and payment.name:
                    cleaned_name = clean_text(payment.name)
                    payment.ar_plan_name = ar_translator.translate(cleaned_name)
                    updated = True
                    time.sleep(1.2)

                if payment.fa_plan_name and payment.name:
                    cleaned_name = clean_text(payment.name)
                    payment.fa_plan_name = fa_translator.translate(cleaned_name)
                    updated = True
                    time.sleep(1.2)
                
                if payment.ar_plan_desc and payment.description:
                    cleaned_name = clean_text(payment.description)
                    payment.ar_plan_desc = ar_translator.translate(cleaned_name)
                    updated = True
                    time.sleep(1.2)

                if payment.fa_plan_desc and payment.description:
                    cleaned_name = clean_text(payment.description)
                    payment.fa_plan_desc = fa_translator.translate(cleaned_name)
                    updated = True
                    time.sleep(1.2)


                if updated:
                    payment.save()
                    self.stdout.write(self.style.SUCCESS(f"✅ Translated payment plan: {payment.name}"))
                else:
                    self.stdout.write(f" Skipped payment plan: {payment.name} - Already translated")

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ Error on payment plan '{payment.name}': {e}"))
        
        # PaymentplanValue
        for value in PaymentPlanValue.objects.all():
            try:
                updated = False

                if value.ar_value_name and value.name:
                    cleaned_name = clean_text(value.name)
                    value.ar_value_name = ar_translator.translate(cleaned_name)
                    updated = True
                    time.sleep(1.2)

                if value.fa_value_name and value.name:
                    cleaned_name = clean_text(value.name)
                    value.fa_value_name = fa_translator.translate(cleaned_name)
                    updated = True
                    time.sleep(1.2)
                
                if updated:
                    value.save()
                    self.stdout.write(self.style.SUCCESS(f"✅ Translated payment plan value: {value.name}"))
                else:
                    self.stdout.write(f" Skipped payment plan value: {value.name} - Already translated")

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ Error on payment plan value '{value.name}': {e}"))
        
        # sales status

        for sales in SalesStatus.objects.all():
            try:
                updated = False

                if sales.ar_sales_status and sales.name:
                    cleaned_name = clean_text(sales.name)
                    sales.ar_sales_status = ar_translator.translate(cleaned_name)
                    updated = True
                    time.sleep(1.2)

                if sales.fa_sales_status and sales.name:
                    cleaned_name = clean_text(sales.name)
                    sales.fa_sales_status = fa_translator.translate(cleaned_name)
                    updated = True
                    time.sleep(1.2)
                
                if updated:
                    sales.save()
                    self.stdout.write(self.style.SUCCESS(f"✅ Translated sales status: {sales.name}"))
                else:
                    self.stdout.write(f" Skipped sales status: {sales.name} - Already translated")

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ Error on sales status '{sales.name}': {e}"))
            
            
            

        self.stdout.write(self.style.SUCCESS("🎉 All translations completed successfully."))
