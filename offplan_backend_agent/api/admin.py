# Updated admin.py
from django.contrib import admin
from django import forms
from .models import AgentDetails, BlogPost
from django.utils.html import format_html, strip_tags
from .models import Contact, BlogPost, AgentDetails
from django.utils.safestring import mark_safe

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at', 'slug', 'content_preview', 'image_tag']
    list_filter = ['author', 'created_at']
    search_fields = ['title', 'excerpt', 'author']
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ['created_at']

    def content_preview(self, obj):
        """Show a preview of the rich content"""
        # Strip HTML tags for preview in admin list
        plain_text = strip_tags(obj.content)
        return plain_text[:100] + "..." if len(plain_text) > 100 else plain_text
    content_preview.short_description = "Content Preview"

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="80" />', obj.image.url)
        return "-"
    image_tag.short_description = 'Image'

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'image'),
            'classes': ('wide',)
        }),
        ('Content', {
            'fields': ('excerpt', 'content'),
            'classes': ('wide',),
            'description': 'Rich text fields with formatting support'
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Arabic Translation', {
            'fields': ('title_ar', 'excerpt_ar', 'content_ar', 'meta_title_ar', 'meta_description_ar'),
            'classes': ('collapse',),
            'description': 'Auto-generated Arabic translations'
        }),
        ('Farsi Translation', {
            'fields': ('title_fa', 'excerpt_fa', 'content_fa', 'meta_title_fa', 'meta_description_fa'),
            'classes': ('collapse',),
            'description': 'Auto-generated Farsi translations'
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    class Media:
        css = {
            'all': ('admin/css/blog-admin.css',)
        }

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    # Django admin automatically queries the database using Django ORM
    # No API calls needed - direct database access
    list_display = ['name', 'email', 'phone_number', 'created_at']
    # This uses: Contact.objects.all() internally

# --------- Agent Details Admin ----------
class AgentDetailsForm(forms.ModelForm):
    SPECIALTIES_CHOICES = [
        ('Luxury Properties', 'Luxury Properties'),
        ('Off-plan Projects', 'Off-plan Projects'),
        ('Investment Advisory', 'Investment Advisory'),
        ('Rental Management', 'Rental Management'),
    ]
    COUNTRY_CHOICES = [
        ('AE', 'United Arab Emirates'),
        ('IR', 'Iran'),
        ('IN', 'India'),
        ('UK', 'United Kingdom'),
    ]
    LANG_CHOICES = [
        ('en', 'English'),
        ('fa', 'Farsi'),
        ('ar', 'Arabic'),
        ('hi', 'Hindi'),
    ]
    BADGE_CHOICES = [
        ('Top Seller', 'Top Seller'),
        ('Fast Closer', 'Fast Closer'),
        ('Master Negotiator', 'Master Negotiator'),
        ('Top Performer', 'Top Performer'),
        ('Rising Star', 'Rising Star'),
        ('Expert', 'Expert'),
        ('Luxury Specialist', 'Luxury Specialist'),
    ]

    GRADIENT_CHOICES = [
    ('from-pink-400 via-purple-500 to-indigo-600', 'Pink → Purple → Indigo'),
    ('from-blue-400 via-indigo-500 to-purple-600', 'Blue → Indigo → Purple'),
    ('from-green-400 via-emerald-500 to-teal-600', 'Green → Emerald → Teal'),
    ('from-yellow-400 via-orange-500 to-red-600', 'Yellow → Orange → Red'),
    ('from-sky-400 via-cyan-500 to-blue-600', 'Sky → Cyan → Blue'),
    ('from-rose-400 via-pink-500 to-fuchsia-600', 'Rose → Pink → Fuchsia'),
    ('from-purple-400 via-violet-500 to-indigo-600', 'Purple → Violet → Indigo'),
    ]


    badge = forms.ChoiceField(
        choices=BADGE_CHOICES,
        required=False,
        label="Agent Badge"
    )

    specialties = forms.MultipleChoiceField(
        choices=SPECIALTIES_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
   
    NATIONALITY_CHOICES = [
            ('https://flagcdn.com/32x24/ae.png', '🇦🇪 United Arab Emirates'),
            ('https://flagcdn.com/32x24/ir.png', '🇮🇷 Iran'),
            ('https://flagcdn.com/32x24/in.png', '🇮🇳 India'),
            ('https://flagcdn.com/32x24/gb.png', '🇬🇧 United Kingdom'),
        ]

    nationality = forms.ChoiceField(
        choices=NATIONALITY_CHOICES,
        required=False,
        label="Nationality"
    )
   
    languages = forms.MultipleChoiceField(
        choices=LANG_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    color_gradient = forms.ChoiceField(
    choices=GRADIENT_CHOICES,
    widget=forms.Select(attrs={'class': 'gradient-preview'}),
    required=False
    )

    totalSales = forms.CharField(
        required=False
    )

    responseTime = forms.CharField(
        required=False
    )

    rating = forms.DecimalField(
        max_digits=2,
        decimal_places=1,
        widget=forms.NumberInput(attrs={
            'type': 'range',
            'min': '1.0',
            'max': '5.0',
            'step': '0.1',
            'oninput': 'document.getElementById("rating_value").value = this.value'
        }),
        required=False
    )

    class Meta:
        model = AgentDetails
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].widget.attrs['style'] = 'width:200px;'
        self.fields['rating'].help_text = mark_safe(
            f'<output id="rating_value" style="margin-left:10px;">'
            f'{self.initial.get("rating", 3.0)}</output>'
        )


@admin.register(AgentDetails)
class AgentDetailsAdmin(admin.ModelAdmin):
    form = AgentDetailsForm
    list_display = ('username', 'name', 'email', 'phone_number', 'gender', 'rating', 'created_at')
    list_filter = ('gender', 'created_at')
    search_fields = ('username', 'name', 'email', 'phone_number')
    ordering = ('-created_at',)

    fieldsets = (
        ('Basic Info', {
            'fields': ('username', 'name', 'gender', 'email', 'phone_number', 'whatsapp_number')
        }),
        ('Media', {
            'fields': ('profile_image_url', 'introduction_video_url', 'color_gradient')
        }),
        ('Professional Info', {
            'fields': ('description', 'specialties', 'nationality', 'languages', 'years_of_experience', 'total_business_deals', 'rank_top_performing', 'rating', 'responseTime', 'badge', 'calendly_url')
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

    # class Media:
    #     js = (
    #         'utils/agent-rating-preview.js',  # Optional for live rating display
    #     )