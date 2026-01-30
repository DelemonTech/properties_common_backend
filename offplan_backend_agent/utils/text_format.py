# yourapp/utils/text_format.py
import re
from django.utils.safestring import mark_safe

def linkify(text):
    # Matches domain names, with or without http(s)
    pattern = re.compile(
        r'((?:https?://|www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)',
        re.IGNORECASE
    )

    def replace(match):
        url = match.group(0)
        href = url
        if not href.startswith(('http://', 'https://')):
            href = 'https://' + href
        return f'<a href="{href}" target="_blank" rel="noopener">{url}</a>'

    # Preserve line breaks by replacing `\n` with `<br>`
    linked = pattern.sub(replace, text)
    linked = linked.replace("\n", "<br>")
    return mark_safe(linked)
