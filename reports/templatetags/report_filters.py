from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Accède à un élément du dictionnaire par sa clé"""
    if dictionary is None:
        return None
    return dictionary.get(str(key), None)

@register.filter
def percentage_of(value, total):
    """Calcule le pourcentage d'une valeur par rapport à un total"""
    if total is None or total == 0:
        return 0
    try:
        return (float(value) / float(total)) * 100
    except (ValueError, ZeroDivisionError):
        return 0