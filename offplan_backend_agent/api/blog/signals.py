from django.db.models.signals import post_save
from django.dispatch import receiver
from deep_translator import GoogleTranslator

from api.models import BlogPost

@receiver(post_save, sender=BlogPost)
def auto_translate_blog(sender, instance, created, **kwargs):
    # Only run ONCE – on initial creation
    if not created:
        return

    translator = GoogleTranslator()
    for lang, suffix in [('ar', '_ar'), ('fa', '_fa')]:
        for f in ['title','excerpt','content','meta_title','meta_description']:
            base_val = getattr(instance, f)
            translated_field = f"{f}{suffix}"
            if base_val and not getattr(instance, translated_field):
                translated = GoogleTranslator(source='auto', target=lang).translate(base_val)
                setattr(instance, translated_field, translated)
    
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
