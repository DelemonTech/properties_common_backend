from django.db import models

class City(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class District(models.Model):
    name = models.CharField(max_length=100)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='districts')

    def __str__(self):
        return self.name


class DeveloperCompany(models.Model):
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

    def __str__(self):
        return self.name


class Property(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    cover = models.URLField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    address_text = models.CharField(max_length=255, blank=True, null=True)
    delivery_date = models.BigIntegerField(blank=True, null=True)  # UNIX timestamp

    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, related_name='properties')
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, related_name='properties')
    developer = models.ForeignKey(DeveloperCompany, on_delete=models.SET_NULL, null=True, related_name='properties')
    property_type = models.ForeignKey(PropertyType, on_delete=models.SET_NULL, null=True, related_name='properties')
    property_status = models.ForeignKey(PropertyStatus, on_delete=models.SET_NULL, null=True, related_name='properties')
    sales_status = models.ForeignKey(SalesStatus, on_delete=models.SET_NULL, null=True, related_name='properties')

    completion_rate = models.IntegerField(default=0, blank=True, null=True)
    residential_units = models.IntegerField(default=0, blank=True, null=True)
    commercial_units = models.IntegerField(default=0, blank=True, null=True)
    payment_plan = models.IntegerField(default=0, null=True, blank=True)
    post_delivery = models.BooleanField(default=False)
    payment_minimum_down_payment = models.IntegerField(default=0, blank=True, null=True)
    guarantee_rental_guarantee = models.BooleanField(default=False)
    guarantee_rental_guarantee_value = models.IntegerField(default=0, blank=True, null=True)
    downPayment = models.BigIntegerField(default=0, blank=True, null=True)
    low_price = models.BigIntegerField(blank=True, null=True)
    min_area = models.IntegerField(blank=True, null=True)

    updated_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-updated_at']


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_images')
    image = models.URLField()
    type = models.IntegerField()  # 1 = floorplan, 2 = gallery, etc.

    def __str__(self):
        return f"Image for {self.property.title}"


class PropertyFacility(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_facilities')
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.property.title} - {self.facility.name}"


class PaymentPlan(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='payment_plans')
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} for {self.property.title}"


class PaymentPlanValue(models.Model):
    property_payment_plan = models.ForeignKey(PaymentPlan, on_delete=models.CASCADE, related_name='values')
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.name}: {self.value}"


class GroupedApartment(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="grouped_apartments")
    unit_type = models.CharField(max_length=100)
    rooms = models.CharField(max_length=100)
    min_price = models.FloatField(null=True, blank=True)
    min_area = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.unit_type} - {self.rooms}"

class AgentDetails(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

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

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        null=True,
        blank=True,
        help_text="Allowed values: male, female, other"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    fa_name = models.TextField(null=True, blank=True)
    fa_description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'agent_details'
        unique_together = ('id', 'username')
        managed = True  # Ensure True only if Django manages the table

    def __str__(self):
        return self.username


class Consultation(models.Model):
    full_name=models.CharField(max_length=20)
    email=models.CharField(max_length=20)
    phone_number=models.CharField(max_length=12)
    message=models.TextField(null=True)    
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    
    def __str__(self):
        return self.full_name
        
class Subscription(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email