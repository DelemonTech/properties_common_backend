from rest_framework import serializers
from .models import Property, City, District, DeveloperCompany
from .models import Facility, PropertyImage, PropertyFacility, PaymentPlan, PaymentPlanValue, GroupedApartment, PropertyUnit
from . import models  # adjust imports as per your structure
from django.db.models import Sum

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
    class Meta:
        model = City
        fields = ["id", "name"]

class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ["id", "name"]

class DeveloperCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeveloperCompany
        fields = ["id", "name"]

class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ["image", "property_id", "type"]

class FacilityNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility  # define this model if not already
        fields = ["id", "name"]

# class PropertyFacilitySerializer(serializers.ModelSerializer):
#     facility = FacilityNameSerializer()

#     class Meta:
#         model = PropertyFacility
#         fields = ["property_id", "facility_id", "facility"]

class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = ['id', 'name']

class PaymentPlanValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentPlanValue
        fields = ["id", "property_payment_plan_id", "name", "value"]

class PaymentPlanSerializer(serializers.ModelSerializer):
    values = PaymentPlanValueSerializer(many=True)

    class Meta:
        model = PaymentPlan
        fields = ["id", "property_id", "name", "description", "values"]

class GroupedApartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupedApartment
        fields = ['id', 'unit_type', 'rooms', 'min_price', 'min_area','ar_unit_type','fa_unit_type',]


class PropertyDetailSerializer(serializers.ModelSerializer):
    city = CitySerializer()
    district = DistrictSerializer()
    developer = DeveloperCompanySerializer()
    property_images = PropertyImageSerializer(many=True)
    facilities = FacilityNameSerializer(many=True)
    grouped_apartments = GroupedApartmentSerializer(many=True)
    payment_plans = PaymentPlanSerializer(many=True)
    property_units = PropertyUnitSerializer(many=True, read_only=True)  # ✅ Add this

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
            'grouped_apartments', 'payment_plans', 'property_units',
            'arabic_title','arabic_desc','farsi_title','farsi_desc'# ✅ Include here
        ]


# class PropertyUnitSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PropertyUnit
#         fields = '__all__'

class PropertySerializer(serializers.ModelSerializer):
    property_units = PropertyUnitSerializer(many=True, read_only=True)
    grouped_apartments = GroupedApartmentSerializer(many=True, read_only=True)
    facilities = FacilitySerializer(many=True, read_only=True)
    payment_plans = PaymentPlanSerializer(many=True, read_only=True)

    # 👇 Add computed field
    subunit_count = serializers.SerializerMethodField()

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
            'arabic_title',
            'arabic_desc',
            'farsi_title',
            'farsi_desc',
            'subunit_count',  # ✅ add this in response
        ]

    def get_subunit_count(self, obj):
        # 👇 Here we fetch the raw annotated count
        total_subunits = getattr(obj, "subunit_count", None)
        if total_subunits is None:
            # fallback if not annotated
            total_subunits = PropertyUnit.objects.filter(
                property=obj
            ).aggregate(total=Sum('unit_count'))['total'] or 0

        # 👇 Now format as string
        if total_subunits <= 1:
            return "1 unit"
        elif total_subunits > 9:
            return "9+ units"
        else:
            return f"{total_subunits} units"