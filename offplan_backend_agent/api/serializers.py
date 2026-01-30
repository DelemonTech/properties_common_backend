from rest_framework import serializers
from .models import AgentDetails, BlogPost, Property, PropertyUnit
from api.models import Property, City, District, DeveloperCompany, Consultation, Subscription, Contact, ReserveNow, RequestCallBack, AgentDetailsAdmin
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
    name = serializers.SerializerMethodField()

    class Meta:
        model = District
        fields = ['id', 'name']  # 'name' now contains multilingual dict

    def get_name(self, obj):
        return {
            "en": obj.name or "",
            "ar": obj.arabic_dist_name or "",
            "fa": obj.farsi_dist_name or "",
        }

class CitySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = City
        fields = ['id', 'name', ]
    def get_name(self,obj):
        return{
            "en":obj.name or "",
            "ar":obj.arabic_city_name or "",
            "fa":obj.farsi_city_name or "",
        }
    
   

class CitySerializerWithDistricts(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    districts = DistrictSerializer(many=True, read_only=True)

    
    class Meta:
        model = City
        fields = ['id', 'name', 'districts']
        
    def get_name (self,obj):
        return{
            "en":obj.name,
            "ar":obj.arabic_city_name,
            "fa":obj.farsi_city_name,
        }
    
    
        model = City
        fields = ['id', 'name', 'arabic_city_name', 'farsi_city_name', 'districts']

class DeveloperCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeveloperCompany
        fields = ["id", "name"]

class PropertySerializer(serializers.ModelSerializer):
    city = CitySerializer()
    district = DistrictSerializer()
    # print(district)
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

    # def get_subunit_count(self, obj):
    #     request = self.context.get("request")
    #     lang = request.query_params.get("lang") if request else "en"
    #     total_subunits = getattr(obj, "subunit_count", None)
    #     if total_subunits is None:
    #         # fallback if not annotated
    #         total_subunits = obj.property_units.aggregate(
    #             total=Sum('unit_count')
    #         )['total'] or 0
    #     unit_labels = {
    #         "en": ("unit", "units"),
    #         "ar": ("وحدة", "وحدات"),
    #         "fa": ("واحد", "واحدها"),
    #     }

    #     singular, plural = unit_labels.get(lang, unit_labels["en"])

    #     if total_subunits <= 1:
    #         return f"1 {singular}"
    #     elif total_subunits > 9:
    #         return f"9+ {plural}"
    #     else:
    #         return f"{total_subunits} {plural}"

    #     # if total_subunits <= 1:
    #     #     return "1 unit"
    #     # elif total_subunits > 9:
    #     #     return "9+ units"
    #     # else:
    #     #     return f"{total_subunits} units"
    
class PropertyBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ["id", "title"]    

class AgentDetailSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    class Meta:
        model = AgentDetails
        fields = '__all__'
    def get_name(self,obj):
        return{
            "en":obj.name,
            "ar":obj.ar_name,
            "fa":obj.fa_name,
        }
    def get_description(self, obj):
        return {
            "en": obj.description,
            "ar": obj.ar_description,
            "fa": obj.fa_description,
        }

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

class BlogPostSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogPost
        fields = '__all__'
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

class AgentDetailsFrontendSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    nationality = serializers.CharField(default="")

    # Non-model fields need to be defined explicitly
    languages = serializers.ListField(child=serializers.CharField(), default=[])
    specialties = serializers.ListField(child=serializers.CharField(), default=[])
    totalSales = serializers.CharField(source='total_business_deals', default=0)
    responseTime = serializers.CharField(default="")
    badge = serializers.CharField(default="")
    color = serializers.CharField(source='color_gradient', default="")

    class Meta:
        model = AgentDetails
        fields = [
            'id',
            'name',
            'username',
            'avatar',
            'nationality',
            'languages',
            'rating',
            'specialties',
            'totalSales',
            'responseTime',
            'badge',
            'color'
        ]

    def get_avatar(self, obj):
        return f"{obj.profile_image_url}"

    def get_nationality(self, obj):
        # You'll need to decide how nationality_code is retrieved
        code = getattr(obj, 'nationality_code', None)
        return f"https://flagcdn.com/32x24/{code.lower()}.png" if code else None