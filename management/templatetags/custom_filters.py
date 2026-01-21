from django import template

register = template.Library()
@register.filter
def until(start, end):
    """Returns a range from start to end (exclusive)."""
    return range(start, end)


@register.filter
def dict_get(d, key):
    if not isinstance(d, dict):
        return []
    return d.get(key, [])