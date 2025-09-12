# a simple template filter to access dict by key
# create file: a templatetag, e.g. project/app_name/templatetags/dict_extras.py
# then load it in the template with {% load dict_extras %}

from django import template
register = template.Library()

@register.filter
def get_item(d, k):
    try:
        return d.get(k, 0)
    except Exception:
        return 0
    


