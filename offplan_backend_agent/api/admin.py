# Updated admin.py
from django.contrib import admin
from .models import AgentDetails, BlogPost
from django.utils.html import format_html, strip_tags
from .models import Contact

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

@admin.register(AgentDetails)
class AgentDetailsAdmin(admin.ModelAdmin):
    list_display = ('username', 'name', 'email', 'phone_number', 'gender', 'created_at')
    list_filter = ('gender', 'created_at')
    search_fields = ('username', 'name', 'email', 'phone_number')
    ordering = ('-created_at',)

    fieldsets = (
        ('Basic Info', {
            'fields': ('username', 'name', 'gender', 'email', 'phone_number', 'whatsapp_number')
        }),
        ('Media', {
            'fields': ('profile_image_url', 'introduction_video_url')
        }),
        ('Professional Info', {
            'fields': ('description', 'years_of_experience', 'total_business_deals', 'rank_top_performing')
        }),
        ('Translations', {
            'fields': ('fa_name', 'fa_description', 'ar_name', 'ar_description'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at',)