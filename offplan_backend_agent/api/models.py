from django.db import models


class City(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class District(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    city = models.ForeignKey(City, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class DeveloperCompany(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class PropertyType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class PropertyStatus(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class SalesStatus(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Facility(models.Model):
    name = models.CharField(max_length=100)

class Property(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    cover = models.URLField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    address_text = models.CharField(max_length=255, blank=True, null=True)
    delivery_date = models.CharField(max_length=50, blank=True, null=True)

    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)
    developer = models.ForeignKey(DeveloperCompany, on_delete=models.SET_NULL, null=True)
    property_type = models.ForeignKey(PropertyType, on_delete=models.SET_NULL, null=True)
    property_status = models.ForeignKey(PropertyStatus, on_delete=models.SET_NULL, null=True)
    sales_status = models.ForeignKey(SalesStatus, on_delete=models.SET_NULL, null=True)

    completion_rate = models.IntegerField(default=0, blank=True, null=True)
    residential_units = models.IntegerField(default=0, blank=True, null=True)
    commercial_units = models.IntegerField(default=0, blank=True, null=True)
    payment_plan = models.IntegerField(default=0)
    post_delivery = models.BooleanField(default=False)
    payment_minimum_down_payment = models.IntegerField(default=0, blank=True, null=True)
    guarantee_rental_guarantee = models.BooleanField(default=False)
    guarantee_rental_guarantee_value = models.IntegerField(default=0, blank=True, null=True)
    downPayment = models.BigIntegerField(default=0, blank=True, null=True)
    low_price = models.BigIntegerField(blank=True, null=True)
    min_area = models.IntegerField(blank=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title




class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_images')
    image = models.URLField()
    type = models.IntegerField()  # 1 = floorplan, 2 = gallery, etc.



class PropertyFacility(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_facilities')
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)

class PaymentPlan(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='payment_plans')
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

class PaymentPlanValue(models.Model):
    property_payment_plan = models.ForeignKey(PaymentPlan, on_delete=models.CASCADE, related_name='values')
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=20)

class GroupedApartment(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="grouped_apartments")
    unit_type = models.CharField(max_length=100)
    rooms = models.CharField(max_length=100)
    min_price = models.FloatField(null=True, blank=True)
    min_area = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.unit_type} - {self.rooms}"

class AgentDetails(models.Model):
    id = models.BigAutoField(primary_key=True)
    username = models.TextField(unique=True)
    name = models.TextField()
    email = models.TextField(null=True, blank=True)
    whatsapp_number = models.TextField(null=True, blank=True)
    phone_number = models.TextField(null=True, blank=True)
    profile_image_url = models.TextField(null=True, blank=True)
    introduction_video_url = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    years_of_experience = models.TextField(null=True, blank=True)
    total_business_deals = models.TextField(null=True, blank=True)
    rank_top_performing = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    fa_name = models.TextField(null=True, blank=True)
    fa_description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'agent_details'
        unique_together = ('id', 'username')  # Matches composite PK in Supabase
        managed = False 

    def __str__(self):
        return self.username
