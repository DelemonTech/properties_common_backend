from rest_framework import serializers
from .models import Property, City, District, DeveloperCompany
from .models import Facility, PropertyImage, PropertyFacility, PaymentPlan, PaymentPlanValue  # adjust imports as per your structure

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

class PropertyFacilitySerializer(serializers.ModelSerializer):
    facility = FacilityNameSerializer()

    class Meta:
        model = PropertyFacility
        fields = ["property_id", "facility_id", "facility"]

class PaymentPlanValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentPlanValue
        fields = ["id", "property_payment_plan_id", "name", "value"]

class PaymentPlanSerializer(serializers.ModelSerializer):
    values = PaymentPlanValueSerializer(many=True)

    class Meta:
        model = PaymentPlan
        fields = ["id", "property_id", "name", "description", "values"]

class PropertyDetailSerializer(serializers.ModelSerializer):
    city = CitySerializer()
    district = DistrictSerializer()
    developer_company = DeveloperCompanySerializer(source='developer')
    property_images = PropertyImageSerializer(many=True)
    property_facilities = PropertyFacilitySerializer(many=True)
    payment_plans = PaymentPlanSerializer(many=True)
    grouped_apartments = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id", "title", "description", "cover", "address", "address_text",
            "delivery_date", "completion_rate", "residential_units", "commercial_units",
            "payment_plan", "post_delivery", "payment_minimum_down_payment",
            "guarantee_rental_guarantee", "guarantee_rental_guarantee_value",
            "updated_at", "downPayment", "low_price", "min_area",

            # FK IDs
            "city_id", "developer_company_id", "property_type_id", "district_id",
            "property_status_id", "sales_status_id",

            # Relations
            "city", "district", "developer_company",
            "property_type", "property_status", "sales_status",
            "property_images", "property_facilities", "payment_plans",

            "grouped_apartments"
        ]

    def get_grouped_apartments(self, obj):
        return [{
            "Unit_Type": "Office",
            "Rooms": "Office",
            "min_price": obj.low_price,
            "min_area": obj.min_area
        }]
