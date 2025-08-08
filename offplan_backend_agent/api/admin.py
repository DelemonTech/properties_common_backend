from django.contrib import admin
from .models import BlogPost
from django.utils.html import format_html

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at', 'slug', 'image_tag']
    list_filter = ['author', 'created_at']
    search_fields = ['title', 'excerpt', 'author']
    prepopulated_fields = {"slug": ("title",)}  # Auto-populate slug in admin
    readonly_fields = ['created_at']

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="80" />', obj.image.url)
        return "-"
    image_tag.short_description = 'Image'

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'excerpt', 'content', 'image', 'author')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Arabic Translation', {
            'fields': ('title_ar', 'excerpt_ar', 'content_ar', 'meta_title_ar', 'meta_description_ar'),
            'classes': ('collapse',)
        }),
        ('Farsi Translation', {
            'fields': ('title_fa', 'excerpt_fa', 'content_fa', 'meta_title_fa', 'meta_description_fa'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
# admin.py - Add this
from .models import TestUpload

@admin.register(TestUpload)
class TestUploadAdmin(admin.ModelAdmin):
    list_display = ['title', 'image']