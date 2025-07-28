from rest_framework import serializers
from .models import AgentDetails, Property
from api.models import Property, City, District, DeveloperCompany, Consultation, Subscription, Contact, ReserveNow, RequestCallBack
from django.db.models import Sum


# class CitySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = City
#         fields = ["id", "name", "farsi_city_name", "arabic_city_name"]

# class DistrictSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = District
#         fields = ["id", "name", "farsi_dist_name", "arabic_dist_name"]

# class CitySerializerWithDistricts(serializers.ModelSerializer):
#     districts = DistrictSerializer(many=True, read_only=True)

#     class Meta:
#         model = City
#         fields = ["id", "name", "farsi_city_name", "arabic_city_name", "districts"]
    # def get_districts(self,obj):
    #     return [district.name for district in obj.districts.all()] 


class DistrictSerializer(serializers.ModelSerializer):
    dist_names = serializers.SerializerMethodField()
    class Meta:
        model = District
        fields = ['id', 'name','dist_names']
    
    def get_dist_names(self, obj):
        return {
            "en": obj.name or "",
            "ar": obj.arabic_dist_name or "",
            "fa": obj.farsi_dist_name or "",
        }

class CitySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = City
        fields = ['id', 'name', ]
    
   

class CitySerializerWithDistricts(serializers.ModelSerializer):
    districts = DistrictSerializer(many=True, read_only=True)
    class Meta:
        model = City
        fields = ['id', 'name', 'districts',]
    
class DeveloperCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeveloperCompany
        fields = ["id", "name"]

class PropertySerializer(serializers.ModelSerializer):
    city = CitySerializer()
    district = DistrictSerializer()
    developer = DeveloperCompanySerializer()
    subunit_count = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id", "title", "cover", "address", "address_text",
            "delivery_date", "min_area", "low_price",
            "property_type", "property_status", "sales_status",
            "updated_at", "city", "district", "developer","subunit_count",
           
        ]
    def get_title(self, obj):
        return {
            "en": obj.title or "",
            "ar": obj.arabic_title or "",
            "fa": obj.farsi_title or "",
        }
    

    def get_subunit_count(self, obj):
        total_subunits = getattr(obj, "subunit_count", None)
        if total_subunits is None:
            # fallback if not annotated
            total_subunits = obj.property_units.aggregate(
                total=Sum('unit_count')
            )['total'] or 0

        if total_subunits <= 1:
            return "1 unit"
        elif total_subunits > 9:
            return "9+ units"
        else:
            return f"{total_subunits} units"
    
    

class AgentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentDetails
        fields = '__all__'

class ConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = '__all__'

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['email']

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model= Contact
        fields = '__all__'
        
class ReserveNowSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReserveNow
        fields = ['name','whatsapp_number','email']

class RequestCallSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestCallBack
        fields = '__all__'
