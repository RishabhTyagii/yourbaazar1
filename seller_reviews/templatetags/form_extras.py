from django import template
register = template.Library()

@register.filter
def add_class(field, css):
    return field.as_widget(attrs={**field.field.widget.attrs, "class": (field.field.widget.attrs.get("class", "") + " " + css).strip()})

@register.filter
def attr(field, arg):
    # usage: {{ field|attr:"rows:5" }}
    k, v = arg.split(":", 1)
    return field.as_widget(attrs={**field.field.widget.attrs, k: v})
