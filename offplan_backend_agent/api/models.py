from django.db import models
from django.utils.text import slugify
from storages.backends.s3boto3 import S3Boto3Storage
from tinymce.models import HTMLField 
from django.contrib import admin
from django.utils.html import format_html
from django.contrib.postgres.fields import ArrayField

class City(models.Model):
    name = models.CharField(max_length=100)
    arabic_city_name = models.CharField(max_length=100,null=True)
    farsi_city_name = models.CharField(max_length=100,null=True)

    def __str__(self):
        return self.name


class District(models.Model):
    name = models.CharField(max_length=100)
    arabic_dist_name = models.CharField(max_length=100,null=True)
    farsi_dist_name = models.CharField(max_length=100,null=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='districts',null=True, blank=True)

    def __str__(self):
        return self.name


class DeveloperCompany(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    user_id = models.IntegerField(null=True, blank=True) # Or ForeignKey if linking to a User model
    
    # Media & Web
    logo = models.URLField(max_length=500, null=True, blank=True)
    website = models.URLField(max_length=500, null=True, blank=True)
    
    # Contact Details
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    
    # Content
    overview = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class PropertyType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class PropertyStatus(models.Model):
    name = models.CharField(max_length=100)
    ar_prop_status = models.CharField(max_length=255,null=True)
    fa_prop_status = models.CharField(max_length=255,null=True)

    def __str__(self):
        return self.name


class SalesStatus(models.Model):
    name = models.CharField(max_length=100)
    ar_sales_status = models.CharField(max_length=255,null=True)
    fa_sales_status = models.CharField(max_length=255,null=True)

    def __str__(self):
        return self.name


class Facility(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    ar_facility = models.CharField(max_length=255,null=True)
    fa_facility = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.name


class Property(models.Model):
    title = models.CharField(max_length=255)
    arabic_title = models.CharField(max_length=255,null=True,blank=True)
    farsi_title = models.CharField(max_length=255,null=True,blank=True)
    
    description = models.TextField(blank=True, null=True)
    farsi_desc = models.TextField(blank=True,null=True)
    arabic_desc = models.TextField(blank=True,null=True)
    
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

    facilities = models.ManyToManyField("Facility", related_name="properties", blank=True)
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

class PropertyUnit(models.Model):
    id = models.BigIntegerField(primary_key=True)
    property = models.ForeignKey("Property", on_delete=models.CASCADE, related_name="property_units")
    apartment_id = models.IntegerField(null=True, blank=True)
    apartment_type_id = models.IntegerField(null=True, blank=True)
    no_of_baths = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)
    area = models.FloatField(null=True, blank=True)
    area_type = models.IntegerField(null=True, blank=True)
    start_area = models.FloatField(null=True, blank=True)
    end_area = models.FloatField(null=True, blank=True)
    price = models.FloatField(null=True, blank=True)
    price_type = models.IntegerField(null=True, blank=True)
    start_price = models.FloatField(null=True, blank=True)
    end_price = models.FloatField(null=True, blank=True)
    floor_no = models.IntegerField(null=True, blank=True)
    apt_no = models.CharField(max_length=255, null=True, blank=True)
    floor_plan_image = models.JSONField(null=True, blank=True)
    unit_image = models.URLField(null=True, blank=True)
    unit_count = models.IntegerField(default=1)
    is_demand = models.BooleanField(default=False)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    def __str__(self):
        return f"{self.apt_no or 'Unit'} in Property {self.property_id}"

class PropertyImage(models.Model):
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_images')
    image = models.URLField()
    type = models.IntegerField()  # 1 = floorplan, 2 = gallery, etc.
    property_unit = models.ForeignKey(PropertyUnit, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Image for {self.property_id}"


class PropertyFacility(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_facilities')
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.property.title} - {self.facility.name}"


class PaymentPlan(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='payment_plans')
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    ar_plan_name = models.CharField(max_length=50,null=True)
    fa_plan_name = models.CharField(max_length=50,null=True)
    ar_plan_desc = models.CharField(max_length=100, null=True)
    fa_plan_desc = models.CharField(max_length=100, null=True)

    def __str__(self):
        return f"{self.name} for {self.property.title}"


class PaymentPlanValue(models.Model):
    property_payment_plan = models.ForeignKey(PaymentPlan, on_delete=models.CASCADE, related_name='values')
    name = models.CharField(max_length=255)  # Keep this large enough
    value = models.CharField(max_length=255)  # Increased from 20 to 255
    ar_value_name = models.CharField(max_length=255,null=True)
    fa_value_name = models.CharField(max_length=255,null=True)

    def __str__(self):
        return f"{self.name}: {self.value}"


class GroupedApartment(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="grouped_apartments")
    unit_type = models.CharField(max_length=100)
    rooms = models.CharField(max_length=100)
    min_price = models.FloatField(null=True, blank=True)
    min_area = models.FloatField(null=True, blank=True)
    ar_unit_type = models.CharField(max_length=50,null=True)
    fa_unit_type = models.CharField(max_length=50,null=True)
    ar_rooms = models.CharField(max_length=50, null=True)
    fa_rooms = models.CharField(max_length=50, null=True)

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
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    responseTime = models.TextField(null=True, blank=True)

    badge = models.CharField(max_length=50, null=True, blank=True)
    color_gradient = models.CharField(max_length=100, null=True, blank=True)


    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        null=True,
        blank=True,
        help_text="Allowed values: male, female, other"
    )

    nationality = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    # ✅ New field for specialties
    specialties = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="List of specialties, e.g., ['Luxury Villas', 'Off-Plan Sales']"
    )

    languages = ArrayField(
        models.CharField(max_length=5),
        default=list,
        blank=True,
        help_text="List of language codes, e.g., ['en', 'fa', 'ae']"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    fa_name = models.TextField(null=True, blank=True)
    fa_description = models.TextField(null=True, blank=True)
    ar_name = models.TextField(null=True, blank=True)
    ar_description = models.TextField(null=True, blank=True)

    specialties_fa = models.TextField(null=True, blank=True)
    specialties_ar = models.TextField(null=True, blank=True)
    badge_fa = models.TextField(null=True, blank=True)
    badge_ar = models.TextField(null=True, blank=True)

    calendly_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Calendly booking link for this agent"
    )

    class Meta:
        db_table = 'agent_details'
        unique_together = ('id', 'username')
        managed = True  # Ensure True only if Django manages the table
        verbose_name_plural = "Agent Details"

    def __str__(self):
        return self.username

class AgentDetailsAdmin(admin.ModelAdmin):
    list_display = ('username', 'name', 'email', 'phone_number', 'rating', 'badge', 'color_preview', 'created_at', 'calendly_url')
    list_filter = ('badge', 'nationality', 'created_at')
    search_fields = ('username', 'name', 'email', 'phone_number')
    ordering = ('-created_at',)

    fieldsets = (
        ('Basic Info', {
            'fields': ('username', 'name', 'gender', 'email', 'phone_number', 'whatsapp_number', 'nationality', 'calendly_url')
        }),
        ('Media', {
            'fields': ('profile_image_url', 'introduction_video_url')
        }),
        ('Professional Info', {
            'fields': ('description', 'specialties', 'languages', 'rating', 'total_sales', 'response_time', 'badge', 'color_gradient')
        }),
        ('Translations', {
            'fields': ('fa_name', 'fa_description', 'ar_name', 'ar_description', 'specialties_fa', 'specialties_ar', 'badge_fa', 'badge_ar'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at',)

    # Predefined dropdown choices
    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == 'badge':
            kwargs['choices'] = [
                ('Top Performer', 'Top Performer'),
                ('Rising Star', 'Rising Star'),
                ('Expert', 'Expert'),
            ]
        if db_field.name == 'color_gradient':
            kwargs['choices'] = [
                ('from-pink-400 via-purple-500 to-indigo-600', 'Pink → Purple → Indigo'),
                ('from-orange-400 via-red-500 to-pink-600', 'Orange → Red → Pink'),
                ('from-emerald-400 via-teal-500 to-cyan-600', 'Emerald → Teal → Cyan'),
            ]
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    # Color preview in list_display
    def color_preview(self, obj):
        return format_html(
            '<div style="background: linear-gradient(to right, var(--tw-gradient-stops)); background-image: {}; width: 100px; height: 20px; border-radius: 5px;"></div>',
            obj.color_gradient
        )
    color_preview.short_description = "Color"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        print(form.base_fields['badge'].choices)  # Debug
        return form



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

class Contact(models.Model):
    name = models.CharField(max_length=255,null=True,blank=True)
    phone_number = models.CharField(max_length=15,null=True)
    email = models.EmailField(max_length=30,null=True)
    message = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class ReserveNow(models.Model):
    name = models.CharField(max_length=255,null=True)
    whatsapp_number = models.CharField(max_length=20,null=True)
    email = models.EmailField(max_length=30,null=True)
    unit_id = models.ForeignKey(PropertyUnit,on_delete=models.CASCADE,related_name="units")

class RequestCallBack(models.Model):
    name = models.CharField(max_length=255, null=True)
    phone_number = models.CharField(max_length=20,null=True)
    email = models.EmailField(max_length=30, null=True)

def upload_to_blogs(instance, filename):
        return f"uploads/{filename}"

class BlogPost(models.Model):
    # ENGLISH - Use HTMLField for rich content
    title = models.CharField(max_length=255)
    excerpt = HTMLField(blank=True, null=True, help_text="Rich text excerpt")
    content = HTMLField(help_text="Rich text content with HTML formatting")  # Changed to HTMLField
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.CharField(max_length=255, blank=True, null=True)

    # ARABIC (auto generated) - Keep as TextField since these are auto-translated
    title_ar = models.CharField(max_length=255, blank=True, null=True)
    excerpt_ar = models.TextField(blank=True, null=True)
    content_ar = models.TextField(blank=True, null=True)
    meta_title_ar = models.CharField(max_length=255, blank=True, null=True)
    meta_description_ar = models.CharField(max_length=255, blank=True, null=True)

    # FARSI (auto generated) - Keep as TextField since these are auto-translated
    title_fa = models.CharField(max_length=255, blank=True, null=True)
    excerpt_fa = models.TextField(blank=True, null=True)
    content_fa = models.TextField(blank=True, null=True)
    meta_title_fa = models.CharField(max_length=255, blank=True, null=True)
    meta_description_fa = models.CharField(max_length=255, blank=True, null=True)

    image = models.ImageField(storage=S3Boto3Storage(), upload_to='', blank=True, null=True)
    author = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True, max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-generate slug from title if not provided
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            
            # Ensure uniqueness by appending numbers if needed
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"


    