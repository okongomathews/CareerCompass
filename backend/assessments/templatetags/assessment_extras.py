from django import template

register = template.Library()


@register.filter
def split(value, arg=","):
    """Split a string by delimiter. Usage: {{ value|split:", " }}"""
    if value:
        return [item.strip() for item in value.split(arg) if item.strip()]
    return []


@register.filter
def attr(obj, attr_name):
    """Get an attribute from an object by name. Usage: {{ obj|attr:field_name }}"""
    try:
        return getattr(obj, attr_name, None)
    except Exception:
        return None


@register.filter
def getitem(obj, key):
    """Dictionary key lookup. Usage: {{ dict|getitem:key }}"""
    try:
        return obj[key]
    except (KeyError, TypeError):
        return None


@register.filter
def mul(value, arg):
    """Multiply value by arg. Usage: {{ value|mul:100 }}"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def percentage(value, total):
    """Compute value/total as a percentage (0–100). Usage: {{ value|percentage:total }}"""
    try:
        t = float(total)
        if t == 0:
            return 0
        return round((float(value) / t) * 100)
    except (ValueError, TypeError):
        return 0
