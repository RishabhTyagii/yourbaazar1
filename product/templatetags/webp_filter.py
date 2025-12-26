from django import template

register = template.Library()

@register.filter
def to_webp(url):
    if not url:
        return url
    return (
        url.replace('.jpg', '.webp')
           .replace('.jpeg', '.webp')
           .replace('.png', '.webp')
    )
