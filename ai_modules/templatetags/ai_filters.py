# ai_modules/templatetags/ai_filters.py
from django import template

register = template.Library()

@register.filter
def split(value, delimiter):
    """
    Divise une chaîne selon un délimiteur.
    Usage: {{ value|split:"," }}
    """
    return value.split(delimiter)