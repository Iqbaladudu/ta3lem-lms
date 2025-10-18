from django import template

register = template.Library()


@register.filter(name='get_class')
def get_class(obj):
    """Return the class name of an object"""
    return obj.__class__.__name__


@register.filter(name='module_id')
def module_id(module):
    """Return the module id"""
    if hasattr(module, 'id'):
        return module.id
    return module


@register.filter(name='index')
def index(indexable, i):
    """Return the item at index i"""
    try:
        return indexable[i]
    except (IndexError, TypeError):
        return None


@register.filter(name='subtract')
def subtract(value, arg):
    """Subtract arg from value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0
