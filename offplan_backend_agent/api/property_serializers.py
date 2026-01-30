from rest_framework import serializers
from .models import Property, City, District, DeveloperCompany
from .models import Facility, PropertyImage, PropertyFacility, PaymentPlan, PaymentPlanValue, GroupedApartment, PropertyUnit,SalesStatus
from . import models  # adjust imports as per your structure
from django.db.models import Sum
from django.db.models import Sum
from django.utils.translation import gettext as _

class PropertyUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyUnit
        fields = [
            'id',
            'apartment_id',
            'apartment_type_id',
            'no_of_baths',
            'status',
            'area',
            'area_type',
            'start_area',
            'end_area',
            'price',
            'price_type',
            'start_price',
            'end_price',
            'floor_no',
            'apt_no',
            'floor_plan_image',
            'unit_image',
            'unit_count',
            'is_demand',
            'created_at',
            'updated_at',
        ]


# Define nested serializers if not already present
class CitySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    class Meta:
        model = City
        fields = ["id", "name"]
    def get_name(self,obj):
        return{
            "en":obj.name,
            "ar":obj.arabic_city_name,
            "fa":obj.farsi_city_name,
        }

class DistrictSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    class Meta:
        model = District
        fields = ["id", "name"]
    def get_name(self,obj):
        return{
            "en":obj.name,
            "ar":obj.arabic_dist_name,
            "fa":obj.farsi_dist_name,
        }

class DeveloperCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeveloperCompany
        fields = ["id", "name"]
        
class SalesStatusSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    class Meta:
        model = SalesStatus
        fields = ["id", "name"]
    def get_name(self,obj):
        return{
            "en":obj.name or "",
            "ar":obj.ar_sales_status or "",
            "fa":obj.fa_sales_status or ""
        }


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ["image", "property_id", "type"]

# class FacilityNameSerializer(serializers.ModelSerializer):
#     facilities = serializers.SerializerMethodField()
#     class Meta:
#         model = Facility  # define this model if not already
#         fields = ["id", "name","facilities"]
#     def get_facilities(self,obj):
#         return{
#             "en":obj.name,
#             "ar":obj.ar_facility,
#             "fa":obj.fa_facility,
#         }

# # class PropertyFacilitySerializer(serializers.ModelSerializer):
# #     facility = FacilityNameSerializer()

# #     class Meta:
# #         model = PropertyFacility
# #         fields = ["property_id", "facility_id", "facility"]

# class FacilitySerializer(serializers.ModelSerializer):
#     facilities=FacilityNameSerializer(many=True)
#     class Meta:
#         model = PropertyFacility
#         fields = ["property_id", "facility_id", "facility","facilities"]
class FacilityNameSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Facility
        fields = ["id", "name"]

    def get_name(self, obj):
        return {
            "en": obj.name,
            "ar": obj.ar_facility or obj.name,
            "fa": obj.fa_facility or obj.name,
        }


class PropertyFacilitySerializer(serializers.ModelSerializer):
    facility = FacilityNameSerializer(read_only=True)

    class Meta:
        model = PropertyFacility
        fields = ["property_id", "facility_id", "facility"]

class PaymentPlanValueSerializer(serializers.ModelSerializer):
    values = serializers.SerializerMethodField()
    class Meta:
        model = PaymentPlanValue
        fields = ["id", "property_payment_plan_id", "name", "value","values"]
        
    def get_values(self,obj):
        return{
            "en":obj.name,
            "ar":obj.ar_value_name,
            "fa":obj.fa_value_name,
        }

class PaymentPlanSerializer(serializers.ModelSerializer):
    values = PaymentPlanValueSerializer(many=True)
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = PaymentPlan
        fields = ["id", "property_id", "name", "description", "values"]
    def get_name(self,obj):
        return{
            "en":obj.name,
            "ar":obj.ar_plan_name,
            "fa":obj.fa_plan_name,
        }
    def get_description(self,obj):
        return{
            "en":obj.description,
            "ar":obj.ar_plan_desc,
            "fa":obj.fa_plan_desc,
        }
class GroupedApartmentSerializer(serializers.ModelSerializer):
    rooms = serializers.SerializerMethodField()
    unit_type = serializers.SerializerMethodField()
    class Meta:
        model = GroupedApartment
        fields = ['id', 'unit_type', 'rooms', 'min_price', 'min_area']
    def get_rooms(self,obj):
        return{
            "en":obj.rooms,
            "ar":obj.ar_rooms,
            "fa":obj.fa_rooms,
        }
    def get_unit_type(self,obj):
        return{
            "en":obj.unit_type,
            "ar":obj.ar_unit_type,
            "fa":obj.fa_unit_type,
        }


class PropertyDetailSerializer(serializers.ModelSerializer):
    city = CitySerializer()
    district = DistrictSerializer()
    developer = DeveloperCompanySerializer()
    property_images = PropertyImageSerializer(many=True)
    facilities = FacilityNameSerializer(many=True)
    grouped_apartments = GroupedApartmentSerializer(many=True)
    payment_plans = PaymentPlanSerializer(many=True)
    property_units = PropertyUnitSerializer(many=True, read_only=True)  # ✅ Add this
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    sales_status = SalesStatusSerializer()


    class Meta:
        model = Property
        fields = [
            'id', 'title', 'description', 'cover', 'address', 'address_text',
            'delivery_date', 'low_price', 'min_area', 'downPayment',
            'completion_rate', 'residential_units', 'commercial_units',
            'payment_plan', 'payment_minimum_down_payment', 'post_delivery',
            'guarantee_rental_guarantee', 'guarantee_rental_guarantee_value',
            'city', 'district', 'developer', 'property_type', 'property_status',
            'sales_status', 'property_images', 'facilities',
            'grouped_apartments', 'payment_plans', 'property_units']
    
    def get_title(self, obj):
        return {
            "en": obj.title or "",
            "ar": obj.arabic_title or "",
            "fa": obj.farsi_title or "",
        }
    
    def get_description(self, obj):
        return {
            "en": obj.description or "",
            "ar": obj.arabic_desc or "",
            "fa": obj.farsi_desc or "",
        }



# class PropertyUnitSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PropertyUnit
#         fields = '__all__'

class PropertySerializer(serializers.ModelSerializer):
    city = CitySerializer()
    district = DistrictSerializer()
    property_units = PropertyUnitSerializer(many=True, read_only=True)
    grouped_apartments = GroupedApartmentSerializer(many=True, read_only=True)
    facilities = FacilityNameSerializer(many=True, read_only=True)
    payment_plans = PaymentPlanSerializer(many=True, read_only=True)
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    # 👇 Add computed field
    subunit_count = serializers.SerializerMethodField()
    sales_status = SalesStatusSerializer()

    class Meta:
        model = Property
        fields = [
            'id',
            'title',
            'cover',
            'address',
            'address_text',
            'delivery_date',
            'min_area',
            'low_price',
            'property_type',
            'property_status',
            'sales_status',
            'updated_at',
            'city',
            'district',
            'developer',
            'subunit_count',  
            'property_units',
            'grouped_apartments',
            'facilities',
            'payment_plans',
            
        ]
    
    def get_title(self, obj):
        return {
            "en": obj.title or "",
            "ar": obj.arabic_title or "",
            "fa": obj.farsi_title or "",
        }
    
    def get_description(self, obj):
        return {
            "en": obj.description or "",
            "ar": obj.arabic_desc or "",
            "fa": obj.farsi_desc or "",
        }

    def get_subunit_count(self, obj):
        # Fetch the annotated count
        total_subunits = getattr(obj, "subunit_count", None)
        if total_subunits is None:
            total_subunits = PropertyUnit.objects.filter(
                property=obj
            ).aggregate(total=Sum('unit_count'))['total'] or 0

        # Format count and translated label
        if total_subunits <= 1:
            value = 1
            label_en = "unit"
            label_ar = "وحدة"
            label_fa = "واحد"
        elif total_subunits > 9:
            value = "9+"
            label_en = "units"
            label_ar = "وحدات"
            label_fa = "واحدها"
        else:
            value = total_subunits
            label_en = "units"
            label_ar = "وحدات"
            label_fa = "واحدها"

        return {
            "value": value,
            "label": {
                "en": label_en,
                "ar": label_ar,
                "fa": label_fa,
            },
        }