# Updated signals.py - Handle HTML content properly in translations
from django.db.models.signals import post_save
from django.dispatch import receiver
from deep_translator import GoogleTranslator
from django.utils.html import strip_tags
import re

from api.models import BlogPost

def clean_html_for_translation(html_content):
    """Extract text from HTML for translation, preserving structure markers"""
    if not html_content:
        return ""
    
    # Replace HTML tags with markers for later reconstruction
    clean_text = strip_tags(html_content)
    return clean_text

def apply_basic_formatting_to_translation(original_html, translated_text):
    """Apply basic formatting from original HTML to translated text"""
    if not original_html or not translated_text:
        return translated_text
    
    # If original had paragraphs, wrap translation in paragraphs
    if '<p>' in original_html:
        # Simple paragraph wrapping - you can enhance this
        paragraphs = translated_text.split('\n\n')
        formatted = ''.join(f'<p>{p.strip()}</p>' for p in paragraphs if p.strip())
        return formatted
    
    return translated_text

@receiver(post_save, sender=BlogPost)
def auto_translate_blog(sender, instance, created, **kwargs):
    # Only run ONCE – on initial creation
    if not created:
        return

    # Fields to translate
    fields_to_translate = ['title', 'excerpt', 'content', 'meta_title', 'meta_description']
    
    for lang, suffix in [('ar', '_ar'), ('fa', '_fa')]:
        for field in fields_to_translate:
            base_val = getattr(instance, field)
            translated_field = f"{field}{suffix}"
            
            if base_val and not getattr(instance, translated_field):
                try:
                    if field in ['excerpt', 'content']:  # HTML fields
                        # Extract text for translation
                        text_to_translate = clean_html_for_translation(base_val)
                        if text_to_translate:
                            translated_text = GoogleTranslator(source='auto', target=lang).translate(text_to_translate)
                            # Apply basic formatting
                            formatted_translation = apply_basic_formatting_to_translation(base_val, translated_text)
                            setattr(instance, translated_field, formatted_translation)
                    else:  # Regular text fields
                        translated = GoogleTranslator(source='auto', target=lang).translate(base_val)
                        setattr(instance, translated_field, translated)
                except Exception as e:
                    print(f"Translation error for {field} to {lang}: {e}")
                    # Set original content as fallback
                    setattr(instance, translated_field, base_val)
    
    # Save once more WITHOUT triggering signal again
    BlogPost.objects.filter(pk=instance.pk).update(
        title_ar=instance.title_ar,
        excerpt_ar=instance.excerpt_ar,
        content_ar=instance.content_ar,
        meta_title_ar=instance.meta_title_ar,
        meta_description_ar=instance.meta_description_ar,
        title_fa=instance.title_fa,
        excerpt_fa=instance.excerpt_fa,
        content_fa=instance.content_fa,
        meta_title_fa=instance.meta_title_fa,
        meta_description_fa=instance.meta_description_fa,
    )